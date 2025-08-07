# Installation

This guide will help you install and set up ChatAPI for development, production, or integration into your existing project.

## Prerequisites

Before installing ChatAPI, ensure you have the following installed:

- **Docker & Docker Compose** - For containerized deployment (recommended)
- **Python 3.10+** - Required only for local development

## Architecture Overview

ChatAPI is designed as a **plug-and-play service** similar to RocketChat. It consists of just **3 simple services**:

- **`chatapi`** - Main application (includes API server + background workers bundled together)
- **`db`** - PostgreSQL database for data persistence
- **`redis`** - Redis for real-time messaging and caching

That's it! No complex microservices to manage.

## Using ChatAPI from Docker Hub (Recommended)

The easiest way to get started is by using the official Docker image from Docker Hub:

### Option 1: Quick Start with Docker Compose

Create a `docker-compose.yml` file in your project:

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
      - SECRET_KEY=your-super-secret-key-change-this-in-production
      - DATABASE_URL=postgresql://chatapi:chatapi_password@db:5432/chatapi
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # PostgreSQL Database - Required for ChatAPI data persistence
  db:
    image: postgres:12
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chatapi -d chatapi"]
      interval: 10s
      retries: 5
      start_period: 30s
      timeout: 10s
    environment:
      - POSTGRES_DB=chatapi
      - POSTGRES_USER=chatapi
      - POSTGRES_PASSWORD=chatapi_password
    volumes:
      - postgres_data:/var/lib/postgresql/data/pgdata
      - PGDATA=/var/lib/postgresql/data/pgdata

  # Redis - Required for ChatAPI pub/sub and caching
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
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  redis_data:
```

Then start the services:

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs chatapi
```

### Option 2: Add to Existing Docker Compose

If you already have a `docker-compose.yml`, add ChatAPI as a service:

```yaml
services:
  # ... your existing services ...

  chatapi:
    image: chatapi/chatapi:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - SECRET_KEY=your-super-secret-key-change-this-in-production
      - POSTGRES_SERVER=chatapi-db
      - POSTGRES_PORT=5432
      - POSTGRES_DB=chatapi
      - POSTGRES_USER=chatapi
      - POSTGRES_PASSWORD=chatapi_password
      - REDIS_URL=redis://chatapi-redis:6379/0
      - CELERY_BROKER_URL=redis://chatapi-redis:6379/0
      - CELERY_RESULT_BACKEND=redis://chatapi-redis:6379/0
      - SECRET_KEY=${CHATAPI_SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - chatapi-db
      - chatapi-redis

  chatapi-db:
    image: postgres:12
    environment:
      - POSTGRES_DB=chatapi
      - POSTGRES_USER=chatapi
      - POSTGRES_PASSWORD=${CHATAPI_DB_PASSWORD}
    volumes:
      - chatapi_db:/var/lib/postgresql/data

  chatapi-redis:
    image: redis:7-alpine
    volumes:
      - chatapi_redis:/data

    depends_on:
      - chatapi-db
      - chatapi-redis

  chatapi-db:
    image: postgres:12
    environment:
      - POSTGRES_DB=chatapi
      - POSTGRES_USER=chatapi
      - POSTGRES_PASSWORD=chatapi_password
    volumes:
      - chatapi_db:/var/lib/postgresql/data

  chatapi-redis:
    image: redis:7-alpine
    volumes:
      - chatapi_redis:/data

volumes:
  chatapi_db:
  chatapi_redis:
```

### Option 3: Using Docker Run Commands

For more control, run containers individually:

```bash
# Create network
docker network create chatapi-network

# Start PostgreSQL
docker run -d \
  --name chatapi-postgres \
  --network chatapi-network \
  -e POSTGRES_DB=chatapi \
  -e POSTGRES_USER=chatapi \
  -e POSTGRES_PASSWORD=chatapi_password \
  -v chatapi-postgres-data:/var/lib/postgresql/data \
  postgres:12

# Start Redis
docker run -d \
  --name chatapi-redis \
  --network chatapi-network \
  -v chatapi-redis-data:/data \
  redis:7-alpine

# Start ChatAPI (includes bundled workers)
docker run -d \
  --name chatapi-app \
  --network chatapi-network \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e SECRET_KEY=your-super-secret-key-change-this-in-production \
  -e POSTGRES_SERVER=chatapi-postgres \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=chatapi \
  -e POSTGRES_USER=chatapi \
  -e POSTGRES_PASSWORD=chatapi_password \
  -e REDIS_URL=redis://chatapi-redis:6379/0 \
  -e CELERY_BROKER_URL=redis://chatapi-redis:6379/0 \
  -e CELERY_RESULT_BACKEND=redis://chatapi-redis:6379/0 \
  chatapi/chatapi:latest
```

That's it! No need for separate worker containers - everything runs in the main ChatAPI container.

The API will be available at `http://localhost:8000`.

## Development Installation (Source Code)

If you want to modify ChatAPI or contribute to the project:

```bash
# Clone the repository
git clone https://github.com/Byabasaija/chatapi.git
cd chatapi

# Start all services
docker-compose up -d
```

This will start:

- ChatAPI application on port 8000
- PostgreSQL database on port 5432
- Redis on port 6379
- Celery worker for background tasks

## Manual Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Byabasaija/chatapi.git
cd chatapi
```

### 2. Set Up Python Environment

Using UV (recommended):

```bash
# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync
```

Using pip:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Set Up Database

Install and start PostgreSQL, then create a database:

```sql
CREATE DATABASE chatapi;
CREATE USER chatapi_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE chatapi TO chatapi_user;
```

### 4. Set Up Redis

Install and start Redis:

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# macOS with Homebrew
brew install redis
brew services start redis

# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

### 5. Environment Configuration

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://chatapi_user:your_password@localhost/chatapi

# Redis
REDIS_URL=redis://localhost:6379

# API Configuration
SECRET_KEY=your-secret-key-here
API_V1_STR=/api/v1
PROJECT_NAME=ChatAPI

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Environment
ENVIRONMENT=development
```

### 6. Database Migration

Run database migrations:

```bash
# Using UV
uv run alembic upgrade head

# Using Python directly
python -m alembic upgrade head
```

### 7. Start the Application

```bash
# Start the web server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start the Celery worker
uv run celery -A app.core.celery_app worker --loglevel=info

# Optionally, start Celery Beat for scheduled tasks
uv run celery -A app.core.celery_app beat --loglevel=info
```

## Development Setup

For development, you'll want hot reloading and debugging capabilities:

```bash
# Install development dependencies
uv sync --dev

# Start with auto-reload
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
uv run pytest

# Format code
uv run black app/
uv run isort app/

# Lint code
uv run flake8 app/
```

## Verification

Once installed, verify the installation:

1. **API Health Check**: Visit `http://localhost:8000/health`
2. **API Documentation**: Visit `http://localhost:8000/docs`
3. **Create a Client**: Use the API to create your first client

```bash
curl -X POST "http://localhost:8000/api/v1/clients/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Client", "description": "My first client"}'
```

## Docker Compose Services

The `docker-compose.yml` includes these services:

| Service | Port | Description                    |
| ------- | ---- | ------------------------------ |
| web     | 8000 | Main ChatAPI application       |
| db      | 5432 | PostgreSQL database            |
| redis   | 6379 | Redis cache and message broker |
| worker  | -    | Celery background worker       |
| beat    | -    | Celery task scheduler          |

## Troubleshooting

### Common Issues

**Port Already in Use**

```bash
# Check what's using port 8000
lsof -i :8000
# Kill the process or change the port
```

**Database Connection Issues**

- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists

**Redis Connection Issues**

- Verify Redis is running: `redis-cli ping`
- Check Redis URL in configuration

**Permission Issues**

```bash
# Fix file permissions
chmod +x scripts/*.sh
```

### Getting Help

- Check the [API Documentation](http://localhost:8000/docs)
- Review [logs](../development/setup.md#logging)
- Open an [issue on GitHub](https://github.com/Byabasaija/chatapi/issues)

## Next Steps

After installation:

1. [Quick Start Guide](quick-start.md) - Create your first client and send messages
2. [Authentication](authentication.md) - Set up API authentication
3. [API Guide](../api/overview.md) - Explore all available endpoints
