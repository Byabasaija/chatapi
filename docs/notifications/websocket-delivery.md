# WebSocket Delivery

The ChatAPI provides real-time notification delivery through WebSocket connections, enabling instant updates for connected clients.

## Overview

WebSocket delivery is the primary real-time notification mechanism in ChatAPI. When events occur (new messages, room updates, client status changes), notifications are immediately pushed to connected clients through their WebSocket connections.

## Connection Management

### Establishing Connections

WebSocket connections are established through the `/ws` endpoint:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws");
```

### Authentication

WebSocket connections must be authenticated using a valid JWT token:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws?token=YOUR_JWT_TOKEN");
```

### Connection States

- **CONNECTING**: Initial connection attempt
- **OPEN**: Connection established and ready for communication
- **CLOSING**: Connection is being closed
- **CLOSED**: Connection has been terminated

## Notification Types

### Message Notifications

Delivered when new messages are sent to rooms the client has access to:

```json
{
	"type": "message",
	"data": {
		"id": "msg_123",
		"room_id": "room_456",
		"client_id": "client_789",
		"content": "Hello, world!",
		"timestamp": "2024-01-15T10:30:00Z"
	}
}
```

### Room Updates

Sent when room properties change or clients join/leave:

```json
{
	"type": "room_update",
	"data": {
		"room_id": "room_456",
		"event": "client_joined",
		"client_id": "client_789",
		"timestamp": "2024-01-15T10:30:00Z"
	}
}
```

### Client Status

Notifications about client presence and status changes:

```json
{
	"type": "client_status",
	"data": {
		"client_id": "client_789",
		"status": "online",
		"last_seen": "2024-01-15T10:30:00Z"
	}
}
```

## Delivery Guarantees

### At-Least-Once Delivery

- Notifications are delivered at least once to connected clients
- Duplicate notifications may occur during network issues
- Clients should implement idempotency handling

### Message Ordering

- Messages within a room are delivered in order
- Cross-room message ordering is not guaranteed
- Use timestamps for precise ordering requirements

### Connection Recovery

When a WebSocket connection is lost:

1. Client attempts automatic reconnection
2. Server queues notifications during disconnection
3. Queued notifications are delivered upon reconnection
4. Maximum queue size: 1000 notifications per client

## Error Handling

### Connection Errors

```json
{
	"type": "error",
	"data": {
		"code": "CONNECTION_ERROR",
		"message": "Authentication failed",
		"timestamp": "2024-01-15T10:30:00Z"
	}
}
```

### Rate Limiting

- Maximum 100 messages per minute per client
- Excess messages are queued or dropped
- Rate limit errors are sent as notifications

```json
{
	"type": "error",
	"data": {
		"code": "RATE_LIMIT_EXCEEDED",
		"message": "Message rate limit exceeded",
		"retry_after": 60
	}
}
```

## Client Implementation

### JavaScript Example

```javascript
class ChatWebSocket {
	constructor(token) {
		this.token = token;
		this.ws = null;
		this.reconnectAttempts = 0;
		this.maxReconnectAttempts = 5;
	}

	connect() {
		this.ws = new WebSocket(`ws://localhost:8000/ws?token=${this.token}`);

		this.ws.onopen = () => {
			console.log("WebSocket connected");
			this.reconnectAttempts = 0;
		};

		this.ws.onmessage = (event) => {
			const notification = JSON.parse(event.data);
			this.handleNotification(notification);
		};

		this.ws.onclose = () => {
			console.log("WebSocket disconnected");
			this.reconnect();
		};

		this.ws.onerror = (error) => {
			console.error("WebSocket error:", error);
		};
	}

	handleNotification(notification) {
		switch (notification.type) {
			case "message":
				this.handleMessage(notification.data);
				break;
			case "room_update":
				this.handleRoomUpdate(notification.data);
				break;
			case "client_status":
				this.handleClientStatus(notification.data);
				break;
			case "error":
				this.handleError(notification.data);
				break;
		}
	}

	reconnect() {
		if (this.reconnectAttempts < this.maxReconnectAttempts) {
			this.reconnectAttempts++;
			const delay = Math.pow(2, this.reconnectAttempts) * 1000;
			setTimeout(() => this.connect(), delay);
		}
	}
}
```

## Monitoring and Debugging

### Connection Metrics

- Active WebSocket connections
- Message delivery rates
- Connection failure rates
- Reconnection attempts

### Debugging Tools

Use browser developer tools to monitor WebSocket traffic:

1. Open Network tab
2. Filter by "WS" (WebSocket)
3. Click on the WebSocket connection
4. View messages in the Messages tab

### Health Checks

The server provides WebSocket health check endpoints:

```http
GET /ws/health
```

Response:

```json
{
	"status": "healthy",
	"active_connections": 42,
	"uptime_seconds": 3600
}
```

## Best Practices

### Client-Side

1. **Implement exponential backoff** for reconnections
2. **Handle duplicate notifications** gracefully
3. **Buffer messages** during disconnections
4. **Validate notification data** before processing
5. **Implement heartbeat/ping** for connection monitoring

### Server-Side

1. **Limit connection lifetime** to prevent memory leaks
2. **Implement proper cleanup** on disconnection
3. **Monitor queue sizes** to prevent memory issues
4. **Use compression** for large notifications
5. **Log connection events** for debugging

## Security Considerations

### Authentication

- Always validate JWT tokens on connection
- Implement token refresh for long-lived connections
- Close connections immediately on authentication failure

### Authorization

- Verify client access to rooms before sending notifications
- Filter notifications based on client permissions
- Audit notification delivery for security compliance

### Rate Limiting

- Implement per-client rate limits
- Use sliding window rate limiting
- Temporarily ban clients exceeding limits

## Troubleshooting

### Common Issues

1. **Connection refused**: Check server status and firewall settings
2. **Authentication failed**: Verify JWT token validity
3. **Message not received**: Check room permissions and connection status
4. **High latency**: Monitor network conditions and server load

### Debug Mode

Enable debug mode for detailed logging:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws?token=TOKEN&debug=true");
```

This provides additional debugging information in notification payloads.
