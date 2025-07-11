# Notifications API

The Notifications API allows you to send notifications via multiple channels including email, WebSocket, and webhooks. It supports automatic fallback between channels and provides comprehensive delivery tracking.

## Overview

Notifications in ChatAPI:

- **Multi-channel delivery** (email, WebSocket, webhook)
- **Automatic fallback** (WebSocket → Email)
- **Room-based targeting** for contextual notifications
- **Flexible recipient lists** with multiple formats
- **Delivery tracking** and status monitoring
- **Client-specific email providers** for branded communications

## Notification Model

```json
{
  "id": "uuid",
  "type": "email|websocket|webhook",
  "room_id": "uuid",
  "client_id": "uuid",
  "recipients": ["email@example.com", "user_123"],
  "subject": "string",
  "content": "string",
  "status": "pending|sent|delivered|failed|partial",
  "email_fallback": true,
  "meta": {...},
  "delivery_attempts": 1,
  "delivered_at": null,
  "failed_at": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## API Endpoints

### Send Notification

Creates and sends a notification through the specified channel.

```http
POST /api/v1/notifications/
```

**Request Body:**

```json
{
	"type": "email",
	"room_id": "550e8400-e29b-41d4-a716-446655440001",
	"recipients": ["john.doe@example.com", "jane.smith@example.com"],
	"subject": "New Message in General Discussion",
	"content": "You have a new message in the General Discussion room. Click here to view: https://app.example.com/rooms/550e8400-e29b-41d4-a716-446655440001",
	"email_fallback": true,
	"meta": {
		"priority": "normal",
		"category": "message_notification",
		"room_name": "General Discussion",
		"sender": "John Doe"
	}
}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440003",
		"type": "email",
		"room_id": "550e8400-e29b-41d4-a716-446655440001",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"recipients": ["john.doe@example.com", "jane.smith@example.com"],
		"subject": "New Message in General Discussion",
		"content": "You have a new message...",
		"status": "pending",
		"email_fallback": true,
		"meta": {
			"priority": "normal",
			"category": "message_notification",
			"room_name": "General Discussion",
			"sender": "John Doe"
		},
		"delivery_attempts": 0,
		"delivered_at": null,
		"failed_at": null,
		"created_at": "2024-01-01T12:00:00Z",
		"updated_at": "2024-01-01T12:00:00Z"
	},
	"status": "success"
}
```

### List Notifications

Retrieves notifications with filtering and pagination.

```http
GET /api/v1/notifications/
```

**Query Parameters:**

- `skip` (int): Number of notifications to skip (default: 0)
- `limit` (int): Maximum notifications to return (default: 50, max: 100)
- `type` (string): Filter by notification type (`email`, `websocket`, `webhook`)
- `room_id` (uuid): Filter by room
- `status` (string): Filter by status (`pending`, `sent`, `delivered`, `failed`, `partial`)
- `created_after` (datetime): Notifications created after this date
- `created_before` (datetime): Notifications created before this date
- `recipient` (string): Filter by specific recipient
- `sort` (string): Sort order (`created_at`, `-created_at`, `status`)

**Example:**

```http
GET /api/v1/notifications/?type=email&status=delivered&limit=20&sort=-created_at
```

**Response:**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "type": "email",
      "room_id": "550e8400-e29b-41d4-a716-446655440001",
      "client_id": "550e8400-e29b-41d4-a716-446655440000",
      "recipients": ["john.doe@example.com"],
      "subject": "New Message in General Discussion",
      "content": "You have a new message...",
      "status": "delivered",
      "email_fallback": true,
      "meta": {...},
      "delivery_attempts": 1,
      "delivered_at": "2024-01-01T12:00:30Z",
      "failed_at": null,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:30Z"
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 20,
    "total": 145,
    "has_more": true
  },
  "status": "success"
}
```

### Get Notification Details

Retrieves detailed information about a specific notification.

```http
GET /api/v1/notifications/{notification_id}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440003",
		"type": "email",
		"room_id": "550e8400-e29b-41d4-a716-446655440001",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"recipients": ["john.doe@example.com"],
		"subject": "New Message in General Discussion",
		"content": "You have a new message...",
		"status": "delivered",
		"email_fallback": true,
		"meta": {
			"priority": "normal",
			"category": "message_notification",
			"delivery_details": {
				"provider": "smtp",
				"message_id": "msg_123456",
				"attempts": [
					{
						"timestamp": "2024-01-01T12:00:30Z",
						"status": "delivered",
						"provider_response": "250 2.0.0 OK"
					}
				]
			}
		},
		"delivery_attempts": 1,
		"delivered_at": "2024-01-01T12:00:30Z",
		"failed_at": null,
		"created_at": "2024-01-01T12:00:00Z",
		"updated_at": "2024-01-01T12:00:30Z"
	},
	"status": "success"
}
```

### Update Notification

Updates notification metadata or content (only for pending notifications).

```http
PUT /api/v1/notifications/{notification_id}
```

**Request Body:**

```json
{
	"subject": "Updated: New Message in General Discussion",
	"content": "Updated content with more details...",
	"meta": {
		"priority": "high",
		"updated_reason": "Added urgency flag"
	}
}
```

### Cancel Notification

Cancels a pending notification to prevent delivery.

```http
POST /api/v1/notifications/{notification_id}/cancel
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440003",
		"status": "cancelled",
		"updated_at": "2024-01-01T12:05:00Z"
	},
	"message": "Notification cancelled successfully",
	"status": "success"
}
```

### Retry Failed Notification

Retries delivery of a failed notification.

```http
POST /api/v1/notifications/{notification_id}/retry
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440003",
		"status": "pending",
		"delivery_attempts": 2,
		"updated_at": "2024-01-01T12:10:00Z"
	},
	"message": "Notification queued for retry",
	"status": "success"
}
```

### Delete Notification

Permanently deletes a notification and its delivery history.

```http
DELETE /api/v1/notifications/{notification_id}
```

**Response:**

```json
{
	"message": "Notification deleted successfully",
	"status": "success"
}
```

## Notification Types

### Email Notifications

Send notifications via email using configured providers.

```json
{
	"type": "email",
	"recipients": ["user@example.com"],
	"subject": "Welcome to ChatAPI",
	"content": "Thank you for joining our platform!",
	"meta": {
		"template": "welcome",
		"html_content": "<h1>Welcome!</h1><p>Thank you for joining our platform!</p>",
		"attachments": [
			{
				"filename": "welcome.pdf",
				"url": "https://example.com/welcome.pdf"
			}
		]
	}
}
```

### WebSocket Notifications

Send real-time notifications to connected users.

```json
{
	"type": "websocket",
	"room_id": "550e8400-e29b-41d4-a716-446655440001",
	"recipients": ["user_123", "user_456"],
	"content": "New message from John Doe",
	"meta": {
		"notification_type": "message",
		"action_url": "/rooms/550e8400-e29b-41d4-a716-446655440001",
		"icon": "message",
		"sound": "notification.mp3"
	}
}
```

### Webhook Notifications

Send notifications to external services via HTTP webhooks.

```json
{
	"type": "webhook",
	"recipients": ["https://api.external-service.com/webhooks/chatapi"],
	"content": "New message in room",
	"meta": {
		"event": "message_created",
		"room_id": "550e8400-e29b-41d4-a716-446655440001",
		"message_id": "550e8400-e29b-41d4-a716-446655440002",
		"sender": "john.doe@example.com",
		"timestamp": "2024-01-01T12:00:00Z"
	}
}
```

## Automatic Fallback

When `email_fallback` is enabled, the system automatically falls back to email if WebSocket delivery fails.

### Fallback Flow

1. **Primary Delivery** - Attempt delivery via specified channel
2. **Check Online Status** - For WebSocket, check if recipients are online
3. **Fallback Decision** - If primary fails and email_fallback=true, send email
4. **Email Delivery** - Use configured email provider
5. **Status Update** - Update notification with final status

### Fallback Configuration

```json
{
	"type": "websocket",
	"email_fallback": true,
	"recipients": ["user_123"],
	"subject": "Fallback email subject",
	"content": "WebSocket content (will be adapted for email if needed)",
	"meta": {
		"fallback_template": "websocket_notification",
		"fallback_delay": 30
	}
}
```

## Delivery Tracking

### Delivery Status

- `pending` - Notification created, queued for delivery
- `sent` - Successfully sent to provider/channel
- `delivered` - Confirmed delivery to recipient
- `failed` - Delivery failed after all attempts
- `partial` - Some recipients succeeded, others failed
- `cancelled` - Notification cancelled before delivery

### Delivery Details

Detailed delivery information is stored in the `meta` field:

```json
{
	"meta": {
		"delivery_details": {
			"provider": "smtp",
			"attempts": [
				{
					"timestamp": "2024-01-01T12:00:30Z",
					"status": "delivered",
					"recipient": "user@example.com",
					"provider_response": "250 2.0.0 OK",
					"message_id": "msg_123456"
				}
			],
			"fallback_used": false
		}
	}
}
```

### Delivery Analytics

Get notification delivery statistics:

```http
GET /api/v1/notifications/analytics
```

**Query Parameters:**

- `date_from` (date): Start date for analytics
- `date_to` (date): End date for analytics
- `type` (string): Filter by notification type
- `room_id` (uuid): Filter by room

**Response:**

```json
{
	"data": {
		"total_notifications": 1250,
		"by_status": {
			"delivered": 1180,
			"failed": 45,
			"pending": 15,
			"partial": 10
		},
		"by_type": {
			"email": 800,
			"websocket": 350,
			"webhook": 100
		},
		"delivery_rate": 94.4,
		"fallback_usage": 12.5
	},
	"status": "success"
}
```

## Best Practices

### Content Optimization

1. **Clear subjects** - Use descriptive, actionable subject lines
2. **Concise content** - Keep messages focused and brief
3. **HTML email support** - Provide both text and HTML versions
4. **Mobile-friendly** - Ensure content displays well on mobile devices

### Delivery Strategy

1. **Use appropriate channels** - WebSocket for real-time, email for persistent
2. **Enable fallbacks** - Use email fallback for important notifications
3. **Batch notifications** - Group related notifications to reduce noise
4. **Respect user preferences** - Honor opt-out and frequency settings

### Performance

1. **Queue notifications** - Use background processing for delivery
2. **Monitor delivery rates** - Track and improve delivery success
3. **Implement retries** - Retry failed deliveries with backoff
4. **Cache recipient data** - Optimize recipient lookup and validation

### Security

1. **Validate recipients** - Ensure recipients are authorized to receive content
2. **Sanitize content** - Prevent injection attacks in notification content
3. **Rate limit** - Implement sending limits to prevent abuse
4. **Audit trails** - Log all notification activities

## Error Handling

### Common Errors

#### Invalid Recipients

```json
{
	"error": {
		"code": "INVALID_RECIPIENTS",
		"message": "One or more recipients are invalid",
		"details": {
			"invalid": ["invalid-email"],
			"valid": ["user@example.com"]
		}
	},
	"status": "error"
}
```

#### Email Provider Not Configured

```json
{
	"error": {
		"code": "EMAIL_PROVIDER_NOT_CONFIGURED",
		"message": "Email provider must be configured to send email notifications"
	},
	"status": "error"
}
```

#### Content Too Long

```json
{
	"error": {
		"code": "CONTENT_TOO_LONG",
		"message": "Notification content exceeds maximum length",
		"details": {
			"max_length": 10000,
			"current_length": 12000
		}
	},
	"status": "error"
}
```

#### Delivery Failed

```json
{
	"error": {
		"code": "DELIVERY_FAILED",
		"message": "Failed to deliver notification",
		"details": {
			"provider_error": "SMTP connection timeout",
			"retry_possible": true
		}
	},
	"status": "error"
}
```

## Examples

### Send Email Notification

```bash
curl -X POST "http://localhost:8000/api/v1/notifications/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "type": "email",
    "room_id": "550e8400-e29b-41d4-a716-446655440001",
    "recipients": ["user@example.com"],
    "subject": "New message in General Discussion",
    "content": "You have a new message from John Doe: \"Hello everyone!\"",
    "meta": {
      "priority": "normal",
      "category": "message_notification"
    }
  }'
```

### Send WebSocket with Email Fallback

```bash
curl -X POST "http://localhost:8000/api/v1/notifications/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "type": "websocket",
    "room_id": "550e8400-e29b-41d4-a716-446655440001",
    "recipients": ["user_123"],
    "subject": "New Message",
    "content": "You have a new message",
    "email_fallback": true,
    "meta": {
      "notification_type": "message",
      "action_url": "/rooms/550e8400-e29b-41d4-a716-446655440001"
    }
  }'
```

### Send Webhook Notification

```bash
curl -X POST "http://localhost:8000/api/v1/notifications/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "type": "webhook",
    "recipients": ["https://api.external-service.com/webhooks/chatapi"],
    "content": "New message event",
    "meta": {
      "event": "message_created",
      "room_id": "550e8400-e29b-41d4-a716-446655440001",
      "message_id": "550e8400-e29b-41d4-a716-446655440002",
      "sender": "john.doe@example.com"
    }
  }'
```

### Get Delivery Analytics

```bash
curl -X GET "http://localhost:8000/api/v1/notifications/analytics?date_from=2024-01-01&date_to=2024-01-31" \
  -H "X-API-Key: your-api-key"
```

## Next Steps

- [Email Providers](../notifications/email-providers.md) - Configure email delivery
- [WebSocket Delivery](../notifications/websocket-delivery.md) - Real-time notifications
- [Delivery Tracking](../notifications/delivery-tracking.md) - Monitor notification success
