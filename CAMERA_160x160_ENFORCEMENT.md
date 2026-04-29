# Camera 224x224 Enforcement

## ✅ Problem Fixed

The camera was capturing images at **640x480** pixels, but the Hybrid CNN-ViT model requires exactly **224x224** pixels as input.

## 🔧 Changes Made

### 1. **[frontend/static/js/camera.js](file:///c:/Users/SAN/Desktop/lsl_project/frontend/static/js/camera.js)**

#### Auto-p Prediction (line 373-378)
```javascript
// BEFORE:
canvas.width = video.videoWidth || 640;
canvas.height = video.videoHeight || 480;

// AFTER:
canvas.width = 224;
canvas.height = 224;
```

#### Manual Capture (line 613-616)
```javascript
// BEFORE:
canvas.width = video.videoWidth || 640;
canvas.height = video.videoHeight || 480;

// AFTER:
canvas.width = 224;
canvas.height = 224;
```

### 2. **[frontend/static/css/style.css](file:///c:/Users/SAN/Desktop/lsl_project/frontend/static/css/style.css)**

Added canvas styling (line 942-946):
```css
/* Hidden canvas for 224x224 capture - matches model input size */
#canvas {
  width: 224px;
  height: 224px;
}
```

### 3. **[frontend/templates/ui/camera.html](file:///c:/Users/SAN/Desktop/lsl_project/frontend/templates/ui/camera.html)**

#### Added Visual Capture Zone Indicator (line 34-39)
- Square dashed border overlay showing the 224x224 capture zone
- Centered in the camera view (60% of video width)
- Label: "📸 224×224 Capture Zone"

#### Updated Help Text (line 96)
```html
<!-- BEFORE: -->
<p>Position your hand in the camera and click...</p>

<!-- AFTER: -->
<p>Position your hand in the square capture zone (224×224px) and click...</p>
```

## 📊 How It Works Now

### Capture Pipeline:
1. **Camera Stream:** 640x480 (for display to user)
2. **Capture Canvas:** 224x224 (for model input)
3. **Backend Preprocessing:** Resizes to 224x224 (confirms size)
4. **Model Input:** 224x224 pixels ✓

### Visual Feedback:
- User sees full camera feed (640x480 display)
- Square overlay shows where to position hand
- Canvas captures exactly 224x224 from the video
- Model receives correctly sized input

## ✅ Verification

The changes ensure:
- ✅ All captures are exactly 224x224 pixels
- ✅ Matches Hybrid CNN-ViT model training size
- ✅ Backend preprocessing confirms 224x224
- ✅ Visual guide helps users position hands correctly
- ✅ Both auto-p prediction and manual capture use 224x224

## 🎯 Testing

1. Start the AI service:
   ```bash
   cd ai_service
   python manage.py runserver 8002
   ```

2. Start the API service:
   ```bash
   cd api_service
   python manage.py runserver 8000
   ```

3. Open camera page and verify:
   - Square capture zone is visible
   - Predictions work correctly
   - Debug images in `ai_service/core/ml/debug_images/` are 224x224

## 📝 Notes

- The **display size** remains 640x480 for good UX
- The **capture size** is now strictly 224x224 for the model
- The canvas `drawImage()` scales the video frame to 224x224 automatically
- Backend still resizes as a safety measure, but input is already correct
