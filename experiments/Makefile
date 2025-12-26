.PHONY: help install test clean run-all visualize docs lint format check

PYTHON := python3
PIP := pip3
PYTEST := pytest
SRC_DIR := src
TEST_DIR := tests
RESULTS_DIR := results
NOTEBOOKS_DIR := notebooks

help:
	@echo "Mathematical Physics Experimental Framework"
	@echo "==========================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install       - Install package and dependencies"
	@echo "  test          - Run test suite"
	@echo "  test-verbose  - Run tests with verbose output"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  run-all       - Run all experiments"
	@echo "  run-cayley    - Run Cayley-Dickson experiments"
	@echo "  run-fractals  - Run fractal analysis"
	@echo "  run-e8        - Run E_8 analysis"
	@echo "  run-lattice   - Run lattice theory analysis"
	@echo "  run-modular   - Run modular forms analysis"
	@echo "  visualize     - Generate all visualizations"
	@echo "  clean         - Clean generated files"
	@echo "  clean-results - Clean results directory"
	@echo "  lint          - Run code quality checks"
	@echo "  format        - Format code"
	@echo "  check         - Run all checks (lint + test)"
	@echo ""

install:
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "Installing package in development mode..."
	$(PIP) install -e .
	@echo "Installation complete!"

test:
	@echo "Running test suite..."
	$(PYTEST) $(TEST_DIR) -q

test-verbose:
	@echo "Running test suite (verbose)..."
	$(PYTEST) $(TEST_DIR) -v

test-coverage:
	@echo "Running test suite with coverage..."
	$(PYTEST) $(TEST_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=term

run-all: run-cayley run-fractals run-e8 run-lattice run-modular visualize
	@echo ""
	@echo "All experiments complete!"
	@echo "Results saved to $(RESULTS_DIR)/"

run-cayley:
	@echo "Running Cayley-Dickson algebra experiments..."
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) $(SRC_DIR)/cayley_dickson.py

run-fractals:
	@echo "Running fractal analysis..."
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) $(SRC_DIR)/fractal_analysis.py

run-e8:
	@echo "Running E_8 Lie algebra analysis..."
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) $(SRC_DIR)/lie_algebras.py

run-lattice:
	@echo "Running lattice theory analysis..."
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) $(SRC_DIR)/lattice_theory.py

run-modular:
	@echo "Running modular forms analysis..."
	@mkdir -p $(RESULTS_DIR)
	$(PYTHON) $(SRC_DIR)/modular_forms.py

visualize:
	@echo "Generating visualizations..."
	@mkdir -p $(RESULTS_DIR)/figures
	$(PYTHON) $(SRC_DIR)/visualization.py

clean:
	@echo "Cleaning generated files..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name 'htmlcov' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '.coverage' -delete
	@echo "Clean complete!"

clean-results:
	@echo "Cleaning results directory..."
	rm -rf $(RESULTS_DIR)/*
	@echo "Results cleaned!"

lint:
	@echo "Running code quality checks..."
	@command -v pylint >/dev/null 2>&1 || { echo "pylint not found, skipping..."; exit 0; }
	pylint $(SRC_DIR) --disable=C0103,C0114,C0115,C0116 || true

format:
	@echo "Formatting code..."
	@command -v black >/dev/null 2>&1 || { echo "black not found, skipping..."; exit 0; }
	black $(SRC_DIR) $(TEST_DIR) || true

check: lint test
	@echo "All checks complete!"

.DEFAULT_GOAL := help