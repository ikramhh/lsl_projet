/* ========================================
   History JS — Fetch & render translations
   ======================================== */

document.addEventListener('DOMContentLoaded', loadHistory);

function loadHistory() {
  const container = document.getElementById('history');
  if (!container) return;

  fetch('/api/history/', {
    credentials: 'same-origin'  // Include cookies in request
  })
    .then(r => {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(data => {
      const items = Array.isArray(data) ? data : (data.results || []);

      if (items.length === 0) {
        container.innerHTML = `
          <div class="empty-history-state">
            <div class="empty-icon">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
            </div>
            <h3>No translations yet</h3>
            <p>Start using the camera to translate sign language. Your history will appear here.</p>
            <a href="/auth/camera-redirect/" class="btn btn-primary">Start Translating</a>
          </div>`;
        return;
      }

      container.innerHTML = items.map(item => renderCard(item)).join('');
    })
    .catch(err => {
      console.error(err);
      container.innerHTML = `
        <div class="empty-history-state error">
          <div class="empty-icon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <h3>Unable to load history</h3>
          <p>Please try again later.</p>
        </div>`;
    });
}

function renderCard(item) {
  const date = item.created_at
    ? new Date(item.created_at).toLocaleString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit'
      })
    : '-';

  const text = escapeHtml(item.translation || item.text || '-');
  const confidence = item.confidence || 0;
  
  // Color coding based on confidence
  let confidenceClass = 'confidence-low';
  let confidenceIcon = '↓';
  if (confidence >= 0.8) {
    confidenceClass = 'confidence-high';
    confidenceIcon = '✓';
  } else if (confidence >= 0.6) {
    confidenceClass = 'confidence-medium';
    confidenceIcon = '~';
  }
  
  const confidencePercent = (confidence * 100).toFixed(0);
  
  // Get icon based on translation text
  const icon = getTranslationIcon(text);

  return `
    <div class="history-card-item">
      <div class="history-card-header">
        <div class="translation-icon">${icon}</div>
        <div class="history-date">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          ${date}
        </div>
      </div>
      <div class="history-card-body">
        <div class="translation-text">${text}</div>
        <div class="confidence-badge ${confidenceClass}">
          <span class="confidence-icon">${confidenceIcon}</span>
          <span class="confidence-value">${confidencePercent}%</span>
        </div>
      </div>
    </div>
  `;
}

function getTranslationIcon(text) {
  const lowerText = text.toLowerCase();
  
  // Map common words to icons
  const iconMap = {
    'hello': '👋',
    'hi': '👋',
    'thank': '🙏',
    'thanks': '🙏',
    'please': '🤲',
    'yes': '✓',
    'no': '✗',
    'love': '❤️',
    'help': '🆘',
    'water': '💧',
    'food': '🍽️',
    'friend': '👥',
    'family': '👨‍👩‍👧‍👦',
    'good': '👍',
    'bad': '👎',
    'happy': '😊',
    'sad': '😢',
  };
  
  for (const [key, icon] of Object.entries(iconMap)) {
    if (lowerText.includes(key)) {
      return `<span class="icon-emoji">${icon}</span>`;
    }
  }
  
  // Default icon
  return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z"/>
  </svg>`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
