# Test Structure

This project follows industry best practices for test organization with clear separation by scope and speed.

## Directory Structure

```
tests/
├── unit/               # Fast, isolated tests with mocks
│   ├── api/           # API router tests (mocked DB)
│   ├── core/          # Core business logic tests
│   ├── automation/    # Workflow utilities tests
│   └── ...
├── integration/        # Component interaction tests
│   └── test_repositories.py  # Repository + real DB
└── e2e/               # Full stack end-to-end tests
    └── test_api_postgres.py  # API → Dependencies → Repositories → DB
```

## Test Types

### Unit Tests (`tests/unit/`)
- **Speed**: Fast (milliseconds)
- **Scope**: Single function/class
- **Dependencies**: Mocked
- **Example**: Test a router function with mocked database

```python
@patch("api.routers.specs.is_db_configured", return_value=True)
def test_get_specs(mock_db):
    # Test logic with mocked DB
    ...
```

### Integration Tests (`tests/integration/`)
- **Speed**: Medium (seconds)
- **Scope**: Multiple components
- **Dependencies**: Real database (SQLite in-memory)
- **Example**: Test repository CRUD operations with real database

```python
async def test_create_spec(test_session):
    repo = SpecRepository(test_session)
    spec = await repo.create(spec_data)
    assert spec.id == "scatter-basic"
```

### E2E Tests (`tests/e2e/`)
- **Speed**: Slow (seconds to minutes)
- **Scope**: Full application stack
- **Dependencies**: Real database, FastAPI TestClient
- **Example**: Test complete API request-response cycle

```python
async def test_get_specs_with_db(async_client, test_db_with_data):
    response = await async_client.get("/specs")
    assert response.status_code == 200
    assert len(response.json()) == 2
```

## Running Tests

### Run all tests
```bash
uv run pytest
```

### Run by type
```bash
# Unit tests only (fast)
uv run pytest tests/unit/

# Integration tests only
uv run pytest -m integration

# E2E tests only
uv run pytest -m e2e
```

### Run with coverage
```bash
uv run pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
uv run pytest tests/integration/test_repositories.py
```

### Run specific test
```bash
uv run pytest tests/integration/test_repositories.py::TestSpecRepository::test_create
```

## Pytest Markers

Tests are marked with custom markers for selective execution:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (real DB)
- `@pytest.mark.e2e` - End-to-end tests (full stack)

**Note**: Markers are registered in `pyproject.toml` under `[tool.pytest.ini_options]`.

## Test Fixtures

### conftest.py

Global fixtures available to all tests:

- `sample_data`: Pandas DataFrame with sample plot data
- `temp_output_dir`: Temporary directory for plot outputs
- `test_engine`: In-memory SQLite async engine
- `test_session`: Async database session
- `test_db_with_data`: Pre-populated test database (2 specs, 2 libraries, 3 implementations)

### Async Client (E2E tests)

```python
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

## Best Practices

1. **Unit tests**: Mock external dependencies, test business logic
2. **Integration tests**: Test component interactions with real dependencies
3. **E2E tests**: Test user journeys and critical paths
4. **Keep tests fast**: Prioritize unit tests, use integration/e2e sparingly
5. **Descriptive names**: `test_get_spec_returns_404_when_not_found` not `test_1`
6. **One assertion per test**: Test one behavior at a time
7. **Use fixtures**: Share setup logic via pytest fixtures

## CI/CD

GitHub Actions runs tests on every PR:

- **ci-tests.yml**: Runs unit and integration tests with SQLite
- **Coverage**: Reports code coverage to ensure >90% coverage

**Note**: Integration tests now work with SQLite thanks to custom database types that support both PostgreSQL and SQLite. E2E tests require database dependency override and are not yet included in CI.

## Writing New Tests

### Unit Test Example
```python
# tests/unit/api/test_new_router.py
from unittest.mock import patch

def test_endpoint_with_mocked_db():
    with patch("api.routers.new.get_db", return_value=None):
        # Test your endpoint
        ...
```

### Integration Test Example
```python
# tests/integration/test_new_repository.py
import pytest

@pytest.mark.integration
class TestNewRepository:
    async def test_create(self, test_session):
        repo = NewRepository(test_session)
        result = await repo.create(data)
        assert result.id == "expected-id"
```

### E2E Test Example
```python
# tests/e2e/test_new_endpoint.py
import pytest

pytestmark = pytest.mark.e2e

@pytest.mark.e2e
class TestNewEndpoint:
    async def test_full_flow(self, async_client, test_db_with_data):
        response = await async_client.get("/new-endpoint")
        assert response.status_code == 200
```

## Coverage

Target: **90%+ code coverage**

View coverage report:
```bash
uv run pytest --cov=. --cov-report=html
open htmlcov/index.html
```
