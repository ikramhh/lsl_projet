/* ========================================
   Camera JS — Webcam + Predict API
   MediaPipe hand skeleton tracking ENABLED
   ======================================== */

let stream = null;
let hands = null;
let handDetector = null;
let cameraUtils = null;

// MediaPipe is now ENABLED
const MEDIAPIPE_AVAILABLE = true;

console.log('✅ MediaPipe enabled - hand skeleton tracking active');
console.log('✅ Camera, skeleton detection, and prediction will work!');

// Debug panel function
function updateDebugStatus(message, type = 'info') {
  const debugPanel = document.getElementById('mediapipe-debug');
  const debugContent = document.getElementById('debug-content');
  
  if (debugPanel && debugContent) {
    debugPanel.style.display = 'block';
    
    const colors = {
      'info': '#856404',
      'success': '#155724',
      'error': '#721c24',
      'warning': '#856404'
    };
    
    const bgColors = {
      'info': '#fff3cd',
      'success': '#d4edda',
      'error': '#f8d7da',
      'warning': '#fff3cd'
    };
    
    debugContent.innerHTML = `<p style="margin:4px 0;color:${colors[type]};">${message}</p>`;
    debugPanel.style.background = bgColors[type];
    debugPanel.style.borderColor = colors[type];
    
    if (type === 'success') {
      setTimeout(() => {
        debugPanel.style.display = 'none';
      }, 3000);
    }
  }
}

// Detect which fingers are up/down
function detectFingers(landmarks) {
  // Finger landmarks indices
  // Thumb: 1, 2, 3, 4
  // Index: 5, 6, 7, 8
  // Middle: 9, 10, 11, 12
  // Ring: 13, 14, 15, 16
  // Pinky: 17, 18, 19, 20
  
  const fingerTips = [4, 8, 12, 16, 20];
  const fingerPIP = [3, 6, 10, 14, 18]; // PIP joint (middle of finger)
  const fingerMCP = [2, 5, 9, 13, 17]; // MCP joint (base of finger)
  
  const fingerNames = ['thumb', 'index', 'middle', 'ring', 'pinky'];
  const fingerStates = [];
  
  // For each finger, check if it's extended
  for (let i = 0; i < 5; i++) {
    const tip = landmarks[fingerTips[i]];
    const pip = landmarks[fingerPIP[i]];
    const mcp = landmarks[fingerMCP[i]];
    
    let isExtended = false;
    
    if (i === 0) { // Thumb - check horizontal distance
      // Thumb moves differently, check if tip is away from palm
      const wrist = landmarks[0];
      const thumbExtended = Math.abs(tip.x - wrist.x) > Math.abs(pip.x - wrist.x);
      isExtended = thumbExtended;
    } else { // Other fingers - check vertical position
      // Finger is extended if tip is higher (smaller y) than PIP joint
      isExtended = tip.y < pip.y;
    }
    
    fingerStates.push(isExtended);
    
    // Update UI
    const element = document.getElementById(fingerNames[i]);
    if (element) {
      const stateElement = element.querySelector('.finger-state');
      if (stateElement) {
        stateElement.textContent = isExtended ? '↑ UP' : '↓ DOWN';
        stateElement.style.color = isExtended ? '#10b981' : '#ef4444';
      }
    }
  }
  
  // Show finger status container
  const fingerStatus = document.getElementById('finger-status');
  if (fingerStatus) {
    fingerStatus.style.display = 'block';
  }
}

function startCamera() {
  const video = document.getElementById('video');
  const placeholder = document.getElementById('camera-placeholder');
  const cameraContainer = document.getElementById('camera-container');
  const overlay = document.getElementById('overlay');

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert('Camera not supported in this browser. Please use a modern browser like Chrome, Firefox, or Edge.');
    return;
  }

  navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
    .then(s => {
      stream = s;
      
      // Hide placeholder and show camera container
      if (placeholder) placeholder.style.display = 'none';
      if (cameraContainer) cameraContainer.style.display = 'block';
      
      if (video) {
        video.srcObject = stream;
        console.log('✅ Camera started successfully');
        
        // Set overlay canvas size when video metadata is loaded
        video.addEventListener('loadedmetadata', () => {
          if (overlay) {
            overlay.width = video.videoWidth;
            overlay.height = video.videoHeight;
            console.log(`📐 Canvas size set to: ${overlay.width}x${overlay.height}`);
          }
        });
        
        // Initialize MediaPipe hand tracking with retry
        initializeHandTrackingWithRetry(video, overlay);
      }
    })
    .catch(err => {
      console.error('Camera error:', err);
      let message = 'Could not access camera. ';
      
      if (err.name === 'NotAllowedError') {
        message += 'Permission denied. Please allow camera access in your browser settings.';
      } else if (err.name === 'NotFoundError') {
        message += 'No camera found on this device.';
      } else if (err.name === 'NotReadableError') {
        message += 'Camera is being used by another application.';
      } else {
        message += 'Please check browser permissions and try again.';
      }
      
      alert(message);
    });
}

// Initialize MediaPipe with retry logic
function initializeHandTrackingWithRetry(video, overlay, retryCount = 0) {
  const maxRetries = 5;
  const retryDelay = 1000; // 1 second between retries
  
  console.log(`🔍 Checking MediaPipe availability (attempt ${retryCount + 1}/${maxRetries})...`);
  
  // Check if MediaPipe is loaded
  if (typeof Hands === 'undefined' || typeof Camera === 'undefined' || 
      typeof drawConnectors === 'undefined' || typeof drawLandmarks === 'undefined') {
    
    if (retryCount < maxRetries) {
      console.warn(`⚠️ MediaPipe not ready, retrying in ${retryDelay}ms...`);
      updateDebugStatus(`⏳ Loading MediaPipe... (attempt ${retryCount + 1}/${maxRetries})`, 'info');
      
      setTimeout(() => {
        initializeHandTrackingWithRetry(video, overlay, retryCount + 1);
      }, retryDelay);
    } else {
      console.error('❌ MediaPipe failed to load after maximum retries');
      updateDebugStatus('❌ MediaPipe failed to load. Please refresh the page.', 'error');
      alert('MediaPipe failed to load. Please check your internet connection and refresh the page.');
    }
    return;
  }
  
  console.log('✅ MediaPipe fully loaded!');
  updateDebugStatus('✅ MediaPipe loaded, initializing hand tracking...', 'success');
  
  // Initialize with a small delay to ensure everything is ready
  setTimeout(() => {
    initializeHandTracking(video, overlay);
  }, 500);
}

// Initialize MediaPipe hand tracking
function initializeHandTracking(video, overlay) {
  console.log('🔧 Initializing MediaPipe Hands...');
  updateDebugStatus('🔧 Initializing MediaPipe...', 'info');
  
  // Check if MediaPipe is loaded
  if (typeof Hands === 'undefined') {
    console.error('❌ MediaPipe Hands not loaded!');
    console.error('Please check your internet connection and reload the page');
    updateDebugStatus('❌ MediaPipe failed to load! Check internet connection and refresh.', 'error');
    alert('MediaPipe failed to load. Please check your internet connection and refresh the page.');
    return;
  }
  
  if (typeof drawConnectors === 'undefined' || typeof drawLandmarks === 'undefined') {
    console.error('❌ MediaPipe drawing utilities not loaded!');
    updateDebugStatus('❌ Drawing utilities not loaded!', 'error');
    return;
  }
  
  console.log('✅ MediaPipe libraries loaded successfully');
  console.log('Hands:', typeof Hands);
  console.log('drawConnectors:', typeof drawConnectors);
  console.log('drawLandmarks:', typeof drawLandmarks);
  updateDebugStatus('✅ MediaPipe libraries loaded', 'success');
  
  const overlayCtx = overlay.getContext('2d');
  
  try {
    hands = new Hands({
      locateFile: (file) => {
        const url = `https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1675469240/${file}`;
        console.log('📦 Loading MediaPipe file:', file);
        return url;
      }
    });
    
    console.log('✅ Hands object created');
    
    hands.setOptions({
      maxNumHands: 1,
      modelComplexity: 1,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });
    
    console.log('✅ Hands options set');
    updateDebugStatus('✅ Hands configured, starting camera...', 'info');
  
    hands.onResults((results) => {
      // Clear overlay canvas
      overlayCtx.save();
      overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
      
      if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        console.log('✋ Hand detected! Landmarks:', results.multiHandLandmarks[0].length);
        
        for (const landmarks of results.multiHandLandmarks) {
          console.log('🎨 Drawing skeleton...');
          
          // Draw hand skeleton with green lines
          drawConnectors(overlayCtx, landmarks, HAND_CONNECTIONS, {
            color: '#00FF00',
            lineWidth: 4
          });
          
          // Draw red dots on landmarks
          drawLandmarks(overlayCtx, landmarks, {
            color: '#FF0000',
            lineWidth: 2,
            radius: 5
          });
          
          console.log('✅ Skeleton drawn successfully');
          
          // Detect fingers and update UI
          detectFingers(landmarks);
          
          // Trigger auto-prediction when hand is detected
          predictAlphabetFromHand();
        }
        
        // Show status indicator
        const statusDiv = document.querySelector('.camera-container > div:last-child');
        if (statusDiv) {
          statusDiv.innerHTML = '✋ Hand detected!';
          statusDiv.style.background = 'rgba(16, 185, 129, 0.9)';
        }
      } else {
        // Show status indicator
        const statusDiv = document.querySelector('.camera-container > div:last-child');
        if (statusDiv) {
          statusDiv.innerHTML = '🔍 Show your hand to camera';
          statusDiv.style.background = 'rgba(239, 68, 68, 0.9)';
        }
        
        // Hide finger status when no hand
        const fingerStatus = document.getElementById('finger-status');
        if (fingerStatus) {
          fingerStatus.style.display = 'none';
        }
      }
      
      overlayCtx.restore();
    });
    
    console.log('✅ onResults handler set');
  
    // Start camera processing
    if (typeof Camera !== 'undefined') {
      cameraUtils = new Camera(video, {
        onFrame: async () => {
          await hands.send({image: video});
        },
        width: 640,
        height: 480
      });
      
      cameraUtils.start();
      console.log('✅ Camera processing started');
    } else {
      console.error('❌ MediaPipe Camera utility not loaded!');
    }
    
    console.log('✅ Hand detector initialized successfully');
    updateDebugStatus('✅ Hand tracking ready! Show your hand to the camera.', 'success');
    
  } catch (error) {
    console.error('❌ Error initializing hand tracking:', error);
    console.error('Error details:', error.message);
    console.error('Error stack:', error.stack);
    updateDebugStatus('❌ Error: ' + error.message, 'error');
    alert('Error initializing hand tracking: ' + error.message);
  }
}

// Process video frames for hand detection
let lastPredictTime = 0;
const PREDICT_INTERVAL = 2000; // Only predict every 2 seconds

function processFrames() {
  const video = document.getElementById('video');
  
  if (!video || video.paused || video.ended) {
    requestAnimationFrame(processFrames);
    return;
  }
  
  if (hands && video.readyState >= 2) { // HAVE_CURRENT_DATA
    hands.send({image: video}).catch(err => {
      console.warn('Hand detection error:', err);
    });
  }
  
  requestAnimationFrame(processFrames);
}

// Real-time alphabet prediction when hand is detected
let lastHandPrediction = null;
let isPredicting = false; // Prevent multiple simultaneous predictions
let predictionHistory = []; // Store recent predictions for consensus
const MAX_HISTORY = 5; // Keep last 5 predictions
const CONSENSUS_THRESHOLD = 0.75; // Minimum 75% confidence (increased for accuracy)
const MIN_CONSENSUS_COUNT = 3; // Need at least 3 agreeing predictions

function predictAlphabetFromHand() {
  const video = document.getElementById('video');
  const result = document.getElementById('result');
  
  if (!video || !video.srcObject) return;
  
  // Don't predict if already predicting
  if (isPredicting) return;
  
  const now = Date.now();
  if (now - lastPredictTime < PREDICT_INTERVAL) {
    return; // Don't predict too frequently
  }
  
  // Capture current frame at 224x224 for MobileNetV2 model input
  const canvas = document.getElementById('canvas');
  canvas.width = 224;
  canvas.height = 224;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, 224, 224);
  
  const imageData = canvas.toDataURL('image/jpeg', 0.85);
  lastPredictTime = now;
  isPredicting = true;
  
  // Get JWT token
  const headers = { 'Content-Type': 'application/json' };
  const jwtToken = sessionStorage.getItem('jwt_access_token');
  if (jwtToken) {
    headers['Authorization'] = `Bearer ${jwtToken}`;
  }
  
  console.log('🔄 Auto-predicting alphabet...');
  
  // Send to AI service directly (bypasses queue for immediate results)
  fetch('/ai/predict/', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ image: imageData }),
    credentials: 'same-origin'  // Include cookies in request
  })
    .then(response => {
      console.log('📡 Auto-predict response status:', response.status);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      isPredicting = false;
      
      if (data.error) {
        console.error('❌ Prediction error:', data.error);
        return;
      }
      
      // Update result with confidence
      const mainText = data.text || '?';
      const confidence = data.confidence || 0;
      const hasConsensus = data.consensus || false;
      const consensusCount = data.consensus_count || 0;
      
      console.log('✅ Auto-predict result:', mainText, `(${(confidence * 100).toFixed(1)}%)`);
      console.log('🎯 Server consensus:', hasConsensus, `(${consensusCount} predictions)`);
      
      // Add to prediction history
      predictionHistory.push({
        label: mainText,
        confidence: confidence,
        timestamp: Date.now()
      });
      
      // Keep only last MAX_HISTORY predictions
      if (predictionHistory.length > MAX_HISTORY) {
        predictionHistory.shift();
      }
      
      // Calculate consensus
      const consensus = calculateConsensus();
      
      // Only update if confidence is reasonable AND we have consensus
      if (confidence >= CONSENSUS_THRESHOLD && consensus) {
        console.log('🎯 Consensus prediction:', consensus.label, `(${(consensus.confidence * 100).toFixed(1)}%)`);
        
        let confidenceColor = '#ef4444';
        let confidenceLabel = 'Low';
        if (consensus.confidence >= 0.85) {
          confidenceColor = '#10b981';
          confidenceLabel = 'High';
        } else if (consensus.confidence >= 0.75) {
          confidenceColor = '#f59e0b';
          confidenceLabel = 'Medium';
        }
        
        let resultHTML = `<div style="font-size:48px;font-weight:bold;margin-bottom:8px;color:${confidenceColor}">${consensus.label}</div>`;
        resultHTML += `<div style="display:inline-block;padding:6px 16px;border-radius:20px;background:${confidenceColor};color:white;font-size:14px;font-weight:600;">`;
        resultHTML += `${(consensus.confidence * 100).toFixed(0)}% - ${confidenceLabel}`;
        resultHTML += `</div>`;
        resultHTML += `<div style="margin-top:8px;font-size:11px;color:var(--text-secondary);">Based on ${consensus.count} predictions</div>`;
        
        // Show consensus indicator
        if (hasConsensus) {
          resultHTML += `<div style="margin-top:8px;padding:4px 12px;border-radius:12px;background:#10b981;color:white;font-size:12px;font-weight:600;">✅ Stable (${consensusCount} frames)</div>`;
        } else {
          resultHTML += `<div style="margin-top:8px;padding:4px 12px;border-radius:12px;background:#f59e0b;color:white;font-size:12px;font-weight:600;">🔄 Building consensus... (${consensusCount})</div>`;
        }
        
        // Show top-3 if available
        if (data.top3 && data.top3.length > 0) {
          resultHTML += '<div style="margin-top:12px;padding:8px;background:var(--bg);border-radius:6px;">';
          resultHTML += '<div style="font-size:11px;color:var(--text-secondary);margin-bottom:4px;">Top 3:</div>';
          data.top3.forEach((pred, i) => {
            const conf = (pred.confidence * 100).toFixed(0);
            resultHTML += `<div style="font-size:12px;padding:2px 0;"><span style="font-weight:${i===0?'700':'400'}">${i+1}. ${pred.label}</span> <span style="color:var(--text-secondary)">${conf}%</span></div>`;
          });
          resultHTML += '</div>';
        }
        
        if (result) result.innerHTML = resultHTML;
        lastHandPrediction = data;
        
        // Save to history automatically
        saveToHistory(consensus.label, consensus.confidence);
      } else if (confidence >= CONSENSUS_THRESHOLD) {
        console.log('⏳ Waiting for consensus... Current:', predictionHistory.map(p => p.label).join(', '));
        // Show waiting message
        if (result) {
          result.innerHTML = `<div style="font-size:24px;color:#f59e0b;">⏳ Hold sign steady...</div><div style="font-size:12px;color:var(--text-secondary);margin-top:8px;">Need ${MIN_CONSENSUS_COUNT}+ matching predictions</div>`;
        }
      } else {
        console.log('⚠️ Confidence too low:', (confidence * 100).toFixed(1) + '%');
        if (result && result.textContent === '-') {
          result.innerHTML = `<div style="font-size:18px;color:#ef4444;">🔍 Improve conditions</div><div style="font-size:11px;color:var(--text-secondary);margin-top:8px;">Better lighting, plain background, hand closer</div>`;
        }
      }
    })
    .catch(err => {
      isPredicting = false;
      console.warn('❌ Auto-prediction error:', err.message);
    });
}

// Calculate consensus from prediction history
function calculateConsensus() {
  if (predictionHistory.length < MIN_CONSENSUS_COUNT) {
    return null;
  }
  
  // Count occurrences of each label
  const labelCounts = {};
  let totalConfidence = {};
  
  predictionHistory.forEach(pred => {
    if (!labelCounts[pred.label]) {
      labelCounts[pred.label] = 0;
      totalConfidence[pred.label] = 0;
    }
    labelCounts[pred.label]++;
    totalConfidence[pred.label] += pred.confidence;
  });
  
  // Find the most common label
  let bestLabel = null;
  let bestCount = 0;
  let bestAvgConfidence = 0;
  
  for (const label in labelCounts) {
    const count = labelCounts[label];
    const avgConfidence = totalConfidence[label] / count;
    
    if (count > bestCount || (count === bestCount && avgConfidence > bestAvgConfidence)) {
      bestLabel = label;
      bestCount = count;
      bestAvgConfidence = avgConfidence;
    }
  }
  
  // Return consensus if we have enough agreement
  if (bestCount >= MIN_CONSENSUS_COUNT) {
    return {
      label: bestLabel,
      confidence: bestAvgConfidence,
      count: bestCount
    };
  }
  
  return null;
}

function stopCamera() {
  const video = document.getElementById('video');
  const placeholder = document.getElementById('camera-placeholder');
  const cameraContainer = document.getElementById('camera-container');
  const overlay = document.getElementById('overlay');
  const fingerStatus = document.getElementById('finger-status');

  // Stop MediaPipe camera
  if (cameraUtils) {
    cameraUtils.stop();
    cameraUtils = null;
  }
  
  if (stream) {
    stream.getTracks().forEach(t => t.stop());
    stream = null;
  }

  if (video) {
    video.srcObject = null;
  }
  
  if (cameraContainer) {
    cameraContainer.style.display = 'none';
  }
  
  // Clear overlay
  if (overlay) {
    const overlayCtx = overlay.getContext('2d');
    overlayCtx.clearRect(0, 0, overlay.width, overlay.height);
  }
  
  if (fingerStatus) {
    fingerStatus.style.display = 'none';
    // Reset finger states
    ['thumb', 'index', 'middle', 'ring', 'pinky'].forEach(finger => {
      const element = document.getElementById(finger);
      if (element) {
        const stateElement = element.querySelector('.finger-state');
        if (stateElement) {
          stateElement.textContent = '-';
          stateElement.style.color = '';
        }
      }
    });
  }
  
  if (placeholder) placeholder.style.display = 'flex';

  // Reset result
  const result = document.getElementById('result');
  if (result) result.textContent = '-';
  
  // Clear prediction history
  predictionHistory = [];
  console.log('🗑️ Prediction history cleared');
}

function saveToHistory(text, confidence) {
  /**
   * Save prediction to history via API
   */
  
  // Don't save uncertain predictions
  if (text === '?' || text === 'QUEUED' || !text) {
    console.log('⏭️ Skipping save to history (uncertain prediction)');
    return;
  }
  
  console.log('💾 Saving to history:', text, `(${(confidence * 100).toFixed(1)}%)`);
  
  // Get JWT token
  const headers = { 'Content-Type': 'application/json' };
  const jwtToken = sessionStorage.getItem('jwt_access_token');
  if (jwtToken) {
    headers['Authorization'] = `Bearer ${jwtToken}`;
  }
  
  // Save to history endpoint
  fetch('/api/history/', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
      translation: text,
      confidence: confidence
    }),
    credentials: 'same-origin'
  })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      console.log('✅ Saved to history successfully:', data);
    })
    .catch(err => {
      console.warn('⚠️ Failed to save to history:', err.message);
      // Don't show error to user - history save is background operation
    });
}

function captureImage() {
  const video = document.getElementById('video');
  const canvas = document.getElementById('canvas');
  const loader = document.getElementById('loader');
  const result = document.getElementById('result');

  if (!video || !video.srcObject) {
    alert('Please start the camera first.');
    return;
  }

  canvas.width = 224;
  canvas.height = 224;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, 224, 224);

  const imageData = canvas.toDataURL('image/jpeg', 0.9);
  
  console.log('📸 Image captured, size:', imageData.length);

  if (result) result.textContent = 'Analyzing...';
  if (loader) loader.classList.add('active');

  const apiUrl = '/ai/predict/';
  console.log('🚀 Sending to:', apiUrl);

  // Get JWT token from cookie or use session
  const headers = { 'Content-Type': 'application/json' };
  
  // If we have a JWT token in session storage, use it
  const jwtToken = sessionStorage.getItem('jwt_access_token');
  if (jwtToken) {
    headers['Authorization'] = `Bearer ${jwtToken}`;
    console.log('🔑 Using JWT authentication');
  } else {
    console.log('⚠️ No JWT token - using session auth');
  }

  const startTime = Date.now();
  console.log('🚀 Fetch START');
  console.log('📍 Request URL:', apiUrl);
  console.log('📝 Request headers:', headers);
  console.log('📦 Request body size:', JSON.stringify({ image: imageData }).length, 'bytes');
  
  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => {
    console.error('⏰ Request timeout after 30 seconds');
    controller.abort();
  }, 30000); // 30 second timeout
  
  fetch(apiUrl, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ image: imageData }),
    credentials: 'same-origin',  // Include cookies in request
    signal: controller.signal
  })
    .then(response => {
      clearTimeout(timeoutId);
      const duration = Date.now() - startTime;
      console.log(`📡 Response received after ${duration}ms`);
      console.log('📡 Response status:', response.status);
      console.log('📡 Response OK:', response.ok);
      console.log('📡 Response type:', response.type);
      console.log('📡 Response URL:', response.url);
      
      // Get response as text first to debug
      return response.text().then(text => {
        console.log('📄 Response text length:', text.length);
        console.log('📄 Response text preview:', text.substring(0, 200));
        
        if (!response.ok) {
          console.error('❌ Error response:', text);
          throw new Error(`HTTP ${response.status}: ${text}`);
        }
        
        // Parse as JSON
        try {
          const data = JSON.parse(text);
          console.log('✅ JSON parsed successfully');
          return data;
        } catch (parseError) {
          console.error('❌ JSON parse error:', parseError);
          console.error('❌ Invalid JSON:', text);
          throw new Error('Invalid JSON response: ' + parseError.message);
        }
      });
    })
    .then(data => {
      const duration = Date.now() - startTime;
      console.log(`✅ Data received after ${duration}ms`);
      console.log('✅ Response data:', JSON.stringify(data, null, 2));
      
      if (loader) loader.classList.remove('active');
      
      if (result) {
        if (data.error) {
          result.textContent = 'Error: ' + data.error;
          console.error('❌ Backend error:', data);
        } else {
          // Show main prediction
          const mainText = data.text || 'No text detected';
          const confidence = data.confidence;
          const confidencePercent = (confidence * 100).toFixed(1);
          
          console.log('🎯 Prediction:', mainText, `(${confidencePercent}%)`);
          
          // Determine confidence level styling
          let confidenceColor = '#ef4444'; // Red - low
          let confidenceLabel = 'Low';
          if (confidence >= 0.85) {
            confidenceColor = '#10b981'; // Green - high
            confidenceLabel = 'High';
          } else if (confidence >= 0.75) {
            confidenceColor = '#f59e0b'; // Orange - medium
            confidenceLabel = 'Medium';
          } else if (confidence >= 0.60) {
            confidenceColor = '#f97316'; // Dark orange
            confidenceLabel = 'Low';
          }
          
          // Build result text with top-3
          let resultHTML = `<div style="font-size:48px;font-weight:bold;margin-bottom:8px;">${mainText}</div>`;
          resultHTML += `<div style="display:inline-block;padding:6px 16px;border-radius:20px;background:${confidenceColor};color:white;font-size:14px;font-weight:600;">`;
          resultHTML += `${confidencePercent}% - ${confidenceLabel} Confidence`;
          resultHTML += `</div>`;
          
          // Show top-3 if available (from AI service)
          if (data.top3 && data.top3.length > 0) {
            resultHTML += '<div style="margin-top:16px;padding:12px;background:var(--bg);border-radius:8px;">';
            resultHTML += '<div style="margin-bottom:8px;font-weight:600;font-size:13px;color:var(--text-secondary);">Top 3 Predictions:</div>';
            data.top3.forEach((pred, i) => {
              const conf = (pred.confidence * 100).toFixed(1);
              const bgColor = i === 0 ? 'var(--primary)' : 'var(--text-secondary)';
              resultHTML += `<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:13px;">`;
              resultHTML += `<span style="font-weight:${i===0?'700':'400'};color:${bgColor}">${i+1}. ${pred.label}</span>`;
              resultHTML += `<span style="color:var(--text-secondary)">${conf}%</span>`;
              resultHTML += `</div>`;
            });
            resultHTML += '</div>';
          }
          
          // Add tip for low confidence
          if (confidence < 0.75) {
            resultHTML += '<div style="margin-top:12px;padding:8px 12px;background:#fef3c7;border-radius:6px;font-size:12px;color:#92400e;">';
            resultHTML += '💡 Tip: Move hand closer, improve lighting, use plain background';
            resultHTML += '</div>';
          }
          
          result.innerHTML = resultHTML;
          
          // Save to history automatically
          saveToHistory(mainText, confidence);
        }
      }
    })
    .catch(err => {
      clearTimeout(timeoutId);
      console.error('❌ Fetch error:', err);
      console.error('❌ Error name:', err.name);
      console.error('❌ Error message:', err.message);
      
      if (loader) loader.classList.remove('active');
      if (result) {
        if (err.name === 'AbortError') {
          result.textContent = 'Error: Request timed out (30s)';
        } else if (err.message.includes('Failed to fetch')) {
          result.textContent = 'Error: Cannot connect to API';
        } else if (err.message.includes('HTTP 401')) {
          result.textContent = 'Error: Please login first';
        } else if (err.message.includes('HTTP 4')) {
          result.textContent = 'Error: Request failed';
        } else if (err.message.includes('HTTP 5')) {
          result.textContent = 'Error: Server error';
        } else {
          result.textContent = 'Error: ' + err.message;
        }
      }
    });
}
