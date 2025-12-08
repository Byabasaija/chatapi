# ChatAPI

A lightweight, multitenant chat service built in Go with SQLite, WebSocket support, and durable message delivery.

## Features

- **Multitenant**: API key-based tenancy with per-tenant rate limiting
- **Real-time messaging**: WebSocket connections for live chat
- **Durable delivery**: Store-then-send with at-least-once guarantees and retry logic
- **Message sequencing**: Per-room message ordering with client acknowledgments
- **Room types**: Support for DMs, groups, and channels
- **Notifications**: Durable notification system for external integrations
- **SQLite backend**: WAL mode for concurrent reads/writes
- **Graceful shutdown**: Clean connection draining and state persistence

## Quick Start

### Prerequisites

- Go 1.21+
- SQLite3 (optional, for CGO builds)

### Build

```bash
# Clone the repository
git clone <repository-url>
cd chatapi

# Install dependencies
go mod download

# Build the binary
go build -o bin/chatapi ./cmd/chatapi
```

### Run

```bash
# Set required environment variables
export LISTEN_ADDR=":8080"
export DATABASE_DSN="file:chatapi.db?_journal_mode=WAL&_busy_timeout=5000"

# Run the server
./bin/chatapi
```

The server will start on port 8080 with an in-memory SQLite database.

## Configuration

Configure the service using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LISTEN_ADDR` | `:8080` | HTTP server listen address |
| `DATA_DIR` | `/var/chatapi` | Directory for data files |
| `DATABASE_DSN` | `file:chatapi.db?_journal_mode=WAL&_busy_timeout=5000` | SQLite database DSN |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warn, error) |
| `DEFAULT_RATE_LIMIT` | `100` | Default requests per second per tenant |
| `RETRY_MAX_ATTEMPTS` | `5` | Maximum delivery retry attempts |
| `RETRY_INTERVAL` | `30s` | Background worker interval |
| `WORKER_INTERVAL` | `30s` | Background worker interval |
| `SHUTDOWN_DRAIN_TIMEOUT` | `10s` | Graceful shutdown timeout |

## API Documentation

### Authentication

All requests require the following headers:

```
X-API-Key: <tenant_api_key>
X-User-Id: <user_id>  # Required for user-scoped operations
```

### REST Endpoints

#### Health Check

```http
GET /health
```

Returns service health status.

#### Rooms

**Create Room**
```http
POST /rooms
Content-Type: application/json

{
  "type": "dm|group|channel",
  "members": ["user1", "user2"],
  "name": "optional room name"
}
```

**Get Room**
```http
GET /rooms/{room_id}
```

**Get Room Members**
```http
GET /rooms/{room_id}/members
```

#### Messages

**Send Message**
```http
POST /rooms/{room_id}/messages
Content-Type: application/json

{
  "content": "Hello, world!",
  "meta": {"key": "value"}
}
```

**Get Messages**
```http
GET /rooms/{room_id}/messages?after_seq=0&limit=50
```

#### Acknowledgments

**Acknowledge Messages**
```http
POST /acks
Content-Type: application/json

{
  "room_id": "room123",
  "seq": 42
}
```

#### Notifications

**Send Notification**
```http
POST /notify
Content-Type: application/json

{
  "topic": "order.shipped",
  "payload": {"order_id": "123"},
  "targets": {
    "user_ids": ["user1", "user2"],
    "room_id": "room123",
    "topic_subscribers": true
  }
}
```

### WebSocket API

Connect to `/ws` with the same authentication headers or query parameters.

**Client → Server Messages:**

```json
// Send message
{
  "type": "send_message",
  "data": {
    "room_id": "room123",
    "content": "Hello!",
    "meta": {}
  }
}

// Acknowledge message
{
  "type": "ack",
  "data": {
    "room_id": "room123",
    "seq": 42
  }
}

// Typing indicators
{
  "type": "typing.start",
  "data": { "room_id": "room123" }
}
```

**Server → Client Messages:**

```json
// New message
{
  "type": "message",
  "room_id": "room123",
  "seq": 42,
  "message_id": "msg_123",
  "sender_id": "user1",
  "content": "Hello!",
  "created_at": "2024-01-01T12:00:00Z"
}

// Acknowledgment received
{
  "type": "ack.received",
  "room_id": "room123",
  "seq": 42,
  "user_id": "user2"
}

// Presence updates
{
  "type": "presence.update",
  "user_id": "user1",
  "status": "online"
}

// Typing indicators
{
  "type": "typing",
  "room_id": "room123",
  "user_id": "user1",
  "action": "start"
}
```

## Architecture

### Project Structure

```
cmd/chatapi/           # Application entry point
internal/
  config/              # Configuration management
  db/                  # Database connection and migrations
  models/              # Data structures
  services/            # Business logic services
    tenant/            # Tenant management and rate limiting
    chatroom/          # Room creation and membership
    message/           # Message storage and sequencing
    realtime/          # WebSocket session management
    notification/      # Durable notifications
    delivery/          # Retry logic and dead-letter queues
  handlers/            # HTTP and WebSocket handlers
    rest/              # REST API endpoints
    ws/                # WebSocket connection handling
  transport/           # HTTP server and graceful shutdown
  worker/              # Background workers
  ratelimit/           # Rate limiting implementation
```

### Key Design Decisions

- **Multitenant via API Keys**: Stateless authentication with database-backed tenant lookup
- **Everything is a Room**: DMs are rooms with 2 members, simplifying the data model
- **Store-then-Send**: Messages are persisted before delivery attempts, ensuring durability
- **At-Least-Once Delivery**: Client acknowledgments prevent duplicate processing
- **SQLite WAL Mode**: Enables concurrent reads and writes for better performance

### Database Schema

The service uses SQLite with the following main tables:

- `tenants`: Tenant information and API keys
- `rooms`: Chat rooms with deterministic DM keys
- `room_members`: User membership in rooms
- `messages`: Chat messages with sequencing
- `delivery_state`: Per-user delivery tracking
- `undelivered_messages`: Persistent delivery queue
- `notifications`: Durable notifications
- `notification_subscriptions`: Topic-based subscriptions

## Development

### Running Tests

```bash
go test ./...
```

### Database Migrations

Migrations are embedded in the binary and run automatically on startup. Migration files are located in `internal/db/migrations/`.

### Adding New Features

1. Define data models in `internal/models/`
2. Implement business logic in appropriate service
3. Add REST endpoints in `internal/handlers/rest/`
4. Add WebSocket message handling in `internal/handlers/ws/`
5. Update database schema with new migrations

### Logging

The service uses structured logging with `log/slog`. All log entries include `tenant_id` and `user_id` where applicable for multi-tenant debugging.

## Deployment

### Docker

```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o chatapi ./cmd/chatapi

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/chatapi .
CMD ["./chatapi"]
```

### Systemd Service

```ini
[Unit]
Description=ChatAPI Service
After=network.target

[Service]
Type=simple
User=chatapi
WorkingDirectory=/var/chatapi
ExecStart=/usr/local/bin/chatapi
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Health Checks

The `/health` endpoint returns:

```json
{
  "status": "ok",
  "service": "chatapi"
}
```

Use this for load balancer health checks and monitoring.

## Monitoring

### Metrics to Monitor

- Request rate per tenant
- WebSocket connection count
- Undelivered message queue depth
- Database connection pool stats
- WAL file size

### Logs

Key log patterns to monitor:

- Rate limit exceeded: `tenant_id=X rate limit exceeded`
- Message delivery failures: `failed to deliver message`
- Database errors: `database error`
- WebSocket connection issues: `WebSocket error`

## Troubleshooting

### Common Issues

**High memory usage**: Check for WebSocket connection leaks or large undelivered message queues.

**Slow message delivery**: Verify WAL checkpointing is working and database isn't locked.

**Rate limiting issues**: Check tenant configuration and request patterns.

**WebSocket disconnections**: Ensure proper heartbeat handling and check network stability.

### Debug Mode

Set `LOG_LEVEL=debug` for verbose logging including message delivery attempts and connection lifecycle events.

## License

[Add your license here]