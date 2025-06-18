# ChatAPI

A high-performance, open-source messaging and notifications API service for in-app communication.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.114.2+-green.svg)](https://fastapi.tiangolo.com/)

---

## Overview

ChatAPI provides a robust, scalable solution for real-time messaging and notifications in modern applications. Built with FastAPI and designed for cloud-native deployments, it offers enterprise-grade performance with developer-friendly APIs.

## ✨ Key Features

- 🚀 **High Performance** - Async FastAPI backend with SQLAlchemy ORM
- 💬 **Real-time Messaging** - WebSocket and Socket.IO support
- 🔐 **Secure Authentication** - API key-based client authentication
- � **PostgreSQL Database** - Reliable data persistence with async drivers
- � **Background Tasks** - Celery integration for async processing
- � **Docker Ready** - Full containerization for easy deployment
- � **Auto Documentation** - Interactive API docs with Swagger UI
- 🧪 **Well Tested** - Comprehensive test suite with coverage reports
- 🏭 **CI/CD Ready** - GitHub Actions workflows included

## 🛠 Technology Stack

| Component          | Technology                                     |
| ------------------ | ---------------------------------------------- |
| **Backend**        | FastAPI 0.114.2+, SQLModel, SQLAlchemy (async) |
| **Database**       | PostgreSQL 12+ with asyncpg driver             |
| **Real-time**      | WebSockets, Socket.IO                          |
| **Task Queue**     | Celery with RabbitMQ                           |
| **Authentication** | API keys with bcrypt hashing                   |
| **Deployment**     | Docker, Docker Compose                         |
| **Testing**        | Pytest with coverage                           |
| **Code Quality**   | Ruff, MyPy, pre-commit hooks                   |

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-started/) and [Docker Compose](https://docs.docker.com/compose/)
- [Git](https://git-scm.com/) for cloning the repository

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Byabasaija/chatapi.git
   cd chatapi
   ```

2. **Setup environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the services:**

   ```bash
   docker compose up --build
   ```

4. **Access the application:**
   - **API:** http://localhost:8000
   - **Interactive Docs:** http://localhost:8000/docs
   - **Database UI:** http://localhost:8080 (Adminer)

### API Usage Example

```bash
# Health check
curl http://localhost:8000/api/v1/utils/health-check

# Create API client (requires authentication)
curl -X POST "http://localhost:8000/api/v1/clients/" \
  -H "Content-Type: application/json" \
  -d '{"name": "My App", "encryption_mode": "none"}'
```

## 📖 Documentation

- **[Development Guide](development.md)** - Comprehensive development setup and workflows
- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI (when running)
- **[Security Guidelines](SECURITY.md)** - Security policies and reporting

## 🧪 Testing

```bash
# Run all tests
bash scripts/run-test.sh

# Run tests locally
bash scripts/test-local.sh
```

Coverage reports are available in the `htmlcov/` directory after running tests.

## 🔒 Security

Security is our top priority. If you discover a vulnerability:

- **Do not** create a public issue
- **Email:** basaijapascal9@gmail.com
- Include detailed reproduction steps
- Allow time for assessment and patching

See [SECURITY.md](SECURITY.md) for our complete security policy.

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Read the [Development Guide](development.md)** for setup instructions
2. **Fork** the repository and create a feature branch
3. **Make your changes** with tests and documentation
4. **Submit a pull request** with a clear description

For questions or discussions, use [GitHub Discussions](https://github.com/Byabasaija/chatapi/discussions).

### Development Quick Start

For detailed development instructions, see [development.md](development.md). Quick commands:

```bash
# Format code
bash scripts/format.sh

# Lint code
bash scripts/lint.sh

# Run migrations
alembic upgrade head
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **[GitHub Repository](https://github.com/Byabasaija/chatapi)**
- **[Issue Tracker](https://github.com/Byabasaija/chatapi/issues)**
- **[Discussions](https://github.com/Byabasaija/chatapi/discussions)**

---

**Built with ❤️ by [Pascal Byabasaija](https://github.com/Byabasaija)**
