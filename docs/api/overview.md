# API Overview

ChatAPI provides a comprehensive REST API for managing messaging, notifications, and real-time communication in your applications.

## Base URL

=== "Local Development"
`    http://localhost:8000/api/v1
   `

=== "Production"
`    https://api.chatapi.dev/api/v1
   `

## Authentication

All API requests require authentication using API keys in the Authorization header:

```bash
Authorization: Bearer YOUR_API_KEY
```

Learn more about [Authentication](../getting-started/authentication.md).

## API Endpoints Overview

### Client Management

<span class="method-post">POST</span> `/clients` - Register a new client application
<span class="method-get">GET</span> `/clients/me` - Get current client information
<span class="method-put">PUT</span> `/clients/me` - Update client information

### User Management

<span class="method-post">POST</span> `/users` - Create a new user
<span class="method-post">POST</span> `/users/login` - Login user (rotate API key)
<span class="method-get">GET</span> `/users` - List all users
<span class="method-get">GET</span> `/users/{user_id}` - Get user details
<span class="method-put">PUT</span> `/users/{user_id}` - Update user
<span class="method-delete">DELETE</span> `/users/{user_id}` - Delete user

### Room Management

<span class="method-post">POST</span> `/rooms` - Create a new room
<span class="method-get">GET</span> `/rooms` - List user's rooms
<span class="method-get">GET</span> `/rooms/all` - List all client rooms (admin)
<span class="method-post">POST</span> `/rooms/{room_id}/join` - Join a room
<span class="method-post">POST</span> `/rooms/{room_id}/leave` - Leave a room

### Messages

<span class="method-post">POST</span> `/messages` - Send a message
<span class="method-get">GET</span> `/messages` - Get messages from a room
<span class="method-put">PUT</span> `/messages/{message_id}` - Update message
<span class="method-delete">DELETE</span> `/messages/{message_id}` - Delete message

### Notifications

<span class="method-post">POST</span> `/notifications` - Send notification
<span class="method-get">GET</span> `/notifications` - List notifications
<span class="method-get">GET</span> `/notifications/{notification_id}` - Get notification details
<span class="method-get">GET</span> `/notifications/analytics` - Get delivery analytics

### Email Providers

<span class="method-put">PUT</span> `/clients/email-providers` - Configure email provider
<span class="method-get">GET</span> `/clients/email-providers` - Get provider config
<span class="method-post">POST</span> `/clients/email-providers/validate` - Validate provider config

### WebSockets

<span class="method-get">GET</span> `/websocket/open` - Open WebSocket connection

### Webhooks

<span class="method-post">POST</span> `/webhooks` - Create webhook endpoint
<span class="method-get">GET</span> `/webhooks` - List webhook endpoints
<span class="method-put">PUT</span> `/webhooks/{webhook_id}` - Update webhook
<span class="method-delete">DELETE</span> `/webhooks/{webhook_id}` - Delete webhook

## Request/Response Format

### Content Type

All requests must use `application/json` content type:

```bash
Content-Type: application/json
```

### Response Format

All responses follow a consistent structure:

=== "Success Response"
`json
    {
      "data": {
        // Response data here
      },
      "status": "success",
      "timestamp": "2024-01-01T12:00:00Z"
    }
    `

=== "Error Response"
`json
    {
      "detail": "Error description",
      "error_code": "ERROR_CODE",
      "status_code": 400,
      "timestamp": "2024-01-01T12:00:00Z"
    }
    `

## HTTP Status Codes

| Code                                  | Meaning          | Description                             |
| ------------------------------------- | ---------------- | --------------------------------------- |
| <span class="response-2xx">200</span> | OK               | Request successful                      |
| <span class="response-2xx">201</span> | Created          | Resource created successfully           |
| <span class="response-2xx">204</span> | No Content       | Request successful, no content returned |
| <span class="response-4xx">400</span> | Bad Request      | Invalid request data                    |
| <span class="response-4xx">401</span> | Unauthorized     | Invalid or missing API key              |
| <span class="response-4xx">403</span> | Forbidden        | Insufficient permissions                |
| <span class="response-4xx">404</span> | Not Found        | Resource not found                      |
| <span class="response-4xx">422</span> | Validation Error | Request data validation failed          |
| <span class="response-4xx">429</span> | Rate Limited     | Too many requests                       |
| <span class="response-5xx">500</span> | Server Error     | Internal server error                   |

## Rate Limiting

API requests are rate limited to ensure fair usage:

| Endpoint Type  | Limit          | Window     |
| -------------- | -------------- | ---------- |
| Authentication | 100 requests   | 1 hour     |
| Messages       | 1000 requests  | 1 hour     |
| Notifications  | 500 requests   | 1 hour     |
| WebSocket      | 10 connections | Per client |

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Pagination

List endpoints support pagination using query parameters:

```bash
GET /api/v1/messages?page=1&size=20&sort=created_at&order=desc
```

**Parameters:**

- `page` - Page number (default: 1)
- `size` - Items per page (default: 20, max: 100)
- `sort` - Sort field (default: created_at)
- `order` - Sort order: `asc` or `desc` (default: desc)

**Response:**

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

## Filtering

Many endpoints support filtering using query parameters:

```bash
# Filter messages by type
GET /api/v1/messages?message_type=text

# Filter notifications by status
GET /api/v1/notifications?status=sent

# Filter by date range
GET /api/v1/messages?start_date=2024-01-01&end_date=2024-01-31
```

## Common Request Examples

### Create a User

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer ck_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "john_doe",
    "full_name": "John Doe"
  }'
```

### Send a Message

```bash
curl -X POST http://localhost:8000/api/v1/messages \
  -H "Authorization: Bearer sk_user_xyz789..." \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "room-uuid-here",
    "content": "Hello, everyone!",
    "message_type": "text"
  }'
```

### Send a Notification

```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer ck_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "to_email": "user@example.com",
    "subject": "Welcome!",
    "content": "<h1>Welcome to our platform!</h1>"
  }'
```

## Error Handling

### Common Error Codes

| Error Code                 | Description               | Resolution                           |
| -------------------------- | ------------------------- | ------------------------------------ |
| `INVALID_CREDENTIALS`      | Invalid API key           | Check API key format and permissions |
| `VALIDATION_ERROR`         | Request validation failed | Check request data format            |
| `RESOURCE_NOT_FOUND`       | Resource doesn't exist    | Verify resource ID                   |
| `INSUFFICIENT_PERMISSIONS` | Access denied             | Use appropriate API key type         |
| `RATE_LIMIT_EXCEEDED`      | Too many requests         | Wait and retry with backoff          |

### Example Error Response

```json
{
	"detail": "Validation error in request data",
	"error_code": "VALIDATION_ERROR",
	"status_code": 422,
	"errors": [
		{
			"field": "email",
			"message": "Invalid email format"
		},
		{
			"field": "content",
			"message": "Content cannot be empty"
		}
	],
	"timestamp": "2024-01-01T12:00:00Z"
}
```

## SDKs and Libraries

### Official SDKs

=== "JavaScript/TypeScript"
`bash
    npm install @chatapi/sdk
    `
```javascript
import { ChatAPI } from '@chatapi/sdk';

    const client = new ChatAPI('your-api-key');
    ```

=== "Python"
`bash
    pip install chatapi-python
    `
```python
from chatapi import ChatAPI

    client = ChatAPI('your-api-key')
    ```

=== "PHP"
`bash
    composer require chatapi/php-sdk
    `
```php
use ChatAPI\Client;

    $client = new Client('your-api-key');
    ```

### Community SDKs

- **Go**: `github.com/chatapi/go-sdk`
- **Ruby**: `gem install chatapi-ruby`
- **Java**: `com.chatapi:java-sdk`

## Interactive API Explorer

Explore the API interactively using our built-in documentation:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI Spec**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Next Steps

- **[Client Management](clients.md)** - Manage your client application
- **[Messages](messages.md)** - Send and receive messages
- **[Notifications](notifications.md)** - Multi-channel notification delivery
- **[WebSockets](websockets.md)** - Real-time communication
- **[API Reference](../reference/api-spec.md)** - Complete API specification
