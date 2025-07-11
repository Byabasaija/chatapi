# Testing

ChatAPI uses a comprehensive testing strategy to ensure reliability, performance, and security across all components.

## Testing Strategy

### Test Pyramid

```mermaid
graph TB
    subgraph "Test Pyramid"
        E2E[End-to-End Tests<br/>~5%]
        Integration[Integration Tests<br/>~15%]
        Unit[Unit Tests<br/>~80%]
    end

    E2E --> Integration
    Integration --> Unit

    style Unit fill:#4CAF50
    style Integration fill:#FF9800
    style E2E fill:#F44336
```

## Test Environment Setup

### Prerequisites

```bash
# Install development dependencies
uv sync --dev

# Set up test database
export DATABASE_URL="postgresql://test_user:test_pass@localhost:5432/chatapi_test"

# Start required services
docker-compose -f docker-compose.test.yml up -d
```

### Configuration

Create a test configuration file:

```python
# tests/config.py
import os
from app.core.config import Settings

class TestSettings(Settings):
    testing: bool = True
    database_url: str = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql://test_user:test_pass@localhost:5432/chatapi_test"
    )
    redis_url: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = True
    email_test_mode: bool = True
```

## Unit Tests

### Testing Models

```python
# tests/test_models/test_client.py
import pytest
from sqlalchemy.orm import Session
from app.models.client import Client
from app.schemas.client import ClientCreate

def test_create_client(db: Session):
    """Test client creation."""
    client_data = ClientCreate(
        email="test@example.com",
        name="Test Client"
    )

    client = Client(**client_data.dict())
    db.add(client)
    db.commit()
    db.refresh(client)

    assert client.id is not None
    assert client.email == "test@example.com"
    assert client.name == "Test Client"
    assert client.created_at is not None

def test_client_str_representation(db: Session):
    """Test client string representation."""
    client = Client(email="test@example.com", name="Test Client")
    assert str(client) == "Test Client <test@example.com>"
```

### Testing Services

```python
# tests/test_services/test_client_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.client import ClientService
from app.schemas.client import ClientCreate, ClientUpdate

@pytest.fixture
def client_service():
    return ClientService()

@pytest.mark.asyncio
async def test_create_client(client_service, db):
    """Test client creation through service."""
    client_data = ClientCreate(
        email="service@example.com",
        name="Service Test Client"
    )

    client = await client_service.create(db, obj_in=client_data)

    assert client.email == "service@example.com"
    assert client.name == "Service Test Client"

@pytest.mark.asyncio
async def test_get_client_by_email(client_service, db, test_client):
    """Test retrieving client by email."""
    client = await client_service.get_by_email(db, email=test_client.email)

    assert client is not None
    assert client.email == test_client.email

@pytest.mark.asyncio
async def test_update_client(client_service, db, test_client):
    """Test client update."""
    update_data = ClientUpdate(name="Updated Name")

    updated_client = await client_service.update(
        db, db_obj=test_client, obj_in=update_data
    )

    assert updated_client.name == "Updated Name"
    assert updated_client.email == test_client.email
```

### Testing API Endpoints

```python
# tests/test_api/test_clients.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_client_endpoint():
    """Test client creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/clients/",
            json={
                "email": "api@example.com",
                "name": "API Test Client"
            },
            headers={"Authorization": "Bearer test_token"}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "api@example.com"
    assert data["name"] == "API Test Client"

@pytest.mark.asyncio
async def test_get_client_endpoint(test_client):
    """Test client retrieval endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(
            f"/api/v1/clients/{test_client.id}",
            headers={"Authorization": "Bearer test_token"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_client.id)

@pytest.mark.asyncio
async def test_unauthorized_access():
    """Test unauthorized access returns 401."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/clients/")

    assert response.status_code == 401
```

## Integration Tests

### Database Integration

```python
# tests/test_integration/test_database.py
import pytest
from sqlalchemy.orm import Session
from app.services.client import ClientService
from app.services.room import RoomService
from app.services.message import MessageService

@pytest.mark.asyncio
async def test_client_room_message_flow(db: Session):
    """Test complete flow from client to message."""
    client_service = ClientService()
    room_service = RoomService()
    message_service = MessageService()

    # Create client
    client = await client_service.create(db, obj_in={
        "email": "integration@example.com",
        "name": "Integration Test"
    })

    # Create room for client
    room = await room_service.create(db, obj_in={
        "name": "Test Room",
        "client_id": client.id
    })

    # Send message in room
    message = await message_service.create(db, obj_in={
        "content": "Hello, World!",
        "room_id": room.id,
        "sender_id": client.id
    })

    # Verify relationships
    assert message.room_id == room.id
    assert message.sender_id == client.id
    assert room.client_id == client.id
```

### External API Integration

```python
# tests/test_integration/test_email_provider.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.notifications.email import EmailNotificationService

@pytest.mark.asyncio
async def test_smtp_provider_integration():
    """Test SMTP provider integration."""
    email_service = EmailNotificationService()

    with patch('smtplib.SMTP_SSL') as mock_smtp:
        mock_server = AsyncMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = await email_service.send_email(
            to="test@example.com",
            subject="Test Email",
            content="Test content"
        )

        assert result.success is True
        mock_server.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_webhook_delivery():
    """Test webhook delivery integration."""
    from app.services.webhooks import WebhookService

    webhook_service = WebhookService()

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = await webhook_service.deliver_webhook(
            url="https://example.com/webhook",
            payload={"event": "test"},
            secret="webhook_secret"
        )

        assert result.delivered is True
        mock_post.assert_called_once()
```

## End-to-End Tests

### API Workflow Tests

```python
# tests/test_e2e/test_notification_flow.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_complete_notification_flow():
    """Test complete notification flow from API to delivery."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Create client
        client_response = await ac.post(
            "/api/v1/clients/",
            json={"email": "e2e@example.com", "name": "E2E Test"},
            headers={"Authorization": "Bearer test_token"}
        )
        assert client_response.status_code == 201
        client_id = client_response.json()["id"]

        # 2. Create room
        room_response = await ac.post(
            "/api/v1/rooms/",
            json={"name": "E2E Room", "client_id": client_id},
            headers={"Authorization": "Bearer test_token"}
        )
        assert room_response.status_code == 201
        room_id = room_response.json()["id"]

        # 3. Send message
        message_response = await ac.post(
            "/api/v1/messages/",
            json={
                "content": "E2E test message",
                "room_id": room_id,
                "sender_id": client_id
            },
            headers={"Authorization": "Bearer test_token"}
        )
        assert message_response.status_code == 201
        message_id = message_response.json()["id"]

        # 4. Send notification
        notification_response = await ac.post(
            "/api/v1/notifications/",
            json={
                "type": "email",
                "recipient_id": client_id,
                "message_id": message_id,
                "template": "new_message"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        assert notification_response.status_code == 201

        # 5. Check notification status
        notification_id = notification_response.json()["id"]
        status_response = await ac.get(
            f"/api/v1/notifications/{notification_id}",
            headers={"Authorization": "Bearer test_token"}
        )
        assert status_response.status_code == 200
        assert status_response.json()["status"] in ["pending", "sent", "delivered"]
```

## Performance Tests

### Load Testing

```python
# tests/test_performance/test_load.py
import asyncio
import time
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_api_performance():
    """Test API performance under load."""
    async def make_request(client, endpoint):
        response = await client.get(
            endpoint,
            headers={"Authorization": "Bearer test_token"}
        )
        return response.status_code

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Warm up
        await make_request(ac, "/api/v1/health")

        # Load test
        start_time = time.time()
        tasks = [
            make_request(ac, "/api/v1/clients/")
            for _ in range(100)
        ]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Assertions
        duration = end_time - start_time
        successful_requests = sum(1 for status in results if status == 200)

        assert successful_requests >= 95  # 95% success rate
        assert duration < 10  # Under 10 seconds for 100 requests

        requests_per_second = len(results) / duration
        assert requests_per_second > 10  # At least 10 RPS
```

### Database Performance

```python
# tests/test_performance/test_database.py
import pytest
import time
from sqlalchemy.orm import Session
from app.models.message import Message

def test_bulk_insert_performance(db: Session):
    """Test bulk insert performance."""
    messages = [
        Message(
            content=f"Test message {i}",
            room_id="test_room_id",
            sender_id="test_sender_id"
        )
        for i in range(1000)
    ]

    start_time = time.time()
    db.bulk_save_objects(messages)
    db.commit()
    end_time = time.time()

    duration = end_time - start_time
    assert duration < 1.0  # Should complete in under 1 second

def test_query_performance(db: Session, test_messages):
    """Test query performance."""
    start_time = time.time()

    # Query with pagination
    messages = db.query(Message)\
        .filter(Message.room_id == "test_room")\
        .order_by(Message.created_at.desc())\
        .limit(50)\
        .all()

    end_time = time.time()
    duration = end_time - start_time

    assert duration < 0.1  # Should complete in under 100ms
    assert len(messages) <= 50
```

## Test Fixtures

### Database Fixtures

```python
# tests/conftest.py
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base_class import Base
from app.core.config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = settings.test_database_url
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db():
    """Create test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_client(db):
    """Create test client."""
    from app.models.client import Client
    client = Client(
        email="test@example.com",
        name="Test Client"
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@pytest.fixture
def test_room(db, test_client):
    """Create test room."""
    from app.models.room import Room
    room = Room(
        name="Test Room",
        client_id=test_client.id
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room
```

### Mock Fixtures

```python
# tests/fixtures/mocks.py
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def mock_email_provider():
    """Mock email provider."""
    provider = AsyncMock()
    provider.send_email.return_value = {
        "success": True,
        "message_id": "test_msg_123",
        "provider": "test_smtp"
    }
    return provider

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = 1
    return redis_mock
```

## Running Tests

### Local Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_unit/
pytest tests/test_integration/
pytest tests/test_e2e/

# Run performance tests
pytest tests/test_performance/ -v

# Run tests with markers
pytest -m "not slow"
pytest -m "integration"
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test_pass
          POSTGRES_USER: test_user
          POSTGRES_DB: chatapi_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --dev

      - name: Run tests
        run: |
          uv run pytest --cov=app --cov-report=xml
        env:
          TEST_DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/chatapi_test
          REDIS_URL: redis://localhost:6379/1

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Test Data Management

### Test Data Factories

```python
# tests/factories.py
import factory
from app.models.client import Client
from app.models.room import Room
from app.models.message import Message

class ClientFactory(factory.Factory):
    class Meta:
        model = Client

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker('name')

class RoomFactory(factory.Factory):
    class Meta:
        model = Room

    name = factory.Faker('sentence', nb_words=3)
    client = factory.SubFactory(ClientFactory)

class MessageFactory(factory.Factory):
    class Meta:
        model = Message

    content = factory.Faker('text')
    room = factory.SubFactory(RoomFactory)
    sender = factory.SubFactory(ClientFactory)
```

### Database Seeding

```python
# tests/seed.py
def seed_test_data(db):
    """Seed database with test data."""
    clients = ClientFactory.create_batch(10)
    rooms = [RoomFactory.create(client=client) for client in clients]
    messages = []

    for room in rooms:
        messages.extend(
            MessageFactory.create_batch(5, room=room, sender=room.client)
        )

    db.add_all(clients + rooms + messages)
    db.commit()

    return {
        'clients': clients,
        'rooms': rooms,
        'messages': messages
    }
```

## Best Practices

### Writing Good Tests

1. **Test Isolation**: Each test should be independent
2. **Clear Naming**: Test names should describe what they test
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Minimal Setup**: Use factories and fixtures efficiently
5. **Error Cases**: Test both success and failure scenarios

### Test Maintenance

1. **Regular Updates**: Keep tests up-to-date with code changes
2. **Performance Monitoring**: Track test execution time
3. **Coverage Goals**: Maintain high code coverage
4. **Documentation**: Document complex test scenarios
5. **Cleanup**: Remove obsolete tests regularly
