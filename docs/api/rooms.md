# Room Management

Rooms are virtual spaces where messages are organized and conversations take place. They enable group discussions, private chats, and organized communication channels.

## Overview

Rooms in ChatAPI:

- **Organize conversations** by topic, team, or purpose
- **Support multiple participants** through join/leave operations
- **Enable WebSocket connections** for real-time messaging
- **Provide message history** and persistence
- **Support custom metadata** for application-specific data

## Room Model

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "client_id": "uuid",
  "is_active": true,
  "meta": {...},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "participant_count": 5,
  "message_count": 142
}
```

## API Endpoints

### Create Room

Creates a new conversation room.

```http
POST /api/v1/rooms/
```

**Request Body:**

```json
{
	"name": "General Discussion",
	"description": "Main channel for team communication",
	"meta": {
		"category": "general",
		"tags": ["team", "announcements"],
		"max_participants": 50
	}
}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440001",
		"name": "General Discussion",
		"description": "Main channel for team communication",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"is_active": true,
		"meta": {
			"category": "general",
			"tags": ["team", "announcements"],
			"max_participants": 50
		},
		"created_at": "2024-01-01T00:00:00Z",
		"updated_at": "2024-01-01T00:00:00Z",
		"participant_count": 0,
		"message_count": 0
	},
	"status": "success"
}
```

### List Rooms

Retrieves rooms for the authenticated client.

```http
GET /api/v1/rooms/
```

**Query Parameters:**

- `skip` (int): Number of rooms to skip (default: 0)
- `limit` (int): Maximum rooms to return (default: 50, max: 100)
- `search` (string): Search rooms by name or description
- `is_active` (bool): Filter by active status
- `sort` (string): Sort field (`name`, `created_at`, `-created_at`)

**Example:**

```http
GET /api/v1/rooms/?search=general&limit=20&sort=-created_at
```

**Response:**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "General Discussion",
      "description": "Main channel for team communication",
      "client_id": "550e8400-e29b-41d4-a716-446655440000",
      "is_active": true,
      "meta": {...},
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "participant_count": 5,
      "message_count": 142
    }
  ],
  "pagination": {
    "skip": 0,
    "limit": 20,
    "total": 1,
    "has_more": false
  },
  "status": "success"
}
```

### Get Room Details

Retrieves detailed information about a specific room.

```http
GET /api/v1/rooms/{room_id}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440001",
		"name": "General Discussion",
		"description": "Main channel for team communication",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"is_active": true,
		"meta": {
			"category": "general",
			"tags": ["team", "announcements"],
			"max_participants": 50
		},
		"created_at": "2024-01-01T00:00:00Z",
		"updated_at": "2024-01-01T00:00:00Z",
		"participant_count": 5,
		"message_count": 142
	},
	"status": "success"
}
```

### Update Room

Updates room information.

```http
PUT /api/v1/rooms/{room_id}
```

**Request Body:**

```json
{
	"name": "Updated Room Name",
	"description": "Updated description",
	"meta": {
		"category": "support",
		"priority": "high"
	}
}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440001",
		"name": "Updated Room Name",
		"description": "Updated description",
		"client_id": "550e8400-e29b-41d4-a716-446655440000",
		"is_active": true,
		"meta": {
			"category": "support",
			"priority": "high"
		},
		"created_at": "2024-01-01T00:00:00Z",
		"updated_at": "2024-01-01T12:00:00Z",
		"participant_count": 5,
		"message_count": 142
	},
	"status": "success"
}
```

### Delete Room

Permanently deletes a room and all its messages.

```http
DELETE /api/v1/rooms/{room_id}
```

**Response:**

```json
{
	"message": "Room deleted successfully",
	"status": "success"
}
```

!!! warning "Data Loss Warning"
Deleting a room will permanently remove all messages, participants, and associated data. This action cannot be undone.

### Deactivate Room

Deactivates a room without deleting it. Deactivated rooms cannot receive new messages but preserve existing data.

```http
POST /api/v1/rooms/{room_id}/deactivate
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440001",
		"name": "General Discussion",
		"is_active": false,
		"updated_at": "2024-01-01T12:00:00Z"
	},
	"message": "Room deactivated successfully",
	"status": "success"
}
```

### Reactivate Room

Reactivates a deactivated room.

```http
POST /api/v1/rooms/{room_id}/activate
```

## Room Participants

### Join Room

Adds a user to a room. This is typically called when a user wants to participate in conversations.

```http
POST /api/v1/rooms/{room_id}/join
```

**Request Body:**

```json
{
	"user_id": "user_123",
	"user_name": "John Doe",
	"meta": {
		"role": "member",
		"joined_via": "invitation"
	}
}
```

**Response:**

```json
{
	"message": "Successfully joined room",
	"status": "success"
}
```

### Leave Room

Removes a user from a room.

```http
POST /api/v1/rooms/{room_id}/leave
```

**Request Body:**

```json
{
	"user_id": "user_123"
}
```

**Response:**

```json
{
	"message": "Successfully left room",
	"status": "success"
}
```

### List Participants

Get all participants in a room.

```http
GET /api/v1/rooms/{room_id}/participants
```

**Response:**

```json
{
	"data": [
		{
			"user_id": "user_123",
			"user_name": "John Doe",
			"joined_at": "2024-01-01T10:00:00Z",
			"meta": {
				"role": "member",
				"joined_via": "invitation"
			}
		}
	],
	"status": "success"
}
```

## WebSocket Integration

Rooms enable real-time communication through WebSocket connections.

### Connect to Room

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${roomId}?token=${apiKey}`);

ws.onopen = function (event) {
	console.log("Connected to room:", roomId);
};

ws.onmessage = function (event) {
	const message = JSON.parse(event.data);
	console.log("New message:", message);
};
```

### Check Online Status

Utility endpoint to check which users are currently online in a room:

```http
GET /api/v1/rooms/{room_id}/online
```

**Response:**

```json
{
	"data": {
		"online_users": ["user_123", "user_456"],
		"total_online": 2
	},
	"status": "success"
}
```

## Room Types and Patterns

### Public Rooms

Open rooms where any authenticated user can join:

```json
{
	"name": "General Chat",
	"description": "Open discussion for all users",
	"meta": {
		"type": "public",
		"auto_join": true
	}
}
```

### Private Rooms

Invite-only rooms for specific groups:

```json
{
	"name": "Team Alpha",
	"description": "Private team discussions",
	"meta": {
		"type": "private",
		"invite_only": true,
		"max_participants": 10
	}
}
```

### Support Rooms

One-on-one support conversations:

```json
{
	"name": "Support - Ticket #12345",
	"description": "Customer support conversation",
	"meta": {
		"type": "support",
		"ticket_id": "12345",
		"priority": "high"
	}
}
```

### Topic Rooms

Rooms organized by specific topics:

```json
{
	"name": "Feature Requests",
	"description": "Discuss new feature ideas",
	"meta": {
		"type": "topic",
		"category": "product",
		"tags": ["features", "feedback"]
	}
}
```

## Best Practices

### Room Organization

1. **Use descriptive names** - Make room purpose clear
2. **Add meaningful descriptions** - Help users understand the room's purpose
3. **Use metadata** - Store application-specific information
4. **Set participant limits** - Prevent overcrowding in focused discussions

### Performance Optimization

1. **Limit message history** - Archive old messages if needed
2. **Monitor participant counts** - Large rooms may need different handling
3. **Use room metadata** - Store frequently accessed data
4. **Implement pagination** - For rooms with many participants

### Security and Privacy

1. **Validate room access** - Ensure users can only access authorized rooms
2. **Implement role-based permissions** - Use metadata to store user roles
3. **Log room activities** - Track joins, leaves, and important events
4. **Clean up inactive rooms** - Regular maintenance of unused rooms

## Error Handling

Common errors when managing rooms:

### Room Not Found

```json
{
	"error": {
		"code": "ROOM_NOT_FOUND",
		"message": "Room not found"
	},
	"status": "error"
}
```

### Room Access Denied

```json
{
	"error": {
		"code": "ROOM_ACCESS_DENIED",
		"message": "You don't have permission to access this room"
	},
	"status": "error"
}
```

### Room Inactive

```json
{
	"error": {
		"code": "ROOM_INACTIVE",
		"message": "Room is deactivated and cannot receive new messages"
	},
	"status": "error"
}
```

### Already in Room

```json
{
	"error": {
		"code": "ALREADY_IN_ROOM",
		"message": "User is already a participant in this room"
	},
	"status": "error"
}
```

## Examples

### Create a Support Room

```bash
curl -X POST "http://localhost:8000/api/v1/rooms/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "name": "Support - John Doe",
    "description": "Customer support conversation",
    "meta": {
      "type": "support",
      "customer_id": "cust_123",
      "priority": "normal",
      "department": "technical"
    }
  }'
```

### Join User to Room

```bash
curl -X POST "http://localhost:8000/api/v1/rooms/550e8400-e29b-41d4-a716-446655440001/join" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "user_id": "john.doe@example.com",
    "user_name": "John Doe",
    "meta": {
      "role": "customer",
      "source": "web_widget"
    }
  }'
```

### Search Rooms

```bash
curl -X GET "http://localhost:8000/api/v1/rooms/?search=support&limit=10&sort=-created_at" \
  -H "X-API-Key: your-api-key"
```

## Next Steps

- [Messages](messages.md) - Send and receive messages in rooms
- [WebSockets](websockets.md) - Real-time communication
- [Notifications](notifications.md) - Set up room-based notifications
