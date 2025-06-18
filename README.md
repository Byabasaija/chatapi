# ChatAPI

An Open Source, free in-app messaging/chatting and notifications API service.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Development](#development)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Features

- ⚡ **FastAPI** backend for high performance APIs
- 🧰 **SQLAlchemy** ORM for database interactions
- 💾 **PostgreSQL** as the primary database
- 🐋 **Docker Compose** for local and production deployments
- 🔑 API key-based authentication for clients
- 🔔 Real-time messaging and notifications (WebSocket & Socket.IO)
- ✅ Automated testing with **Pytest**
- 🏭 CI/CD with GitHub Actions
- 📖 Interactive API docs (Swagger UI)

## Technology Stack

- Python 3.10+
- FastAPI
- SQLModel & SQLAlchemy
- PostgreSQL
- Celery (for background tasks)
- Docker & Docker Compose
- Pydantic v2
- Starlette (ASGI server)
- Socket.IO (real-time communication)

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

### Clone the Repository

```bash
git clone https://github.com/Byabasaija/chatapi.git
cd chatapi
```

### Environment Variables

Copy the example environment file and update as needed:

```bash
cp .env.example .env
```

### Start the Application

```bash
docker compose up --build
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Adminer (DB UI): http://localhost:8080

## Development

- Start the local stack:
  ```bash
  docker compose watch
  ```
- View logs:
  ```bash
  docker compose logs
  # or for a specific service
  docker compose logs api
  ```
- Run code formatting and linting:
  ```bash
  bash scripts/format.sh
  bash scripts/lint.sh
  ```
- Run migrations:
  ```bash
  bash scripts/migrate.sh
  ```

## API Documentation

- Interactive docs: [Swagger UI](http://localhost:8000/docs)
- OpenAPI schema: [OpenAPI JSON](http://localhost:8000/api/v1/openapi.json)

## Testing

- Run all tests:
  ```bash
  bash scripts/test-local.sh
  ```
- Coverage reports are generated in the `htmlcov/` directory.

## Security

Security is a top priority. If you discover a vulnerability, please report it by email to: basaijapascal9@gmail.com. Do not disclose security issues publicly until they are resolved. See [SECURITY.md](./SECURITY.md) for more details.

## Contributing

Contributions are welcome! Please open issues or pull requests. For questions, use [GitHub Discussions](https://github.com/Byabasaija/chatapi/discussions/categories/questions).

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
