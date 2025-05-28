# Testing Strategy for Smart Maintenance SaaS

This directory contains tests for the Smart Maintenance SaaS application. The testing strategy is designed to ensure code quality and prevent regressions while keeping tests fast and reliable.

## Test Types

### Unit Tests
- Test individual components in isolation
- Fast execution, no external dependencies
- Marker: `@pytest.mark.unit`

### Integration Tests
- Test interactions between components
- May require external services like databases
- Marker: `@pytest.mark.integration`

### API Tests
- Test HTTP endpoints and responses
- Marker: `@pytest.mark.api`

## Database Testing Strategy

We use multiple approaches for database testing to accommodate different testing scenarios:

### 1. Docker Container Approach (Default)

We use `testcontainers` to spin up a PostgreSQL with TimescaleDB container for integration tests:

**Pros:**
- Tests run against a real database instance
- Complete isolation from development and production databases
- Tests can freely modify data without affecting other environments
- Each test session gets a fresh database state
- No need for manual database setup

**Cons:**
- Requires Docker to be installed and running
- Slower startup time for the test suite
- Resource-intensive

### 2. Dedicated Test Database Approach

Alternatively, you can use a pre-configured test database by running tests with `--no-container`:

**Pros:**
- Faster startup time for the test suite
- Doesn't require Docker
- Good for CI/CD environments with pre-configured databases

**Cons:**
- Requires manual setup of a test database
- Potential for test interference if multiple test runs occur simultaneously

## Running Tests

Use the provided script to run tests:

```bash
# Run all tests with Docker container for database
./scripts/run_tests.sh

# Run only unit tests (no database required)
./scripts/run_tests.sh -m unit

# Run only integration tests
./scripts/run_tests.sh -m integration

# Run tests without using Docker container
./scripts/run_tests.sh --no-container

# Run tests with coverage report
./scripts/run_tests.sh --cov
```

## Test Database Configuration

The test database connection is configured via the `.env.test` file or environment variables:

- When using the Docker container approach, connection details are managed automatically
- When using the direct database approach (`--no-container`), the test database URL is determined from:
  1. The `DATABASE_TEST_URL` environment variable, if set
  2. The standard `DATABASE_URL` with the database name appended with `_test`

## Best Practices

1. **Isolation**: Each test should be independent and leave no side effects
2. **Fixtures**: Use pytest fixtures for test setup and teardown
3. **Async**: Use `@pytest.mark.asyncio` for async tests
4. **Markers**: Apply appropriate markers to categorize tests
5. **Mocking**: Use mocks for external services when appropriate
6. **Coverage**: Aim for high test coverage, especially for critical components
