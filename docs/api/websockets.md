# WebSockets API

WebSockets provide real-time bidirectional communication between clients and ChatAPI. Connect to rooms for instant message delivery, typing indicators, and live presence updates.

## Overview

WebSocket features in ChatAPI:

- **Real-time messaging** with instant delivery
- **Room-based connections** for organized communication
- **Presence tracking** to see who's online
- **Typing indicators** for better user experience
- **Event broadcasting** for system notifications
- **Automatic reconnection** and connection recovery
- **Authentication** via API keys or tokens

## Connection

### WebSocket Endpoint

```
ws://localhost:8000/ws/{room_id}?token={api_key}
```

**Production:**

```
wss://api.chatapi.dev/ws/{room_id}?token={api_key}
```

### Authentication

Authenticate using your API key as a query parameter:

```javascript
const roomId = "550e8400-e29b-41d4-a716-446655440001";
const apiKey = "sk_test_1234567890abcdef";
const ws = new WebSocket(`ws://localhost:8000/ws/${roomId}?token=${apiKey}`);
```

### Connection Parameters

- `room_id` (required): UUID of the room to connect to
- `token` (required): Your API key for authentication
- `user_id` (optional): Identifier for the connecting user
- `user_name` (optional): Display name for the user

**Example with user info:**

```javascript
const ws = new WebSocket(
	`ws://localhost:8000/ws/${roomId}?token=${apiKey}&user_id=user_123&user_name=John%20Doe`
);
```

## Message Types

### Incoming Messages

Messages received from the server have the following structure:

```json
{
  "type": "message_type",
  "data": {...},
  "timestamp": "2024-01-01T12:00:00Z",
  "room_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### New Message

```json
{
	"type": "message",
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440002",
		"sender_id": "user_123",
		"sender_name": "John Doe",
		"content": "Hello everyone! 👋",
		"message_type": "text",
		"meta": {
			"mentions": ["user_456"],
			"priority": "normal"
		},
		"created_at": "2024-01-01T12:00:00Z"
	},
	"timestamp": "2024-01-01T12:00:00Z",
	"room_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### Message Updated

```json
{
	"type": "message_updated",
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440002",
		"content": "Updated message content! 🎉",
		"edited_at": "2024-01-01T12:05:00Z",
		"edit_reason": "Fixed typo"
	},
	"timestamp": "2024-01-01T12:05:00Z",
	"room_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### Message Deleted

```json
{
	"type": "message_deleted",
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440002",
		"deleted_by": "user_123",
		"deleted_at": "2024-01-01T12:10:00Z"
	},
	"timestamp": "2024-01-01T12:10:00Z",
	"room_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### User Joined

```json
{
	"type": "user_joined",
	"data": {
		"user_id": "user_789",
		"user_name": "Jane Smith",
		"joined_at": "2024-01-01T12:00:00Z",
		"meta": {
			"role": "member"
		}
	},
	"timestamp": "2024-01-01T12:00:00Z",
	"room_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### User Left

```json
{
	"type": "user_left",
	"data": {
		"user_id": "user_789",
		"user_name": "Jane Smith",
		"left_at": "2024-01-01T12:30:00Z"
	},
	"timestamp": "2024-01-01T12:30:00Z",
	"room_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### Typing Indicator

```json
{
	"type": "typing",
	"data": {
		"user_id": "user_123",
		"user_name": "John Doe",
		"is_typing": true
	},
	"timestamp": "2024-01-01T12:00:15Z",
	"room_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### Notification

```json
{
	"type": "notification",
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440003",
		"title": "New Message",
		"content": "You have a new message from John Doe",
		"action_url": "/rooms/550e8400-e29b-41d4-a716-446655440001",
		"priority": "normal",
		"icon": "message"
	},
	"timestamp": "2024-01-01T12:00:00Z",
	"room_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### Connection Status

```json
{
	"type": "connection_status",
	"data": {
		"status": "connected",
		"user_id": "user_123",
		"room_id": "550e8400-e29b-41d4-a716-446655440001",
		"online_users": ["user_123", "user_456", "user_789"],
		"total_participants": 15
	},
	"timestamp": "2024-01-01T12:00:00Z"
}
```

### Outgoing Messages

Send messages to the server with this structure:

```json
{
  "type": "message_type",
  "data": {...}
}
```

#### Send Typing Indicator

```json
{
	"type": "typing",
	"data": {
		"is_typing": true
	}
}
```

#### Request Online Users

```json
{
	"type": "get_online_users",
	"data": {}
}
```

#### Ping/Heartbeat

```json
{
	"type": "ping",
	"data": {}
}
```

## JavaScript Client Example

### Basic Connection

```javascript
class ChatAPIWebSocket {
	constructor(roomId, apiKey, userId = null, userName = null) {
		this.roomId = roomId;
		this.apiKey = apiKey;
		this.userId = userId;
		this.userName = userName;
		this.ws = null;
		this.reconnectAttempts = 0;
		this.maxReconnectAttempts = 5;
		this.reconnectDelay = 1000;
	}

	connect() {
		const params = new URLSearchParams({
			token: this.apiKey,
			...(this.userId && { user_id: this.userId }),
			...(this.userName && { user_name: this.userName }),
		});

		const wsUrl = `ws://localhost:8000/ws/${this.roomId}?${params}`;
		this.ws = new WebSocket(wsUrl);

		this.ws.onopen = this.onOpen.bind(this);
		this.ws.onmessage = this.onMessage.bind(this);
		this.ws.onclose = this.onClose.bind(this);
		this.ws.onerror = this.onError.bind(this);
	}

	onOpen(event) {
		console.log("Connected to ChatAPI WebSocket");
		this.reconnectAttempts = 0;

		// Request current online users
		this.send("get_online_users", {});
	}

	onMessage(event) {
		try {
			const message = JSON.parse(event.data);
			this.handleMessage(message);
		} catch (error) {
			console.error("Failed to parse WebSocket message:", error);
		}
	}

	onClose(event) {
		console.log("WebSocket connection closed:", event.code, event.reason);

		if (
			event.code !== 1000 &&
			this.reconnectAttempts < this.maxReconnectAttempts
		) {
			this.reconnect();
		}
	}

	onError(event) {
		console.error("WebSocket error:", event);
	}

	handleMessage(message) {
		switch (message.type) {
			case "message":
				this.onNewMessage(message.data);
				break;
			case "message_updated":
				this.onMessageUpdated(message.data);
				break;
			case "message_deleted":
				this.onMessageDeleted(message.data);
				break;
			case "user_joined":
				this.onUserJoined(message.data);
				break;
			case "user_left":
				this.onUserLeft(message.data);
				break;
			case "typing":
				this.onTyping(message.data);
				break;
			case "notification":
				this.onNotification(message.data);
				break;
			case "connection_status":
				this.onConnectionStatus(message.data);
				break;
			case "pong":
				this.onPong(message.data);
				break;
			default:
				console.log("Unknown message type:", message.type);
		}
	}

	send(type, data) {
		if (this.ws && this.ws.readyState === WebSocket.OPEN) {
			this.ws.send(JSON.stringify({ type, data }));
		} else {
			console.warn("WebSocket not connected");
		}
	}

	sendTyping(isTyping) {
		this.send("typing", { is_typing: isTyping });
	}

	getOnlineUsers() {
		this.send("get_online_users", {});
	}

	ping() {
		this.send("ping", {});
	}

	reconnect() {
		this.reconnectAttempts++;
		const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

		console.log(
			`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`
		);

		setTimeout(() => {
			this.connect();
		}, delay);
	}

	disconnect() {
		if (this.ws) {
			this.ws.close(1000, "Client disconnect");
		}
	}

	// Event handlers (override these in your implementation)
	onNewMessage(data) {
		console.log("New message:", data);
	}

	onMessageUpdated(data) {
		console.log("Message updated:", data);
	}

	onMessageDeleted(data) {
		console.log("Message deleted:", data);
	}

	onUserJoined(data) {
		console.log("User joined:", data);
	}

	onUserLeft(data) {
		console.log("User left:", data);
	}

	onTyping(data) {
		console.log("Typing indicator:", data);
	}

	onNotification(data) {
		console.log("Notification:", data);
	}

	onConnectionStatus(data) {
		console.log("Connection status:", data);
	}

	onPong(data) {
		console.log("Pong received");
	}
}

// Usage
const chat = new ChatAPIWebSocket(
	"550e8400-e29b-41d4-a716-446655440001",
	"sk_test_1234567890abcdef",
	"user_123",
	"John Doe"
);

// Override event handlers
chat.onNewMessage = (data) => {
	// Update UI with new message
	addMessageToUI(data);
};

chat.onTyping = (data) => {
	// Show/hide typing indicator
	updateTypingIndicator(data.user_name, data.is_typing);
};

// Connect
chat.connect();

// Send typing indicator when user starts typing
document.getElementById("messageInput").addEventListener("input", () => {
	chat.sendTyping(true);

	// Stop typing indicator after 3 seconds of inactivity
	clearTimeout(typingTimeout);
	typingTimeout = setTimeout(() => {
		chat.sendTyping(false);
	}, 3000);
});
```

### React Hook Example

```javascript
import { useState, useEffect, useRef, useCallback } from "react";

function useChatWebSocket(roomId, apiKey, userId, userName) {
	const [isConnected, setIsConnected] = useState(false);
	const [onlineUsers, setOnlineUsers] = useState([]);
	const [messages, setMessages] = useState([]);
	const [typingUsers, setTypingUsers] = useState([]);

	const ws = useRef(null);
	const reconnectAttempts = useRef(0);

	const connect = useCallback(() => {
		const params = new URLSearchParams({
			token: apiKey,
			user_id: userId,
			user_name: userName,
		});

		ws.current = new WebSocket(`ws://localhost:8000/ws/${roomId}?${params}`);

		ws.current.onopen = () => {
			setIsConnected(true);
			reconnectAttempts.current = 0;
		};

		ws.current.onmessage = (event) => {
			const message = JSON.parse(event.data);

			switch (message.type) {
				case "message":
					setMessages((prev) => [...prev, message.data]);
					break;
				case "user_joined":
					setOnlineUsers((prev) => [...prev, message.data.user_id]);
					break;
				case "user_left":
					setOnlineUsers((prev) =>
						prev.filter((id) => id !== message.data.user_id)
					);
					break;
				case "typing":
					if (message.data.is_typing) {
						setTypingUsers((prev) => [...prev, message.data.user_name]);
					} else {
						setTypingUsers((prev) =>
							prev.filter((name) => name !== message.data.user_name)
						);
					}
					break;
				case "connection_status":
					setOnlineUsers(message.data.online_users);
					break;
			}
		};

		ws.current.onclose = () => {
			setIsConnected(false);

			if (reconnectAttempts.current < 5) {
				reconnectAttempts.current++;
				setTimeout(connect, 1000 * reconnectAttempts.current);
			}
		};
	}, [roomId, apiKey, userId, userName]);

	useEffect(() => {
		connect();

		return () => {
			if (ws.current) {
				ws.current.close();
			}
		};
	}, [connect]);

	const sendTyping = useCallback((isTyping) => {
		if (ws.current && ws.current.readyState === WebSocket.OPEN) {
			ws.current.send(
				JSON.stringify({
					type: "typing",
					data: { is_typing: isTyping },
				})
			);
		}
	}, []);

	return {
		isConnected,
		onlineUsers,
		messages,
		typingUsers,
		sendTyping,
	};
}

// Usage in React component
function ChatRoom({ roomId, apiKey, userId, userName }) {
	const { isConnected, onlineUsers, messages, typingUsers, sendTyping } =
		useChatWebSocket(roomId, apiKey, userId, userName);

	return (
		<div>
			<div>Status: {isConnected ? "Connected" : "Disconnected"}</div>
			<div>Online Users: {onlineUsers.join(", ")}</div>
			<div>Typing: {typingUsers.join(", ")}</div>

			<div>
				{messages.map((message) => (
					<div key={message.id}>
						<strong>{message.sender_name}:</strong> {message.content}
					</div>
				))}
			</div>

			<input
				onFocus={() => sendTyping(true)}
				onBlur={() => sendTyping(false)}
				placeholder="Type a message..."
			/>
		</div>
	);
}
```

## Connection States

### Connection Lifecycle

1. **Connecting** - WebSocket connection being established
2. **Connected** - Successfully connected and authenticated
3. **Disconnected** - Connection lost or closed
4. **Reconnecting** - Attempting to reconnect after failure
5. **Failed** - Connection failed and won't retry

### Error Codes

| Code | Description                    |
| ---- | ------------------------------ |
| 1000 | Normal closure                 |
| 1001 | Going away                     |
| 1002 | Protocol error                 |
| 1003 | Unsupported data               |
| 1006 | Abnormal closure               |
| 1011 | Server error                   |
| 4001 | Unauthorized (invalid API key) |
| 4002 | Room not found                 |
| 4003 | Room access denied             |
| 4004 | Rate limit exceeded            |

## Utility Functions

ChatAPI provides utility functions for checking connection status:

### Check Online Users

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

### Check Room Membership

```http
GET /api/v1/rooms/{room_id}/participants
```

## Best Practices

### Connection Management

1. **Implement reconnection** - Handle connection drops gracefully
2. **Use exponential backoff** - Avoid overwhelming the server
3. **Limit reconnect attempts** - Don't retry indefinitely
4. **Handle authentication errors** - Refresh tokens when needed

### Performance

1. **Debounce typing indicators** - Don't send on every keystroke
2. **Batch messages** - Group rapid updates when possible
3. **Use heartbeats** - Keep connections alive with ping/pong
4. **Clean up connections** - Close connections when leaving rooms

### User Experience

1. **Show connection status** - Indicate when offline/reconnecting
2. **Queue messages offline** - Send when reconnected
3. **Handle message ordering** - Display messages in correct order
4. **Provide feedback** - Show when messages are delivered

### Security

1. **Validate tokens** - Ensure API keys are valid
2. **Check permissions** - Verify room access rights
3. **Rate limit** - Prevent spam and abuse
4. **Sanitize input** - Clean user-generated content

## Troubleshooting

### Common Issues

#### Connection Refused

- Check if WebSocket endpoint is accessible
- Verify API key is valid
- Ensure room exists and is accessible

#### Frequent Disconnections

- Check network stability
- Implement proper reconnection logic
- Monitor server logs for errors

#### Messages Not Received

- Verify WebSocket connection is open
- Check if user is properly joined to room
- Ensure event types are handled correctly

#### High Latency

- Check network conditions
- Verify server performance
- Consider using CDN or regional servers

## Examples

### Simple Chat Client

```html
<!DOCTYPE html>
<html>
	<head>
		<title>ChatAPI WebSocket Demo</title>
	</head>
	<body>
		<div id="status">Disconnected</div>
		<div id="messages"></div>
		<div id="typing"></div>
		<input id="messageInput" placeholder="Type a message..." />
		<button onclick="sendMessage()">Send</button>

		<script>
			const roomId = "550e8400-e29b-41d4-a716-446655440001";
			const apiKey = "sk_test_1234567890abcdef";
			const userId = "demo_user";
			const userName = "Demo User";

			const ws = new WebSocket(
				`ws://localhost:8000/ws/${roomId}?token=${apiKey}&user_id=${userId}&user_name=${userName}`
			);

			ws.onopen = () => {
				document.getElementById("status").textContent = "Connected";
			};

			ws.onmessage = (event) => {
				const message = JSON.parse(event.data);

				if (message.type === "message") {
					addMessage(message.data);
				} else if (message.type === "typing") {
					updateTyping(message.data);
				}
			};

			ws.onclose = () => {
				document.getElementById("status").textContent = "Disconnected";
			};

			function addMessage(data) {
				const messages = document.getElementById("messages");
				const div = document.createElement("div");
				div.innerHTML = `<strong>${data.sender_name}:</strong> ${data.content}`;
				messages.appendChild(div);
			}

			function updateTyping(data) {
				const typing = document.getElementById("typing");
				if (data.is_typing) {
					typing.textContent = `${data.user_name} is typing...`;
				} else {
					typing.textContent = "";
				}
			}

			function sendMessage() {
				const input = document.getElementById("messageInput");
				if (input.value.trim()) {
					// Send via REST API (WebSocket is for receiving only in this example)
					fetch(`/api/v1/rooms/${roomId}/messages/`, {
						method: "POST",
						headers: {
							"Content-Type": "application/json",
							"X-API-Key": apiKey,
						},
						body: JSON.stringify({
							sender_id: userId,
							sender_name: userName,
							content: input.value,
							message_type: "text",
						}),
					});
					input.value = "";
				}
			}

			// Typing indicator
			let typingTimeout;
			document.getElementById("messageInput").addEventListener("input", () => {
				ws.send(
					JSON.stringify({
						type: "typing",
						data: { is_typing: true },
					})
				);

				clearTimeout(typingTimeout);
				typingTimeout = setTimeout(() => {
					ws.send(
						JSON.stringify({
							type: "typing",
							data: { is_typing: false },
						})
					);
				}, 3000);
			});
		</script>
	</body>
</html>
```

## Next Steps

- [Messages](messages.md) - Send messages via REST API
- [Notifications](notifications.md) - Real-time notifications via WebSocket
- [Room Management](rooms.md) - Create and manage rooms for WebSocket connections
