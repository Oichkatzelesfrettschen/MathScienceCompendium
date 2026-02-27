# Quick Start (5 minutes)

## 1. Clone and Install

```bash
git clone <repo-url> MathScienceCompendium
cd MathScienceCompendium
make install          # creates venv, installs package + dev dependencies
```

## 2. Run Tests

```bash
make test             # 500+ tests, target >= 60% coverage
```

Expect a few SKIPPED lines for JAX/qiskit (optional dependencies). All others should PASS.

## 3. Explore the Algebra

```python
from mathphysics.algebras.roots import RootSystem, ExceptionalLieAlgebras

# E8 has 240 roots
e8 = RootSystem("E8")
print(len(e8.positive_roots))  # 120 positive roots

# Enumerate all exceptional Lie algebras
for name, algebra in ExceptionalLieAlgebras.get_all().items():
    print(name, algebra.dimension)
```

## 4. Run a Simulation

```bash
PYTHONPATH=src ./venv/bin/python -m mathphysics --run --output /tmp/results
```

This runs the full validation suite (Cayley-Dickson, lattice, fractal) and writes
JSON/parquet results to `/tmp/results`.

## 5. Generate Figures

```bash
make figures          # writes PNG and interactive HTML to figures/
```

Open `figures/e8_exceptional_interactive.html` in a browser for an interactive
3D view of E8 root systems.

## 6. Build the LaTeX Compendium

```bash
make papers           # requires pdflatex + bibtex
# Output: papers/main.pdf
```

---

## Key Entry Points

| Task | Command |
|------|---------|
| Install | `make install` |
| Test | `make test` |
| Lint | `make lint` |
| Type check | `make check-types` |
| Run algebra analysis | `PYTHONPATH=src python -m mathphysics --module e8` |
| Run all experiments | `make run-highres` |
| Build PDF | `make papers` |
| Refresh reproducibility indexes | `make repro-refresh` |
| Full clean build | `make cleanbuild` |

## Contributor Workflow

```bash
git checkout -b feature/my-change
# make changes, run make lint && make test
git add <files>
git commit -m "feat: add my change"
git push origin feature/my-change
# open PR targeting main
```

See `docs/ARCHITECTURE.md` for a full module map and data flow description.
