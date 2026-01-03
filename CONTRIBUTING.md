# Contributing to Mathematical Physics Compendium

Thank you for your interest in contributing to the Mathematical Physics Compendium! This document provides guidelines and instructions for contributing to this project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Quality Standards](#code-quality-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)
- [Documentation](#documentation)

---

## Code of Conduct

This project adheres to professional and respectful collaboration standards. Please:
- Be respectful and inclusive
- Focus on constructive feedback
- Welcome newcomers and help them learn
- Maintain scientific rigor and accuracy

---

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- Basic understanding of mathematical physics concepts (helpful but not required)

### Areas for Contribution
1. **Mathematical Implementations**: New algebraic structures, group theory, topology
2. **Quantum Computing**: Circuit implementations, algorithms
3. **Visualization**: Scientific plotting, interactive tools
4. **Documentation**: Improving explanations, examples, tutorials
5. **Testing**: Adding test coverage, finding bugs
6. **Performance**: Optimization, profiling, benchmarking

---

## Development Setup

### 1. Fork and Clone
```bash
git clone https://github.com/YOUR-USERNAME/MathScienceCompendium.git
cd MathScienceCompendium
```

### 2. Install in Development Mode
```bash
# Install with all development dependencies
pip install -e ".[dev,lint,viz]"

# For quantum computing features
pip install -e ".[quantum]"

# For topology features
pip install -e ".[topology]"

# For everything
pip install -e ".[all]"
```

### 3. Set Up Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

This will automatically run quality checks before each commit.

### 4. Verify Installation
```bash
# Run tests
pytest

# Run linting
ruff check src/

# Run type checking
mypy src/mathphysics --ignore-missing-imports
```

---

## Code Quality Standards

### Linting and Formatting
We use **Ruff** for linting and formatting:
```bash
# Check for issues
ruff check src/

# Auto-fix issues
ruff check src/ --fix

# Format code
ruff format src/
```

### Type Hints
- Add type hints to all new functions
- Use modern syntax: `list[int]` instead of `List[int]`
- Use `|` for unions: `int | None` instead of `Optional[int]`

Example:
```python
def compute_roots(dimension: int, normalize: bool = True) -> np.ndarray:
    """Compute root system for given dimension.
    
    Args:
        dimension: The dimension of the root system
        normalize: Whether to normalize roots to unit length
        
    Returns:
        Array of roots with shape (n_roots, dimension)
    """
    ...
```

### Docstrings
Use Google-style docstrings:
```python
def my_function(arg1: int, arg2: str) -> bool:
    """Brief description of function.
    
    Longer description if needed. Can include mathematical notation:
    The function computes: f(x) = x² + 2x + 1
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When input is invalid
        
    Example:
        >>> my_function(5, "test")
        True
    """
    ...
```

### Code Organization
- Keep functions focused and single-purpose
- Maximum function length: ~50 lines (guideline, not strict)
- Use meaningful variable names
- Avoid magic numbers - use named constants

---

## Testing Guidelines

### Writing Tests
We use **pytest** for testing. Place tests in the `tests/` directory.

```python
import pytest
import numpy as np
from mathphysics.algebras.roots import E8RootSystem

def test_e8_root_count():
    """Test that E8 generates exactly 240 roots."""
    e8 = E8RootSystem()
    roots = e8.generate_roots()
    assert len(roots) == 240

def test_e8_root_norms():
    """Test that all E8 roots have norm squared = 2."""
    e8 = E8RootSystem()
    roots = e8.generate_roots()
    norms_squared = np.sum(roots**2, axis=1)
    np.testing.assert_allclose(norms_squared, 2.0, rtol=1e-10)

@pytest.mark.slow
def test_expensive_computation():
    """Mark slow tests so they can be skipped."""
    ...

@pytest.mark.quantum
@pytest.mark.skipif(not has_qiskit, reason="Qiskit not installed")
def test_quantum_circuit():
    """Use markers for optional dependencies."""
    ...
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_all.py::TestE8::test_root_system

# Skip slow tests
pytest -m "not slow"

# Run only unit tests
pytest -m unit
```

### Test Coverage
- Aim for >80% coverage for new code
- Critical algorithms should have >95% coverage
- Check coverage report: `pytest --cov=src --cov-report=html` then open `htmlcov/index.html`

---

## Submitting Changes

### Branch Naming
- Feature: `feature/description`
- Bug fix: `fix/description`
- Documentation: `docs/description`
- Refactoring: `refactor/description`

Example: `feature/add-e7-root-system`

### Commit Messages
Follow conventional commits:
```
type(scope): brief description

Longer description if needed

- Bullet points for details
- Reference issues: Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(algebras): add E7 root system implementation

Implements the E7 exceptional Lie algebra root system with:
- 126 roots in 7D subspace
- Cartan matrix computation
- Root classification

Fixes #42
```

```
fix(quantum): correct Hadamard gate phase

The previous implementation had an incorrect phase factor.
Now matches standard quantum computing conventions.
```

### Pull Request Process

1. **Update your branch**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Ensure quality checks pass**
   ```bash
   ruff check src/
   mypy src/mathphysics --ignore-missing-imports
   pytest
   ```

3. **Create Pull Request**
   - Provide clear description of changes
   - Reference related issues
   - Include test results
   - Add examples if applicable

4. **PR Template**
   ```markdown
   ## Description
   Brief description of changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Performance improvement
   - [ ] Refactoring
   
   ## Testing
   - [ ] All tests pass
   - [ ] New tests added
   - [ ] Coverage maintained/improved
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No new warnings
   ```

5. **Review Process**
   - Address reviewer feedback
   - Keep discussions constructive
   - Update PR as needed

---

## Documentation

### Code Documentation
- All public functions/classes need docstrings
- Include mathematical formulas using LaTeX in docstrings
- Provide examples in docstrings

### LaTeX Papers
Mathematical derivations should be added to the `papers/` directory:
```bash
cd papers
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

### Jupyter Notebooks
For exploratory work and tutorials:
```bash
jupyter notebook experiments/notebooks/
```

---

## Project-Specific Guidelines

### Mathematical Code
- Verify against primary literature
- Include references in docstrings
- Test against known results
- Document assumptions and limitations

Example:
```python
def compute_e8_weyl_order() -> int:
    """Compute order of E8 Weyl group.
    
    The Weyl group W(E8) has order:
    |W(E8)| = 2^14 · 3^5 · 5^2 · 7 = 696,729,600
    
    Reference:
        Humphreys, J. (1990). Reflection Groups and Coxeter Groups.
        Cambridge University Press, p. 75.
        
    Returns:
        Order of Weyl group (696729600)
    """
    return 2**14 * 3**5 * 5**2 * 7
```

### Performance Considerations
- Profile before optimizing
- Use NumPy vectorization when possible
- Consider JIT compilation (numba, jax) for hot loops
- Document performance characteristics

### Quantum Computing Code
- Follow Qiskit conventions
- Verify against quantum circuit simulator
- Document qubit indexing clearly
- Include circuit diagrams in docstrings

---

## Getting Help

### Resources
- **Documentation**: See `README.md` and `docs/`
- **Examples**: Check `experiments/` directory
- **Tests**: Look at `tests/` for usage examples

### Contact
- Open an issue for bugs or feature requests
- Start a discussion for questions
- Tag maintainers for urgent issues

---

## Recognition

Contributors will be acknowledged in:
- Git commit history
- Paper acknowledgments (for significant contributions)
- CONTRIBUTORS.md file

Thank you for contributing to advancing mathematical physics research!

---

**Last Updated**: 2026-01-03
**Version**: 1.0
