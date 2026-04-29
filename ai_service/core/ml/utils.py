"""
Image Preprocessing and Prediction Utilities
MobileNetV2 Model (224x224)
"""

import torch
import base64
import numpy as np
import os
from PIL import Image
import io
from torchvision import transforms
from .model import MobileNetV2ASL
from .classes import ASL_CLASSES

# Image preprocessing pipeline for Advanced Hybrid Model
# IMPORTANT: This must match exactly what was used during training

# Advanced Hybrid Model preprocessing (224x224) - ImageNet normalization
preprocess_advanced = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                        std=[0.229, 0.224, 0.225])
])

# Debug mode - save images for analysis
DEBUG_SAVE_IMAGES = True  # Enabled to diagnose prediction errors
DEBUG_IMAGE_DIR = os.path.join(os.path.dirname(__file__), 'debug_images')
if DEBUG_SAVE_IMAGES and not os.path.exists(DEBUG_IMAGE_DIR):
    os.makedirs(DEBUG_IMAGE_DIR)


def decode_base64_image(base64_string):
    """
    Decode base64 image string to PIL Image
    
    Args:
        base64_string: Base64 encoded image (with or without data URI prefix)
    
    Returns:
        PIL.Image in RGB mode
    """
    # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    # Decode base64
    image_bytes = base64.b64decode(base64_string)
    
    # Convert to PIL Image
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    
    # Debug: Save original image
    if DEBUG_SAVE_IMAGES:
        import time
        timestamp = int(time.time() * 1000)
        image.save(os.path.join(DEBUG_IMAGE_DIR, f'original_{timestamp}.jpg'))
        print(f"💾 Saved original image: original_{timestamp}.jpg")
    
    return image


def crop_hand_from_image(pil_image, margin=0.2):
    """
    Crop image to focus on center region (where hand typically is)
    This simulates having a clean, centered hand like training data
    
    Args:
        pil_image: PIL.Image object
        margin: How much margin to keep (0.2 = keep center 60%)
    
    Returns:
        Cropped PIL.Image
    """
    width, height = pil_image.size
    
    # Calculate crop box (center region)
    left = int(width * margin)
    top = int(height * margin)
    right = int(width * (1 - margin))
    bottom = int(height * (1 - margin))
    
    # Crop to center region
    cropped = pil_image.crop((left, top, right, bottom))
    
    # Resize back to original size to maintain model input expectations
    cropped = cropped.resize((width, height), Image.Resampling.LANCZOS)
    
    return cropped


def enhance_image_for_model(pil_image):
    """
    Enhance image to better match training conditions
    
    Args:
        pil_image: PIL.Image object
    
    Returns:
        Enhanced PIL.Image
    """
    from PIL import ImageEnhance
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(pil_image)
    pil_image = enhancer.enhance(1.3)  # 30% more contrast
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(pil_image)
    pil_image = enhancer.enhance(1.5)  # 50% more sharpness
    
    # Adjust brightness if needed
    enhancer = ImageEnhance.Brightness(pil_image)
    pil_image = enhancer.enhance(1.1)  # 10% brighter
    
    return pil_image


def preprocess_image(pil_image, crop_hand=True):
    """
    Apply preprocessing transforms to PIL Image for Advanced Hybrid Model
    
    Args:
        pil_image: PIL.Image object
        crop_hand: Whether to crop to center region (default True)
    
    Returns:
        torch.Tensor of shape (1, 3, 224, 224)
    """
    # Log image info for debugging
    print(f"📊 Input image size: {pil_image.size}, mode: {pil_image.mode}")
    print(f"🎯 Model type: advanced_hybrid, target size: (224, 224)")
    
    # Enhance image to match training conditions
    pil_image = enhance_image_for_model(pil_image)
    print("🎨 Enhanced image (contrast + sharpness + brightness)")
    
    # Crop to hand region (reduces background noise)
    if crop_hand:
        pil_image = crop_hand_from_image(pil_image, margin=0.10)
        print("✂️ Cropped image to focus on center (hand region)")
    
    # Apply Advanced Hybrid Model transforms
    tensor = preprocess_advanced(pil_image)
    
    # Debug: Save preprocessed image
    if DEBUG_SAVE_IMAGES:
        import time
        import numpy as np
        timestamp = int(time.time() * 1000)
        
        # Convert tensor back to image for visualization
        img_tensor = tensor.squeeze()
        img_tensor = img_tensor * 0.5 + 0.5  # Unnormalize
        img_tensor = torch.clamp(img_tensor, 0, 1)
        img_pil = transforms.ToPILImage()(img_tensor)
        img_pil.save(os.path.join(DEBUG_IMAGE_DIR, f'preprocessed_{timestamp}.jpg'))
        print(f"💾 Saved preprocessed image: preprocessed_{timestamp}.jpg")
    
    # Add batch dimension
    tensor = tensor.unsqueeze(0)
    
    return tensor


def load_model(model_path, device='cpu'):
    """
    Load trained MobileNetV2 model from .pth file
    Uses MobileNetV2ASL from model.py
    
    Args:
        model_path: Path to .pth file
        device: 'cpu' or 'cuda'
    
    Returns:
        Loaded model in eval mode
    """
    # Initialize model
    num_classes = len(ASL_CLASSES)
    
    # Load state dict first to check format
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    
    # Handle checkpoint format (may contain additional metadata)
    if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
        state_dict = checkpoint['model_state_dict']
        print(f"📦 Loaded checkpoint with metadata")
    else:
        state_dict = checkpoint
        print(f"📦 Loaded raw state dict")
    
    # Create MobileNetV2 model
    model = MobileNetV2ASL(num_classes=num_classes)
    print(f"📦 Using MobileNetV2: Pre-trained features + Custom classifier (1280->256->29)")
    
    # Fix state_dict keys if needed
    # Check if keys need "model." prefix
    first_key = list(state_dict.keys())[0]
    if not first_key.startswith('model.'):
        print(f"🔧 Fixing state_dict keys (adding 'model.' prefix)")
        new_state_dict = {}
        for key, value in state_dict.items():
            if not key.startswith('model.'):
                new_state_dict[f'model.{key}'] = value
            else:
                new_state_dict[key] = value
        state_dict = new_state_dict
    
    # Load state dict with strict=False to handle minor mismatches
    model.load_state_dict(state_dict, strict=False)
    
    # Set to evaluation mode
    model.eval()
    
    # Move to device
    model = model.to(device)
    
    print(f"✅ MobileNetV2 Model loaded successfully from {model_path}")
    print(f"📊 Number of classes: {num_classes}")
    print(f"🖥️  Device: {device}")
    
    return model


def predict_image(model, image_tensor, device='cpu'):
    """
    Perform prediction on preprocessed image
    
    Args:
        model: Loaded MobileNetV2 Model
        image_tensor: Preprocessed tensor (1, 3, 224, 224)
        device: 'cpu' or 'cuda'
    
    Returns:
        dict with 'label', 'confidence', and 'probabilities'
    """
    # Move to device
    image_tensor = image_tensor.to(device)
    
    # Run inference (no gradient computation)
    with torch.no_grad():
        outputs = model(image_tensor)
        
        # Apply softmax to get probabilities
        probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
        
        # Get predicted class
        confidence, predicted_idx = torch.max(probabilities, 0)
        
        # Convert to Python types
        predicted_class = ASL_CLASSES[predicted_idx.item()]
        confidence_score = confidence.item()
        
        # Get top-5 predictions for better debugging
        top5_confidences, top5_indices = torch.topk(probabilities, 5)
        top5_predictions = [
            {
                'label': ASL_CLASSES[idx.item()],
                'confidence': conf.item()
            }
            for idx, conf in zip(top5_indices, top5_confidences)
        ]
        
        # Log prediction details
        print(f"🎯 Prediction: {predicted_class} ({confidence_score*100:.1f}%)")
        top5_str = ", ".join([f"{p['label']}({p['confidence']*100:.1f}%)" for p in top5_predictions])
        print(f"📊 Top 5: {top5_str}")
        
        # Check if "nothing" or "delete" is predicted with high confidence
        # This usually means no clear hand sign is visible
        if predicted_class in ['nothing', 'delete'] and confidence_score > 0.5:
            print("⚠️ WARNING: Model predicts 'nothing' or 'delete' - hand sign may not be clear!")
            print("💡 TIP: Make sure hand is visible, centered, and sign is clear")
    
    return {
        'label': predicted_class,
        'confidence': confidence_score,
        'top3': top5_predictions[:3],  # Return top 3 for API
        'top5': top5_predictions,  # Return top 5 for debugging
        'all_probabilities': probabilities.cpu().numpy().tolist()
    }


def process_base64_image(model, base64_string, device='cpu', model_type='mobilenetv2'):
    """
    Complete pipeline: base64 → prediction
    
    Args:
        model: Loaded MobileNetV2 Model
        base64_string: Base64 encoded image
        device: 'cpu' or 'cuda'
        model_type: Model type (default 'mobilenetv2')
    
    Returns:
        Prediction result dict
    """
    # Step 1: Decode base64 to image
    image = decode_base64_image(base64_string)
    
    # Step 2: Preprocess (with hand cropping enabled)
    image_tensor = preprocess_image(image, crop_hand=True)
    
    # Step 3: Predict
    result = predict_image(model, image_tensor, device)
    
    return result
