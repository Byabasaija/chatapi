# Development Setup

This guide will help you set up a local development environment for ChatAPI, including hot reloading, debugging, and testing capabilities.

## Prerequisites

Before setting up the development environment, ensure you have:

- **Python 3.10+** - Required for the application
- **UV** - Python package manager (recommended)
- **Docker & Docker Compose** - For services (PostgreSQL, Redis)
- **Git** - For version control
- **VS Code** (optional) - Recommended IDE with Python extensions

## Quick Setup

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
uv sync --dev
```

Using pip:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Start Services

```bash
# Start PostgreSQL and Redis using Docker Compose
docker-compose up -d db redis

# Or start all services including the app
docker-compose up -d
```

### 4. Configure Environment

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql://chatapi_user:chatapi_password@localhost:5432/chatapi

# Redis
REDIS_URL=redis://localhost:6379

# API Configuration
SECRET_KEY=your-secret-key-for-development
API_V1_STR=/api/v1
PROJECT_NAME=ChatAPI

# CORS (allow frontend development servers)
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080", "http://localhost:5173"]

# Environment
ENVIRONMENT=development
DEBUG=true

# Logging
LOG_LEVEL=DEBUG
```

### 5. Initialize Database

```bash
# Run migrations
uv run alembic upgrade head

# Or if using pip
python -m alembic upgrade head
```

### 6. Start Development Server

```bash
# Start with hot reloading
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal, start Celery worker
uv run celery -A app.core.celery_app worker --loglevel=debug

# Optionally, start Celery Beat for scheduled tasks
uv run celery -A app.core.celery_app beat --loglevel=debug
```

## Development Workflow

### Code Formatting and Linting

```bash
# Format code with Black
uv run black app/ tests/

# Sort imports with isort
uv run isort app/ tests/

# Lint with flake8
uv run flake8 app/ tests/

# Type checking with mypy
uv run mypy app/

# Run all checks
./scripts/lint.sh
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/api/routes/test_messages.py

# Run tests with verbose output
uv run pytest -v

# Run tests in parallel
uv run pytest -n auto
```

### Database Management

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1

# Reset database (development only)
uv run alembic downgrade base
uv run alembic upgrade head
```

### Hot Reloading

The development server supports hot reloading for Python files:

- **FastAPI app** - Automatically reloads on code changes
- **Celery worker** - Restart manually or use `--reload` flag (experimental)
- **Database migrations** - Run manually when schema changes
- **Static files** - No server restart needed

### Debugging

#### VS Code Configuration

Create `.vscode/launch.json`:

```json
{
	"version": "0.2.0",
	"configurations": [
		{
			"name": "ChatAPI FastAPI",
			"type": "python",
			"request": "launch",
			"program": "${workspaceFolder}/.venv/bin/uvicorn",
			"args": [
				"app.main:app",
				"--host",
				"0.0.0.0",
				"--port",
				"8000",
				"--reload"
			],
			"env": {
				"PYTHONPATH": "${workspaceFolder}"
			},
			"console": "integratedTerminal"
		},
		{
			"name": "Celery Worker",
			"type": "python",
			"request": "launch",
			"module": "celery",
			"args": ["-A", "app.core.celery_app", "worker", "--loglevel=debug"],
			"env": {
				"PYTHONPATH": "${workspaceFolder}"
			},
			"console": "integratedTerminal"
		}
	]
}
```

#### Python Debugger

Add breakpoints in your code:

```python
import pdb; pdb.set_trace()  # Traditional debugger

# Or use ipdb for enhanced debugging
import ipdb; ipdb.set_trace()
```

#### Logging Configuration

Configure detailed logging for development:

```python
# app/core/config.py
import logging

if ENVIRONMENT == "development":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
```

## Testing

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                 # Test configuration and fixtures
├── api/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── test_clients.py     # Client API tests
│       ├── test_rooms.py       # Room API tests
│       ├── test_messages.py    # Message API tests
│       └── test_notifications.py # Notification API tests
├── services/
│   ├── __init__.py
│   ├── test_client_service.py  # Client service tests
│   └── test_message_service.py # Message service tests
├── workers/
│   ├── __init__.py
│   └── test_notification_tasks.py # Celery task tests
└── utils/
    ├── __init__.py
    └── utils.py                # Test utilities
```

### Test Configuration

The test suite uses:

- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **httpx** - HTTP client for API testing
- **fakeredis** - In-memory Redis for testing
- **pytest-cov** - Coverage reporting

### Writing Tests

#### API Tests

```python
# tests/api/routes/test_messages.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_send_message(
    client: AsyncClient,
    test_client_with_room: dict,
    auth_headers: dict
):
    room_id = test_client_with_room["room"]["id"]

    message_data = {
        "sender_id": "test_user",
        "sender_name": "Test User",
        "content": "Hello, world!",
        "message_type": "text"
    }

    response = await client.post(
        f"/api/v1/rooms/{room_id}/messages/",
        json=message_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["data"]["content"] == "Hello, world!"
    assert data["data"]["sender_name"] == "Test User"
```

#### Service Tests

```python
# tests/services/test_message_service.py
import pytest
from app.services.message import MessageService

@pytest.mark.asyncio
async def test_create_message(db_session, test_room):
    service = MessageService(db_session)

    message_data = {
        "room_id": test_room.id,
        "client_id": test_room.client_id,
        "sender_id": "test_user",
        "sender_name": "Test User",
        "content": "Test message",
        "message_type": "text"
    }

    message = await service.create(**message_data)

    assert message.content == "Test message"
    assert message.sender_name == "Test User"
    assert message.room_id == test_room.id
```

#### Worker Tests

```python
# tests/workers/test_notification_tasks.py
import pytest
from app.workers.notification_tasks import send_notification

@pytest.mark.asyncio
async def test_send_email_notification(
    db_session,
    test_client_with_email_config,
    mock_smtp
):
    notification_data = {
        "type": "email",
        "recipients": ["test@example.com"],
        "subject": "Test Subject",
        "content": "Test content"
    }

    result = await send_notification.apply_async(args=[notification_data])

    assert result.successful()
    assert mock_smtp.send_message.called
```

### Test Fixtures

Key test fixtures in `conftest.py`:

```python
@pytest.fixture
async def db_session():
    """Database session for testing."""
    # Creates isolated test database session

@pytest.fixture
async def client():
    """HTTP client for API testing."""
    # Creates test client with test database

@pytest.fixture
async def test_client():
    """Test client with API key."""
    # Creates client record for testing

@pytest.fixture
async def test_room(test_client):
    """Test room associated with test client."""
    # Creates room for testing

@pytest.fixture
async def auth_headers(test_client):
    """Authentication headers for requests."""
    return {"X-API-Key": test_client.api_key}
```

## Environment Configuration

### Development Environment Variables

Create different `.env` files for different scenarios:

#### `.env.development`

```env
DATABASE_URL=postgresql://chatapi_user:chatapi_password@localhost:5432/chatapi
REDIS_URL=redis://localhost:6379
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
```

#### `.env.testing`

```env
DATABASE_URL=postgresql://chatapi_user:chatapi_password@localhost:5432/chatapi_test
REDIS_URL=redis://localhost:6379/1
ENVIRONMENT=testing
DEBUG=true
LOG_LEVEL=DEBUG
```

#### `.env.local`

```env
# Local overrides (git ignored)
DATABASE_URL=postgresql://username:password@localhost:5432/chatapi_local
SECRET_KEY=local-development-key
```

### Loading Environment Files

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    environment: str = "development"
    database_url: str
    redis_url: str

    class Config:
        env_file = [".env.local", f".env.{os.getenv('ENV', 'development')}", ".env"]
        env_file_encoding = "utf-8"
```

## Database Development

### Schema Changes

When modifying models:

1. **Update the model** in `app/models/`
2. **Generate migration**:
   ```bash
   uv run alembic revision --autogenerate -m "Add new field to user model"
   ```
3. **Review the migration** file in `app/alembic/versions/`
4. **Apply migration**:
   ```bash
   uv run alembic upgrade head
   ```
5. **Update tests** if schema changes affect existing tests

### Seeding Data

Create seed data for development:

```python
# scripts/seed_data.py
from app.core.db import get_session
from app.services.client import ClientService

async def seed_development_data():
    async with get_session() as session:
        client_service = ClientService(session)

        # Create test client
        client = await client_service.create(
            name="Development Client",
            description="Client for local development"
        )

        print(f"Created client: {client.id} with API key: {client.api_key}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_development_data())
```

Run with: `uv run python scripts/seed_data.py`

## Monitoring and Debugging

### Application Monitoring

#### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Check database connection
curl http://localhost:8000/health/db

# Check Redis connection
curl http://localhost:8000/health/redis
```

#### Metrics Endpoint

```bash
# Get application metrics
curl http://localhost:8000/metrics
```

### Log Analysis

#### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "Message sent",
    room_id=room_id,
    sender_id=sender_id,
    message_type=message_type,
    recipients_count=len(recipients)
)
```

#### Log Levels

- **DEBUG** - Detailed information for debugging
- **INFO** - General information about application flow
- **WARNING** - Warning messages for potential issues
- **ERROR** - Error messages for handled exceptions
- **CRITICAL** - Critical errors that might stop the application

### Performance Profiling

#### Profile API Endpoints

```python
import cProfile
import pstats
from fastapi import Request

@app.middleware("http")
async def profile_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/") and "profile" in request.query_params:
        profiler = cProfile.Profile()
        profiler.enable()

        response = await call_next(request)

        profiler.disable()
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative")
        stats.print_stats(20)  # Top 20 functions

        return response

    return await call_next(request)
```

Usage: `curl "http://localhost:8000/api/v1/rooms/?profile=1"`

## IDE Configuration

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
	"python.defaultInterpreterPath": "./.venv/bin/python",
	"python.formatting.provider": "black",
	"python.linting.enabled": true,
	"python.linting.flake8Enabled": true,
	"python.linting.mypyEnabled": true,
	"python.testing.pytestEnabled": true,
	"python.testing.pytestArgs": ["tests"],
	"files.exclude": {
		"**/__pycache__": true,
		"**/.pytest_cache": true,
		"**/.mypy_cache": true
	}
}
```

### Recommended Extensions

- **Python** - Python language support
- **Pylance** - Python language server
- **Python Docstring Generator** - Auto-generate docstrings
- **Thunder Client** - API testing (alternative to Postman)
- **SQLite Viewer** - View SQLite databases
- **Docker** - Docker support

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

#### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### Redis Connection Issues

```bash
# Test Redis connection
redis-cli ping

# Check Docker container
docker-compose ps redis
```

#### Import Errors

```bash
# Ensure PYTHONPATH is set correctly
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# Or use UV which handles this automatically
uv run python -c "import app.main"
```

### Getting Help

- **Check logs** for detailed error messages
- **Use debugger** to step through code
- **Run tests** to ensure functionality works
- **Check documentation** for API usage
- **Open GitHub issues** for bugs or questions

## Next Steps

- [Testing](testing.md) - Learn about the testing framework
- [Architecture](architecture.md) - Understand the system design
- [Contributing](contributing.md) - Contribute to the project
