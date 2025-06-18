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
