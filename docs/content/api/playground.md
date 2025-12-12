+++
title = "API Playground"
weight = 23
draft = false
+++

# API Playground

Test the ChatAPI endpoints interactively using Swagger UI. This playground allows you to explore the REST API, view request/response formats, and test endpoints with your own data.

**Authentication Required**: Remember to set your `X-API-Key` and `X-User-Id` headers for authenticated requests.

## Interactive API Documentation

<div id="swagger-ui"></div>

<link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.7.2/swagger-ui.css" />
<script src="https://unpkg.com/swagger-ui-dist@5.7.2/swagger-ui-bundle.js"></script>
<script src="https://unpkg.com/swagger-ui-dist@5.7.2/swagger-ui-standalone-preset.js"></script>

<script>
window.onload = function() {
  const ui = SwaggerUIBundle({
    url: '/api/openapi.yaml',
    dom_id: '#swagger-ui',
    deepLinking: true,
    presets: [
      SwaggerUIBundle.presets.apis,
      SwaggerUIStandalonePreset
    ],
    plugins: [
      SwaggerUIBundle.plugins.DownloadUrl
    ],
    layout: "StandaloneLayout",
    requestInterceptor: function(request) {
      // Add authentication headers if available
      const apiKey = localStorage.getItem('chatapi-api-key');
      const userId = localStorage.getItem('chatapi-user-id');

      if (apiKey) {
        request.headers['X-API-Key'] = apiKey;
      }
      if (userId) {
        request.headers['X-User-Id'] = userId;
      }

      return request;
    }
  });

  // Add authentication controls
  const authDiv = document.createElement('div');
  authDiv.innerHTML = `
    <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff;">
      <h4 style="margin-top: 0;">🔐 Authentication</h4>
      <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
        <div>
          <label for="api-key" style="display: block; font-weight: bold; margin-bottom: 5px;">API Key:</label>
          <input type="text" id="api-key" placeholder="your-api-key" style="padding: 5px; border: 1px solid #ddd; border-radius: 3px; width: 200px;">
        </div>
        <div>
          <label for="user-id" style="display: block; font-weight: bold; margin-bottom: 5px;">User ID:</label>
          <input type="text" id="user-id" placeholder="user123" style="padding: 5px; border: 1px solid #ddd; border-radius: 3px; width: 150px;">
        </div>
        <button id="save-auth" style="padding: 5px 15px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">Save</button>
        <button id="clear-auth" style="padding: 5px 15px; background: #6c757d; color: white; border: none; border-radius: 3px; cursor: pointer;">Clear</button>
      </div>
      <p style="margin: 10px 0 0 0; font-size: 14px; color: #666;">
        Set your authentication credentials to test protected endpoints. Credentials are stored locally in your browser.
      </p>
    </div>
  `;

  // Insert auth controls before Swagger UI
  const swaggerContainer = document.getElementById('swagger-ui');
  swaggerContainer.parentNode.insertBefore(authDiv, swaggerContainer);

  // Load saved credentials
  const apiKeyInput = document.getElementById('api-key');
  const userIdInput = document.getElementById('user-id');
  const saveBtn = document.getElementById('save-auth');
  const clearBtn = document.getElementById('clear-auth');

  apiKeyInput.value = localStorage.getItem('chatapi-api-key') || '';
  userIdInput.value = localStorage.getItem('chatapi-user-id') || '';

  saveBtn.onclick = function() {
    localStorage.setItem('chatapi-api-key', apiKeyInput.value);
    localStorage.setItem('chatapi-user-id', userIdInput.value);
    alert('Authentication credentials saved!');
  };

  clearBtn.onclick = function() {
    localStorage.removeItem('chatapi-api-key');
    localStorage.removeItem('chatapi-user-id');
    apiKeyInput.value = '';
    userIdInput.value = '';
    alert('Authentication credentials cleared!');
  };
};
</script>

## Quick Start Guide

### 1. Set Authentication
Enter your API key and user ID in the authentication section above. These will be automatically included in all API requests.

### 2. Explore Endpoints
Browse through the different API endpoints in the Swagger UI. Each endpoint includes:
- **Parameters**: Required and optional parameters
- **Request Body**: Expected JSON structure
- **Responses**: Success and error response formats
- **Try it out**: Interactive testing

### 3. Test Endpoints
Click the "Try it out" button on any endpoint to:
- Modify request parameters
- Execute the request
- View the response
- See request/response headers

## Common Test Scenarios

### Create a Room
1. Go to `POST /rooms`
2. Set request body:
   ```json
   {
     "type": "dm",
     "members": ["alice", "bob"]
   }
   ```
3. Click "Execute"

### Send a Message
1. Go to `POST /rooms/{room_id}/messages`
2. Replace `{room_id}` with actual room ID
3. Set request body:
   ```json
   {
     "content": "Hello from the API playground!"
   }
   ```
4. Click "Execute"

### Check Health
1. Go to `GET /health`
2. Click "Execute" (no authentication required)

## Troubleshooting

### Authentication Errors
- Ensure your API key is valid and has the correct format
- Check that the user ID corresponds to an existing user
- Verify headers are being sent (check browser network tab)

### CORS Issues
- The playground works best when testing against a local ChatAPI instance
- For production APIs, ensure CORS is properly configured

### Rate Limiting
- Monitor the response headers for rate limit information
- Wait for the reset period if you hit rate limits

## WebSocket Testing

For WebSocket testing, you'll need a WebSocket client. Here are some options:

### Browser Console
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8080/ws?api_key=YOUR_KEY&user_id=YOUR_USER');

// Handle messages
ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};

// Send a message
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'send_message',
    room_id: 'your-room-id',
    content: 'Hello via WebSocket!'
  }));
};
```

### Online WebSocket Testers
- [WebSocket King](https://websocketking.com/)
- [PieSocket WebSocket Tester](https://www.piesocket.com/websocket-tester)
- [Browser WebSocket Client](https://chromewebstore.google.com/detail/web-socket-client/cbcmnbkdlkijpgnnbepkopfoabfbngnj)

## Next Steps

- [REST API Reference](/api/rest/) - Complete API documentation
- [WebSocket API Reference](/api/websocket/) - Real-time API documentation
- [Getting Started](/getting-started/) - Installation and setup guide
