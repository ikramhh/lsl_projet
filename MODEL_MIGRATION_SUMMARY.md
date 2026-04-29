# Model Migration Summary

## ✅ Changes Completed

### **Model Replacement**
- **Removed:** Hybrid CNN-ViT model (`hybrid_vit_cnn.pth`)
- **Active:** MobileNetV2 model (`asl_model.pth`) from IKRAM

### **Files Modified**

1. **[ai_service/core/views.py](file:///c:/Users/SAN/Desktop/lsl_project/ai_service/core/views.py)**
   - Removed model switching functionality
   - Simplified to only load MobileNetV2 model
   - Updated to use `load_mobilenet_model` only

2. **[ai_service/ai_service/settings.py](file:///c:/Users/SAN/Desktop/lsl_project/ai_service/ai_service/settings.py)**
   - Removed hybrid_vit configuration
   - Set ACTIVE_MODEL to 'mobilenet' only

3. **[ai_service/core/ml/model.py](file:///c:/Users/SAN/Desktop/lsl_project/ai_service/core/ml/model.py)**
   - Removed HybridCNNViT class definition
   - Simplified to module placeholder

4. **[ai_service/core/ml/utils.py](file:///c:/Users/SAN/Desktop/lsl_project/ai_service/core/ml/utils.py)**
   - Removed hybrid_vit preprocessing pipeline
   - Updated to use only MobileNetV2 preprocessing (224x224)
   - Simplified load_model to wrap load_mobilenet_model

5. **[ai_service/core/ml/__init__.py](file:///c:/Users/SAN/Desktop/lsl_project/ai_service/core/ml/__init__.py)**
   - Removed HybridCNNViT import

### **Files Deleted**
- `ai_service/core/ml/hybrid_vit_cnn.pth` (Hybrid model - 22.4MB)
- `ai_service/test_both_models.py` (no longer needed)

### **Model Architecture**

The active MobileNetV2 model:
- **Architecture:** MobileNetV2 (lightweight, efficient)
- **Input Size:** 224x224 pixels
- **Preprocessing:** ImageNet normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
- **Model File:** `IKRAM/saved_model/asl_model.pth`
- **Classes:** 29 ASL signs

### **Verification**

✅ MobileNetV2 model loads successfully on startup
✅ Django system check passes with no issues
✅ AI service responds on `http://localhost:8002/predict/`
✅ Returns correct response: 29 classes, model loaded

### **Current Status**

The AI service is now running with only the MobileNetV2 model from IKRAM. The hybrid_vit_cnn model has been completely removed from the codebase.

### **How to Test**

```bash
# Start the AI service
cd ai_service
python manage.py runserver 8002

# Test the endpoint (PowerShell)
curl http://localhost:8002/predict/

# Or run the test script
python test_model.py
```

### **Notes**

- The model switching API endpoint (/switch_model/) has been removed
- Only MobileNetV2 preprocessing is now active (224x224 with ImageNet norms)
- All 29 ASL classes are properly defined in `core/ml/classes.py`
- The rule-based classifier is still available if needed: `core/ml/rule_based_classifier.py`
