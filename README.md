# Smart CLI

[![Build Status](https://github.com/smart-cli/smart-cli/workflows/CI/badge.svg)](https://github.com/smart-cli/smart-cli/actions)
[![Coverage Status](https://codecov.io/gh/smart-cli/smart-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/smart-cli/smart-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful AI-powered CLI tool for code generation, project management, and development automation.

## ✨ Features

- **AI-Powered Code Generation**: Generate functions, classes, and APIs in multiple programming languages
- **Multi-LLM Support**: Seamlessly switch between GPT-4, Claude, and Gemini
- **Enterprise Security**: OAuth 2.0, RBAC, and comprehensive audit logging
- **High Performance**: Advanced caching and async operations
- **Project Templates**: Quick project initialization with best practices
- **Code Review**: Automated code analysis and security scanning
- **Health Monitoring**: Built-in health checks and system monitoring

## 🚀 Quick Start

### Installation

```bash
# Using pip
pip install smart-cli

# Development installation
git clone https://github.com/smart-cli/smart-cli.git
cd smart-cli-python
pip install -r requirements.txt
pip install -e .
```

### Basic Usage

```bash
# Show version and help
smart-cli --help
smart-cli version

# Configure API keys
smart-cli config --set openrouter_api_key --value your_api_key_here

# Initialize a new project
smart-cli init project my-app --template python

# Generate code
smart-cli generate function --name fibonacci --language python --desc "Calculate fibonacci sequence"

# Review existing code
smart-cli review code src/main.py --focus security

# Check system health
smart-cli health
```

## 📖 Commands

### Project Initialization
```bash
# Create new Python project
smart-cli init project my-python-app --template python

# Create new Node.js project  
smart-cli init project my-node-app --template node

# Create new React app
smart-cli init project my-react-app --template react
```

### Code Generation
```bash
# Generate a function
smart-cli generate function calculate_sum --lang python --desc "Sum two numbers"

# Generate a class
smart-cli generate class-definition User --lang python --desc "User management class"

# Generate API boilerplate
smart-cli generate api my-api --framework fastapi --endpoints "users,posts,comments"
```

### Code Review & Analysis
```bash
# Review single file
smart-cli review code app.py --focus security

# Review entire project
smart-cli review project . --focus performance --tests

# Focus areas: general, security, performance, style
```

### Configuration Management
```bash
# Show current configuration
smart-cli config --show

# Set configuration values
smart-cli config --set temperature --value 0.7
smart-cli config --set default_model --value "anthropic/claude-3-sonnet-20240229"

# Check system health
smart-cli health
```

## ⚙️ Configuration

Smart CLI uses a layered configuration system:

1. **Environment variables** (highest priority)
2. **Command line options**
3. **Configuration files** (`~/.smart-cli/config.yaml`)
4. **Default values** (lowest priority)

### Environment Variables

```bash
export OPENROUTER_API_KEY="your_api_key"
export ANTHROPIC_API_KEY="your_claude_key"
export OPENAI_API_KEY="your_openai_key"
export REDIS_URL="redis://localhost:6379"
export LOG_LEVEL="INFO"
```

### Configuration File

```yaml
# ~/.smart-cli/config.yaml
default_model: "anthropic/claude-3-sonnet-20240229"
temperature: 0.7
max_tokens: 4000
cache_enabled: true
log_level: "INFO"

fallback_models:
  - "anthropic/claude-3-sonnet-20240229"
  - "openai/gpt-4-turbo"
  - "google/gemini-pro"
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/smart-cli/smart-cli.git
cd smart-cli-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_cli.py

# Run with verbose output
pytest -v

# Run security tests
pytest tests/security/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Run all quality checks
pre-commit run --all-files
```

### Project Structure

```
smart-cli-python/
├── .claude/                    # Claude Code integration
├── src/
│   ├── cli.py                 # Main CLI entry point
│   ├── commands/              # Command implementations
│   │   ├── generate.py        # Code generation commands
│   │   ├── init.py           # Project initialization
│   │   └── review.py         # Code review commands
│   └── utils/                 # Configuration and utilities
│       ├── config.py         # Configuration management
│       └── health_checker.py # Health monitoring
├── tests/                     # Comprehensive testing
├── docs/                      # Documentation
├── pyproject.toml             # Python packaging config
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## 🛡️ Security

Smart CLI implements multiple security layers:

- **Encrypted credential storage** using PBKDF2 and Fernet
- **Input validation** to prevent injection attacks
- **Secure API communication** with TLS
- **Role-based access control** (RBAC)
- **Audit logging** for all operations

### Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Regularly rotate API keys** and credentials
4. **Review generated code** before execution
5. **Keep dependencies updated** for security patches

## 📊 Monitoring & Observability

Smart CLI includes built-in monitoring capabilities:

```bash
# Check system health
smart-cli health

# View configuration
smart-cli config --show

# Monitor performance (requires Prometheus setup)
# Metrics available at http://localhost:9090/metrics
```

### Health Checks

The health command verifies:
- Python environment
- Configuration validity
- Database connectivity
- AI service availability
- Required dependencies

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) for details on:

- Development setup
- Code standards  
- Testing requirements
- Pull request process

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **GitHub Issues**: [Create an issue](https://github.com/smart-cli/smart-cli/issues)
- **GitHub Discussions**: [Join the discussion](https://github.com/smart-cli/smart-cli/discussions)

## 🚧 Roadmap

### Phase 1: Foundation ✅
- [x] Basic CLI framework
- [x] Project initialization templates
- [x] Configuration management
- [x] Health monitoring

### Phase 2: AI Integration (In Progress)
- [ ] OpenRouter API integration
- [ ] Multi-LLM support with fallbacks
- [ ] Context management
- [ ] Prompt optimization

### Phase 3: Advanced Features (Planned)
- [ ] Plugin system
- [ ] Custom templates
- [ ] Team collaboration
- [ ] Advanced analytics

### Phase 4: Enterprise (Future)
- [ ] SSO integration
- [ ] Enterprise deployment
- [ ] Advanced monitoring
- [ ] Compliance features

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for the CLI framework
- Uses [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Inspired by modern development tools and best practices
- Community feedback and contributions