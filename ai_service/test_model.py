"""
Test script to verify Advanced Hybrid Model loads and works correctly
Run this BEFORE starting Django server
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_service.settings')
django.setup()

from core.ml import load_model, process_base64_image
import torch
from PIL import Image
import base64
import io

print("=" * 60)
print("TESTING ADVANCED HYBRID MODEL LOADING")
print("=" * 60)

# Test 1: Load model
print("\n1. Loading model...")
try:
    from django.conf import settings
    model_path = settings.MODEL_PATHS['advanced_hybrid']
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = load_model(model_path, device=device)
    print("✅ Model loaded successfully!")
    print(f"   Device: {device}")
    print(f"   Model type: Advanced Hybrid CNN + ViT")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Create a dummy image and test prediction
print("\n2. Testing prediction with dummy image...")
try:
    # Create a simple 224x224 RGB image
    dummy_image = Image.new('RGB', (224, 224), color='white')
    
    # Convert to base64
    buffer = io.BytesIO()
    dummy_image.save(buffer, format='JPEG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Test prediction
    result = process_base64_image(model, img_base64, device, model_type='advanced_hybrid')
    
    print("✅ Prediction successful!")
    print(f"   Predicted: {result['label']}")
    print(f"   Confidence: {result['confidence']:.4f}")
    print(f"   Top 3:")
    for i, pred in enumerate(result['top3'], 1):
        print(f"      {i}. {pred['label']} ({pred['confidence']:.4f})")
        
except Exception as e:
    print(f"❌ Prediction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED! ✅")
print("=" * 60)
print("\nYou can now start the Django server:")
print("python manage.py runserver 8002")
