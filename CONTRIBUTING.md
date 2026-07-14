# Contributing to geodoctor

Thank you for your interest in contributing to geodoctor! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Adding New Checks](#adding-new-checks)
- [Adding New Fixers](#adding-new-fixers)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)

## Code of Conduct

This project adheres to the Contributor Covenant [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- Clear descriptive title
- Detailed description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Sample data (if applicable)
- Environment information (OS, Python version, geodoctor version)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- Clear use case description
- Expected behavior
- Any relevant examples or mockups

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation as needed
7. Submit a pull request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/geodoctor.git
cd geodoctor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Adding New Checks

Checks are functions that validate geospatial data. To add a new check:

1. Create a new file in `src/geodoctor/checks/` or add to existing file
2. Follow this pattern:

```python
from typing import List
from geodoctor.models import CheckResult, Severity

def check_my_validation(gdf, config) -> List[CheckResult]:
    """
    Brief description of what this check does.
    
    Args:
        gdf: GeoDataFrame to check
        config: Configuration dictionary
    
    Returns:
        List of CheckResult objects
    """
    results = []
    
    # Your validation logic here
    for idx, row in gdf.iterrows():
        if not is_valid(row):
            results.append(CheckResult(
                check_name="my_validation",
                severity=Severity.ERROR,
                message=f"Feature {idx} failed validation",
                feature_id=row.get('id', idx),
                details={"reason": "specific reason"}
            ))
    
    return results
```

3. Register the check in `src/geodoctor/registry.py`:

```python
from .checks.my_check import check_my_validation

CHECKS = {
    # ... existing checks ...
    "my_validation": check_my_validation,
}
```

4. Add configuration options in `src/geodoctor/config.py` if needed
5. Write tests in `tests/test_checks.py`
6. Update README.md with the new check

## Adding New Fixers

Fixers automatically correct issues found by checks. To add a new fixer:

1. Create a new file in `src/geodoctor/fixers/` or add to existing file
2. Follow this pattern:

```python
import geopandas as gpd

def fix_my_issue(gdf: gpd.GeoDataFrame, config: dict) -> gpd.GeoDataFrame:
    """
    Brief description of what this fixer does.
    
    Args:
        gdf: GeoDataFrame to fix
        config: Configuration dictionary
    
    Returns:
        Fixed GeoDataFrame
    """
    # Your fixing logic here
    # Make sure to return a copy, not modify in place
    
    return gdf_fixed
```

3. Register the fixer in `src/geodoctor/fixers/__init__.py`:

```python
from .my_fixer import fix_my_issue

FIXERS = {
    # ... existing fixers ...
    "my_issue": fix_my_issue,
}
```

4. Write tests in `tests/test_fixers.py`
5. Update README.md with the new fixer

## Testing

We use pytest for testing. All new code must include tests.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=geodoctor

# Run specific test file
pytest tests/test_checks.py

# Run with verbose output
pytest -v
```

### Test Guidelines

- Write tests for both success and failure cases
- Use fixtures for common test data
- Test edge cases and error conditions
- Aim for high test coverage (>90%)
- Use descriptive test names that explain what is being tested

## Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting
- **MyPy**: Type checking

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

### Style Guidelines

- Follow PEP 8
- Use type hints for all function signatures
- Write docstrings for all public functions (Google style)
- Keep functions focused and single-purpose
- Use descriptive variable names
- Add comments for complex logic

## Submitting Changes

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(checks): add topology overlap detection
fix(fixers): correct geometry repair for multipolygons
docs(readme): add usage examples for batch processing
```

### Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/)
3. Ensure all CI checks pass
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested

### Review Process

- All PRs require at least one review
- CI must pass (tests, linting, type checking)
- Code coverage should not decrease
- Documentation should be updated

## Questions?

Feel free to open an issue for questions or join discussions in the repository.

Thank you for contributing to geodoctor! 🎉

## AI-assisted maintenance

This project uses [Codex](https://openai.com/codex/) for AI-assisted PR review. The `.github/workflows/codex-review.yml` workflow triggers automated review on pull requests. Maintainers manually approve all changes — no AI-generated commits are merged without human review.
