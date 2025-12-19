# ChatAPI

A lightweight, multitenant chat service built in Go with SQLite, WebSocket support, and durable message delivery.

[![Documentation](https://img.shields.io/badge/docs-hugo-blue)](https://byabasaija.github.io/chatapi/)
[![Go Version](https://img.shields.io/badge/go-1.21+-blue)](https://golang.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Features

- **Multitenant**: API key-based tenancy with per-tenant rate limiting
- **Real-time messaging**: WebSocket connections for instant chat
- **Durable delivery**: Store-then-send with at-least-once guarantees
- **Message sequencing**: Per-room message ordering with acknowledgments
- **SQLite backend**: WAL mode for concurrent reads/writes
- **REST & WebSocket APIs**: Complete HTTP and real-time interfaces

## Quick Start

### Prerequisites

- Go 1.21+
- SQLite3 (optional, for CGO builds)

### Installation

```bash
# Clone the repository
git clone https://github.com/hastenr/chatapi.git
cd chatapi

# Install dependencies
go mod download

# Build the binary
go build ./cmd/chatapi
```

### Run

```bash
# Set required environment variables
export LISTEN_ADDR=":8080"
export DATABASE_DSN="file:chatapi.db?_journal_mode=WAL&_busy_timeout=5000"

# Start the server
./chatapi
```

### Health Check

```bash
curl http://localhost:8080/health
# {"status":"ok","service":"chatapi","uptime":"1m30s","db_writable":true}
```

## Documentation

📚 **[Complete Documentation](https://byabasaija.github.io/chatapi/)**

- **Getting Started**: Installation and setup guides
- **API Reference**: REST and WebSocket API documentation
- **Guides**: Advanced usage and integration examples
- **Architecture**: System design and database schema
- **API Playground**: Interactive API testing

### Local Documentation

```bash
# Install Hugo
sudo snap install hugo

# Start docs server
cd docs && hugo server

# Visit http://localhost:1313
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LISTEN_ADDR` | `:8080` | Server listen address |
| `DATABASE_DSN` | `file:chatapi.db?_journal_mode=WAL&_busy_timeout=5000` | SQLite database DSN |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warn, error) |
| `DEFAULT_RATE_LIMIT` | `100` | Requests per second per tenant |

See [Configuration Guide](https://byabasaija.github.io/chatapi/getting-started/) for all options.

## API Example

```bash
# Create a room
curl -X POST http://localhost:8080/rooms \
  -H "X-API-Key: your-api-key" \
  -H "X-User-Id: user123" \
  -H "Content-Type: application/json" \
  -d '{"type": "dm", "members": ["alice", "bob"]}'

# Send a message
curl -X POST http://localhost:8080/rooms/room_123/messages \
  -H "X-API-Key: your-api-key" \
  -H "X-User-Id: user123" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, World!"}'
```

## Architecture

```
cmd/chatapi/           # Application entry point
internal/
  config/              # Configuration management
  db/                  # Database connection and migrations
  models/              # Data structures
  services/            # Business logic (tenant, chat, realtime, etc.)
  handlers/            # HTTP and WebSocket handlers
  transport/           # HTTP server and graceful shutdown
  worker/              # Background workers
```

## Development

```bash
# Run tests
go test ./...

# Build with race detection
go build -race ./cmd/chatapi

# Debug logging
export LOG_LEVEL=debug && ./chatapi
```

## Deployment

### Docker

```dockerfile
FROM golang:1.21-alpine
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o chatapi ./cmd/chatapi
CMD ["./chatapi"]
```

### Systemd

```ini
[Unit]
Description=ChatAPI Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/chatapi
Restart=always

[Install]
WantedBy=multi-user.target
```

## License

MIT License - see [LICENSE](LICENSE) file for details.