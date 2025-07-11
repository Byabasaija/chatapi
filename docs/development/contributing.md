# Contributing

We welcome contributions to ChatAPI! This guide will help you get started with contributing to the project.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Git
- PostgreSQL (for local development)
- Redis (for local development)

### Development Setup

1. **Fork and Clone**

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/chatapi.git
cd chatapi

# Add upstream remote
git remote add upstream https://github.com/Byabasaija/chatapi.git
```

2. **Set up Development Environment**

```bash
# Install uv (Python package manager)
pip install uv

# Install dependencies
uv sync --dev

# Set up pre-commit hooks
uv run pre-commit install
```

3. **Start Development Services**

```bash
# Start PostgreSQL and Redis
docker-compose -f docker-compose.override.yml up -d postgres redis

# Run database migrations
uv run alembic upgrade head

# Start the development server
uv run python app/main.py
```

4. **Verify Setup**

```bash
# Run tests to ensure everything is working
uv run pytest

# Check code formatting
uv run ruff check .
uv run black --check .

# Type checking
uv run mypy app/
```

## Development Workflow

### Branching Strategy

We use a Git flow-inspired branching strategy:

- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature development branches
- `hotfix/*`: Emergency fixes for production
- `release/*`: Release preparation branches

### Creating a Feature Branch

```bash
# Ensure you're on the latest develop branch
git checkout develop
git pull upstream develop

# Create a new feature branch
git checkout -b feature/your-feature-name

# Make your changes and commit
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name
```

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

**Examples:**

```bash
feat(api): add WebSocket support for real-time notifications
fix(auth): resolve token expiration edge case
docs(readme): update installation instructions
test(services): add unit tests for message service
```

## Code Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- Line length: 88 characters (Black default)
- Use type hints for all functions and methods
- Use docstrings for all public functions, classes, and modules

### Code Formatting

```bash
# Format code with Black
uv run black .

# Sort imports with isort
uv run isort .

# Lint with Ruff
uv run ruff check . --fix

# Type checking with mypy
uv run mypy app/
```

### Documentation Strings

Use Google-style docstrings:

```python
def send_notification(
    client_id: str,
    message: str,
    notification_type: str = "email"
) -> NotificationResult:
    """Send a notification to a client.

    Args:
        client_id: Unique identifier for the client
        message: Message content to send
        notification_type: Type of notification (email, sms, push)

    Returns:
        NotificationResult: Result of the notification operation

    Raises:
        ClientNotFoundError: If the client doesn't exist
        InvalidNotificationTypeError: If notification type is not supported

    Example:
        >>> result = send_notification("client_123", "Hello!", "email")
        >>> print(result.success)
        True
    """
```

## Testing Guidelines

### Test Coverage

- Maintain minimum 80% test coverage
- All new features must include tests
- Bug fixes should include regression tests

### Test Structure

```python
# tests/test_example.py
import pytest
from app.services.example import ExampleService

class TestExampleService:
    """Test cases for ExampleService."""

    def test_create_example_success(self, db_session):
        """Test successful example creation."""
        # Arrange
        service = ExampleService()
        data = {"name": "test", "value": 123}

        # Act
        result = service.create(db_session, data)

        # Assert
        assert result.name == "test"
        assert result.value == 123

    def test_create_example_validation_error(self, db_session):
        """Test example creation with invalid data."""
        # Arrange
        service = ExampleService()
        invalid_data = {"name": "", "value": "not_a_number"}

        # Act & Assert
        with pytest.raises(ValidationError):
            service.create(db_session, invalid_data)
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_services/test_client.py

# Run tests matching pattern
uv run pytest -k "test_create"

# Run tests with markers
uv run pytest -m "not slow"
```

## API Development

### Adding New Endpoints

1. **Define the Schema**

```python
# app/schemas/example.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ExampleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ExampleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class ExampleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
```

2. **Create the Model**

```python
# app/models/example.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base

class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

3. **Implement the Service**

```python
# app/services/example.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.example import Example
from app.schemas.example import ExampleCreate, ExampleUpdate
from app.services.base import CRUDBase

class ExampleService(CRUDBase[Example, ExampleCreate, ExampleUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Example]:
        return db.query(Example).filter(Example.name == name).first()

    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Example]:
        return db.query(Example).offset(skip).limit(limit).all()

example_service = ExampleService(Example)
```

4. **Create the API Router**

```python
# app/api/api_v1/routes/example.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.example import ExampleCreate, ExampleUpdate, ExampleResponse
from app.services.example import example_service

router = APIRouter()

@router.post("/", response_model=ExampleResponse, status_code=status.HTTP_201_CREATED)
def create_example(
    example_in: ExampleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExampleResponse:
    """Create a new example."""
    example = example_service.create(db, obj_in=example_in)
    return example

@router.get("/{example_id}", response_model=ExampleResponse)
def get_example(
    example_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ExampleResponse:
    """Get example by ID."""
    example = example_service.get(db, id=example_id)
    if not example:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Example not found"
        )
    return example

@router.get("/", response_model=List[ExampleResponse])
def list_examples(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ExampleResponse]:
    """List examples."""
    examples = example_service.get_multi(db, skip=skip, limit=limit)
    return examples
```

### Database Migrations

When adding new models or modifying existing ones:

```bash
# Generate migration
uv run alembic revision --autogenerate -m "add example table"

# Review the generated migration file
# Edit if necessary

# Apply migration
uv run alembic upgrade head
```

## Documentation

### API Documentation

- API endpoints are automatically documented via OpenAPI/Swagger
- Add comprehensive docstrings to all endpoint functions
- Include example requests and responses

### Code Documentation

- Document all public functions and classes
- Keep docstrings up-to-date with code changes
- Add inline comments for complex logic

### User Documentation

- Update relevant documentation files in `docs/`
- Include examples and tutorials for new features
- Test documentation instructions

## Security Considerations

### Security Checklist

- [ ] Input validation and sanitization
- [ ] Authentication and authorization checks
- [ ] SQL injection prevention (use ORM)
- [ ] XSS prevention
- [ ] Rate limiting implementation
- [ ] Sensitive data encryption
- [ ] Secure error messages (no information leakage)

### Authentication

All API endpoints should include appropriate authentication:

```python
from app.api.deps import get_current_user

@router.get("/protected-endpoint")
def protected_endpoint(
    current_user: User = Depends(get_current_user)
):
    # Endpoint implementation
    pass
```

### Input Validation

Use Pydantic models for all input validation:

```python
from pydantic import BaseModel, Field, validator

class CreateUserRequest(BaseModel):
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)

    @validator('password')
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

## Performance Guidelines

### Database Optimization

- Use appropriate indexes
- Implement query pagination
- Avoid N+1 query problems
- Use database-level constraints

### API Performance

- Implement caching where appropriate
- Use async/await for I/O operations
- Implement proper error handling
- Monitor response times

### Example: Efficient Querying

```python
# Good: Single query with join
def get_user_with_posts(db: Session, user_id: int):
    return db.query(User)\
        .options(joinedload(User.posts))\
        .filter(User.id == user_id)\
        .first()

# Bad: N+1 query problem
def get_user_with_posts_bad(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    posts = []
    for post_id in user.post_ids:  # This triggers N queries
        post = db.query(Post).filter(Post.id == post_id).first()
        posts.append(post)
    return user, posts
```

## Pull Request Process

### Before Submitting

1. **Code Review Checklist**

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No debugging code left in
- [ ] Error handling implemented
- [ ] Security considerations addressed

2. **Self Review**

```bash
# Run full test suite
uv run pytest

# Check code quality
uv run ruff check .
uv run black --check .
uv run mypy app/

# Check for security issues
uv run bandit -r app/

# Update dependencies if needed
uv sync --upgrade
```

### Submitting Pull Request

1. **Push your branch**

```bash
git push origin feature/your-feature-name
```

2. **Create Pull Request**

- Use a descriptive title
- Reference related issues
- Include a detailed description
- Add screenshots for UI changes
- List breaking changes if any

### Pull Request Template

```markdown
## Description

Brief description of the changes.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes or breaking changes documented

## Related Issues

Fixes #123
```

## Code Review Guidelines

### For Authors

- Keep PRs small and focused
- Write clear commit messages
- Respond to feedback promptly
- Test thoroughly before submitting

### For Reviewers

- Be constructive and respectful
- Focus on code quality and maintainability
- Suggest improvements, don't just criticize
- Ask questions when something is unclear

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Checklist

1. **Prepare Release**

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
# Create release branch
git checkout -b release/v1.2.0
```

2. **Test Release**

```bash
# Run full test suite
uv run pytest

# Build and test Docker image
docker build -t chatapi:v1.2.0 .
docker run --rm chatapi:v1.2.0 python -m pytest
```

3. **Create Release**

```bash
# Merge to main
git checkout main
git merge release/v1.2.0

# Tag release
git tag v1.2.0
git push origin main --tags
```

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Discord**: Real-time chat (link in repository)

### Resources

- [Project Documentation](https://chatapi.dev/docs)
- [API Reference](https://api.chatapi.dev/docs)
- [Development Setup Guide](./setup.md)
- [Architecture Overview](./architecture.md)

## Recognition

### Contributors

All contributors are recognized in:

- `CONTRIBUTORS.md` file
- Release notes
- Project website

### Types of Contributions

We welcome all types of contributions:

- Code contributions
- Documentation improvements
- Bug reports
- Feature suggestions
- Testing and quality assurance
- Community support
- Translations

Thank you for contributing to ChatAPI! 🚀
