# Environment Variables

This page describes all environment variables used by ChatAPI for configuration across different deployment environments.

## Core Configuration

### Database

| Variable       | Description                  | Default     | Required |
| -------------- | ---------------------------- | ----------- | -------- |
| `DATABASE_URL` | PostgreSQL connection string | -           | ✅       |
| `DB_HOST`      | Database host                | `localhost` | -        |
| `DB_PORT`      | Database port                | `5432`      | -        |
| `DB_NAME`      | Database name                | `chatapi`   | -        |
| `DB_USER`      | Database username            | -           | ✅       |
| `DB_PASSWORD`  | Database password            | -           | ✅       |

### Redis (Message Broker)

| Variable         | Description             | Default     | Required |
| ---------------- | ----------------------- | ----------- | -------- |
| `REDIS_URL`      | Redis connection string | -           | ✅       |
| `REDIS_HOST`     | Redis host              | `localhost` | -        |
| `REDIS_PORT`     | Redis port              | `6379`      | -        |
| `REDIS_PASSWORD` | Redis password          | -           | -        |
| `REDIS_DB`       | Redis database number   | `0`         | -        |

## Security

### Authentication & Encryption

| Variable                      | Description                           | Default | Required |
| ----------------------------- | ------------------------------------- | ------- | -------- |
| `SECRET_KEY`                  | Application secret key for JWT tokens | -       | ✅       |
| `ALGORITHM`                   | JWT algorithm                         | `HS256` | -        |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time             | `30`    | -        |

### CORS

| Variable               | Description                       | Default | Required |
| ---------------------- | --------------------------------- | ------- | -------- |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["*"]` | -        |

## Messaging Configuration

### WebSocket Settings

| Variable                       | Description                    | Default | Required |
| ------------------------------ | ------------------------------ | ------- | -------- |
| `WEBSOCKET_HEARTBEAT_INTERVAL` | Heartbeat interval in seconds  | `30`    | -        |
| `WEBSOCKET_MAX_CONNECTIONS`    | Maximum concurrent connections | `1000`  | -        |

### Message Limits

| Variable                 | Description                   | Default | Required |
| ------------------------ | ----------------------------- | ------- | -------- |
| `MAX_MESSAGE_SIZE`       | Maximum message size in bytes | `65536` | -        |
| `MESSAGE_RETENTION_DAYS` | Days to retain messages       | `30`    | -        |

## Notification Configuration

### Email Settings

| Variable        | Description      | Default | Required |
| --------------- | ---------------- | ------- | -------- |
| `SMTP_HOST`     | SMTP server host | -       | -        |
| `SMTP_PORT`     | SMTP server port | `587`   | -        |
| `SMTP_USER`     | SMTP username    | -       | -        |
| `SMTP_PASSWORD` | SMTP password    | -       | -        |
| `SMTP_TLS`      | Enable TLS       | `true`  | -        |

### Notification Providers

| Variable           | Description      | Default | Required |
| ------------------ | ---------------- | ------- | -------- |
| `SENDGRID_API_KEY` | SendGrid API key | -       | -        |
| `MAILGUN_API_KEY`  | Mailgun API key  | -       | -        |
| `MAILGUN_DOMAIN`   | Mailgun domain   | -       | -        |

## Application Settings

### Server Configuration

| Variable  | Description                      | Default   | Required |
| --------- | -------------------------------- | --------- | -------- |
| `HOST`    | Server host                      | `0.0.0.0` | -        |
| `PORT`    | Server port                      | `8000`    | -        |
| `WORKERS` | Number of worker processes       | `1`       | -        |
| `RELOAD`  | Enable auto-reload (development) | `false`   | -        |

### Logging

| Variable     | Description            | Default | Required |
| ------------ | ---------------------- | ------- | -------- |
| `LOG_LEVEL`  | Logging level          | `INFO`  | -        |
| `LOG_FORMAT` | Log format (json/text) | `json`  | -        |

## Development Settings

| Variable      | Description         | Default      | Required |
| ------------- | ------------------- | ------------ | -------- |
| `DEBUG`       | Enable debug mode   | `false`      | -        |
| `TESTING`     | Enable testing mode | `false`      | -        |
| `ENVIRONMENT` | Environment name    | `production` | -        |

## Production Recommendations

### Security

- Always use strong, randomly generated `SECRET_KEY`
- Use SSL/TLS for database connections
- Restrict CORS origins to your domains only
- Use environment-specific passwords

### Performance

- Configure Redis with appropriate memory limits
- Set reasonable connection limits
- Use connection pooling for database
- Enable logging for monitoring

### Monitoring

- Set up proper log aggregation
- Monitor database and Redis performance
- Track WebSocket connection metrics
- Set up health checks

## Environment Files

### .env.example

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/chatapi
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chatapi
DB_USER=chatapi_user
DB_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=your_very_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "https://yourapp.com"]

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### Docker Environment

```bash
# Use Docker secrets for sensitive data
DATABASE_URL_FILE=/run/secrets/database_url
SECRET_KEY_FILE=/run/secrets/secret_key
REDIS_PASSWORD_FILE=/run/secrets/redis_password
```

## Validation

ChatAPI validates environment variables on startup and will fail fast if required variables are missing or invalid. Check the application logs for specific validation errors.
