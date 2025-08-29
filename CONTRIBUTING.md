# Contributing to Smart CLI

Thank you for your interest in contributing to Smart CLI! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR-USERNAME/smart-cli.git
   cd smart-cli
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install in development mode
   pip install -e ".[dev,test]"
   
   # Install pre-commit hooks
   pre-commit install
   ```

3. **Run tests to ensure everything works**
   ```bash
   pytest tests/
   ```

## 🎯 How to Contribute

### 🐛 Reporting Bugs

- **Search existing issues** before creating a new one
- **Use the bug report template** when creating issues
- **Provide detailed information**:
  - Smart CLI version (`smart version`)
  - Operating system
  - Python version
  - Complete error messages
  - Steps to reproduce

### 💡 Suggesting Features

- **Search existing feature requests** first
- **Use the feature request template**
- **Explain the problem** you're trying to solve
- **Describe your proposed solution**
- **Consider alternative approaches**

### 📝 Improving Documentation

- **Fix typos, improve clarity**
- **Add missing examples**
- **Update outdated information**
- **Translate documentation** (future)

### 🔧 Code Contributions

#### Branch Strategy
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make your changes
# ...

# Push and create PR
git push origin feature/your-feature-name
```

#### Code Style Guidelines

**Python Code Style:**
- Follow **PEP 8** style guide
- Use **Black** for formatting: `black src tests`
- Use **isort** for imports: `isort src tests`
- Maximum line length: **88 characters**
- Use **type hints** for all functions
- Write **docstrings** for all public functions/classes

**Example:**
```python
from typing import Optional, Dict, Any
import typer


def generate_code(
    prompt: str, 
    language: str = "python",
    temperature: float = 0.7
) -> Dict[str, Any]:
    """Generate code using AI based on the given prompt.
    
    Args:
        prompt: The code generation prompt
        language: Target programming language
        temperature: AI creativity level (0.0-2.0)
        
    Returns:
        Dictionary containing generated code and metadata
        
    Raises:
        ValueError: If temperature is out of range
        APIError: If AI service is unavailable
    """
    if not 0.0 <= temperature <= 2.0:
        raise ValueError("Temperature must be between 0.0 and 2.0")
        
    # Implementation here
    return {"code": "...", "language": language}
```

#### Testing Guidelines

**Write Tests For:**
- All new functions and classes
- Bug fixes (regression tests)
- Edge cases and error conditions
- Integration points with external services

**Test Structure:**
```python
# tests/test_feature.py
import pytest
from unittest.mock import Mock, patch
from src.feature import your_function


class TestYourFunction:
    """Test suite for your_function."""
    
    def test_basic_functionality(self):
        """Test basic successful case."""
        result = your_function("input")
        assert result == "expected_output"
    
    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            your_function("invalid_input")
    
    @patch('src.feature.external_service')
    def test_with_mocked_dependency(self, mock_service):
        """Test with mocked external dependencies."""
        mock_service.return_value = "mocked_response"
        result = your_function("input")
        assert result == "expected_with_mock"
```

#### Performance Considerations

- **Use async/await** for I/O operations
- **Implement caching** for expensive operations
- **Monitor memory usage** for large data processing
- **Profile performance** for critical paths

### 🔒 Security Guidelines

- **Never commit API keys** or secrets
- **Validate all user inputs**
- **Use secure communication** (HTTPS/TLS)
- **Follow security best practices**
- **Report security issues privately**

## 🛠️ Development Workflow

### 1. Local Development

```bash
# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_cli.py -v

# Run code quality checks
black src tests
isort src tests
flake8 src tests
mypy src

# Run security scan
bandit -r src/
safety check
```

### 2. Pre-commit Hooks

Pre-commit hooks automatically run when you commit:

```bash
# Install hooks (one time)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

### 3. Continuous Integration

Our CI pipeline runs:
- **Tests** on Python 3.9, 3.10, 3.11, 3.12
- **Code quality** checks (black, flake8, mypy)
- **Security scans** (bandit, safety)
- **Package building** and validation
- **Integration tests**

## 📦 Release Process

### Version Numbering
We use [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes (backward compatible)

### Release Steps
1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md**
3. **Create release PR**
4. **Merge to main**
5. **Create GitHub release**
6. **Automatic PyPI publication**

## 💻 Development Environment Setup

### Required Tools
- **Python 3.9+**
- **Git**
- **Text editor** (VS Code recommended)

### VS Code Configuration
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

### Useful Commands
```bash
# Install development dependencies
pip install -e ".[dev,test,docs]"

# Build documentation locally
sphinx-build -b html docs/ docs/_build/

# Build package
python -m build

# Install from local build
pip install dist/*.whl
```

## 🤝 Community Guidelines

### Code of Conduct
We follow the [Contributor Covenant](https://www.contributor-covenant.org/):

- **Be respectful** and inclusive
- **Welcome newcomers**
- **Focus on constructive feedback**
- **Help others learn and grow**
- **Assume good intentions**

### Communication Channels
- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Pull Request Reviews**: Code discussions

### Recognition
Contributors will be:
- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes**
- **Recognized in documentation**

## 📚 Additional Resources

### Documentation
- **User Guide**: [docs/user-guide.md](docs/user-guide.md)
- **API Reference**: [docs/api-reference.md](docs/api-reference.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)

### External Resources
- [Python Packaging Guide](https://packaging.python.org/)
- [Typer Documentation](https://typer.tiangolo.com/)
- [pytest Documentation](https://pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)

## ❓ Getting Help

### Common Issues
- **Import errors**: Ensure you've installed in development mode (`pip install -e .`)
- **Test failures**: Check Python version compatibility
- **Style errors**: Run `black src tests` and `isort src tests`

### Ask for Help
- **GitHub Discussions**: For general questions
- **GitHub Issues**: For specific problems
- **Review existing discussions**: Your question might be answered already

---

## 🙏 Thank You!

Every contribution, no matter how small, makes Smart CLI better for everyone. We appreciate your time and effort!

**Happy Coding!** 🚀