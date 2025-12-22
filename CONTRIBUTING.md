# Contributing to Trinity Protocol

First off, thank you for considering contributing to Trinity Protocol! 🎉

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

---

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code.

**Be respectful, inclusive, and constructive.**

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Environment** (OS, Python version, Trinity version)
- **Logs/Screenshots** if applicable

### 💡 Suggesting Features

Feature suggestions are welcome! Please include:

- **Use case** - Why is this feature needed?
- **Proposed solution** - How would it work?
- **Alternatives** - Other approaches considered

### 🔧 Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a PR

---

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Virtual environment support

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/trinity-protocol.git
cd trinity-protocol/.ai

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black flake8

# Run tests to verify setup
pytest cli/tests/ -v
```

### Running Tests

```bash
# All tests
pytest cli/tests/ -v

# Specific test
pytest cli/tests/test_basic.py -v

# With coverage
pytest cli/tests/ --cov=cli --cov-report=html
```

---

## Pull Request Process

### 1. Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring

Example: `feature/add-batch-verify`

### 2. Commit Messages

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

Examples:
```
feat(sandbox): add batch apply support
fix(verify): handle empty dev folder
docs(readme): update installation steps
```

### 3. PR Checklist

Before submitting:

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New features have tests
- [ ] Documentation updated
- [ ] No merge conflicts

### 4. Review Process

1. Automated checks run
2. Maintainer reviews code
3. Address feedback
4. Merge when approved

---

## Style Guidelines

### Python Code

- Follow **PEP 8**
- Use **type hints** where possible
- Add **docstrings** to functions/classes
- Maximum line length: **100 characters**

```python
def verify_session(session_path: Path, scope: str = "dev") -> bool:
    """
    Verify a session's code quality and safety.
    
    Args:
        session_path: Path to the session directory
        scope: Verification scope ('dev' or 'prod')
    
    Returns:
        True if verification passes, False otherwise
    """
    ...
```

### Formatting

Use `black` for formatting:

```bash
black cli/ --line-length 100
```

Use `flake8` for linting:

```bash
flake8 cli/ --max-line-length 100
```

### Documentation

- Use Markdown for docs
- Include code examples
- Keep language clear and concise

---

## 📁 Project Structure

When contributing, understand the structure:

```
cli/
├── main.py          # Entry point - register commands here
├── commands/        # CLI commands - one file per command
│   └── *.py
├── core/            # Core modules - shared logic
│   └── *.py
└── tests/           # Tests - mirror command structure
    └── test_*.py
```

### Adding a New Command

1. Create `cli/commands/your_command.py`
2. Define Typer app: `app = typer.Typer()`
3. Register in `cli/main.py`
4. Add tests in `cli/tests/test_your_command.py`
5. Update documentation

---

## 🙏 Thank You!

Your contributions make Trinity Protocol better for everyone.

Questions? Open an issue or reach out!

