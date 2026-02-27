# Architecture

## Overview

MathScienceCompendium is a 4-volume LaTeX mathematical physics compendium
backed by a Python computational framework. It synthesizes and validates
unified field theory frameworks, with a focus on exceptional Lie algebras
(E6, E7, E8, F4), Kac-Moody extensions, quantum encoding schemes, and
turbulence simulation via lattice Boltzmann methods.

## Directory Structure

```
MathScienceCompendium/
  src/mathphysics/       Python package (38 modules)
    algebras/            Algebraic structures (see below)
    main.py              CLI entry point (argparse)
    config.py            Shared SimulationConfig dataclass
    optional_deps.py     Optional dependency detection (JAX, qiskit, gudhi)
  papers/                LaTeX compendium
    main.tex             Top-level document
    sections/            Per-chapter .tex files (4 volumes, 7 chapters + appendices)
    references.bib       BibTeX bibliography (60+ entries)
  tests/                 Pytest test suite (500+ tests, 60%+ coverage)
    unit/                Unit tests per module
    conftest.py          autouse fixtures: seed_random, collect_ignore for qiskit
  experiments/           Standalone experiment scripts and Jupyter notebooks
    notebooks/           6 demonstration notebooks (01-06)
  data/                  External source manifests and provenance records
    external/            sources.toml, PROVENANCE.json
    registry/            TOML indexes: artifacts, experiments, corpus
  docs/                  Documentation and indexes
    reports/             Archived analysis reports
    ARCHITECTURE.md      This file
    DOCS_INDEX.md        Registry of all documentation
    OFFLINE_REPRODUCIBILITY.md  Offline fetch / checksum workflow
  schemas/               JSON schemas for registry and provenance validation
  scripts/               Data pipeline scripts (fetch, normalize, validate)
  benchmarks/            Performance benchmarks (NumPy vs JAX LBM)
  figures/               Generated plots and interactive HTML explorers
  results/               Parquet simulation snapshots
  research/              Kac-Moody analysis, fact checks, primary sources
```

## Module Map: src/mathphysics/

### Core Infrastructure

| Module | Purpose |
|--------|---------|
| `config.py` | `SimulationConfig` dataclass; shared parameters |
| `optional_deps.py` | `HAS_JAX`, `HAS_QISKIT`, `HAS_GUDHI`; `safe_import()` |
| `data_handler.py` | Parquet I/O for simulation snapshots |
| `main.py` | CLI: `--run`, `--module`, `--output` |

### Algebraic Structures (`algebras/`)

| Module | Purpose |
|--------|---------|
| `cayley_dickson.py` | Cayley-Dickson construction: R->C->H->O->S->P |
| `clifford.py` | Clifford algebras Cl(p,q,r), geometric product |
| `jordan.py` | Jordan algebras, Albert algebra (3x3 octonion matrices) |
| `roots.py` | E6/E7/E8/F4 root systems, Cartan matrices, Weyl groups |
| `invariant_theory.py` | Hilbert series, Molien series, E8 invariant verification |
| `loop_algebras.py` | Affine Lie algebras, Kac-Moody extensions (requires JAX) |
| `projective_geometry.py` | PG(n,q) projective spaces, Fano plane, GF(2) vectors |
| `liesym_bridge.py` | Optional interface to the `lie` sympy extension |
| `lmfdb_bridge.py` | Optional interface to LMFDB L-functions database |

### Physics and Simulation

| Module | Purpose |
|--------|---------|
| `lattice_theory.py` | E8/Leech lattices, sphere packing, kissing numbers |
| `modular_forms.py` | Modular forms, j-invariant, Monstrous Moonshine, elliptic curves |
| `fractal_analysis.py` | Box-counting, IFS fractals, multifractal analysis |
| `topology_bridge.py` | Persistent homology (via gudhi or fallback), Betti numbers |
| `genesis_harmonics.py` | ZPE-modulated harmonic layers, material response functions |
| `aqgm_framework.py` | Algebraic quantum gravity model, spectral triples |
| `unified_physics.py` | Cross-domain UnifiedSimulation, E11 Jordan trace analysis |
| `accelerated_lbm.py` | Lattice Boltzmann Method, JAX-accelerated (D2Q9) |
| `quantum_lattice_boltzmann.py` | Quantum-classical LBM hybrid |
| `inverse_design.py` | Inverse design optimization stubs |

### Quantum Circuits (require qiskit)

| Module | Purpose |
|--------|---------|
| `quantum_encoding.py` | 5 encoding schemes: index, amplitude, basis, hybrid, sparse |
| `quantum_e7_circuits.py` | E7 root oracle, Grover operator, state preparation |
| `quantum_e8_circuits.py` | E8 root oracle, Weyl reflection circuits |
| `quantum_simulation.py` | Unified quantum simulation runner |
| `jax_quantum.py` | JAX quantum gate primitives (H, X, CNOT) |

### Visualization

| Module | Purpose |
|--------|---------|
| `viz.py` | `PhysicsVisualizer`: root system plots, LBM vorticity |
| `generate_scientific_figures.py` | Production PNG figures for the LaTeX compendium |
| `generate_interactive_explorer.py` | Plotly interactive E8 HTML explorer |
| `generate_anchor_diagrams.py` | Geometric anchor diagrams |
| `algebras_explorer.py` | Multi-algebra root explorer |
| `interactive_explorer_template.py` | Jinja2 template string for the HTML explorer |
| `algebra.py` | Legacy algebra utilities |

## Data Flow

```
CLI (main.py)
  |
  +--> run_experiments(output_dir)
  |      |
  |      +--> CayleyDicksonValidator  --> results/*.json
  |      +--> LatticeAnalyzer        --> results/*.parquet
  |      +--> FractalAnalyzer        --> results/*.parquet
  |
  +--> --module e8  --> ExceptionalLieAlgebras.get_all()
  +--> --module lattice --> LatticeAnalyzer
  +--> --module modular --> ModularForms
  +--> --module fractal --> FractalAnalyzer
  +--> --module algebra --> run_comprehensive_validation

Offline Pipeline (make repro-refresh):
  scripts/normalize_txt_to_json.py   --> data/corpus/*.json
  scripts/build_registries.py        --> data/registry/*.toml
  scripts/build_docs_index.py        --> docs/DOCS_INDEX.md
  scripts/verify_offline_integrity.py --> console summary
```

## Dependency Graph (optional)

```
Required:
  numpy, scipy, matplotlib, sympy, pandas, pyarrow, plotly

Optional (graceful fallback):
  jax, jaxlib     --> accelerated LBM, loop algebras, unified_physics
  qiskit          --> quantum_encoding, quantum_e7/e8_circuits
  gudhi           --> topology_bridge persistent homology
  requests        --> fetch_external_sources, lmfdb_bridge
```

## 4-Volume LaTeX Structure

| Volume | Chapters | Focus |
|--------|----------|-------|
| I | 1-3 | Algebraic Foundations (Cayley-Dickson, Clifford, Lie algebras) |
| II | 4-7 | Physical Applications (E7, E8, String Theory, Quantum Gravity) |
| III | 8-10 | Synthesis and Emergence (unified framework) |
| IV | 11-12 | Experimental Validation and Future Directions |

Appendix A: Computational Methods (algorithm catalog, pseudocode, complexity)
Appendix B: Data Provenance (source PDF table, results inventory, reproducibility recipes)

## Common Pitfalls

1. **JAX not installed**: `HAS_JAX=False` disables accelerated LBM and loop algebras.
   Tests using JAX are automatically skipped via `pytest.importorskip("jax")`.

2. **Qiskit not installed**: Entire quantum circuit modules import-fail at collection time.
   Fixed by `collect_ignore` in `tests/conftest.py`.

3. **NumPy bool in JSON**: `json.dump` rejects `np.True_`/`np.False_`. Use
   `_NumpyEncoder` from `algebras/cayley_dickson.py` or convert before dumping.

4. **PYTHONHASHSEED**: Tests must set `PYTHONHASHSEED=0` for deterministic ordering.
   Already configured in `Makefile` and `.github/workflows/ci.yml`.

5. **XLA pre-allocation**: JAX pre-allocates GPU memory by default. Set
   `XLA_PYTHON_CLIENT_PREALLOCATE=false` (already in `Makefile`).
