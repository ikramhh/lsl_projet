from django.shortcuts import render
import json
import os
import traceback
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import torch

# Import ML utilities
from core.ml import load_model, process_base64_image, ASL_CLASSES

# Global model variables
current_model = None
device = 'cpu'
active_model_type = 'mobilenetv2'

def load_ai_model():
    """
    Load the MobileNetV2 AI model
    """
    global current_model, device, active_model_type
    
    try:
        # Determine device
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # Get model path from settings
        model_paths = getattr(settings, 'MODEL_PATHS', {})
        active_model_type = 'mobilenetv2'
        
        print(f"🔧 Loading MobileNetV2 Model on {device}...")
        
        # Get model path
        model_path = model_paths.get(active_model_type)
        
        if not model_path or not os.path.exists(model_path):
            print(f"❌ Model file not found at: {model_path}")
            return False
        
        # Load MobileNetV2 model
        current_model = load_model(model_path, device=device)
        print("✅ MobileNetV2 model loaded successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print(traceback.format_exc())
        return False

# Load model when Django starts
load_ai_model()


@csrf_exempt
def predict(request):
    """
    AI Prediction endpoint
    Accepts base64 encoded image and returns prediction
    """
    
    if request.method == "GET":
        return JsonResponse({
            "message": "AI Service is running",
            "model_loaded": current_model is not None,
            "active_model": "mobilenetv2",
            "device": device,
            "classes": len(ASL_CLASSES)
        })
    
    elif request.method == "POST":
        try:
            # Check if model is loaded
            if current_model is None:
                return JsonResponse({
                    "error": "Model not loaded",
                    "message": "AI model failed to load on startup"
                }, status=500)
            
            # Parse request
            data = json.loads(request.body)
            image_base64 = data.get("image")
            
            if not image_base64:
                return JsonResponse({
                    "error": "No image provided",
                    "message": "Please provide base64 encoded image"
                }, status=400)
            
            # Run prediction with MobileNetV2 model
            result = process_base64_image(current_model, image_base64, device, model_type='mobilenetv2')
            
            # Apply confidence threshold
            confidence = result['confidence']
            label = result['label']
            
            # If confidence is too low, return "uncertain"
            if confidence < 0.70:
                label = "?"
            elif confidence < 0.80:
                # Medium confidence - add warning
                label = label + " (~)"
            
            # Return response with detailed info
            return JsonResponse({
                "text": label,
                "confidence": round(confidence, 4),
                "top3": result['top3'],
                "debug": {
                    "device": device,
                    "image_received": image_base64 is not None,
                    "all_classes": ASL_CLASSES[:5]  # First 5 classes for verification
                }
            })
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            print(traceback.format_exc())
            return JsonResponse({
                "error": "Prediction failed",
                "message": str(e),
                "trace": traceback.format_exc()
            }, status=500)
    
    return JsonResponse({"error": "Method not allowed"}, status=405)