from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken
import json

def home(request):
    return render(request, "ui/home.html")

@require_GET
def camera_redirect(request):
    """Redirect to camera page if authenticated, otherwise to login"""
    if request.user.is_authenticated:
        return redirect("/ui/camera/")
    else:
        request.session['next_url'] = '/ui/camera/'
        return redirect("/auth/login/")

@require_GET
def history_redirect(request):
    """Redirect to history page if authenticated, otherwise to login"""
    if request.user.is_authenticated:
        return redirect("/ui/history/")
    else:
        request.session['next_url'] = '/ui/history/'
        return redirect("/auth/login/")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Store tokens in session for web interface
            request.session['jwt_access_token'] = access_token
            request.session['jwt_refresh_token'] = str(refresh)
            
            # Also store in sessionStorage via a script that will be executed
            # This is for API calls from frontend
            
            # Check if there's a stored next URL
            next_url = request.session.pop('next_url', None)
            if next_url:
                return redirect(next_url)
            return redirect("/auth/")  # Redirect to home page by default
        
        # Check if user exists to provide specific error
        from django.contrib.auth.models import User
        try:
            User.objects.get(username=username)
            # User exists but password is wrong
            return render(request, "ui/login.html", {"error": "Incorrect password. Please try again."})
        except User.DoesNotExist:
            # User doesn't exist
            return render(request, "ui/login.html", {"error": "Username not found. Please check your username or create an account."})

    return render(request, "ui/login.html")


def register_view(request):
    if request.method == "POST":
        # création user simple
        from django.contrib.auth.models import User

        User.objects.create_user(
            username=request.POST["username"],
            password=request.POST["password"],
            first_name=request.POST.get("first_name", ""),
            last_name=request.POST.get("last_name", ""),
            email=request.POST.get("email", "")
        )
        return redirect("/auth/login/")

    return render(request, "ui/register.html")


def logout_view(request):
    logout(request)
    return redirect("/auth/")

@csrf_exempt
def api_login(request):
    """
    API endpoint for JWT authentication
    POST /api/login/
    Body: {"username": "user", "password": "pass"}
    Returns: {"access": "token", "refresh": "token", "user": {...}}
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return JsonResponse({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)