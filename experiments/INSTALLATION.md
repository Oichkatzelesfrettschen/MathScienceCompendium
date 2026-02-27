# Installation Guide

## Prerequisites

| Tool | Minimum Version | Notes |
|------|----------------|-------|
| Python | 3.9 | 3.11 recommended; tested on 3.9-3.12 |
| pip | 23.0 | `python3 -m pip install --upgrade pip` |
| pdflatex | any | For `make papers`; install via texlive |
| bibtex | any | Included with texlive |
| pdftotext | any | `poppler-utils` package |
| ripgrep (rg) | any | Optional; used in `make lint-latex` |

Check tools with:

```bash
make check-deps
```

## Canonical Setup (Repository Root)

Run these commands from the repository root:

```bash
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/pip install -e ".[dev,lint]"
```

Or use the Makefile shortcut:

```bash
make install
```

## Quick Validation

```bash
PYTHONPATH=src ./venv/bin/python -c "from mathphysics.algebras.cayley_dickson import Complex; z = Complex([3,4]); print(z.norm())"
```

Expected output includes `5.0`.

```bash
make test
```

Expected: 500+ tests pass, 0 failures.

## Optional Dependencies

These are not required for the core framework but unlock additional features:

```bash
# JAX/XLA acceleration (GPU/TPU) -- unlocks accelerated LBM and loop algebras
./venv/bin/pip install jax jaxlib

# Qiskit -- unlocks quantum circuit modules (E7/E8 oracles, encoding)
./venv/bin/pip install qiskit qiskit-aer

# GUDHI -- unlocks topological data analysis (persistent homology)
./venv/bin/pip install gudhi
```

Without optional dependencies, tests for those modules are automatically skipped.

## Experiment Execution

From repository root:

```bash
make benchmark         # NumPy vs JAX LBM performance comparison
make run-highres       # High-resolution JAX simulation (requires JAX)
make run-unified       # Unified cross-domain simulation
make run-jordan        # E11 Jordan algebra trace analysis
make run-clifford      # Clifford algebra rotation demo
```

## LaTeX Paper Build

Requires `pdflatex` and `bibtex`:

```bash
make figures   # Generate PNG figures and interactive HTML explorers
make papers    # Compile LaTeX into papers/main.pdf (4 passes)
```

## Reproducibility Pipeline

```bash
make normalize-corpus    # Convert .txt corpus to JSON
make build-registries    # Build TOML artifact/experiment indexes
make parquet-audit       # Audit parquet simulation snapshots
make verify-offline      # Validate provenance and registry schemas
make repro-refresh       # Run all of the above in sequence
```

## Optional: External Source Fetch

This step requires network access and is separate from the test suite:

```bash
make fetch-external     # Fetch PDFs from sources.toml manifest
make fetch-arxiv        # Batch-download arXiv papers (rate-limited)
make verify-checksums   # Verify SHA-256 of all cached PDFs
make fetch-all          # fetch-external + fetch-arxiv
```

PDF artifacts are cached under `source_materials/pdfs/`.

## Troubleshooting

**"ruff not installed"**: Run `make install` to provision the venv, or check that
`./venv/bin/ruff` exists.

**"No module named 'jax'"**: JAX is optional. Install with `pip install jax jaxlib`
or ignore the 2-3 skipped tests.

**"No module named 'qiskit'"**: Qiskit is optional. The quantum circuit test files
are excluded from collection when qiskit is absent (`tests/conftest.py`).

**JSON serialization error (`np.bool_`)**: Means a numpy boolean reached `json.dump`
without conversion. Use `_NumpyEncoder` from `algebras/cayley_dickson.py`.

**LaTeX compilation fails ("undefined reference")**: Run `bibtex main` between
the two `pdflatex` passes. `make papers` does this automatically.

**XLA GPU pre-allocation (OOM)**: Set `XLA_PYTHON_CLIENT_PREALLOCATE=false`
(already set in the Makefile JAX targets).
