+++
title = "ChatAPI Documentation"
type = "book"
weigh## 📚 **Documentation Sections**

- [Getting Started](/getting-started/) - Installation and basic setup
- [API Reference](/api/) - REST and WebSocket API documentation
- [Guides](/guides/) - Advanced usage and integration guides
- [Architecture](/architecture/) - System design and database schema 1
+++

# ChatAPI

A lightweight, multitenant chat service built in Go with SQLite, WebSocket support, and durable message delivery.

{{< columns >}}

## 🚀 **Key Features**

- **Multitenant Architecture**: API key-based tenancy with per-tenant rate limiting
- **Real-time Messaging**: WebSocket connections for instant chat delivery
- **Durable Delivery**: Store-then-send with at-least-once guarantees and retry logic
- **Message Sequencing**: Per-room message ordering with client acknowledgments
- **Room Types**: Support for DMs, groups, and channels
- **SQLite Backend**: WAL mode for concurrent reads/writes
- **Graceful Shutdown**: Clean connection draining and state persistence

<--->

## 📖 **Quick Start**

### Prerequisites
- Go 1.21+
- SQLite3 (optional, for CGO builds)

### Installation
```bash
# Clone the repository
git clone https://github.com/Byabasaija/chatapi.git
cd chatapi

# Install dependencies
go mod download

# Build the binary
go build -o bin/chatapi ./cmd/chatapi
```

### Run
```bash
# Set environment variables
export LISTEN_ADDR=":8080"
export DATABASE_DSN="file:chatapi.db?_journal_mode=WAL&_busy_timeout=5000"

# Start the server
./bin/chatapi
```

{{< /columns >}}

## 📚 **Documentation Sections**

{{< section-menu >}}

## 🔗 **Links**

- [GitHub Repository](https://github.com/Byabasaija/chatapi)
- [Go Package Documentation](https://pkg.go.dev/github.com/Byabasaija/chatapi)
- [Issues & Feature Requests](https://github.com/Byabasaija/chatapi/issues)

---

**ChatAPI** is designed for modern chat applications requiring reliable, real-time messaging with multi-tenant support. Built with performance and simplicity in mind.
