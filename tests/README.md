# FLEET System Test Suite

This directory contains comprehensive tests for the FLEET vehicle and driver management system. The test suite follows the testing requirements outlined in the steering file and design documents.

## Test Structure

```
tests/
├── unit/                           # Unit tests for individual components
│   ├── test_vehicle_management.py  # Vehicle CRUD operations
│   └── test_service_records.py     # Service record management
├── property/                       # Property-based tests using Hypothesis
│   ├── test_vehicle_properties.py  # Vehicle data integrity properties
│   └── test_service_properties.py  # Service record completeness properties
├── integration/                    # Integration tests for component interactions
│   ├── test_api_endpoints.py       # API Gateway to Lambda integration
│   └── test_database_operations.py # Lambda to Aurora Serverless integration
├── fixtures/                       # Test data and mock responses
│   ├── sample_vehicles.py          # Sample vehicle data
│   └── mock_responses.py           # Mock API responses
├── requirements.txt                # Test dependencies
├── run_tests.py                   # Test runner script
└── README.md                      # This file
```

## Test Types

### 1. Unit Tests
Test individual functions and components in isolation:
- **Vehicle Management**: CRUD operations, validation, error handling
- **Service Records**: Service record creation, history retrieval, maintenance alerts
- **Database Utilities**: Parameter creation, query execution, result formatting
- **API Handlers**: Request parsing, response formatting, CORS headers

**Coverage Target**: ≥80% code coverage

### 2. Property-Based Tests
Test universal properties across randomized inputs using Hypothesis:
- **Property 1: Vehicle Data Integrity** - Vehicle data should be preserved exactly during storage/retrieval
- **Property 2: Service Record Completeness** - Service records should capture all required fields
- **Property 3: Cost Threshold Alerting** - High-cost services should generate appropriate alerts
- **Property 4: Service History Persistence** - Service history should return all records chronologically

**Test Iterations**: 100+ iterations per property test

### 3. Integration Tests
Test component interactions and end-to-end workflows:
- **API Endpoints**: Complete API Gateway to Lambda integration
- **Database Operations**: Lambda to Aurora Serverless connectivity
- **Cross-Component**: Vehicle and service record interactions
- **Error Handling**: Database failures, invalid inputs, authentication errors

## Test Dependencies

Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

Required packages:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `hypothesis` - Property-based testing
- `moto` - AWS service mocking
- `boto3` - AWS SDK

## Running Tests

### Quick Start
```bash
# Run all tests
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py --verbose

# Install dependencies and run all tests
python tests/run_tests.py --install-deps --all
```

### Specific Test Suites
```bash
# Unit tests only
python tests/run_tests.py --unit

# Property-based tests only
python tests/run_tests.py --property

# Integration tests only
python tests/run_tests.py --integration

# All tests with coverage report
python tests/run_tests.py --coverage
```

### Individual Tests
```bash
# Run specific test file
python tests/run_tests.py --test tests/unit/test_vehicle_management.py

# Run specific test function
python tests/run_tests.py --test tests/unit/test_vehicle_management.py::TestVehicleManagement::test_create_vehicle_success
```

### Code Quality
```bash
# Run linting
python tests/run_tests.py --lint

# Run everything (tests + linting + coverage)
python tests/run_tests.py --all
```

## Test Configuration

### Environment Variables
Set these environment variables for testing:
```bash
export AWS_DEFAULT_REGION=eu-west-1
export CLUSTER_ARN=arn:aws:rds:eu-west-1:123456789012:cluster:fleet-db-dev
export SECRET_ARN=arn:aws:secretsmanager:eu-west-1:123456789012:secret:fleet-db-secret
export DATABASE_NAME=fleet_db
```

### Mock Configuration
Tests use mocked AWS services to avoid dependencies on actual AWS resources:
- **RDS Data API**: Mocked using unittest.mock
- **Aurora Serverless**: Database operations mocked at the client level
- **API Gateway**: Events created using test fixtures

## Property-Based Testing

### Hypothesis Configuration
Property tests use Hypothesis with these settings:
- **Max Examples**: 100 iterations per test
- **Data Generation**: Domain-appropriate generators for realistic test data
- **Shrinking**: Automatic test case minimization on failure

### Custom Strategies
- `valid_vehicle_data()` - Generates realistic vehicle data
- `valid_service_record_data()` - Generates valid service records
- `invalid_vehicle_data()` - Generates invalid data for error testing
- `cost_range_data()` - Generates cost data for threshold testing

### Property Examples
```python
@given(valid_vehicle_data())
@settings(max_examples=100)
def test_property_vehicle_data_integrity(self, vehicle_data):
    """Vehicle data should be preserved exactly during storage/retrieval"""
    # Test implementation...
```

## Coverage Reporting

### HTML Coverage Report
After running tests with coverage:
```bash
open tests/coverage_html/index.html
```

### Coverage Requirements
- **Minimum Coverage**: 80%
- **Critical Paths**: 100% coverage for error handling
- **Business Logic**: 95% coverage for CRUD operations

### Coverage Exclusions
Lines excluded from coverage:
- Import statements
- Debug logging
- Exception handling for external service failures

## Continuous Integration

### Pre-commit Hooks
Run tests before committing:
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
python tests/run_tests.py --unit --property
```

### CI/CD Pipeline
Tests should run in CI/CD with these stages:
1. **Lint**: Code quality checks
2. **Unit Tests**: Fast feedback on individual components
3. **Property Tests**: Comprehensive property validation
4. **Integration Tests**: End-to-end workflow validation
5. **Coverage**: Ensure minimum coverage thresholds

## Test Data Management

### Fixtures
Test data is centralized in `tests/fixtures/`:
- **sample_vehicles.py**: Realistic vehicle data for testing
- **mock_responses.py**: AWS API response mocks
- **Helper functions**: Data generation utilities

### Data Isolation
Each test method:
- Uses fresh mock objects
- Generates unique test data
- Cleans up after execution
- Avoids shared state between tests

## Debugging Tests

### Verbose Output
```bash
python tests/run_tests.py --verbose
```

### Individual Test Debugging
```bash
# Run single test with full output
pytest tests/unit/test_vehicle_management.py::TestVehicleManagement::test_create_vehicle_success -v -s
```

### Hypothesis Debugging
```bash
# Show Hypothesis statistics
pytest tests/property/ --hypothesis-show-statistics
```

### Mock Debugging
Add debug prints in tests:
```python
print(f"Mock called with: {mock_db.execute_query.call_args}")
```

## Performance Testing

### Test Execution Time
Monitor test performance:
```bash
pytest tests/ --durations=10
```

### Property Test Performance
Hypothesis tests include performance monitoring:
- Track test execution time
- Monitor data generation overhead
- Optimize slow property tests

## Security Testing

### Input Validation
Tests verify proper input validation:
- SQL injection prevention
- XSS protection in API responses
- UUID format validation
- Data type validation

### Error Handling
Tests ensure secure error handling:
- No sensitive data in error messages
- Proper HTTP status codes
- Consistent error response format

## Maintenance

### Adding New Tests
When adding new features:
1. **Unit Tests**: Test individual functions
2. **Property Tests**: Define universal properties
3. **Integration Tests**: Test component interactions
4. **Update Documentation**: Update this README

### Test Maintenance
Regular maintenance tasks:
- Update test data for new requirements
- Refactor tests for code changes
- Monitor test execution time
- Update dependencies

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure src is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

**Mock Issues**:
```python
# Reset mocks between tests
def setup_method(self):
    self.mock_db.reset_mock()
```

**Hypothesis Failures**:
```bash
# Run with seed for reproducible failures
pytest --hypothesis-seed=12345
```

### Getting Help
- Check test output for specific error messages
- Review mock configurations in test setup
- Verify environment variables are set correctly
- Check AWS service mocking is properly configured

## Best Practices

### Test Writing
- **Arrange-Act-Assert**: Clear test structure
- **Descriptive Names**: Test names explain what is being tested
- **Single Responsibility**: Each test verifies one behavior
- **Independent Tests**: No dependencies between tests

### Mock Usage
- **Minimal Mocking**: Mock only external dependencies
- **Realistic Mocks**: Mock responses should match real AWS responses
- **Verify Interactions**: Assert that mocks are called correctly

### Property Testing
- **Realistic Data**: Use domain-appropriate generators
- **Clear Properties**: Properties should be easy to understand
- **Good Coverage**: Test edge cases and boundary conditions

This comprehensive test suite ensures the FLEET system is reliable, maintainable, and ready for production deployment.