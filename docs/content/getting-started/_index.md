---
title: "Getting Started"
weight: 10
---

# Getting Started with ChatAPI

Welcome to ChatAPI! This guide will help you get up and running with your own chat service instance.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Go 1.21 or later** - [Download from golang.org](https://golang.org/dl/)
- **Git** - For cloning the repository
- **SQLite3** (optional) - For CGO builds with native SQLite driver

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/hastenr/chatapi.git
cd chatapi
```

### 2. Install Dependencies

```bash
go mod download
```

### 3. Build the Application

```bash
# Build with modernc SQLite driver (recommended)
go build -o bin/chatapi ./cmd/chatapi

# Or build with CGO SQLite driver (if you have SQLite3 installed)
CGO_ENABLED=1 go build -o bin/chatapi ./cmd/chatapi
```

## Configuration

ChatAPI uses environment variables for configuration. Create a `.env` file or set them directly:

```bash
# Server configuration
export LISTEN_ADDR=":8080"
export DATABASE_DSN="file:chatapi.db?_journal_mode=WAL&_busy_timeout=5000"

# Optional: Database directory
export DATA_DIR="./data"

# Optional: Logging level
export LOG_LEVEL="info"
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LISTEN_ADDR` | `:8080` | Server listen address |
| `DATABASE_DSN` | `file:chatapi.db` | SQLite database connection string |
| `DATA_DIR` | `./` | Directory for data files |
| `LOG_LEVEL` | `info` | Logging level (debug, info, warn, error) |
| `WAL_AUTOCHECKPOINT` | `1000` | WAL checkpoint frequency |
| `RETRY_MAX_ATTEMPTS` | `5` | Max delivery retry attempts |
| `RETRY_INTERVAL` | `30s` | Retry interval |
| `WORKER_INTERVAL` | `30s` | Background worker interval |
| `SHUTDOWN_DRAIN_TIMEOUT` | `10s` | Graceful shutdown timeout |

## Running ChatAPI

### Start the Server

```bash
./bin/chatapi
```

You should see output similar to:
```
2025/12/13 12:00:00 Starting ChatAPI server addr=:8080
2025/12/13 12:00:00 Starting delivery worker interval=30s
2025/12/13 12:00:00 Starting WAL checkpoint worker interval=5m0s
2025/12/13 12:00:00 Starting HTTP server addr=:8080
```

### Health Check

Verify the server is running:

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "ok",
  "uptime": "1m30s",
  "db_writable": true
}
```

## Next Steps

Now that you have ChatAPI running, you can:

1. **[Create a Tenant](/guides/tenants/)** - Set up your first tenant with API keys
2. **[Create Rooms](/guides/rooms/)** - Start creating chat rooms
3. **[Send Messages](/guides/messaging/)** - Begin messaging
4. **[Integrate WebSockets](/guides/websockets/)** - Add real-time functionality

## Development Mode

For development with live reloading:

```bash
# Run with debug logging
export LOG_LEVEL="debug"
./bin/chatapi

# Or use air for hot reloading (if installed)
air
```

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Change the port
export LISTEN_ADDR=":3000"
```

**Database permission errors:**
```bash
# Ensure write permissions to data directory
mkdir -p ./data
chmod 755 ./data
```

**Build errors:**
```bash
# Clean and rebuild
go clean
go mod tidy
go build ./cmd/chatapi
```

### Logs

Check the structured JSON logs for debugging:
```bash
./bin/chatapi 2>&1 | jq .
```

For more help, check the [troubleshooting guide](/guides/troubleshooting/) or [open an issue](https://github.com/hastenr/chatapi/issues).

