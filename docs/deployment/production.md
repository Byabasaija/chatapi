# Production Deployment

This guide covers deploying ChatAPI in a production environment with proper security, monitoring, and scalability considerations.

## Production Architecture

```mermaid
graph TB
    LB[Load Balancer] --> API1[API Instance 1]
    LB --> API2[API Instance 2]
    LB --> API3[API Instance 3]

    API1 --> DB[(PostgreSQL)]
    API2 --> DB
    API3 --> DB

    API1 --> REDIS[(Redis)]
    API2 --> REDIS
    API3 --> REDIS

    API1 --> MQ[RabbitMQ]
    API2 --> MQ
    API3 --> MQ

    MQ --> W1[Worker 1]
    MQ --> W2[Worker 2]
```

## Prerequisites

### Infrastructure Requirements

- **CPU**: Minimum 2 cores per API instance
- **Memory**: Minimum 4GB RAM per API instance
- **Storage**: SSD storage recommended
- **Network**: High bandwidth for WebSocket connections

### External Services

- PostgreSQL 13+ (managed service recommended)
- Redis 6+ for caching and sessions
- RabbitMQ 3.9+ for message queuing
- SMTP service for email notifications
- SSL certificates for HTTPS

## Deployment Steps

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Environment Configuration

Create production environment file:

```bash
# /opt/chatapi/.env.production
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/chatapi
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://redis-host:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://user:password@rabbitmq-host:5672

# Security
SECRET_KEY=your-super-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Email
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-smtp-password
EMAILS_FROM_EMAIL=noreply@yourdomain.com

# API Configuration
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]
PROJECT_NAME="ChatAPI Production"

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# SSL
SSL_KEYFILE=/certs/private.key
SSL_CERTFILE=/certs/certificate.crt
```

### 3. Docker Compose Production Setup

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "80:80"
      - "443:443"
    environment:
      - ENVIRONMENT=production
    env_file:
      - .env.production
    volumes:
      - ./certs:/certs:ro
      - ./logs:/app/logs
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  worker:
    build: .
    command: celery -A app.celeryworker worker --loglevel=info
    env_file:
      - .env.production
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G

volumes:
  redis_data:
```

### 4. SSL Certificate Setup

#### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Auto-renewal cron job
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

#### Manual Certificate Installation

```bash
# Copy certificates to the correct location
sudo mkdir -p /opt/chatapi/certs
sudo cp your-certificate.crt /opt/chatapi/certs/certificate.crt
sudo cp your-private-key.key /opt/chatapi/certs/private.key
sudo chown -R 1000:1000 /opt/chatapi/certs
sudo chmod 600 /opt/chatapi/certs/*
```

### 5. Database Migration

```bash
# Run database migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Create initial admin user (optional)
docker-compose -f docker-compose.prod.yml exec api python -c "
from app.core.config import settings
from app.services.client import ClientService
from app.core.db import SessionLocal

db = SessionLocal()
client_service = ClientService(db)
admin_client = client_service.create_client(
    name='Admin',
    email='admin@yourdomain.com',
    is_admin=True
)
print(f'Admin client created with ID: {admin_client.id}')
db.close()
"
```

## Load Balancer Configuration

### Nginx Configuration

```nginx
upstream chatapi_backend {
    server api1.internal:80;
    server api2.internal:80;
    server api3.internal:80;
}

upstream chatapi_websocket {
    ip_hash;  # Sticky sessions for WebSocket
    server api1.internal:80;
    server api2.internal:80;
    server api3.internal:80;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # API routes
    location /api/ {
        proxy_pass http://chatapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket routes
    location /ws {
        proxy_pass http://chatapi_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Health check
    location /health {
        proxy_pass http://chatapi_backend;
        access_log off;
    }
}
```

## Monitoring and Logging

### Health Checks

```python
# Add to your main.py
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

### Logging Configuration

```yaml
# logging.yml
version: 1
disable_existing_loggers: false
formatters:
  default:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  json:
    format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: /app/logs/chatapi.log
    maxBytes: 10485760 # 10MB
    backupCount: 5
root:
  level: INFO
  handlers: [console, file]
```

### Metrics Collection

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    REQUEST_COUNT.labels(method=request.method, endpoint=request.url.path).inc()
    REQUEST_DURATION.observe(time.time() - start_time)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Security Hardening

### 1. Firewall Configuration

```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Docker Security

```dockerfile
# Use non-root user in Dockerfile
RUN groupadd -r chatapi && useradd -r -g chatapi chatapi
USER chatapi
```

### 3. Environment Secrets

Use Docker secrets or external secret management:

```yaml
# docker-compose.prod.yml
secrets:
  database_password:
    external: true
  secret_key:
    external: true

services:
  api:
    secrets:
      - database_password
      - secret_key
```

## Backup Strategy

### Database Backups

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DATABASE_URL="postgresql://user:password@host:5432/chatapi"

# Create backup
pg_dump $DATABASE_URL > $BACKUP_DIR/chatapi_backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/chatapi_backup_$DATE.sql

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "chatapi_backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/chatapi_backup_$DATE.sql.gz s3://your-backup-bucket/
```

### Automated Backup Cron

```bash
# Add to crontab
0 2 * * * /opt/chatapi/scripts/backup.sh
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**

   - Check for memory leaks in logs
   - Adjust connection pool sizes
   - Monitor worker processes

2. **WebSocket Connection Issues**

   - Verify sticky sessions in load balancer
   - Check proxy timeout settings
   - Monitor connection counts

3. **Database Performance**
   - Analyze slow queries
   - Check connection pool utilization
   - Consider read replicas

### Log Analysis

```bash
# View API logs
docker-compose -f docker-compose.prod.yml logs -f api

# Check error rates
grep "ERROR" /opt/chatapi/logs/chatapi.log | tail -100

# Monitor resource usage
docker stats
```

## Scaling Considerations

### Horizontal Scaling

- Add more API instances behind load balancer
- Scale worker processes based on queue length
- Consider database read replicas

### Vertical Scaling

- Increase CPU/memory for existing instances
- Optimize database queries and indexes
- Implement caching strategies

### Auto-scaling with Kubernetes

Consider migrating to Kubernetes for advanced auto-scaling capabilities:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chatapi
spec:
  replicas: 3
  selector:
    matchLabels:
      app: chatapi
  template:
    spec:
      containers:
        - name: chatapi
          image: chatapi:latest
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
            limits:
              memory: "4Gi"
              cpu: "2000m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: chatapi-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: chatapi
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

This production deployment guide provides a comprehensive approach to deploying ChatAPI in a production environment with proper security, monitoring, and scalability considerations.
