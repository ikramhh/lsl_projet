from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import traceback
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User

from .models import Translation, History
from .serializers import TranslationSerializer, HistorySerializer, UserSerializer
from .permissions import IsOwnerOrAdmin, IsAdminUser, IsOwner
from .rabbitmq import send_to_queue
import random


def health_check(request):
    """
    Health check endpoint pour Consul
    """
    return JsonResponse({
        "status": "healthy",
        "service": "api-django",
        "timestamp": timezone.now().isoformat()
    })


def home(request):
    """Home page"""
    return render(request, "ui/home.html")

# Prediction history for consensus (in-memory cache)
# Format: {user_id: [{'label': 'A', 'confidence': 0.9, 'timestamp': 123456}]}
prediction_cache = {}
MAX_CACHE_SIZE = 10  # Keep last 10 predictions per user
CONSENSUS_THRESHOLD = 0.70  # Minimum confidence
MIN_CONSENSUS_COUNT = 3  # Need at least 3 matching predictions

import requests


def calculate_consensus(user_id, new_prediction):
    """
    Calculate consensus from recent predictions to improve stability
    
    Args:
        user_id: User ID
        new_prediction: {'label': 'A', 'confidence': 0.9}
    
    Returns:
        {'label': 'A', 'confidence': 0.85, 'consensus': True/False}
    """
    import time
    
    # Initialize cache for user if not exists
    if user_id not in prediction_cache:
        prediction_cache[user_id] = []
    
    # Add new prediction
    prediction_cache[user_id].append({
        'label': new_prediction['label'],
        'confidence': new_prediction['confidence'],
        'timestamp': time.time()
    })
    
    # Keep only last MAX_CACHE_SIZE predictions
    if len(prediction_cache[user_id]) > MAX_CACHE_SIZE:
        prediction_cache[user_id] = prediction_cache[user_id][-MAX_CACHE_SIZE:]
    
    # Get recent predictions (last 5 seconds)
    current_time = time.time()
    recent_preds = [
        p for p in prediction_cache[user_id]
        if current_time - p['timestamp'] < 5.0
    ]
    
    # Need at least MIN_CONSENSUS_COUNT predictions
    if len(recent_preds) < MIN_CONSENSUS_COUNT:
        return {
            'label': new_prediction['label'],
            'confidence': new_prediction['confidence'],
            'consensus': False,
            'count': len(recent_preds)
        }
    
    # Count occurrences of each label
    label_counts = {}
    label_confidences = {}
    
    for pred in recent_preds:
        label = pred['label']
        if label not in label_counts:
            label_counts[label] = 0
            label_confidences[label] = []
        
        label_counts[label] += 1
        label_confidences[label].append(pred['confidence'])
    
    # Find most common label
    most_common_label = max(label_counts, key=label_counts.get)
    most_common_count = label_counts[most_common_label]
    avg_confidence = sum(label_confidences[most_common_label]) / len(label_confidences[most_common_label])
    
    # Check if we have consensus (at least MIN_CONSENSUS_COUNT matching)
    if most_common_count >= MIN_CONSENSUS_COUNT and avg_confidence >= CONSENSUS_THRESHOLD:
        print(f"🎯 CONSENSUS: {most_common_label} ({most_common_count}/{len(recent_preds)} predictions, {avg_confidence:.1%} confidence)")
        return {
            'label': most_common_label,
            'confidence': avg_confidence,
            'consensus': True,
            'count': most_common_count
        }
    else:
        print(f"⚠️ NO CONSENSUS: Most common is {most_common_label} ({most_common_count}/{len(recent_preds)})")
        return {
            'label': new_prediction['label'],
            'confidence': new_prediction['confidence'],
            'consensus': False,
            'count': most_common_count
        }

# =========================
# HOME API
# =========================
def home(request):
    return JsonResponse({"message": "API LSL fonctionne"})


# =========================
# TRANSLATIONS API
# =========================
@csrf_exempt
def translations(request):

    if request.method == "GET":
        # 🔒 AUTHENTICATION: Try JWT first, then Session
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        authenticated_user = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                authenticated_user = jwt_auth.get_user(validated_token)
            except Exception as e:
                return JsonResponse({"error": "Invalid or expired token", "message": str(e)}, status=401)
        
        # Fallback to session
        if not authenticated_user and hasattr(request, 'user') and request.user.is_authenticated:
            authenticated_user = request.user
        
        if not authenticated_user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # 🔐 AUTHORIZATION: Check if user is admin
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        
        # Admin can see all translations, users see only their own
        if is_admin:
            translations = Translation.objects.all().order_by('-created_at')
            print(f"👑 Admin access: {authenticated_user.username} viewing ALL translations")
        else:
            translations = Translation.objects.filter(user=authenticated_user).order_by('-created_at')
            print(f"👤 User access: {authenticated_user.username} viewing own translations")
        
        return JsonResponse(list(translations.values()), safe=False)

    if request.method == "POST":
        # 🔒 AUTHENTICATION
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        authenticated_user = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                authenticated_user = jwt_auth.get_user(validated_token)
            except:
                pass
        
        if not authenticated_user and hasattr(request, 'user') and request.user.is_authenticated:
            authenticated_user = request.user
        
        if not authenticated_user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        data = json.loads(request.body)
        
        # 🔐 AUTHORIZATION: Users can only create their own translations
        # Admin can create translations for any user
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        
        user_id = data.get("user_id")
        
        if not is_admin and user_id and user_id != authenticated_user.id:
            return JsonResponse({
                "error": "Forbidden",
                "message": "You can only create translations for yourself"
            }, status=403)
        
        # If user_id not provided, use authenticated user
        if not user_id:
            user_id = authenticated_user.id

        t = Translation.objects.create(
            user_id=user_id,
            text=data.get("text"),
            confidence=data.get("confidence", 0.9)
        )

        return JsonResponse({"id": t.id, "text": t.text, "confidence": t.confidence}, status=201)


@csrf_exempt
def translation_detail(request, id):
    # 🔒 AUTHENTICATION
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    authenticated_user = None
    
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            authenticated_user = jwt_auth.get_user(validated_token)
        except:
            pass
    
    if not authenticated_user and hasattr(request, 'user') and request.user.is_authenticated:
        authenticated_user = request.user
    
    if not authenticated_user:
        return JsonResponse({"error": "Authentication required"}, status=401)

    t = get_object_or_404(Translation, id=id)

    if request.method == "GET":
        # 🔐 PERMISSION CHECK: view_translation
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        if not is_admin and not authenticated_user.has_perm('core.view_translation'):
            return JsonResponse({"error": "Forbidden: You don't have permission to view translations"}, status=403)
        
        # Users can only view their own translations
        if not is_admin and t.user != authenticated_user:
            return JsonResponse({"error": "Forbidden: You can only view your own translations"}, status=403)
        
        return JsonResponse({
            "id": t.id,
            "text": t.text,
            "confidence": t.confidence
        })

    if request.method in ["PUT", "PATCH"]:
        # 🔐 PERMISSION CHECK: change_translation
        if not authenticated_user.has_perm('core.change_translation'):
            return JsonResponse({"error": "Forbidden: You don't have permission to modify translations"}, status=403)
        
        # Even if they have permission, only allow modifying their own
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        if not is_admin and t.user != authenticated_user:
            return JsonResponse({"error": "Forbidden: You can only modify your own translations"}, status=403)
        
        data = json.loads(request.body)
        t.text = data.get("text", t.text)
        t.confidence = data.get("confidence", t.confidence)
        t.save()
        return JsonResponse({"message": "updated"})

    if request.method == "DELETE":
        # 🔐 PERMISSION CHECK: delete_translation
        if not authenticated_user.has_perm('core.delete_translation'):
            return JsonResponse({"error": "Forbidden: You don't have permission to delete translations"}, status=403)
        
        # Even if they have permission, only allow deleting their own
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        if not is_admin and t.user != authenticated_user:
            return JsonResponse({"error": "Forbidden: You can only delete your own translations"}, status=403)
        
        t.delete()
        return JsonResponse({"message": "deleted"})


# =========================
# HISTORY API
# =========================
@method_decorator(csrf_exempt, name='dispatch')
class HistoryView(View):

    def get(self, request):
        # 🔒 AUTHENTICATION: Try JWT first, then Session
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        authenticated_user = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                authenticated_user = jwt_auth.get_user(validated_token)
            except Exception as e:
                return JsonResponse({"error": "Invalid or expired token", "message": str(e)}, status=401)
        
        # Fallback to session
        if not authenticated_user and hasattr(request, 'user') and request.user.is_authenticated:
            authenticated_user = request.user
        
        if not authenticated_user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # 🔐 AUTHORIZATION: Check if user is admin
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        
        # Admin can see all history, users see only their own
        if is_admin:
            history = History.objects.all().order_by('-created_at')
            print(f"👑 Admin access: {authenticated_user.username} viewing ALL history")
        else:
            history = History.objects.filter(user=authenticated_user).order_by('-created_at')
            print(f"👤 User access: {authenticated_user.username} viewing own history")
        
        # Return history with all fields
        history_list = list(history.values(
            'id',
            'user_id',
            'translation',
            'confidence',
            'created_at'
        ))
        
        return JsonResponse(history_list, safe=False)

    def post(self, request):
        # 🔒 AUTHENTICATION
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        authenticated_user = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                authenticated_user = jwt_auth.get_user(validated_token)
            except:
                pass
        
        if not authenticated_user and hasattr(request, 'user') and request.user.is_authenticated:
            authenticated_user = request.user
        
        if not authenticated_user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Parse request body
        data = json.loads(request.body)
        
        # 🔐 AUTHORIZATION: Users can only create their own history
        # Admin can create history for any user
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        
        user_id = data.get("user_id")
        
        if not is_admin and user_id and user_id != authenticated_user.id:
            return JsonResponse({
                "error": "Forbidden",
                "message": "You can only create history for yourself"
            }, status=403)
        
        # If user_id not provided, use authenticated user
        if not user_id:
            user_id = authenticated_user.id

        # Create history entry with translation text and confidence
        h = History.objects.create(
            user_id=user_id,
            translation=data.get("translation", ""),
            confidence=data.get("confidence", 0.0)
        )

        return JsonResponse({
            "id": h.id,
            "translation": h.translation,
            "confidence": h.confidence,
            "created_at": h.created_at
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class HistoryDetailView(View):

    def get(self, request, id):
        # 🔒 AUTHENTICATION
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        authenticated_user = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                authenticated_user = jwt_auth.get_user(validated_token)
            except:
                pass
        
        if not authenticated_user and hasattr(request, 'user') and request.user.is_authenticated:
            authenticated_user = request.user
        
        if not authenticated_user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # Get history object
        h = get_object_or_404(History, id=id)
        
        # 🔐 PERMISSION CHECK: view_history
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        if not is_admin and not authenticated_user.has_perm('core.view_history'):
            return JsonResponse({"error": "Forbidden: You don't have permission to view history"}, status=403)
        
        # Users can only view their own history
        if not is_admin and h.user != authenticated_user:
            return JsonResponse({
                "error": "Forbidden",
                "message": "You can only view your own history"
            }, status=403)
        
        return JsonResponse({
            "id": h.id,
            "user_id": h.user_id,
            "translation_id": h.translation_id
        })
    
    def put(self, request, id):
        # 🔒 AUTHENTICATION
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        authenticated_user = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                authenticated_user = jwt_auth.get_user(validated_token)
            except:
                pass
        
        if not authenticated_user and hasattr(request, 'user') and request.user.is_authenticated:
            authenticated_user = request.user
        
        if not authenticated_user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # 🔐 PERMISSION CHECK: change_history (Users should NOT have this)
        if not authenticated_user.has_perm('core.change_history'):
            return JsonResponse({"error": "Forbidden: You don't have permission to modify history"}, status=403)
        
        # Get history object
        h = get_object_or_404(History, id=id)
        
        # Only allow modifying own history
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        if not is_admin and h.user != authenticated_user:
            return JsonResponse({"error": "Forbidden: You can only modify your own history"}, status=403)
        
        return JsonResponse({"error": "History cannot be modified"}, status=405)
    
    def delete(self, request, id):
        # 🔒 AUTHENTICATION
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        authenticated_user = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                authenticated_user = jwt_auth.get_user(validated_token)
            except:
                pass
        
        if not authenticated_user and hasattr(request, 'user') and request.user.is_authenticated:
            authenticated_user = request.user
        
        if not authenticated_user:
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        # 🔐 PERMISSION CHECK: delete_history (Users should NOT have this)
        if not authenticated_user.has_perm('core.delete_history'):
            return JsonResponse({"error": "Forbidden: You don't have permission to delete history"}, status=403)
        
        # Get history object
        h = get_object_or_404(History, id=id)
        
        # Only allow deleting own history
        is_admin = authenticated_user.groups.filter(name='Admin').exists()
        if not is_admin and h.user != authenticated_user:
            return JsonResponse({"error": "Forbidden: You can only delete your own history"}, status=403)
        
        h.delete()
        return JsonResponse({"message": "History deleted"})


# =========================
# DRF VIEWSETS
# =========================
class UserViewSet(viewsets.ModelViewSet):
    """
    User management endpoint
    Admin: Can view/create/update/delete all users
    User: Can only view their own profile
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only admins can create/update/delete users
            return [IsAdminUser()]
        # List and retrieve allowed for authenticated users
        return [IsAuthenticated()]
    
    def get_queryset(self):
        # Admins see all users, regular users see only themselves
        if self.request.user.groups.filter(name='Admin').exists():
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)


class TranslationViewSet(viewsets.ModelViewSet):
    """
    Translation management with role-based access
    Admin: Can access all translations
    User: Can only access their own translations (add/view only)
    """
    serializer_class = TranslationSerializer
    permission_classes = [IsOwnerOrAdmin]
    model_class = Translation  # For permission checking
    
    def get_queryset(self):
        # Admins see all translations, users see only their own
        if self.request.user.groups.filter(name='Admin').exists():
            return Translation.objects.all().order_by('-created_at')
        return Translation.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Automatically set user to authenticated user
        serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        # Check if user has change permission
        if not request.user.has_perm('core.change_translation'):
            return JsonResponse({"error": "Forbidden: You don't have permission to modify translations"}, status=403)
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        # Check if user has delete permission
        if not request.user.has_perm('core.delete_translation'):
            return JsonResponse({"error": "Forbidden: You don't have permission to delete translations"}, status=403)
        return super().destroy(request, *args, **kwargs)


class HistoryViewSet(viewsets.ModelViewSet):
    """
    History management with role-based access
    Admin: Can access all history
    User: Can only access their own history (add/view only)
    """
    serializer_class = HistorySerializer
    permission_classes = [IsOwnerOrAdmin]
    model_class = History  # For permission checking
    
    def get_queryset(self):
        # Admins see all history, users see only their own
        if self.request.user.groups.filter(name='Admin').exists():
            return History.objects.all().order_by('-created_at')
        return History.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Automatically set user to authenticated user
        serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        # Check if user has change permission
        if not request.user.has_perm('core.change_history'):
            return JsonResponse({"error": "Forbidden: You don't have permission to modify history"}, status=403)
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        # Check if user has delete permission
        if not request.user.has_perm('core.delete_history'):
            return JsonResponse({"error": "Forbidden: You don't have permission to delete history"}, status=403)
        return super().destroy(request, *args, **kwargs)


# =========================
# UI (OPTION SIMPLE)
# =========================
def camera_page(request):
    return render(request, "ui/camera.html")

@csrf_exempt
def predict(request):
    """
    Predict endpoint - Accepts JWT OR Session authentication
    For web interface: uses Django session
    For API calls: uses JWT Bearer token
    """
    
    try:

        if request.method != "POST":
            return JsonResponse({"message": "POST only"}, status=405)

        # 🔒 AUTHENTICATION: Try JWT first, then Session
        authenticated_user = None
        
        # Method 1: Check for JWT token in Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token)
                authenticated_user = jwt_auth.get_user(validated_token)
                
                if not authenticated_user or not authenticated_user.is_authenticated:
                    return JsonResponse({
                        "error": "Invalid token",
                        "message": "User not found or inactive"
                    }, status=401)
                    
            except Exception as jwt_error:
                return JsonResponse({
                    "error": "Invalid or expired token",
                    "message": str(jwt_error)
                }, status=401)
        
        # Method 2: Fallback to session authentication (for web interface)
        elif hasattr(request, 'user') and request.user.is_authenticated:
            authenticated_user = request.user
            print(f"✅ Session auth: {authenticated_user.username}")
        
        # No authentication found
        else:
            return JsonResponse({
                "error": "Authentication required",
                "message": "Please login first"
            }, status=401)
        
        print(f"✅ Authenticated user: {authenticated_user.username} (ID: {authenticated_user.id})")
        
        # Parse request body
        try:
            data = json.loads(request.body.decode("utf-8"))
        except:
            data = {}

        image = data.get("image", None)
        
        if not image:
            return JsonResponse({
                "error": "No image provided",
                "message": "Please provide a base64 encoded image"
            }, status=400)

        print(f"📸 Image received, size: {len(image)} bytes")

        # 🐰 SEND TO RABBITMQ QUEUE
        try:
            print(f"🚀 Sending to RabbitMQ queue...")
            
            # Send to queue
            result = send_to_queue(image, metadata={
                'user_id': authenticated_user.id,
                'username': authenticated_user.username
            })
            
            if result['status'] == 'error':
                return JsonResponse({
                    "error": "Failed to queue prediction",
                    "message": result['message']
                }, status=500)
            
            # Return task ID immediately
            return JsonResponse({
                "text": "QUEUED",
                "task_id": result['task_id'],
                "status": "queued",
                "message": "Prediction sent to AI worker",
                "confidence": 0
            })
            
        except Exception as e:
            print(f"❌ RabbitMQ error: {e}")
            import traceback
            print(traceback.format_exc())
            return JsonResponse({
                "error": "Failed to send to queue",
                "message": str(e)
            }, status=500)

    except Exception as e:
        print(f"❌ Predict error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            "error": str(e),
            "trace": traceback.format_exc()
        }, status=500)