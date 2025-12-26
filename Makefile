# ==============================================================================
# Mathematical Physics Compendium - Unified Build System
# ==============================================================================

# Variables
PYTHON = XLA_PYTHON_CLIENT_PREALLOCATE=false ./venv/bin/python3
PIP = ./venv/bin/pip
RUFF = ./venv/bin/ruff
MYPY = ./venv/bin/mypy
PYTEST = ./venv/bin/pytest
SPHINX = sphinx-build

# Project Directories
SRC_DIR = src/mathphysics
TESTS_DIR = tests
BENCH_DIR = benchmarks
RESULTS_DIR = results
FIGURES_DIR = figures

.PHONY: all clean help install test lint check-types benchmark run-highres run-unified run-jordan run-clifford docs papers cleanbuild lint-latex figures

# Default target
all: lint check-types test benchmark figures papers

# ==============================================================================
# Benchmarking and Execution
# ==============================================================================

benchmark:
	@echo "[BENCHMARK] Running LBM performance comparison (NumPy vs JAX)..."
	PYTHONPATH=src $(PYTHON) $(BENCH_DIR)/benchmark_lbm.py

figures:
	@echo "[VIZ] Generating production-grade scientific figures..."
	PYTHONPATH=src $(PYTHON) src/mathphysics/generate_scientific_figures.py
	@echo "[VIZ] Generating enhanced interactive explorer..."
	PYTHONPATH=src $(PYTHON) src/mathphysics/generate_interactive_explorer.py
	@echo "[VIZ] Generating geometric and topological anchor diagrams..."
	PYTHONPATH=src $(PYTHON) src/mathphysics/generate_anchor_diagrams.py

run-highres:
	@echo "[EXPERIMENT] Running high-resolution JAX-accelerated LBM..."
	PYTHONPATH=src $(PYTHON) experiments/run_exhaustive_experiments.py

run-unified:
	@echo "[EXPERIMENT] Running unified cross-domain simulation..."
	PYTHONPATH=src $(PYTHON) -c "from mathphysics.unified_physics import UnifiedSimulation; sim = UnifiedSimulation(); sim.run_experiment(100)"

run-jordan:
	@echo "[EXPERIMENT] Running Jordan Algebra trace analysis..."
	PYTHONPATH=src $(PYTHON) -c "from mathphysics.unified_physics import run_e11_analysis; run_e11_analysis()"

run-clifford:
	@echo "[EXPERIMENT] Running Clifford Algebra rotation demo..."
	PYTHONPATH=src $(PYTHON) -c "from mathphysics.algebras.clifford import Multivector; import numpy as np; mv = Multivector(np.random.rand(8), (3,0,0)); print(mv.geometric_product(mv).coeffs)"

viz-interactive: figures
	@echo "[VIZ] Launching interactive 3D visualizations..."
	@# Cross-platform open command
	@if command -v xdg-open > /dev/null; then xdg-open $(FIGURES_DIR)/e8_exceptional_interactive.html; \
	elif command -v open > /dev/null; then open $(FIGURES_DIR)/e8_exceptional_interactive.html; \
	else echo "Please open $(FIGURES_DIR)/e8_exceptional_interactive.html in your browser"; fi

viz-explorer:
	@echo "[VIZ] Launching Multi-Algebra Root Explorer..."
	@PYTHONPATH=src $(PYTHON) src/mathphysics/algebras_explorer.py
	@if command -v xdg-open > /dev/null; then xdg-open $(FIGURES_DIR)/lie_algebras_explorer.html; \
	elif command -v open > /dev/null; then open $(FIGURES_DIR)/lie_algebras_explorer.html; \
	else echo "Please open $(FIGURES_DIR)/lie_algebras_explorer.html in your browser"; fi

# ==============================================================================
# Documentation
# ==============================================================================

docs:
	@echo "[DOCS] Generating Sphinx documentation..."
	mkdir -p docs/sphinx
	sphinx-apidoc -o docs/sphinx/source $(SRC_DIR)
	cd docs/sphinx && $(SPHINX) -b html source build/html

# ==============================================================================
# Full Pipeline
# ==============================================================================

cleanbuild: clean-all install lint check-types lint-latex run-highres run-unified figures test benchmark papers
	@echo "[SUCCESS] Clean build completed with zero warnings/errors."

# ==============================================================================
# LaTeX Paper Build
# ==============================================================================

papers: figures
	@echo "[BUILD] Building LaTeX compendium (halt-on-error)..."
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd papers && bibtex main
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd papers && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	@echo "PDF generated: papers/main.pdf"

# ==============================================================================
# Status and Utilities
# ==============================================================================

status:
	@echo "==================================================================="
	@echo "Mathematical Physics Compendium - Framework Status"
	@echo "==================================================================="
	@echo "JAX Acceleration: $$( $(PYTHON) -c 'import jax; print(jax.devices())' 2>/dev/null || echo 'Not Configured' )"
	@echo "Source Files:    $$(find $(SRC_DIR) -name '*.py' | wc -l)"
	@echo "Test Files:      $$(find $(TESTS_DIR) -name '*.py' | wc -l)"
	@echo "Results:         $$(ls -1 $(RESULTS_DIR)/*.parquet 2>/dev/null | wc -l) parquet snapshots"
	@echo "Figures:         $$(ls -1 $(FIGURES_DIR)/*.png 2>/dev/null | wc -l) generated plots"
	@echo "==================================================================="

# ==============================================================================
# Cleaning
# ==============================================================================

clean:
	@echo "[CLEAN] Removing build artifacts..."
	cd papers && rm -f *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.bcf *.run.xml *.fls *.fdb_latexmk *.synctex.gz
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .coverage docs/sphinx/build

clean-all: clean
	@echo "[CLEAN-ALL] Removing generated data and PDFs..."
	rm -f papers/main.pdf
	rm -rf $(RESULTS_DIR)/*
	rm -rf $(FIGURES_DIR)/*


# ==============================================================================
# Help
# ==============================================================================

help:
	@echo "Unified Mathematical Physics Compendium Build System"
	@echo ""
	@echo "DEVELOPMENT:"
	@echo "  make install      - Provision virtual environment and dependencies"
	@echo "  make lint         - Run ruff linter (with auto-fix)"
	@echo "  make check-types  - Run mypy static type checking"
	@echo "  make test         - Run full test suite with coverage"
	@echo "  make cleanbuild   - Full clean, install, QA, and PDF build"
	@echo ""
	@echo "EXECUTION:"
	@echo "  make benchmark    - Compare NumPy vs JAX performance"
	@echo "  make run-highres  - Execute high-resolution production simulation"
	@echo "  make papers       - Build LaTeX documentation"
	@echo ""
	@echo "UTILITIES:"
	@echo "  make status       - Display framework health and telemetry"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make clean-all    - Deep clean (artifacts + data + figures)"
