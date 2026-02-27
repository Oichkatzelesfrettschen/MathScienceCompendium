# CLAUDE.md - MathScienceCompendium Project Instructions

## Overview

4-volume LaTeX mathematical physics compendium + Python computational framework.
Synthesizes exceptional Lie algebras (E6/E7/E8/F4), Kac-Moody extensions,
quantum encoding schemes, and turbulence simulation (LBM).

Source: `src/mathphysics/` (38 modules).
Tests: `tests/` (500+ tests, 60%+ coverage).
Papers: `papers/main.tex` (4 volumes + 2 appendices).

Full module map: `docs/ARCHITECTURE.md`.

## Build Commands

```bash
make install        # venv + pip install -e ".[dev,lint]"
make lint           # ruff check src tests benchmarks experiments
make check-types    # mypy src/mathphysics --ignore-missing-imports
make test           # pytest tests -q with PYTHONHASHSEED=0
make benchmark      # NumPy vs JAX LBM benchmark
make figures        # generate PNG + interactive HTML
make papers         # pdflatex + bibtex + pdflatex (x2) -> papers/main.pdf
make repro-refresh  # normalize + registries + audit + verify pipeline
make cleanbuild     # full clean + install + all quality gates + papers
```

## Standards

- **Linter**: ruff (0 violations required for CI to pass)
- **Formatter**: ruff format (enforced in CI)
- **Type checker**: mypy (continue-on-error; fix incrementally)
- **Security**: bandit (continue-on-error; informational)
- **Tests**: pytest; PYTHONHASHSEED=0 for determinism
- **Coverage target**: 60%+ (qiskit-only modules excluded from measurement)
- **Branches**: main; feature/x, fix/x, docs/x; PRs require green CI

## Directory Conventions

```
src/mathphysics/           Python package root
src/mathphysics/algebras/  Algebraic structures subpackage
tests/unit/                One test file per source module
tests/conftest.py          Shared fixtures + collect_ignore for qiskit
experiments/               Standalone scripts; NOT imported by src/
data/external/             sources.toml + PROVENANCE.json
data/registry/             TOML indexes (built by make repro-refresh)
docs/reports/              Archived analysis reports (do not edit)
schemas/                   JSON schemas for validation
scripts/                   Data pipeline scripts (fetch, validate, normalize)
```

## Common Issues and Fixes

1. **ruff E402** (module-level import not at top): Move helper classes that
   reference top-level imports to AFTER the imports block.

2. **qiskit collection errors**: `tests/conftest.py` has `collect_ignore`
   that skips quantum circuit test files when qiskit is absent.

3. **np.bool_ in json.dump**: Use `_NumpyEncoder` from
   `src/mathphysics/algebras/cayley_dickson.py` as the `cls=` argument.

4. **JAX pre-allocation (OOM)**: Set `XLA_PYTHON_CLIENT_PREALLOCATE=false`
   (the Makefile already does this for JAX targets).

5. **LaTeX undefined references**: Run all 4 LaTeX passes:
   `pdflatex -> bibtex -> pdflatex -> pdflatex` (`make papers` does this).

## Optional Dependencies

| Package | Enables |
|---------|---------|
| `jax jaxlib` | Accelerated LBM, loop algebras, unified_physics |
| `qiskit qiskit-aer` | Quantum circuit modules (E7/E8 oracles, encoding) |
| `gudhi` | Persistent homology in topology_bridge |
| `requests` | External source fetching, LMFDB bridge |

## References

- Architecture: `docs/ARCHITECTURE.md`
- Quick start: `docs/QUICK_START.md`
- Installation: `experiments/INSTALLATION.md`
- Bibliography: `papers/references.bib` (60+ entries)
- Offline reproducibility: `docs/OFFLINE_REPRODUCIBILITY.md`
