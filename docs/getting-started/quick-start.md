# Quick Start Guide

Get ChatAPI up and running in minutes with this comprehensive quick start guide.

## Prerequisites

Before starting, ensure you have:

- **Docker & Docker Compose** - For containerized deployment
- **Python 3.10+** - For local development (optional)
- **PostgreSQL** - Database (included in Docker setup)
- **Redis** - For background jobs (included in Docker setup)

## Installation Methods

### Option 1: Docker Compose (Recommended)

The fastest way to get started is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/Byabasaija/chatapi
cd chatapi

# Copy environment template
cp .env.example .env

# Edit .env file with your settings
nano .env

# Start all services
docker compose up --build
```

### Option 2: Local Development

For development and customization:

```bash
# Clone and setup
git clone https://github.com/Byabasaija/chatapi
cd chatapi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv sync

# Setup database
docker compose up db redis -d
alembic upgrade head

# Start the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Access Points

Once running, you can access:

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Interactive API**: http://localhost:8000/redoc
- **Database Admin**: http://localhost:8080 (Adminer)

## Your First API Call

### 1. Create a Client Application

Every application using ChatAPI needs a client registration:

```bash
curl -X POST http://localhost:8000/api/v1/clients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Chat App",
    "description": "My first ChatAPI integration"
  }'
```

**Response:**

```json
{
	"id": "550e8400-e29b-41d4-a716-446655440000",
	"name": "My Chat App",
	"description": "My first ChatAPI integration",
	"master_api_key": "ck_live_abc123...",
	"is_active": true,
	"created_at": "2024-01-01T00:00:00Z"
}
```

!!! warning "Store Your API Key"
Save the `master_api_key` securely - it won't be shown again!

### 2. Create a Room

Create a chat room for messaging:

```bash
curl -X POST http://localhost:8000/api/v1/rooms \
  -H "Authorization: Bearer ck_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "General Discussion",
    "room_type": "group",
    "description": "Main chat room for the team"
  }'
```

### 3. Send a Message

Send your first message to the room:

```bash
curl -X POST http://localhost:8000/api/v1/messages \
  -H "Authorization: Bearer ck_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": "ROOM_ID_FROM_STEP_2",
    "content": "Hello, ChatAPI!",
    "message_type": "text"
  }'
```

### 4. Send a Notification

Send a multi-channel notification:

```bash
curl -X POST http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer ck_live_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "to_email": "user@example.com",
    "subject": "Welcome to ChatAPI!",
    "content": "<h1>Welcome!</h1><p>Your account is now active.</p>",
    "email_fallback": {
      "enabled": true
    }
  }'
```

## Testing Real-time Features

### WebSocket Connection

Connect to WebSocket for real-time updates:

```javascript
// Browser/Node.js WebSocket client
const ws = new WebSocket("ws://localhost:8000/api/v1/websocket/open");

ws.onopen = function () {
	console.log("Connected to ChatAPI WebSocket");

	// Authenticate
	ws.send(
		JSON.stringify({
			type: "auth",
			token: "your_api_key_here",
		})
	);
};

ws.onmessage = function (event) {
	const data = JSON.parse(event.data);
	console.log("Received:", data);
};
```

### Socket.IO Client

For Socket.IO integration:

```javascript
import { io } from "socket.io-client";

const socket = io("http://localhost:8000", {
	path: "/sockets",
	auth: {
		token: "your_api_key_here",
	},
});

socket.on("connect", () => {
	console.log("Connected to ChatAPI");
});

socket.on("message", (data) => {
	console.log("New message:", data);
});
```

## Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=chatapi

# Security
SECRET_KEY=your-secret-key-here
CLIENT_KEY=your-client-key-here

# Redis
REDIS_URL=redis://localhost:6379

# Environment
ENVIRONMENT=local
DEBUG=true
```

### Database Migration

Apply database migrations:

```bash
# Check current migration status
alembic current

# Apply all pending migrations
alembic upgrade head

# Create new migration (for development)
alembic revision --autogenerate -m "description"
```

## Next Steps

Now that you have ChatAPI running:

1. **[Authentication](authentication.md)** - Learn about API keys and user management
2. **[API Guide](../api/overview.md)** - Explore all available endpoints
3. **[Notifications](../notifications/overview.md)** - Set up email providers and delivery
4. **[WebSockets](../api/websockets.md)** - Implement real-time features
5. **[Deployment](../deployment/production.md)** - Deploy to production

## Troubleshooting

### Common Issues

**Port already in use:**

```bash
# Find and kill process using port 8000
sudo lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.override.yml
```

**Database connection failed:**

```bash
# Check database logs
docker compose logs db

# Restart database
docker compose restart db
```

**Dependencies issues:**

```bash
# Clean rebuild
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up --build
```

### Getting Help

- **[GitHub Issues](https://github.com/Byabasaija/chatapi/issues)** - Bug reports and feature requests
- **[Discussions](https://github.com/Byabasaija/chatapi/discussions)** - Community support
- **[API Documentation](http://localhost:8000/docs)** - Interactive API explorer

## What's Next?

Continue with the [Authentication Guide](authentication.md) to learn about securing your API and managing users.
