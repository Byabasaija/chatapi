# Installation

This guide will help you install and set up ChatAPI for development or production use.

## Prerequisites

Before installing ChatAPI, ensure you have the following installed:

- **Python 3.10+** - Required for running the application
- **Docker & Docker Compose** - For containerized deployment (recommended)
- **Redis** - For background job processing and caching
- **PostgreSQL** - For data persistence
- **UV** - Python package manager (optional but recommended)

## Quick Installation with Docker

The fastest way to get started is using Docker Compose:

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

The API will be available at `http://localhost:8000`.

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
