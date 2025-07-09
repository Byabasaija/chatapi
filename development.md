# ChatAPI - Development Guide

Welcome to the ChatAPI development guide! This document provides comprehensive instructions for setting up, developing, and contributing to the ChatAPI project - an open-source messaging and notifications API service.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Docker Development](#docker-development)
- [Local Development](#local-development)
- [Code Quality & Pre-commit](#code-quality--pre-commit)
- [Testing](#testing)
- [Database Operations](#database-operations)
- [Background Tasks](#background-tasks)
- [Real-time Features](#real-time-features)
- [Scripts Reference](#scripts-reference)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

ChatAPI is a high-performance, open-source messaging and notifications API service designed for in-app communication. It features:

- ⚡ **FastAPI** backend for high-performance APIs
- 🔔 **Real-time messaging** via WebSockets and Socket.IO
- 🔑 **API key-based authentication** for secure client access
- 💾 **PostgreSQL** with async SQLAlchemy/SQLModel
- 🏭 **Celery** for background task processing
- 🐋 **Full Docker** support for development and production

---

## Technology Stack

- **Backend:** FastAPI 0.114.2+, SQLModel, SQLAlchemy (async)
- **Database:** PostgreSQL 12+ with asyncpg driver
- **Real-time:** Socket.IO, WebSockets
- **Task Queue:** Celery with RabbitMQ
- **Authentication:** API keys with bcrypt hashing
- **Containerization:** Docker & Docker Compose
- **Testing:** Pytest with coverage reports
- **Code Quality:** Ruff (linting & formatting), MyPy, pre-commit
- **Migrations:** Alembic
- **Monitoring:** Sentry integration

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-started/) & [Docker Compose](https://docs.docker.com/compose/)
- [uv](https://docs.astral.sh/uv/) (for local development)
- Python 3.10+ (if developing without Docker)

### Environment Setup

1. **Clone and setup:**
   ```bash
   git clone https://github.com/Byabasaija/chatapi
   cd chatapi
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start the development stack:**
   ```bash
   docker compose up --build
   ```

3. **Access the services:**
   - **API:** http://localhost:8000
   - **API Docs:** http://localhost:8000/docs
   - **Adminer (DB UI):** http://localhost:8080
   - **Socket.IO:** ws://localhost:8000/sockets

---

## Docker Development

### Using Docker Compose

The project uses Docker Compose for orchestrated development with hot-reload:

```bash
# Start all services with hot-reload
docker compose up --build

# Start with watch mode (auto-rebuild on changes)
docker compose watch

# View logs
docker compose logs
docker compose logs api  # specific service

# Stop services
docker compose down -v --remove-orphans
```

### Individual Service Management

```bash
# Start specific services
docker compose up db adminer
docker compose start api

# Stop specific services
docker compose stop api

# Restart with rebuild
docker compose up --build api
```

### Container Access

```bash
# Access running API container
docker compose exec api bash

# Run commands in container
docker compose exec api python app/api_pre_start.py
docker compose exec api alembic upgrade head
```

---

## Local Development

### Setup without Docker

1. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

2. **Install dependencies:**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -e .
   ```

3. **Setup database:**
   ```bash
   # Start PostgreSQL (via Docker or local install)
   docker compose up db -d

   # Run migrations
   alembic upgrade head
   ```

4. **Start the API:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

## Code Quality & Pre-commit

We use [pre-commit](https://pre-commit.com/) for code quality enforcement with Ruff and MyPy.

### Setup Pre-commit

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

### Manual Code Quality

```bash
# Format code
bash scripts/format.sh
# or
uv run ruff format app scripts

# Lint code
bash scripts/lint.sh
# or
uv run ruff check app scripts --fix

# Type checking
uv run mypy app
```

### Pre-commit Configuration

The `.pre-commit-config.yaml` includes:
- **Ruff** for linting and formatting
- **YAML/TOML** validation
- **Large file** detection
- **Trailing whitespace** removal

---

## Testing

### Running Tests

```bash
# Run all tests with Docker
bash scripts/run-test.sh

# Run tests locally (without Docker)
bash scripts/test-local.sh

# Run specific tests
bash scripts/tests-start.sh

# Run tests with coverage
uv run pytest --cov=app --cov-report=html
```

### Test Structure

- **Unit tests:** `app/tests/api/routes/`
- **Integration tests:** `app/tests/scripts/`
- **Test utilities:** `app/tests/utils/`
- **Coverage reports:** `htmlcov/` directory

---

## Database Operations

### Migrations with Alembic

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade to specific revision
alembic downgrade <revision>

# View migration history
alembic history
```

### Database Access

```bash
# Access via Adminer UI
# http://localhost:8080
# Server: db, User: postgres, Password: (from .env)

# Direct database access
docker compose exec db psql -U postgres -d chatapi
```

---

## Background Tasks

### Celery Workers

The project uses Celery for background task processing:

```bash
# Start worker manually
bash scripts/worker-start.sh

# Access worker container
docker compose exec celeryworker bash

# Monitor tasks
docker compose logs celeryworker
```

### Task Examples

- Message processing
- Notification delivery
- Data cleanup tasks

---

## Real-time Features

### WebSocket Connections

- **FastAPI WebSockets:** `/api/v1/websocket/open`
- **Socket.IO:** `/sockets` endpoint

### Testing WebSockets

```bash
# Test WebSocket connection
wscat -c ws://localhost:8000/api/v1/websocket/open

# Test Socket.IO
# Use Socket.IO client or browser developer tools
```

---

## Scripts Reference

Available scripts in `scripts/` directory:

- **`format.sh`** - Format code with Ruff
- **`lint.sh`** - Lint code with Ruff
- **`migrate.sh`** - Run database migrations
- **`prestart.sh`** - Pre-start database checks
- **`run-test.sh`** - Run all tests with Docker
- **`test-local.sh`** - Run tests locally
- **`tests-start.sh`** - Start test suite
- **`worker-start.sh`** - Start Celery worker

---

## API Documentation

### Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/api/v1/openapi.json

### API Endpoints

- **Health Check:** `GET /api/v1/utils/health-check`
- **Client Management:** `/api/v1/clients/*`
- **Message Operations:** `/api/v1/messages/*`
- **WebSocket:** `/api/v1/websocket/*`

---

## Troubleshooting

### Common Issues

**Database connection issues:**
```bash
# Check database status
docker compose logs db

# Restart database
docker compose restart db

# Verify connection
docker compose exec api python app/api_pre_start.py
```

**Port conflicts:**
- Change exposed ports in `docker-compose.override.yml`
- Kill processes using the ports: `sudo lsof -ti:8000 | xargs kill -9`

**Dependency issues:**
```bash
# Clean rebuild
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up --build
```

**Migration problems:**
```bash
# Check migration status
alembic current

# Reset database (development only)
docker compose down -v
docker compose up db -d
alembic upgrade head
```

### Environment Variables

Ensure your `.env` file contains:
- `POSTGRES_*` variables for database connection
- `SECRET_KEY` for security
- `ENVIRONMENT=local` for development
- `CLIENT_KEY` for API authentication

---

## Contributing

### Development Workflow

1. **Fork and clone** the repository
2. **Create a feature branch:** `git checkout -b feature/your-feature`
3. **Make changes** and add tests
4. **Run quality checks:** `uv run pre-commit run --all-files`
5. **Run tests:** `bash scripts/test-local.sh`
6. **Commit with descriptive messages**
7. **Push and create a pull request**

### Code Standards

- Follow **PEP 8** style guidelines
- Use **type hints** for all functions
- Write **comprehensive tests**
- Document **complex logic**
- Keep **commits atomic** and well-described

---

For further questions, refer to the [README.md](README.md), check the [SECURITY.md](SECURITY.md) for security guidelines, or open a discussion on GitHub.


## MSC
                    ChatAPI Platform
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    │  Messaging Service     Notifications Service    │
    │  ┌──────────────┐    ┌──────────────────────┐  │
    │  │ • Rooms      │    │ • Webhooks           │  │
    │  │ • Messages   │    │ • Multi-channel      │  │
    │  │ • WebSockets │    │ • Templates          │  │
    │  │ • Real-time  │    │ • External Events    │  │
    │  └──────────────┘    └──────────────────────┘  │
    │           │                      │              │
    │           └──────────────────────┘              │
    │              Shared Foundation:                 │
    │           • Clients & API Keys                  │
    │           • Users & Authentication              │
    │           • Rate Limiting                       │
    │           • Analytics                           │
    └─────────────────────────────────────────────────┘


    External System        ChatAPI Platform         End Users
     │                       │                      │
     │  POST /webhooks/      │                      │
     │  client1/user-events  │                      │
     ├──────────────────────►│                      │
     │                       │                      │
     │                       │ Process Event        │
     │                       │ ├─ Create room?      │
     │                       │ ├─ Send message?     │
     │                       │ ├─ Send email?       │
     │                       │ └─ Push notification?│
     │                       │                      │
     │                       ├─────────────────────►│
     │                       │                      │
     │ 200 OK Response       │                      │
     │◄──────────────────────┤                      │


     Great idea! Let me summarize everything we've agreed upon in this conversation to ensure we're aligned:

## **✅ Agreed Upon: Chat API + Notifications System**

### **1. Core Architecture:**
- **Dual-purpose system**: Messaging (chat rooms) + Notifications (multi-channel delivery)
- **API-only service**: No UI, pure backend infrastructure
- **Open source tool**: Standards-based, vendor-agnostic approach

### **2. Authentication System:**
- **Always-rotate on login**: Every user login creates new API key and revokes old one
- **Master + Scoped keys**: Master keys for admin operations, scoped keys for users
- **Security benefits**: Fresh credentials, automatic cleanup, simplified frontend logic

### **3. Room Management:**
- **Room-based messaging**: Users join rooms for conversations
- **Auto-deactivation by room type**:
  - `support`: 7 days (helpdesk rooms)
  - `group`: 30 days
  - `direct`: 90 days
  - `channel`: 180 days
- **Auto-reactivation**: Sending message to inactive room reactivates it
- **Admin room listing**: `GET /rooms/all` with master key returns all client rooms

### **4. Infrastructure Changes:**
- **Switch from RabbitMQ to Redis**: Simpler setup, multi-purpose (cache + job queue)
- **Redis + Celery**: For background jobs (room cleanup, notification processing)

### **5. Notifications System Design:**
- **Pure relay/orchestrator**: No template management on our side
- **Client-owned content**: Clients send ready-to-send content (HTML emails, message text)
- **Multi-channel delivery**: Email, WebSocket, Push, SMS in single API call
- **Webhook-based**: External systems POST events to our webhooks for processing

### **6. Notification Channels (Tier 1):**
- **WebSocket**: Real-time in-app notifications (existing infrastructure)
- **Email**: SMTP integration with client-provided content
- **Webhook**: Forward to other systems (maximum flexibility)

### **7. Value Proposition:**
> **"We don't manage your content - we guarantee it gets delivered."**

- **Multi-channel delivery** in one API call
- **Delivery tracking** and analytics
- **Provider abstraction** (clients don't manage SMTP/providers directly)
- **Reliability** (retries, failovers, monitoring)
- **Rate limiting** and compliance

### **8. API Design Philosophy:**
- **Ready-to-send content**: Clients provide fully-formed emails, messages, etc.
- **No template system**: Zero template complexity on our side
- **Provider agnostic**: Support any email/SMS provider via client configuration
- **Immediate value**: No setup time, just send notifications

### **9. Use Case Examples:**
- **Helpdesk widget**: Creates support rooms, admin dashboard lists all rooms
- **E-commerce notifications**: Order confirmations via email + push + websocket
- **User management**: Signup notifications, password resets, etc.

## **Next Steps We Haven't Implemented Yet:**
1. **Redis migration** from RabbitMQ
2. **Notification models** and API endpoints
3. **Webhook management** system
4. **Multi-channel delivery** engines
5. **Background job processing** for notifications

## **Questions Still Open:**
1. **Provider configuration**: How clients configure their SMTP/SMS providers
2. **Webhook direction**: Who registers webhooks and the flow details
3. **Rate limiting specifics**: Exact limits per channel
4. **Analytics scope**: What metrics to track

Does this accurately capture our alignment? Did I miss anything or misrepresent any decisions?


🎯 Implementation Roadmap: Notifications System
Phase 1: Foundation & Infrastructure
Step 1: Redis Migration & Background Jobs
<input disabled="" type="checkbox"> 1.1 Update docker-compose.yml - Replace RabbitMQ with Redis
<input disabled="" type="checkbox"> 1.2 Update celery_app.py - Configure Redis as broker
<input disabled="" type="checkbox"> 1.3 Create app/tasks.py - Basic Celery task structure
<input disabled="" type="checkbox"> 1.4 Test Redis + Celery integration
<input disabled="" type="checkbox"> 1.5 Update environment variables and settings
Step 2: Database Models for Notifications
<input disabled="" type="checkbox"> 2.1 Create app/models/notification.py - Core notification models
<input disabled="" type="checkbox"> 2.2 Create app/models/webhook.py - Webhook management models
<input disabled="" type="checkbox"> 2.3 Create app/models/email_config.py - Client email configuration
<input disabled="" type="checkbox"> 2.4 Generate and run Alembic migrations
<input disabled="" type="checkbox"> 2.5 Test database schema
Step 3: Provider Architecture Foundation
<input disabled="" type="checkbox"> 3.1 Create app/providers/__init__.py - Provider package
<input disabled="" type="checkbox"> 3.2 Create app/providers/base.py - Abstract provider interface
<input disabled="" type="checkbox"> 3.3 Create app/providers/registry.py - Provider registry system
<input disabled="" type="checkbox"> 3.4 Test provider architecture foundation
Phase 2: Email Providers Implementation
Step 4: SMTP Provider (Transactional)
<input disabled="" type="checkbox"> 4.1 Create app/providers/smtp.py - SMTP provider implementation
<input disabled="" type="checkbox"> 4.2 Create app/services/email_config.py - Client email config service
<input disabled="" type="checkbox"> 4.3 Add email configuration API endpoints
<input disabled="" type="checkbox"> 4.4 Test SMTP sending with client configurations
<input disabled="" type="checkbox"> 4.5 Add encryption for SMTP credentials
Step 5: Mailgun Provider (Bulk)
<input disabled="" type="checkbox"> 5.1 Create app/providers/mailgun.py - Mailgun provider implementation
<input disabled="" type="checkbox"> 5.2 Add Mailgun configuration to settings
<input disabled="" type="checkbox"> 5.3 Implement bulk sending logic
<input disabled="" type="checkbox"> 5.4 Test Mailgun integration
<input disabled="" type="checkbox"> 5.5 Add Mailgun webhook handling for delivery tracking
Step 6: Smart Routing Logic
<input disabled="" type="checkbox"> 6.1 Create app/services/notification.py - Core notification service
<input disabled="" type="checkbox"> 6.2 Implement auto-detection logic (SMTP vs Mailgun)
<input disabled="" type="checkbox"> 6.3 Add volume thresholds and routing rules
<input disabled="" type="checkbox"> 6.4 Test routing with different recipient counts
<input disabled="" type="checkbox"> 6.5 Add configuration for custom thresholds
Phase 3: API Endpoints & Webhook System
Step 7: Webhook Management
<input disabled="" type="checkbox"> 7.1 Create app/api/api_v1/routes/webhook.py - Webhook CRUD endpoints
<input disabled="" type="checkbox"> 7.2 Create app/services/webhook.py - Webhook service layer
<input disabled="" type="checkbox"> 7.3 Implement webhook URL generation and validation
<input disabled="" type="checkbox"> 7.4 Add signature verification for incoming webhooks
<input disabled="" type="checkbox"> 7.5 Test webhook registration and event receiving
Step 8: Notification API Endpoints
<input disabled="" type="checkbox"> 8.1 Create app/api/api_v1/routes/notification.py - Notification endpoints
<input disabled="" type="checkbox"> 8.2 Create app/schemas/notification.py - Notification schemas
<input disabled="" type="checkbox"> 8.3 Implement /notifications/send endpoint
<input disabled="" type="checkbox"> 8.4 Add notification history and tracking endpoints
<input disabled="" type="checkbox"> 8.5 Test complete notification flow
Step 9: Background Processing
<input disabled="" type="checkbox"> 9.1 Create notification processing tasks in app/tasks.py
<input disabled="" type="checkbox"> 9.2 Implement queue-based notification dispatch
<input disabled="" type="checkbox"> 9.3 Add retry logic for failed notifications
<input disabled="" type="checkbox"> 9.4 Implement delivery tracking and status updates
<input disabled="" type="checkbox"> 9.5 Test background processing with Redis + Celery
Phase 4: Integration & Polish
Step 10: Rate Limiting & Validation
<input disabled="" type="checkbox"> 10.1 Implement rate limiting per client and provider
<input disabled="" type="checkbox"> 10.2 Add notification content validation
<input disabled="" type="checkbox"> 10.3 Add daily/hourly limits enforcement
<input disabled="" type="checkbox"> 10.4 Test rate limiting behavior
<input disabled="" type="checkbox"> 10.5 Add rate limit status in API responses
Step 11: Analytics & Monitoring
<input disabled="" type="checkbox"> 11.1 Create delivery analytics models
<input disabled="" type="checkbox"> 11.2 Implement analytics collection in background tasks
<input disabled="" type="checkbox"> 11.3 Add analytics API endpoints
<input disabled="" type="checkbox"> 11.4 Create notification dashboard data
<input disabled="" type="checkbox"> 11.5 Test analytics tracking
Step 12: Error Handling & Logging
<input disabled="" type="checkbox"> 12.1 Add comprehensive error handling across all providers
<input disabled="" type="checkbox"> 12.2 Implement structured logging for notifications
<input disabled="" type="checkbox"> 12.3 Add error tracking and reporting
<input disabled="" type="checkbox"> 12.4 Create failure notification webhooks
<input disabled="" type="checkbox"> 12.5 Test error scenarios and recovery
Phase 5: Testing & Documentation
Step 13: Integration Testing
<input disabled="" type="checkbox"> 13.1 Create end-to-end notification tests
<input disabled="" type="checkbox"> 13.2 Test webhook-to-notification flow
<input disabled="" type="checkbox"> 13.3 Test multi-channel notification sending
<input disabled="" type="checkbox"> 13.4 Performance testing with high volumes
<input disabled="" type="checkbox"> 13.5 Test provider failover scenarios
Step 14: Documentation & Examples
<input disabled="" type="checkbox"> 14.1 Update API documentation
<input disabled="" type="checkbox"> 14.2 Create notification system documentation
<input disabled="" type="checkbox"> 14.3 Add provider configuration guides
<input disabled="" type="checkbox"> 14.4 Create integration examples
<input disabled="" type="checkbox"> 14.5 Update main README with notification features
🎯 Current Priority: Phase 1, Step 1
Next Action: Start with Redis migration to replace RabbitMQ

Estimated Timeline:

Phase 1: 2-3 days
Phase 2: 3-4 days
Phase 3: 4-5 days
Phase 4: 2-3 days
Phase 5: 2-3 days
Total: ~2 weeks for complete notifications system
