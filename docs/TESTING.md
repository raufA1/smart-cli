# Smart CLI Testing & Coverage Guide

## Overview

Smart CLI employs a comprehensive testing strategy with professional coverage reporting through Codecov integration. Our testing framework ensures code quality, reliability, and maintainability across all system components.

## 📊 Coverage Standards

### Target Metrics
- **Overall Coverage**: 80% minimum
- **New Code Coverage**: 75% minimum  
- **Critical Components**: 90%+ coverage
- **Enhanced Mode System**: 85%+ coverage

### Current Status
[![Coverage Status](https://codecov.io/gh/raufA1/smart-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/raufA1/smart-cli)

## 🧪 Test Categories

### 1. Unit Tests (`@pytest.mark.unit`)
- **Purpose**: Test individual functions and classes in isolation
- **Coverage Target**: 90%+
- **Execution**: Fast, no external dependencies

```bash
# Run unit tests only
pytest -m unit

# Run with coverage
pytest -m unit --cov=src --cov-report=term-missing
```

### 2. Integration Tests (`@pytest.mark.integration`) 
- **Purpose**: Test component interactions and workflows
- **Coverage Target**: 80%+
- **Execution**: May involve multiple components

```bash
# Run integration tests
pytest -m integration

# Run with specific component focus
pytest tests/test_*_integration.py
```

### 3. End-to-End Tests (`@pytest.mark.e2e`)
- **Purpose**: Test complete user workflows and CLI functionality
- **Coverage Target**: 75%+
- **Execution**: Full system testing

```bash
# Run E2E tests
pytest -m e2e

# Run CLI-specific E2E tests
pytest tests/test_e2e_cli.py
```

### 4. Performance Tests (`@pytest.mark.performance`)
- **Purpose**: Benchmark and performance validation
- **Tools**: pytest-benchmark integration
- **Execution**: Slower, resource monitoring

```bash
# Run performance tests with benchmarking
pytest -m performance --benchmark-only
```

### 5. Security Tests (`@pytest.mark.security`)
- **Purpose**: Security validation and vulnerability testing
- **Coverage**: Security-critical components
- **Tools**: Custom security test suite

```bash
# Run security-focused tests
pytest -m security
```

### 6. Mode System Tests (`@pytest.mark.mode_system`)
- **Purpose**: Enhanced Mode System functionality validation
- **Coverage Target**: 85%+
- **Components**: All mode-related functionality

```bash
# Run Enhanced Mode System tests
pytest -m mode_system
```

## 🏗️ Test Structure

### Directory Layout
```
tests/
├── __init__.py
├── conftest.py                 # Test configuration and fixtures
├── test_basic.py              # Basic functionality tests
├── test_cli.py                # CLI interface tests
├── test_e2e_cli.py           # End-to-end CLI tests
├── test_agents.py            # AI agent tests
├── test_cost_handler.py      # Cost management tests
├── test_budget_profiles.py   # Budget profile tests
├── test_performance.py       # Performance benchmarks
├── test_security.py          # Security validation tests
├── test_config.py            # Configuration tests
├── test_cache.py             # Caching system tests
├── test_session_manager_integration.py  # Session integration
├── test_intelligent_execution_planner.py  # Execution planner
└── mode_system/              # Enhanced Mode System tests
    ├── test_mode_manager.py
    ├── test_context_manager.py
    ├── test_enhanced_router.py
    ├── test_config_manager.py
    └── test_integration.py
```

### Component-Specific Testing

#### Core System Components
```python
# Example: Core system unit test
@pytest.mark.unit
@pytest.mark.core
def test_session_manager_initialization():
    """Test session manager proper initialization."""
    manager = SessionManager(debug=False)
    assert manager.session_active is False
    assert manager.session_id is not None
```

#### Enhanced Mode System
```python
# Example: Mode system integration test
@pytest.mark.integration
@pytest.mark.mode_system
async def test_mode_switching_workflow():
    """Test complete mode switching workflow."""
    mode_manager = get_mode_manager()
    
    # Test mode switch
    result = await mode_manager.switch_mode("code", "development task")
    assert result is True
    assert mode_manager.current_mode == SmartMode.CODE
    
    # Test context isolation
    context_manager = get_context_manager()
    context = context_manager.get_mode_context("code")
    assert "mode_specific" in context
```

## 🚀 Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run with coverage reporting
pytest --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src --cov-report=html
```

### Filtered Test Execution
```bash
# Run specific test categories
pytest -m "unit and not slow"
pytest -m "integration or e2e"
pytest -m "mode_system and integration"

# Run tests for specific components
pytest tests/test_agents.py
pytest tests/mode_system/

# Run tests with specific patterns
pytest -k "mode" -v
pytest -k "test_config" -v
```

### Advanced Test Options
```bash
# Run with maximum verbosity
pytest -vv

# Stop on first failure
pytest -x

# Run failed tests from last run
pytest --lf

# Run only modified tests
pytest --testmon

# Run with coverage and fail under threshold
pytest --cov=src --cov-fail-under=80

# Generate JUnit XML for CI/CD
pytest --junitxml=junit.xml
```

## 📈 Coverage Analysis

### Coverage Reports

#### Terminal Coverage
```bash
# Basic coverage report
pytest --cov=src --cov-report=term

# Detailed missing lines report
pytest --cov=src --cov-report=term-missing

# Skip covered files for clarity
pytest --cov=src --cov-report=term-missing:skip-covered
```

#### HTML Coverage Report
```bash
# Generate interactive HTML report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### XML Coverage for Codecov
```bash
# Generate XML report for CI/CD
pytest --cov=src --cov-report=xml

# This generates coverage.xml used by Codecov
```

### Coverage Configuration

#### Component-Based Coverage Tracking
- **Core System**: `src/core/` - 90%+ target
- **Enhanced Mode System**: `src/core/mode_*.py` - 85%+ target
- **AI Agents**: `src/agents/` - 80%+ target
- **Request Handlers**: `src/handlers/` - 85%+ target
- **Integrations**: `src/integrations/` - 75%+ target
- **Utilities**: `src/utils/` - 90%+ target

#### Exclusions and Filters
```ini
# pytest.ini exclusions
omit = 
    */tests/*
    */test_*
    */__pycache__/*
    */venv/*
    setup.py
    conftest.py

# .codecov.yml exclusions
ignore:
    - "setup.py"
    - "tests/"
    - "docs/"
    - "*.example"
    - ".github/"
```

## 🔧 Test Development

### Writing Effective Tests

#### Test Structure (AAA Pattern)
```python
def test_feature_functionality():
    # Arrange
    manager = ComponentManager()
    test_data = {"key": "value"}
    
    # Act
    result = manager.process(test_data)
    
    # Assert
    assert result.success is True
    assert result.data["key"] == "value"
```

#### Async Test Patterns
```python
@pytest.mark.asyncio
async def test_async_functionality():
    """Test async operations properly."""
    async with AsyncContext() as context:
        result = await context.async_operation()
        assert result is not None
```

#### Parameterized Tests
```python
@pytest.mark.parametrize("mode,expected", [
    ("smart", SmartMode.SMART),
    ("code", SmartMode.CODE),
    ("analysis", SmartMode.ANALYSIS),
])
def test_mode_parsing(mode, expected):
    """Test mode parsing with multiple inputs."""
    parsed = parse_mode_string(mode)
    assert parsed == expected
```

### Fixtures and Test Data

#### Common Fixtures
```python
# conftest.py
@pytest.fixture
def mock_ai_client():
    """Provide mock AI client for testing."""
    with patch('src.utils.simple_ai_client.SimpleOpenRouterClient') as mock:
        yield mock

@pytest.fixture
async def initialized_mode_system():
    """Provide initialized mode system."""
    from src.core.mode_integration_manager import get_mode_integration_manager
    
    manager = get_mode_integration_manager(mock_smart_cli)
    await manager.initialize_enhanced_mode_system()
    yield manager
```

#### Test Data Management
```python
# Test data factories
class TestDataFactory:
    @staticmethod
    def create_mode_config(mode_name="test"):
        return ModeConfig(
            name=f"Test {mode_name}",
            description=f"Test mode for {mode_name}",
            context_size=4000
        )
```

## 🔍 Quality Gates

### Pre-Commit Testing
```bash
# Install pre-commit hooks
pre-commit install

# Run all pre-commit checks
pre-commit run --all-files
```

### CI/CD Integration
The GitHub Actions workflow automatically:
- Runs complete test suite across Python versions
- Generates coverage reports 
- Uploads to Codecov
- Performs security scanning
- Validates performance benchmarks

### Coverage Gates
- **Pull Requests**: Require 75%+ coverage on new code
- **Main Branch**: Maintain 80%+ overall coverage
- **Critical Components**: 90%+ coverage requirement
- **Regression Prevention**: No coverage decrease allowed

## 📊 Codecov Integration

### Dashboard Features
- **Pull Request Comments**: Automatic coverage analysis
- **Component Tracking**: Per-component coverage metrics
- **Trend Analysis**: Coverage changes over time
- **Flag-Based Reporting**: Separate tracking for test types

### Configuration
```yaml
# .codecov.yml highlights
coverage:
  status:
    project:
      default:
        target: 80%
        threshold: 1%
    patch:
      default:
        target: 75%
        threshold: 0%
```

### Report Analysis
- **Coverage Sunburst**: Visual coverage breakdown
- **File Coverage**: Line-by-line analysis
- **Commit Comparison**: Coverage changes per commit
- **Component Trends**: Long-term coverage tracking

## 🛠️ Troubleshooting

### Common Issues

#### Coverage Not Detected
```bash
# Ensure proper source specification
pytest --cov=src --cov-branch

# Check .coveragerc configuration
cat .coveragerc
```

#### Async Test Failures
```bash
# Install required async testing dependencies
pip install pytest-asyncio

# Mark async tests properly
@pytest.mark.asyncio
```

#### Slow Test Execution
```bash
# Run only fast tests
pytest -m "not slow"

# Use parallel execution
pytest -n auto  # requires pytest-xdist
```

### Performance Optimization
- Use `pytest-xdist` for parallel test execution
- Mark slow tests appropriately
- Mock external dependencies
- Use appropriate test isolation levels

## 📋 Best Practices

### Test Design
1. **Single Responsibility**: One test per functionality
2. **Clear Naming**: Descriptive test names
3. **Proper Isolation**: Independent test execution
4. **Comprehensive Coverage**: Edge cases and error conditions
5. **Performance Awareness**: Keep tests fast and efficient

### Coverage Strategy
1. **Focus on Critical Paths**: Prioritize important functionality
2. **Include Error Scenarios**: Test failure conditions
3. **Mock External Dependencies**: Reliable test execution
4. **Regular Review**: Maintain coverage standards
5. **Component-Based Tracking**: Monitor specific areas

### Continuous Improvement
- Regular coverage analysis
- Performance benchmark tracking
- Security test expansion
- Test suite optimization
- Documentation updates

---

This comprehensive testing strategy ensures Smart CLI maintains high quality, reliability, and performance standards while providing detailed coverage insights through professional tooling integration.