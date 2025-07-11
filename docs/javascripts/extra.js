// ChatAPI Documentation JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Add copy buttons to code blocks
  addCopyButtons();

  // Initialize API endpoint examples
  initializeAPIExamples();

  // Add status badge functionality
  addStatusBadges();
});

function addCopyButtons() {
  const codeBlocks = document.querySelectorAll('pre code');

  codeBlocks.forEach(function(codeBlock) {
    const button = document.createElement('button');
    button.className = 'md-clipboard md-icon';
    button.title = 'Copy to clipboard';
    button.innerHTML = '📋';

    button.addEventListener('click', function() {
      navigator.clipboard.writeText(codeBlock.textContent).then(function() {
        button.innerHTML = '✅';
        setTimeout(function() {
          button.innerHTML = '📋';
        }, 2000);
      });
    });

    const pre = codeBlock.parentNode;
    pre.style.position = 'relative';
    pre.appendChild(button);

    button.style.position = 'absolute';
    button.style.top = '8px';
    button.style.right = '8px';
    button.style.background = 'rgba(255,255,255,0.1)';
    button.style.border = 'none';
    button.style.borderRadius = '4px';
    button.style.padding = '4px 8px';
    button.style.cursor = 'pointer';
  });
}

function initializeAPIExamples() {
  // Auto-fill API examples with base URL
  const baseURL = window.location.origin.includes('localhost')
    ? 'http://localhost:8000'
    : 'https://api.chatapi.dev';

  const codeBlocks = document.querySelectorAll('code');
  codeBlocks.forEach(function(code) {
    if (code.textContent.includes('http://localhost:8000')) {
      code.innerHTML = code.innerHTML.replace(
        /http:\/\/localhost:8000/g,
        `<span class="api-base-url">${baseURL}</span>`
      );
    }
  });
}

function addStatusBadges() {
  // Convert status text to badges
  const statusTexts = document.querySelectorAll('code');
  statusTexts.forEach(function(code) {
    const text = code.textContent.trim();

    if (['pending', 'processing', 'sent', 'failed', 'retrying', 'cancelled'].includes(text)) {
      code.className += ` status-badge ${getStatusClass(text)}`;
    }

    if (text.match(/^[2-5]\d{2}$/)) {
      code.className += ` response-${text[0]}xx`;
    }
  });
}

function getStatusClass(status) {
  const statusMap = {
    'sent': 'success',
    'pending': 'info',
    'processing': 'info',
    'failed': 'error',
    'retrying': 'warning',
    'cancelled': 'warning'
  };

  return statusMap[status] || 'info';
}

// Add interactive API testing
function createAPITester(endpoint, method, data) {
  const container = document.createElement('div');
  container.className = 'api-tester';
  container.innerHTML = `
    <h4>Try this API</h4>
    <div class="api-form">
      <input type="text" placeholder="Your API Key" class="api-key-input">
      <button class="test-button">Test ${method} ${endpoint}</button>
    </div>
    <div class="api-response" style="display: none;">
      <h5>Response:</h5>
      <pre><code class="response-content"></code></pre>
    </div>
  `;

  const button = container.querySelector('.test-button');
  const keyInput = container.querySelector('.api-key-input');
  const responseDiv = container.querySelector('.api-response');
  const responseContent = container.querySelector('.response-content');

  button.addEventListener('click', async function() {
    const apiKey = keyInput.value.trim();
    if (!apiKey) {
      alert('Please enter your API key');
      return;
    }

    button.textContent = 'Testing...';
    button.disabled = true;

    try {
      const baseURL = window.location.origin.includes('localhost')
        ? 'http://localhost:8000'
        : 'https://api.chatapi.dev';

      const response = await fetch(`${baseURL}${endpoint}`, {
        method: method,
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        body: method !== 'GET' ? JSON.stringify(data) : undefined
      });

      const result = await response.json();
      responseContent.textContent = JSON.stringify(result, null, 2);
      responseDiv.style.display = 'block';

    } catch (error) {
      responseContent.textContent = `Error: ${error.message}`;
      responseDiv.style.display = 'block';
    } finally {
      button.textContent = `Test ${method} ${endpoint}`;
      button.disabled = false;
    }
  });

  return container;
}

// Export for global use
window.ChatAPIDocs = {
  addCopyButtons,
  initializeAPIExamples,
  addStatusBadges,
  createAPITester
};
