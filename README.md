# ChatAPI

A **plug-and-play** messaging and notifications API service for in-app communication.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.114.2+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker Hub](https://img.shields.io/docker/pulls/chatapi/chatapi.svg)](https://hub.docker.com/r/chatapi/chatapi)

---

## Overview

ChatAPI is a **simple, plug-and-play service** similar to RocketChat - just run 3 containers and you're ready to go! Built with FastAPI and designed for easy deployment, it offers enterprise-grade messaging with minimal setup complexity.

## ✨ Key Features

- � **Plug & Play** - Just 3 services: `chatapi`, `db`, `redis` - that's it!
- �🚀 **High Performance** - Async FastAPI with bundled background workers
- 💬 **Real-time Messaging** - WebSocket support with Redis pub/sub
- 🔐 **Secure by Default** - API key authentication, encryption at rest
- 🏢 **Multi-tenant** - Room-based isolation, client separation
- 📧 **Email Providers** - SMTP, Mailgun, SendGrid, Postmark, SES support
- 🐳 **Docker Ready** - Official image on Docker Hub
- 📚 **Auto Documentation** - Interactive API docs with Swagger UI
- ⚖️ **Production Ready** - Background tasks, health checks, monitoring

## 🏗 Simple Architecture

Unlike complex microservices setups, ChatAPI follows the **RocketChat model**:

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   chatapi   │───▶│ PostgreSQL   │    │   Redis     │
│ (bundled)   │    │    (db)      │    │ (pub/sub)   │
│ • API       │    │              │    │             │
│ • Workers   │    └──────────────┘    └─────────────┘
│ • WebSocket │
└─────────────┘
```

**That's it!** No separate worker containers, no complex orchestration.

## 🛠 Technology Stack

| Component          | Technology                                     |
| ------------------ | ---------------------------------------------- |
| **Backend**        | FastAPI 0.114.2+, SQLModel, SQLAlchemy (async) |
| **Database**       | PostgreSQL 12+ with asyncpg driver             |
| **Real-time**      | WebSockets, Redis pub/sub                      |
| **Task Queue**     | Celery (bundled with main app)                 |
| **Authentication** | API keys with bcrypt hashing                   |
| **Deployment**     | Docker Hub official image                      |
| **Testing**        | Pytest with coverage                           |
| **Code Quality**   | Ruff, MyPy, pre-commit hooks                   |

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-started/) and [Docker Compose](https://docs.docker.com/compose/)

### Installation

**Option 1: Using Docker Hub (Recommended)**

Create a `docker-compose.yml` file:

```yaml
version: "3.8"

services:
  # ChatAPI - Main application with bundled workers
  chatapi:
    image: chatapi/chatapi:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - SECRET_KEY=change-this-to-a-secure-random-string
      - POSTGRES_SERVER=db
      - POSTGRES_DB=chatapi
      - POSTGRES_USER=chatapi
      - POSTGRES_PASSWORD=chatapi_password
      - REDIS_URL=redis://redis:6379/0
      - BACKEND_CORS_ORIGINS=["http://localhost:3000"]
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # PostgreSQL Database
  db:
    image: postgres:12
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chatapi -d chatapi"]
      interval: 10s
      retries: 5
    environment:
      - POSTGRES_DB=chatapi
      - POSTGRES_USER=chatapi
      - POSTGRES_PASSWORD=chatapi_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis for real-time messaging and caching
  redis:
    image: redis:7-alpine
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Start the services:

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs chatapi
```

**Option 2: Development from Source**

```bash
git clone https://github.com/Byabasaija/chatapi.git
cd chatapi
cp .env.example .env
docker compose up --build
```

**Access the application:**

- **API:** http://localhost:8000
- **Interactive Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/utils/health-check

### API Usage Example

```bash
# Health check
curl http://localhost:8000/api/v1/utils/health-check

# Create API client (requires authentication)
curl -X POST "http://localhost:8000/api/v1/clients/" \
  -H "Content-Type: application/json" \
  -d '{"name": "My App", "encryption_mode": "none"}'
```

## 📖 Documentation

- **[Development Guide](development.md)** - Comprehensive development setup and workflows
- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI (when running)
- **[Security Guidelines](SECURITY.md)** - Security policies and reporting

## 🧪 Testing

```bash
# Run all tests
bash scripts/run-test.sh

# Run tests locally
bash scripts/test-local.sh
```

Coverage reports are available in the `htmlcov/` directory after running tests.

## 🔒 Security

Security is our top priority. If you discover a vulnerability:

- **Do not** create a public issue
- **Email:** basaijapascal9@gmail.com
- Include detailed reproduction steps
- Allow time for assessment and patching

See [SECURITY.md](SECURITY.md) for our complete security policy.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Read the [Development Guide](development.md)** for setup instructions
2. **Fork** the repository and create a feature branch
3. **Make your changes** with tests and documentation
4. **Submit a pull request** with a clear description

For questions or discussions, use [GitHub Discussions](https://github.com/Byabasaija/chatapi/discussions).

### Development Quick Start

For detailed development instructions, see [development.md](development.md). Quick commands:

```bash
# Format code
bash scripts/format.sh

# Lint code
bash scripts/lint.sh

# Run migrations
alembic upgrade head
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **[GitHub Repository](https://github.com/Byabasaija/chatapi)**
- **[Issue Tracker](https://github.com/Byabasaija/chatapi/issues)**
- **[Discussions](https://github.com/Byabasaija/chatapi/discussions)**

---

**Built with ❤️ by [Pascal Byabasaija](https://github.com/Byabasaija)**
