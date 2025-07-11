# Docker Deployment

ChatAPI is designed to be deployed using Docker containers for easy scalability and consistent environments across development, staging, and production.

## Quick Start with Docker

### Using Docker Compose (Recommended)

The fastest way to get ChatAPI running is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/Byabasaija/chatapi.git
cd chatapi

# Copy environment configuration
cp .env.example .env

# Edit environment variables
nano .env

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

This will start:

- ChatAPI application server
- PostgreSQL database
- Redis cache
- Celery worker processes
- Nginx reverse proxy (optional)

### Using Docker Run

For more control, you can run containers individually:

```bash
# Create network
docker network create chatapi-network

# Start PostgreSQL
docker run -d \
  --name chatapi-postgres \
  --network chatapi-network \
  -e POSTGRES_DB=chatapi \
  -e POSTGRES_USER=chatapi \
  -e POSTGRES_PASSWORD=your_password \
  -v chatapi-postgres-data:/var/lib/postgresql/data \
  postgres:13

# Start Redis
docker run -d \
  --name chatapi-redis \
  --network chatapi-network \
  -v chatapi-redis-data:/data \
  redis:6-alpine

# Start ChatAPI application
docker run -d \
  --name chatapi-app \
  --network chatapi-network \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://chatapi:your_password@chatapi-postgres:5432/chatapi \
  -e REDIS_URL=redis://chatapi-redis:6379/0 \
  chatapi:latest

# Start Celery worker
docker run -d \
  --name chatapi-worker \
  --network chatapi-network \
  -e DATABASE_URL=postgresql://chatapi:your_password@chatapi-postgres:5432/chatapi \
  -e REDIS_URL=redis://chatapi-redis:6379/0 \
  chatapi:latest \
  celery -A app.celeryworker worker --loglevel=info
```

## Building the Docker Image

### Production Build

```dockerfile
# Dockerfile (already included in the repository)
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build Commands

```bash
# Build the image
docker build -t chatapi:latest .

# Build with specific tag
docker build -t chatapi:v1.0.0 .

# Build for multi-platform (ARM64 + AMD64)
docker buildx build --platform linux/amd64,linux/arm64 -t chatapi:latest .

# Build with build args
docker build \
  --build-arg PYTHON_VERSION=3.10 \
  --build-arg UV_VERSION=latest \
  -t chatapi:custom .
```

## Docker Compose Configuration

### Full Stack Configuration

```yaml
# docker-compose.yml
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://chatapi:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    build: .
    command: celery -A app.celeryworker worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://chatapi:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app:ro
    restart: unless-stopped
    deploy:
      replicas: 2

  beat:
    build: .
    command: celery -A app.celeryworker beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://chatapi:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./app:/app/app:ro
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=${POSTGRES_DB:-chatapi}
      - POSTGRES_USER=${POSTGRES_USER:-chatapi}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-chatapi}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Development Override

```yaml
# docker-compose.override.yml
version: "3.8"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./app:/app/app
    environment:
      - DEBUG=True
      - RELOAD=True
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./app:/app/app
    environment:
      - DEBUG=True

  postgres:
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=chatapi_dev

  redis:
    ports:
      - "6379:6379"
```

## Environment Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database
POSTGRES_DB=chatapi
POSTGRES_USER=chatapi
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://chatapi:your_secure_password@postgres:5432/chatapi

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Application
SECRET_KEY=your_super_secret_key_here
ENVIRONMENT=production
DEBUG=False
CORS_ORIGINS=["https://yourapp.com"]

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAILS_FROM_EMAIL=noreply@yourapp.com

# API Keys
API_V1_STR=/api/v1
PROJECT_NAME="ChatAPI"

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=10080  # 7 days

# External Services
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# Monitoring
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project_id
LOG_LEVEL=INFO
```

## Health Checks and Monitoring

### Application Health Check

```python
# app/api/api_v1/routes/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.celery_app import celery_app

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check."""
    checks = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "celery": "unknown"
    }

    try:
        # Database check
        db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception:
        checks["database"] = "unhealthy"
        checks["status"] = "unhealthy"

    try:
        # Redis check
        from app.core.config import settings
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = "healthy"
    except Exception:
        checks["redis"] = "unhealthy"
        checks["status"] = "unhealthy"

    try:
        # Celery check
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        if stats:
            checks["celery"] = "healthy"
        else:
            checks["celery"] = "unhealthy"
            checks["status"] = "unhealthy"
    except Exception:
        checks["celery"] = "unhealthy"
        checks["status"] = "unhealthy"

    return checks
```

### Docker Health Checks

```dockerfile
# Add to Dockerfile
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### Monitoring with Prometheus

```yaml
# Add to docker-compose.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.console.libraries=/etc/prometheus/console_libraries"
      - "--web.console.templates=/etc/prometheus/consoles"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning

volumes:
  grafana_data:
```

## Scaling with Docker

### Horizontal Scaling

```bash
# Scale application servers
docker-compose up -d --scale app=3

# Scale workers
docker-compose up -d --scale worker=5

# Scale specific services
docker-compose up -d --scale app=3 --scale worker=5 --scale beat=1
```

### Load Balancing

```nginx
# nginx/nginx.conf
upstream chatapi_backend {
    least_conn;
    server app:8000 max_fails=3 fail_timeout=30s;
    server app_2:8000 max_fails=3 fail_timeout=30s;
    server app_3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.yourapp.com;

    location / {
        proxy_pass http://chatapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Security Best Practices

### Container Security

```dockerfile
# Use specific version tags
FROM python:3.10.12-slim

# Run as non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Use multi-stage builds to reduce image size
FROM python:3.10.12-slim AS builder
# Build stage...

FROM python:3.10.12-slim AS runtime
COPY --from=builder /app /app
# Runtime stage...
```

### Secrets Management

```yaml
# docker-compose.yml with secrets
version: "3.8"

services:
  app:
    secrets:
      - postgres_password
      - secret_key
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/postgres_password
      - SECRET_KEY_FILE=/run/secrets/secret_key

secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

### Network Security

```yaml
# docker-compose.yml with custom networks
version: "3.8"

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  app:
    networks:
      - frontend
      - backend

  postgres:
    networks:
      - backend # Only accessible from backend

  nginx:
    networks:
      - frontend # Only accessible from frontend
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**

```bash
# Check what's using the port
sudo lsof -i :8000

# Use different port
docker-compose up -d -p 8001:8000
```

2. **Database Connection Issues**

```bash
# Check database logs
docker-compose logs postgres

# Test database connection
docker-compose exec app python -c "from app.db.session import SessionLocal; SessionLocal().execute('SELECT 1')"
```

3. **Memory Issues**

```bash
# Check container resource usage
docker stats

# Increase memory limits
docker-compose up -d --memory=2g
```

### Debugging

```bash
# View logs
docker-compose logs -f app
docker-compose logs -f worker

# Execute commands in container
docker-compose exec app bash
docker-compose exec app python -c "import app; print('App loaded successfully')"

# Run tests in container
docker-compose exec app pytest

# Database shell
docker-compose exec postgres psql -U chatapi -d chatapi
```

### Performance Optimization

```yaml
# docker-compose.yml with performance optimizations
version: "3.8"

services:
  app:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "1.0"
          memory: 1G
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

## Backup and Recovery

### Database Backup

```bash
# Create backup
docker-compose exec postgres pg_dump -U chatapi chatapi > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U chatapi chatapi < backup.sql

# Automated backup script
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U chatapi chatapi | gzip > "backup_${TIMESTAMP}.sql.gz"
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v chatapi_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volumes
docker run --rm -v chatapi_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```
