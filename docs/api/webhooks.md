# Webhooks API

Webhooks allow you to receive real-time HTTP notifications when events occur in ChatAPI. Set up webhook endpoints to integrate ChatAPI with external services and automate workflows.

## Overview

Webhooks in ChatAPI:

- **Real-time event notifications** delivered via HTTP POST
- **Flexible event filtering** by type, room, or custom criteria
- **Reliable delivery** with automatic retries and exponential backoff
- **Signature verification** for security and authenticity
- **Custom headers and authentication** for external services
- **Delivery tracking** and failure monitoring

## Webhook Model

```json
{
  "id": "uuid",
  "client_id": "uuid",
  "url": "string",
  "events": ["message.created", "room.joined"],
  "secret": "string",
  "is_active": true,
  "custom_headers": {...},
  "room_filters": ["uuid1", "uuid2"],
  "meta": {...},
  "last_delivery_at": "2024-01-01T12:00:00Z",
  "failure_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## API Endpoints

### Create Webhook

Creates a new webhook endpoint to receive event notifications.

```http
POST /api/v1/webhooks/
```

**Request Body:**

```json
{
	"url": "https://api.yourservice.com/webhooks/chatapi",
	"events": ["message.created", "message.updated", "room.joined", "room.left"],
	"secret": "your-webhook-secret-key",
	"custom_headers": {
		"Authorization": "Bearer your-api-token",
		"X-Service-ID": "chatapi-integration"
	},
	"room_filters": ["550e8400-e29b-41d4-a716-446655440001"],
	"meta": {
		"description": "Integration with customer support system",
		"contact": "dev@yourservice.com",
		"version": "1.0"
	}
}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440004",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"url": "https://api.yourservice.com/webhooks/chatapi",
		"events": [
			"message.created",
			"message.updated",
			"room.joined",
			"room.left"
		],
		"secret": "your-webhook-secret-key",
		"is_active": true,
		"custom_headers": {
			"Authorization": "Bearer your-api-token",
			"X-Service-ID": "chatapi-integration"
		},
		"room_filters": ["550e8400-e29b-41d4-a716-446655440001"],
		"meta": {
			"description": "Integration with customer support system",
			"contact": "dev@yourservice.com",
			"version": "1.0"
		},
		"last_delivery_at": null,
		"failure_count": 0,
		"created_at": "2024-01-01T12:00:00Z",
		"updated_at": "2024-01-01T12:00:00Z"
	},
	"status": "success"
}
```

### List Webhooks

Retrieves all webhooks for the authenticated client.

```http
GET /api/v1/webhooks/
```

**Query Parameters:**

- `skip` (int): Number of webhooks to skip (default: 0)
- `limit` (int): Maximum webhooks to return (default: 50, max: 100)
- `is_active` (bool): Filter by active status
- `event` (string): Filter by specific event type
- `sort` (string): Sort order (`created_at`, `-created_at`, `last_delivery_at`)

**Response:**

```json
{
	"data": [
		{
			"id": "550e8400-e29b-41d4-a716-446655440004",
			"client_id": "550e8400-e29b-41d4-a716-446655440000",
			"url": "https://api.yourservice.com/webhooks/chatapi",
			"events": ["message.created", "room.joined"],
			"is_active": true,
			"last_delivery_at": "2024-01-01T12:30:00Z",
			"failure_count": 0,
			"created_at": "2024-01-01T12:00:00Z",
			"updated_at": "2024-01-01T12:00:00Z"
		}
	],
	"pagination": {
		"skip": 0,
		"limit": 50,
		"total": 1,
		"has_more": false
	},
	"status": "success"
}
```

### Get Webhook Details

Retrieves detailed information about a specific webhook.

```http
GET /api/v1/webhooks/{webhook_id}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440004",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"url": "https://api.yourservice.com/webhooks/chatapi",
		"events": ["message.created", "room.joined"],
		"secret": "your-webhook-secret-key",
		"is_active": true,
		"custom_headers": {
			"Authorization": "Bearer your-api-token",
			"X-Service-ID": "chatapi-integration"
		},
		"room_filters": ["550e8400-e29b-41d4-a716-446655440001"],
		"meta": {
			"description": "Integration with customer support system",
			"delivery_stats": {
				"total_deliveries": 150,
				"successful_deliveries": 147,
				"failed_deliveries": 3,
				"average_response_time": 245
			}
		},
		"last_delivery_at": "2024-01-01T12:30:00Z",
		"failure_count": 0,
		"created_at": "2024-01-01T12:00:00Z",
		"updated_at": "2024-01-01T12:00:00Z"
	},
	"status": "success"
}
```

### Update Webhook

Updates webhook configuration.

```http
PUT /api/v1/webhooks/{webhook_id}
```

**Request Body:**

```json
{
	"url": "https://api.yourservice.com/webhooks/chatapi-v2",
	"events": [
		"message.created",
		"message.updated",
		"message.deleted",
		"room.joined"
	],
	"custom_headers": {
		"Authorization": "Bearer updated-api-token",
		"X-Service-ID": "chatapi-integration-v2"
	},
	"meta": {
		"description": "Updated integration with enhanced features",
		"version": "2.0"
	}
}
```

### Delete Webhook

Permanently deletes a webhook endpoint.

```http
DELETE /api/v1/webhooks/{webhook_id}
```

**Response:**

```json
{
	"message": "Webhook deleted successfully",
	"status": "success"
}
```

### Activate/Deactivate Webhook

Enable or disable webhook delivery without deleting the configuration.

```http
POST /api/v1/webhooks/{webhook_id}/activate
POST /api/v1/webhooks/{webhook_id}/deactivate
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440004",
		"is_active": false,
		"updated_at": "2024-01-01T12:05:00Z"
	},
	"message": "Webhook deactivated successfully",
	"status": "success"
}
```

## Webhook Events

### Available Events

| Event                 | Description                         |
| --------------------- | ----------------------------------- |
| `message.created`     | New message sent to a room          |
| `message.updated`     | Message content or metadata updated |
| `message.deleted`     | Message marked as deleted           |
| `message.restored`    | Deleted message restored            |
| `room.created`        | New room created                    |
| `room.updated`        | Room information updated            |
| `room.deleted`        | Room deleted                        |
| `room.joined`         | User joined a room                  |
| `room.left`           | User left a room                    |
| `client.updated`      | Client information updated          |
| `notification.sent`   | Notification delivered successfully |
| `notification.failed` | Notification delivery failed        |

### Event Payload Structure

All webhook events follow this structure:

```json
{
	"id": "evt_550e8400-e29b-41d4-a716-446655440005",
	"event": "message.created",
	"created_at": "2024-01-01T12:00:00Z",
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440002",
		"room_id": "550e8400-e29b-41d4-a716-446655440001",
		"sender_id": "user_123",
		"sender_name": "John Doe",
		"content": "Hello everyone!",
		"message_type": "text",
		"created_at": "2024-01-01T12:00:00Z"
	},
	"meta": {
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"webhook_id": "550e8400-e29b-41d4-a716-446655440004",
		"delivery_id": "del_123456789",
		"attempt": 1
	}
}
```

### Example Event Payloads

#### Message Created

```json
{
	"id": "evt_message_created_123",
	"event": "message.created",
	"created_at": "2024-01-01T12:00:00Z",
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440002",
		"room_id": "550e8400-e29b-41d4-a716-446655440001",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"sender_id": "user_123",
		"sender_name": "John Doe",
		"content": "Hello everyone! 👋",
		"message_type": "text",
		"meta": {
			"mentions": ["user_456"],
			"priority": "normal"
		},
		"created_at": "2024-01-01T12:00:00Z"
	}
}
```

#### Room Joined

```json
{
	"id": "evt_room_joined_456",
	"event": "room.joined",
	"created_at": "2024-01-01T12:00:00Z",
	"data": {
		"room_id": "550e8400-e29b-41d4-a716-446655440001",
		"user_id": "user_789",
		"user_name": "Jane Smith",
		"joined_at": "2024-01-01T12:00:00Z",
		"meta": {
			"role": "member",
			"invited_by": "user_123"
		}
	}
}
```

#### Notification Failed

```json
{
	"id": "evt_notification_failed_789",
	"event": "notification.failed",
	"created_at": "2024-01-01T12:05:00Z",
	"data": {
		"notification_id": "550e8400-e29b-41d4-a716-446655440003",
		"type": "email",
		"recipients": ["user@example.com"],
		"failure_reason": "SMTP connection timeout",
		"attempt_count": 3,
		"will_retry": false
	}
}
```

## Security

### Signature Verification

ChatAPI signs webhook payloads using HMAC-SHA256. Verify signatures to ensure authenticity.

**Signature Header:**

```
X-ChatAPI-Signature: sha256=a8b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b4
```

**Verification (Python):**

```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )

# Usage
webhook_secret = "your-webhook-secret-key"
payload = request.body  # Raw request body
signature = request.headers.get("X-ChatAPI-Signature")

if verify_signature(payload, signature, webhook_secret):
    # Process webhook
    pass
else:
    # Invalid signature
    return 401
```

### Custom Headers

Add authentication headers for your webhook endpoint:

```json
{
	"custom_headers": {
		"Authorization": "Bearer your-api-token",
		"X-API-Key": "your-service-api-key",
		"X-Service-Version": "1.0",
		"User-Agent": "ChatAPI-Webhook/1.0"
	}
}
```

## Delivery Reliability

### Retry Policy

Failed webhook deliveries are automatically retried with exponential backoff:

- **Attempt 1**: Immediate
- **Attempt 2**: 30 seconds
- **Attempt 3**: 2 minutes
- **Attempt 4**: 8 minutes
- **Attempt 5**: 32 minutes
- **Final**: Webhook disabled after 5 failures

### Success Criteria

A webhook delivery is considered successful if:

- HTTP status code is 200-299
- Response received within 30 seconds
- No connection errors

### Failure Handling

Webhooks are automatically disabled after 5 consecutive failures. You can:

- **Monitor failure counts** via the API
- **Receive notifications** about webhook failures
- **Manually reactivate** after fixing issues
- **View delivery logs** for troubleshooting

### Test Webhook

Test webhook delivery with a sample event:

```http
POST /api/v1/webhooks/{webhook_id}/test
```

**Request Body:**

```json
{
	"event": "message.created",
	"test_data": {
		"sender_name": "Test User",
		"content": "This is a test message"
	}
}
```

**Response:**

```json
{
	"data": {
		"delivered": true,
		"response_status": 200,
		"response_time": 245,
		"response_body": "OK"
	},
	"message": "Test webhook delivered successfully",
	"status": "success"
}
```

## Filtering Events

### Event Filtering

Subscribe only to specific events:

```json
{
	"events": ["message.created", "room.joined"]
}
```

### Room Filtering

Receive events only from specific rooms:

```json
{
	"room_filters": [
		"550e8400-e29b-41d4-a716-446655440001",
		"550e8400-e29b-41d4-a716-446655440002"
	]
}
```

### Advanced Filtering

Use metadata for complex filtering logic in your webhook handler:

```json
{
	"meta": {
		"filters": {
			"message_types": ["text", "image"],
			"priority": ["high", "urgent"],
			"sender_roles": ["admin", "moderator"]
		}
	}
}
```

## Webhook Analytics

Get delivery statistics and performance metrics:

```http
GET /api/v1/webhooks/{webhook_id}/analytics
```

**Query Parameters:**

- `date_from` (date): Start date for analytics
- `date_to` (date): End date for analytics
- `event` (string): Filter by event type

**Response:**

```json
{
	"data": {
		"total_deliveries": 1250,
		"successful_deliveries": 1180,
		"failed_deliveries": 70,
		"success_rate": 94.4,
		"average_response_time": 245,
		"by_event": {
			"message.created": 800,
			"room.joined": 250,
			"message.updated": 130,
			"room.left": 70
		},
		"by_status_code": {
			"200": 1100,
			"201": 80,
			"400": 20,
			"500": 30,
			"timeout": 20
		}
	},
	"status": "success"
}
```

## Best Practices

### Endpoint Design

1. **Use HTTPS** - Always use secure endpoints
2. **Validate signatures** - Verify webhook authenticity
3. **Handle duplicates** - Use event IDs to detect duplicates
4. **Respond quickly** - Return 200 status within 30 seconds

### Error Handling

1. **Return appropriate status codes** - 200 for success, 4xx/5xx for errors
2. **Log webhook events** - Keep audit trail of received events
3. **Implement retries** - Handle temporary failures gracefully
4. **Monitor failure rates** - Alert on high failure counts

### Performance

1. **Process asynchronously** - Queue webhook processing for fast response
2. **Limit processing time** - Avoid blocking webhook responses
3. **Use connection pooling** - Optimize HTTP performance
4. **Monitor response times** - Track and optimize webhook processing

### Security

1. **Verify signatures** - Always validate webhook signatures
2. **Use authentication** - Secure your webhook endpoints
3. **Validate payloads** - Sanitize and validate incoming data
4. **Rate limit** - Protect against abuse

## Examples

### Create Integration Webhook

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "url": "https://api.yourservice.com/webhooks/chatapi",
    "events": [
      "message.created",
      "room.joined",
      "room.left"
    ],
    "secret": "webhook-secret-12345",
    "custom_headers": {
      "Authorization": "Bearer your-service-token",
      "X-Integration": "chatapi-v1"
    },
    "meta": {
      "description": "Customer support integration",
      "contact": "dev@yourservice.com"
    }
  }'
```

### Test Webhook Delivery

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/550e8400-e29b-41d4-a716-446655440004/test" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "event": "message.created",
    "test_data": {
      "sender_name": "Test User",
      "content": "This is a test webhook message"
    }
  }'
```

### Get Webhook Analytics

```bash
curl -X GET "http://localhost:8000/api/v1/webhooks/550e8400-e29b-41d4-a716-446655440004/analytics?date_from=2024-01-01&date_to=2024-01-31" \
  -H "X-API-Key: your-api-key"
```

## Sample Webhook Handler

Here's a sample webhook handler in Python:

```python
from flask import Flask, request, jsonify
import hmac
import hashlib
import json

app = Flask(__name__)
WEBHOOK_SECRET = "your-webhook-secret-key"

def verify_signature(payload, signature):
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )

@app.route('/webhooks/chatapi', methods=['POST'])
def handle_webhook():
    signature = request.headers.get('X-ChatAPI-Signature')
    payload = request.data

    if not verify_signature(payload, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    event = request.json
    event_type = event['event']

    if event_type == 'message.created':
        handle_message_created(event['data'])
    elif event_type == 'room.joined':
        handle_room_joined(event['data'])
    elif event_type == 'notification.failed':
        handle_notification_failed(event['data'])

    return jsonify({'status': 'ok'}), 200

def handle_message_created(data):
    # Process new message
    print(f"New message from {data['sender_name']}: {data['content']}")

def handle_room_joined(data):
    # Process room join
    print(f"{data['user_name']} joined room {data['room_id']}")

def handle_notification_failed(data):
    # Handle notification failure
    print(f"Notification failed: {data['failure_reason']}")
```

## Next Steps

- [WebSockets](websockets.md) - Real-time communication
- [Notifications](notifications.md) - Send notifications via webhooks
- [Development](../development/setup.md) - Set up local webhook testing
