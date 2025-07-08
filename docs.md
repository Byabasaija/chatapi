# Chat API Documentation

## Overview

This is a FastAPI-based chat API that provides real-time messaging capabilities with robust authentication and room-based architecture. The API uses a dual-key authentication system designed for client applications that manage multiple users.

## Authentication System

### Dual-Key Architecture

The API implements a secure dual-key authentication system:

1. **Master API Key**: Used by client applications to authenticate with the API
2. **Scoped API Keys**: User-specific keys generated for individual users within a client application

### Security Features

- **Always-Rotate Login**: Every user login automatically generates a new API key and revokes the old one
- **Automatic Key Cleanup**: Prevents accumulation of stale or potentially compromised keys
- **Permission-Based Access**: Granular control over what users can do
- **Audit Trail**: Clear security events for every authentication action

## Authentication Flow

### 1. Client Registration

First, register your client application to get a master API key:

```bash
POST /api/v1/clients
Content-Type: application/json

{
  "name": "My Chat App"
}
```

**Response:**

```json
{
	"id": "client-uuid",
	"name": "My Chat App",
	"master_api_key": "master_key_abc123...",
	"is_active": true,
	"created_at": "2024-01-01T00:00:00Z"
}
```

⚠️ **Important**: Store the `master_api_key` securely - it won't be shown again!

### 2. User Authentication (Always-Rotate)

When a user logs into your application, authenticate them with the API to get their scoped key:

```javascript
const response = await fetch("/api/v1/auth/user-login", {
	method: "POST",
	headers: {
		Authorization: "Bearer YOUR_MASTER_API_KEY",
		"Content-Type": "application/json",
	},
	body: JSON.stringify({
		user_id: "john_doe",
		display_name: "John Doe",
		permissions: ["read_messages", "send_messages"],
	}),
});

const data = await response.json();
// Always store the new API key - previous key is automatically revoked
localStorage.setItem("userApiKey", data.api_key);
```

**Response:**

```json
{
	"user_id": "john_doe",
	"display_name": "John Doe",
	"api_key": "scoped_key_xyz789...",
	"permissions": ["read_messages", "send_messages"]
}
```

### 3. Using Scoped Keys

Once authenticated, use the scoped API key for all user actions:

```javascript
// Send a message
await fetch("/api/v1/messages", {
	method: "POST",
	headers: {
		Authorization: "Bearer " + localStorage.getItem("userApiKey"),
		"Content-Type": "application/json",
	},
	body: JSON.stringify({
		room_id: "general",
		content: "Hello, world!",
	}),
});
```

## Benefits of Always-Rotate Authentication

### Enhanced Security

- **Fresh Credentials**: Every login provides a new, unused API key
- **Automatic Cleanup**: Old keys are immediately revoked, preventing misuse
- **Reduced Attack Surface**: No accumulation of potentially compromised keys

### Simplified Frontend Logic

- **Single Endpoint**: Only need to call `/user-login` for authentication
- **Predictable Flow**: Always get a new key, always store it
- **No Key Management**: No need to check if keys exist or are valid

### Better User Experience

- **Reliable Authentication**: Login always works and provides fresh credentials
- **Clear State**: Each login creates a clean authentication state
- **Automatic Recovery**: Lost keys are automatically replaced on next login

## API Permissions

Configure user permissions when authenticating:

```javascript
{
  "permissions": [
    "read_messages",      // Can read messages in rooms they have access to
    "send_messages",      // Can send messages to rooms
    "manage_rooms",       // Can create, update, delete rooms
    "invite_users"        // Can invite other users to rooms
  ]
}
```

## WebSocket Authentication

For real-time features, authenticate WebSocket connections using scoped keys:

```javascript
const socket = io("ws://localhost:8000/ws", {
	auth: {
		token: localStorage.getItem("userApiKey"),
	},
});

// Join a room
socket.emit("join_room", {
	room_id: "general",
});

// Send a message
socket.emit("send_message", {
	room_id: "general",
	content: "Hello via WebSocket!",
});
```

## Socket Events

### Client → Server Events

| Event          | Description            | Payload                                 |
| -------------- | ---------------------- | --------------------------------------- |
| `join_room`    | Join a chat room       | `{room_id: string}`                     |
| `leave_room`   | Leave a chat room      | `{room_id: string}`                     |
| `send_message` | Send a message         | `{room_id: string, content: string}`    |
| `typing_start` | Start typing indicator | `{room_id: string}`                     |
| `typing_stop`  | Stop typing indicator  | `{room_id: string}`                     |
| `mark_read`    | Mark messages as read  | `{room_id: string, message_id: string}` |

### Server → Client Events

| Event              | Description          | Payload                                              |
| ------------------ | -------------------- | ---------------------------------------------------- |
| `message_received` | New message in room  | `{room_id, message_id, user_id, content, timestamp}` |
| `user_joined`      | User joined room     | `{room_id, user_id, display_name}`                   |
| `user_left`        | User left room       | `{room_id, user_id}`                                 |
| `typing_indicator` | Someone is typing    | `{room_id, user_id, is_typing}`                      |
| `message_read`     | Message read receipt | `{room_id, message_id, user_id, read_at}`            |
| `error`            | Error occurred       | `{message, code}`                                    |

## API Endpoints

### Authentication Endpoints

| Method | Endpoint                      | Description                            | Auth Required |
| ------ | ----------------------------- | -------------------------------------- | ------------- |
| `POST` | `/api/v1/auth/user-login`     | Authenticate user (always rotates key) | Master Key    |
| `POST` | `/api/v1/auth/user-reset-key` | Reset user key (redundant)             | Master Key    |
| `POST` | `/api/v1/auth/user-logout`    | Revoke user key                        | Master Key    |
| `POST` | `/api/v1/auth/validate-token` | Validate scoped key                    | Scoped Key    |

### Message Endpoints

| Method   | Endpoint                        | Description       | Auth Required |
| -------- | ------------------------------- | ----------------- | ------------- |
| `GET`    | `/api/v1/messages/{room_id}`    | Get room messages | Scoped Key    |
| `POST`   | `/api/v1/messages`              | Send message      | Scoped Key    |
| `PUT`    | `/api/v1/messages/{message_id}` | Update message    | Scoped Key    |
| `DELETE` | `/api/v1/messages/{message_id}` | Delete message    | Scoped Key    |

### Room Endpoints

| Method   | Endpoint                  | Description       | Auth Required |
| -------- | ------------------------- | ----------------- | ------------- |
| `GET`    | `/api/v1/rooms`           | List user's rooms | Scoped Key    |
| `POST`   | `/api/v1/rooms`           | Create room       | Scoped Key    |
| `GET`    | `/api/v1/rooms/{room_id}` | Get room details  | Scoped Key    |
| `PUT`    | `/api/v1/rooms/{room_id}` | Update room       | Scoped Key    |
| `DELETE` | `/api/v1/rooms/{room_id}` | Delete room       | Scoped Key    |

## Error Handling

The API uses standard HTTP status codes and provides detailed error messages:

```json
{
	"detail": "Only master API key can authenticate users",
	"error_code": "INVALID_AUTH_TYPE"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Best Practices

### Frontend Integration

1. **Store Keys Securely**: Use secure storage for API keys
2. **Handle Rotation**: Always use the new key returned from login
3. **Error Recovery**: Re-authenticate if API calls fail with 401
4. **User Feedback**: Show clear authentication states to users

```javascript
class ChatAPI {
	constructor(masterKey) {
		this.masterKey = masterKey;
		this.userKey = localStorage.getItem("userApiKey");
	}

	async authenticateUser(userId, displayName) {
		const response = await fetch("/api/v1/auth/user-login", {
			method: "POST",
			headers: {
				Authorization: `Bearer ${this.masterKey}`,
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				user_id: userId,
				display_name: displayName,
				permissions: ["read_messages", "send_messages"],
			}),
		});

		if (response.ok) {
			const data = await response.json();
			this.userKey = data.api_key;
			localStorage.setItem("userApiKey", this.userKey);
			return data;
		}

		throw new Error("Authentication failed");
	}

	async sendMessage(roomId, content) {
		try {
			const response = await fetch("/api/v1/messages", {
				method: "POST",
				headers: {
					Authorization: `Bearer ${this.userKey}`,
					"Content-Type": "application/json",
				},
				body: JSON.stringify({ room_id: roomId, content }),
			});

			if (response.status === 401) {
				// Key might be expired, re-authenticate
				throw new Error("Re-authentication required");
			}

			return await response.json();
		} catch (error) {
			if (error.message === "Re-authentication required") {
				// Handle re-authentication
				throw error;
			}
			throw new Error("Failed to send message");
		}
	}
}
```

### Security Considerations

1. **Master Key Security**: Never expose master keys in client-side code
2. **HTTPS Only**: Always use HTTPS in production
3. **Key Rotation**: Leverage the automatic key rotation on login
4. **Permission Principle**: Grant minimal required permissions
5. **Audit Logging**: Monitor authentication and key usage patterns

### Production Deployment

1. **Environment Variables**: Store master keys in secure environment variables
2. **Rate Limiting**: Implement rate limiting for authentication endpoints
3. **Monitoring**: Set up alerts for unusual authentication patterns
4. **Backup Strategy**: Implement key recovery procedures for emergencies

## Integration Examples

### React Hook for Authentication

```javascript
import { useState, useEffect } from "react";

export function useChat(masterKey) {
	const [user, setUser] = useState(null);
	const [isAuthenticated, setIsAuthenticated] = useState(false);

	const login = async (userId, displayName) => {
		try {
			const response = await fetch("/api/v1/auth/user-login", {
				method: "POST",
				headers: {
					Authorization: `Bearer ${masterKey}`,
					"Content-Type": "application/json",
				},
				body: JSON.stringify({
					user_id: userId,
					display_name: displayName,
					permissions: ["read_messages", "send_messages"],
				}),
			});

			if (response.ok) {
				const userData = await response.json();
				localStorage.setItem("userApiKey", userData.api_key);
				setUser(userData);
				setIsAuthenticated(true);
				return userData;
			}
		} catch (error) {
			console.error("Login failed:", error);
			setIsAuthenticated(false);
		}
	};

	const logout = () => {
		localStorage.removeItem("userApiKey");
		setUser(null);
		setIsAuthenticated(false);
	};

	return { user, isAuthenticated, login, logout };
}
```

### Vue.js Plugin

```javascript
// chatapi-plugin.js
export default {
	install(app, options) {
		const chatAPI = {
			masterKey: options.masterKey,
			userKey: localStorage.getItem("userApiKey"),

			async login(userId, displayName) {
				const response = await fetch("/api/v1/auth/user-login", {
					method: "POST",
					headers: {
						Authorization: `Bearer ${this.masterKey}`,
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						user_id: userId,
						display_name: displayName,
						permissions: ["read_messages", "send_messages"],
					}),
				});

				if (response.ok) {
					const data = await response.json();
					this.userKey = data.api_key;
					localStorage.setItem("userApiKey", this.userKey);
					return data;
				}
				throw new Error("Login failed");
			},
		};

		app.config.globalProperties.$chat = chatAPI;
		app.provide("chat", chatAPI);
	},
};

// main.js
import { createApp } from "vue";
import ChatAPI from "./chatapi-plugin.js";

const app = createApp(App);
app.use(ChatAPI, {
	masterKey: process.env.VUE_APP_MASTER_KEY,
});
```

## FAQ

### Why does login always create a new key?

This approach provides several security and usability benefits:

- **Enhanced Security**: Fresh credentials prevent reuse of potentially compromised keys
- **Simplified Logic**: Frontend always knows it has a valid, current key
- **Automatic Recovery**: Users don't need separate "forgot key" flows
- **Audit Trail**: Clear security events for every authentication

### What happens to old keys?

Old keys are immediately revoked when a new one is created. This ensures:

- No accumulation of stale credentials
- Immediate invalidation of potentially compromised keys
- Clean security state for each login session

### Can I disable automatic key rotation?

The current implementation always rotates keys for security reasons. If you need different behavior, consider:

- Using the `/user-reset-key` endpoint for explicit key management
- Implementing custom logic in your client application
- Extending the service layer for alternative authentication flows

### How do I handle multiple devices?

Each device should authenticate independently:

- Each device gets its own scoped API key
- Keys are device-specific and managed separately
- Users can have multiple active keys across devices
- Use `user_id` to identify the same logical user across devices
