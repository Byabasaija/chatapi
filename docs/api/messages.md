# Messages

Messages are the core communication units in ChatAPI. They represent individual pieces of content sent within rooms and support various types including text, media, and structured data.

## Overview

Messages in ChatAPI:

- **Belong to rooms** and maintain conversation context
- **Support multiple types** (text, image, file, system, etc.)
- **Store metadata** for rich content and application-specific data
- **Enable real-time delivery** via WebSocket connections
- **Provide edit/delete capabilities** with audit trails
- **Support threading** for organized discussions

## Message Model

```json
{
  "id": "uuid",
  "room_id": "uuid",
  "client_id": "uuid",
  "sender_id": "string",
  "sender_name": "string",
  "content": "string",
  "message_type": "text|image|file|system|custom",
  "meta": {...},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "edited_at": null,
  "is_deleted": false
}
```

## API Endpoints

### Send Message

Sends a new message to a room.

```http
POST /api/v1/rooms/{room_id}/messages/
```

**Request Body:**

```json
{
	"sender_id": "user_123",
	"sender_name": "John Doe",
	"content": "Hello everyone! 👋",
	"message_type": "text",
	"meta": {
		"mentions": ["user_456"],
		"thread_id": null,
		"priority": "normal"
	}
}
```

**Response:**

```json
{
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
			"thread_id": null,
			"priority": "normal"
		},
		"created_at": "2024-01-01T12:00:00Z",
		"updated_at": "2024-01-01T12:00:00Z",
		"edited_at": null,
		"is_deleted": false
	},
	"status": "success"
}
```

### List Messages

Retrieves messages from a room with pagination and filtering.

```http
GET /api/v1/rooms/{room_id}/messages/
```

**Query Parameters:**

- `skip` (int): Number of messages to skip (default: 0)
- `limit` (int): Maximum messages to return (default: 50, max: 100)
- `sender_id` (string): Filter by specific sender
- `message_type` (string): Filter by message type
- `created_after` (datetime): Messages created after this date
- `created_before` (datetime): Messages created before this date
- `search` (string): Search message content
- `include_deleted` (bool): Include deleted messages (default: false)
- `sort` (string): Sort order (`created_at`, `-created_at`)

**Example:**

```http
GET /api/v1/rooms/550e8400-e29b-41d4-a716-446655440001/messages/?limit=20&sort=-created_at&message_type=text
```

**Response:**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "room_id": "550e8400-e29b-41d4-a716-446655440001",
      "client_id": "550e8400-e29b-41d4-a716-446655440000",
      "sender_id": "user_123",
      "sender_name": "John Doe",
      "content": "Hello everyone! 👋",
      "message_type": "text",
      "meta": {...},
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z",
      "edited_at": null,
      "is_deleted": false
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 20,
    "total": 142,
    "has_more": true
  },
  "status": "success"
}
```

### Get Message Details

Retrieves detailed information about a specific message.

```http
GET /api/v1/messages/{message_id}
```

**Response:**

```json
{
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
			"thread_id": null,
			"priority": "normal"
		},
		"created_at": "2024-01-01T12:00:00Z",
		"updated_at": "2024-01-01T12:00:00Z",
		"edited_at": null,
		"is_deleted": false
	},
	"status": "success"
}
```

### Update Message

Updates an existing message. Only the content and metadata can be modified.

```http
PUT /api/v1/messages/{message_id}
```

**Request Body:**

```json
{
	"content": "Updated message content! 🎉",
	"meta": {
		"edited_reason": "Fixed typo",
		"mentions": ["user_456", "user_789"]
	}
}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440002",
		"room_id": "550e8400-e29b-41d4-a716-446655440001",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"sender_id": "user_123",
		"sender_name": "John Doe",
		"content": "Updated message content! 🎉",
		"message_type": "text",
		"meta": {
			"edited_reason": "Fixed typo",
			"mentions": ["user_456", "user_789"]
		},
		"created_at": "2024-01-01T12:00:00Z",
		"updated_at": "2024-01-01T12:05:00Z",
		"edited_at": "2024-01-01T12:05:00Z",
		"is_deleted": false
	},
	"status": "success"
}
```

### Delete Message

Marks a message as deleted. The message is soft-deleted and can be restored if needed.

```http
DELETE /api/v1/messages/{message_id}
```

**Response:**

```json
{
	"message": "Message deleted successfully",
	"status": "success"
}
```

### Restore Message

Restores a previously deleted message.

```http
POST /api/v1/messages/{message_id}/restore
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440002",
		"is_deleted": false,
		"updated_at": "2024-01-01T12:10:00Z"
	},
	"message": "Message restored successfully",
	"status": "success"
}
```

## Message Types

### Text Messages

Standard text-based messages with optional formatting.

```json
{
	"content": "Hello **world**! Here's a [link](https://example.com)",
	"message_type": "text",
	"meta": {
		"format": "markdown",
		"mentions": ["@john"],
		"hashtags": ["#general"]
	}
}
```

### Image Messages

Messages containing image content with metadata.

```json
{
	"content": "Check out this screenshot!",
	"message_type": "image",
	"meta": {
		"image_url": "https://example.com/image.jpg",
		"image_width": 1920,
		"image_height": 1080,
		"file_size": 245760,
		"alt_text": "Screenshot of the new dashboard"
	}
}
```

### File Messages

Messages with file attachments.

```json
{
	"content": "Here's the project documentation",
	"message_type": "file",
	"meta": {
		"file_url": "https://example.com/document.pdf",
		"file_name": "project_docs.pdf",
		"file_size": 2048000,
		"file_type": "application/pdf",
		"download_count": 0
	}
}
```

### System Messages

Automated messages for system events.

```json
{
	"content": "John Doe joined the room",
	"message_type": "system",
	"sender_id": "system",
	"sender_name": "System",
	"meta": {
		"event_type": "user_joined",
		"user_id": "user_123",
		"timestamp": "2024-01-01T12:00:00Z"
	}
}
```

### Custom Messages

Application-specific message types with custom structure.

```json
{
	"content": "Poll: What's your favorite programming language?",
	"message_type": "poll",
	"meta": {
		"poll_id": "poll_123",
		"options": ["Python", "JavaScript", "Go", "Rust"],
		"allow_multiple": false,
		"expires_at": "2024-01-08T12:00:00Z",
		"votes": {}
	}
}
```

## Real-Time Delivery

Messages are automatically delivered to connected WebSocket clients when sent.

### WebSocket Message Format

```json
{
  "type": "message",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "room_id": "550e8400-e29b-41d4-a716-446655440001",
    "sender_id": "user_123",
    "sender_name": "John Doe",
    "content": "Hello everyone! 👋",
    "message_type": "text",
    "meta": {...},
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

### Message Events

Different events are sent via WebSocket:

- `message` - New message sent
- `message_updated` - Message edited
- `message_deleted` - Message deleted
- `message_restored` - Message restored
- `typing_start` - User started typing
- `typing_stop` - User stopped typing

## Threading and Replies

Support for threaded conversations and message replies.

### Reply to Message

```json
{
	"content": "That's a great point!",
	"message_type": "text",
	"meta": {
		"reply_to": "550e8400-e29b-41d4-a716-446655440002",
		"thread_id": "thread_123"
	}
}
```

### Thread Operations

```http
# Get thread messages
GET /api/v1/messages/{message_id}/thread

# Get thread summary
GET /api/v1/messages/{message_id}/thread/summary
```

## Message Search

Advanced search capabilities across message content and metadata.

```http
GET /api/v1/messages/search
```

**Query Parameters:**

- `q` (string): Search query
- `room_ids` (array): Limit to specific rooms
- `sender_ids` (array): Limit to specific senders
- `message_types` (array): Filter by message types
- `date_from` (datetime): Start date range
- `date_to` (datetime): End date range
- `has_mentions` (bool): Messages with mentions
- `has_attachments` (bool): Messages with files/images

**Example:**

```http
GET /api/v1/messages/search?q=project%20deadline&message_types=text&date_from=2024-01-01
```

## Best Practices

### Message Content

1. **Validate content** - Ensure appropriate content length and format
2. **Support rich formatting** - Use markdown or HTML for enhanced display
3. **Handle mentions properly** - Parse and highlight user mentions
4. **Moderate content** - Implement content filtering if needed

### Performance

1. **Paginate message lists** - Load messages incrementally
2. **Cache recent messages** - Store frequently accessed messages
3. **Optimize search** - Use database indexing for content search
4. **Limit message size** - Set reasonable content length limits

### User Experience

1. **Show typing indicators** - Indicate when users are composing
2. **Mark messages as read** - Track message read status
3. **Support offline sync** - Queue messages when offline
4. **Enable message reactions** - Allow emoji reactions to messages

### Security

1. **Validate sender identity** - Ensure sender_id matches authenticated user
2. **Sanitize content** - Prevent XSS and injection attacks
3. **Rate limit messages** - Prevent spam and abuse
4. **Audit message changes** - Log edits and deletions

## Error Handling

Common errors when working with messages:

### Message Not Found

```json
{
	"error": {
		"code": "MESSAGE_NOT_FOUND",
		"message": "Message not found"
	},
	"status": "error"
}
```

### Room Inactive

```json
{
	"error": {
		"code": "ROOM_INACTIVE",
		"message": "Cannot send messages to inactive room"
	},
	"status": "error"
}
```

### Content Too Long

```json
{
	"error": {
		"code": "CONTENT_TOO_LONG",
		"message": "Message content exceeds maximum length",
		"details": {
			"max_length": 10000,
			"current_length": 12000
		}
	},
	"status": "error"
}
```

### Unauthorized Edit

```json
{
	"error": {
		"code": "UNAUTHORIZED_EDIT",
		"message": "You can only edit your own messages"
	},
	"status": "error"
}
```

## Examples

### Send a Text Message

```bash
curl -X POST "http://localhost:8000/api/v1/rooms/550e8400-e29b-41d4-a716-446655440001/messages/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "sender_id": "john.doe@example.com",
    "sender_name": "John Doe",
    "content": "Hello team! How is everyone doing today? 😊",
    "message_type": "text",
    "meta": {
      "mentions": ["jane.smith@example.com"],
      "priority": "normal"
    }
  }'
```

### Send an Image Message

```bash
curl -X POST "http://localhost:8000/api/v1/rooms/550e8400-e29b-41d4-a716-446655440001/messages/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "sender_id": "john.doe@example.com",
    "sender_name": "John Doe",
    "content": "Check out our new dashboard design!",
    "message_type": "image",
    "meta": {
      "image_url": "https://cdn.example.com/dashboard-preview.png",
      "image_width": 1600,
      "image_height": 1200,
      "alt_text": "New dashboard design with improved navigation"
    }
  }'
```

### Search Messages

```bash
curl -X GET "http://localhost:8000/api/v1/messages/search?q=dashboard&message_types=text,image&limit=10" \
  -H "X-API-Key: your-api-key"
```

### Edit a Message

```bash
curl -X PUT "http://localhost:8000/api/v1/messages/550e8400-e29b-41d4-a716-446655440002" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "content": "Hello team! How is everyone doing today? 😊 (Updated with emoji)",
    "meta": {
      "edited_reason": "Added emoji for friendliness"
    }
  }'
```

## Next Steps

- [WebSockets](websockets.md) - Real-time message delivery
- [Notifications](notifications.md) - Message-based notifications
- [Room Management](rooms.md) - Organizing conversations
