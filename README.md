# ChatAPI

A lightweight, multitenant chat service built in Go with SQLite, WebSocket support, and durable message delivery.

[![Documentation](https://img.shields.io/badge/docs-hugo-blue)](https://hastenr.github.io/chatapi/)
[![Go Version](https://img.shields.io/badge/go-1.21+-blue)](https://golang.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/hastenr/chatapi)](https://github.com/hastenr/chatapi/releases)
[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/hastenr/chatapi)](https://hub.docker.com/r/hastenr/chatapi)

## Releases

Download pre-built binaries and Docker images from [GitHub Releases](https://github.com/hastenr/chatapi/releases).

### Binary Installation

```bash
# Download latest release for your platform
curl -L https://github.com/hastenr/chatapi/releases/latest/download/chatapi-linux-amd64.tar.gz | tar xz
sudo mv chatapi /usr/local/bin/
```

### Docker Installation

```bash
# Pull from Docker Hub
docker pull hastenr/chatapi:latest

# Run with environment variables
docker run -p 8080:8080 -e MASTER_API_KEY=your-key hastenr/chatapi
```

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

# Or use Makefile
make build

# Build for all platforms
make build-all
```

### Docker

```bash
# Build the Docker image
docker build -t chatapi .

# Or use Makefile
make docker-build

# Run the container
docker run -p 8080:8080 -e MASTER_API_KEY=your-key chatapi

# Or use Makefile
make docker-run
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

📚 **[Complete Documentation](https://hastenr.github.io/chatapi/)**

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
| `MASTER_API_KEY` | `` | Master API key for admin operations (required for tenant creation) |

See [Configuration Guide](https://hastenr.github.io/chatapi/getting-started/) for all options.

## API Example

### Create a Tenant (Admin)

```bash
curl -X POST http://localhost:8080/admin/tenants \
  -H "X-Master-Key: your-master-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "MyCompany"}'
```

### Create a Room

```bash
curl -X POST http://localhost:8080/rooms \
  -H "X-API-Key: your-api-key" \
  -H "X-User-Id: user123" \
  -H "Content-Type: application/json" \
  -d '{"type": "dm", "members": ["alice", "bob"]}'
```

### Send a Message

```bash
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