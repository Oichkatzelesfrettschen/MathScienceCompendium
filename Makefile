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
SOURCE_DATE_EPOCH ?= 0
export SOURCE_DATE_EPOCH

# Project Directories
SRC_DIR = src/mathphysics
TESTS_DIR = tests
BENCH_DIR = benchmarks
RESULTS_DIR = results
FIGURES_DIR = figures

.PHONY: all clean help install test lint check-types benchmark run-highres run-unified run-jordan run-clifford docs papers cleanbuild lint-latex figures paper-evidence-artifacts fetch-external sync-super-force-analysis normalize-corpus framework-decomposition framework-overlap corpus-dedupe build-registries docs-index claim-coverage critique-evidence hypothesis-registry validate-clean-reproduction validate-hypothesis-promotions validate-external-provenance validate-registry-schemas parquet-audit evidence-audits beta-plane-sweep beta-plane-refinement beta-plane-controls lbm-evidence-figures pdf-text-quality-audit document-ocr-mineru document-ocr-tesseract document-ocr-generate document-decomposition-index verify-offline reproducibility-indexes repro-refresh check-pdf-deps archive-pdfs notebooks fetch-arxiv resolve-dois fetch-all verify-checksums check-deps

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
	@$(MAKE) paper-evidence-artifacts

paper-evidence-artifacts:
	@echo "[VIZ] Generating registry-driven paper evidence artifacts..."
	python3 scripts/generate_paper_evidence_artifacts.py

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
# Development Quality Gates
# ==============================================================================

install:
	@echo "[SETUP] Creating virtual environment and installing package..."
	python3 -m venv venv
	./venv/bin/python -m pip install --upgrade pip
	./venv/bin/pip install -e ".[dev,lint]"

lint:
	@echo "[LINT] Running ruff checks..."
	@if [ -x "$(RUFF)" ]; then \
	  $(RUFF) check src tests benchmarks experiments scripts; \
	elif command -v ruff > /dev/null; then \
	  ruff check src tests benchmarks experiments scripts; \
	else \
	  echo "ruff is required; run make install" >&2; \
	  exit 1; \
	fi

check-types:
	@echo "[TYPE] Running mypy..."
	@if [ -x "$(MYPY)" ]; then \
	  $(MYPY) src/mathphysics --ignore-missing-imports --no-error-summary; \
	elif command -v mypy > /dev/null; then \
	  mypy src/mathphysics --ignore-missing-imports --no-error-summary; \
	else \
	  echo "mypy is required; run make install" >&2; \
	  exit 1; \
	fi

test:
	@echo "[TEST] Running pytest..."
	@if [ -x "$(PYTEST)" ]; then \
	  PYTHONHASHSEED=0 PYTHONPATH=src $(PYTEST) tests -q; \
	elif command -v pytest > /dev/null; then \
	  PYTHONHASHSEED=0 PYTHONPATH=src pytest tests -q; \
	else \
	  echo "pytest is required; run make install" >&2; \
	  exit 1; \
	fi

notebooks:
	@echo "[NOTEBOOKS] Executing all Jupyter notebooks..."
	@if [ -x "./venv/bin/jupyter" ]; then \
	  for nb in experiments/notebooks/0*.ipynb; do \
	    echo "[NOTEBOOK] $$nb"; \
	    ./venv/bin/jupyter nbconvert --to notebook --execute --inplace "$$nb"; \
	  done; \
	else \
	  echo "jupyter and nbconvert are required; run make install" >&2; \
	  exit 1; \
	fi

lint-latex: critique-evidence paper-evidence-artifacts
	@echo "[LATEX] Checking publication sources..."
	@! rg -n "(Chapter stub|To be developed)" papers/main.tex papers/sections/review_*.tex papers/generated/*.tex || (echo "Found unresolved LaTeX stubs." && exit 1)
	@! rg --pcre2 -n "[^\\x00-\\x7F]" papers/main.tex papers/sections/review_*.tex papers/generated/*.tex || (echo "Found non-ASCII text in publication sources." && exit 1)

# ==============================================================================
# Documentation
# ==============================================================================

docs:
	@echo "[DOCS] Generating Sphinx documentation..."
	mkdir -p docs/sphinx
	sphinx-apidoc -o docs/sphinx/source $(SRC_DIR)
	cd docs/sphinx && $(SPHINX) -b html source build/html

# ==============================================================================
# Offline Reproducibility Pipeline
# ==============================================================================

fetch-external:
	@echo "[DATA] Fetching external sources from manifest..."
	python3 scripts/fetch_external_sources.py --manifest data/external/sources.toml --extract-text || true

fetch-arxiv:
	@echo "[DATA] Batch downloading arXiv papers (rate-limited)..."
	python3 scripts/fetch_arxiv.py

resolve-dois:
	@echo "[DATA] Resolving DOIs to download URLs..."
	python3 scripts/resolve_dois.py

fetch-all: fetch-external fetch-arxiv
	@echo "[DATA] All sources fetched."

verify-checksums:
	@echo "[VERIFY] Verifying SHA-256 checksums of cached PDFs..."
	python3 scripts/verify_checksums.py

check-deps:
	@echo "[CHECK] Verifying required external tools..."
	@command -v pdftotext > /dev/null && echo "  pdftotext: OK" || echo "  pdftotext: MISSING (install poppler-utils)"
	@command -v pdflatex > /dev/null && echo "  pdflatex:  OK" || echo "  pdflatex:  MISSING (install texlive)"
	@command -v bibtex   > /dev/null && echo "  bibtex:    OK" || echo "  bibtex:    MISSING (install texlive)"
	@command -v rg       > /dev/null && echo "  ripgrep:   OK" || echo "  ripgrep:   MISSING (install ripgrep)"
	@python3 --version 2>&1 | sed 's/^/  python3:  /'

sync-super-force-analysis:
	@echo "[DATA] Syncing curated assets from Super-Force-Analysis..."
	python3 scripts/sync_super_force_analysis_assets.py

normalize-corpus:
	@echo "[DATA] Normalizing text corpus to JSON..."
	python3 scripts/normalize_txt_to_json.py

framework-decomposition:
	@echo "[DATA] Decomposing retained framework documents into traceable Markdown..."
	python3 scripts/decompose_framework_documents.py

framework-overlap:
	@echo "[DATA] Auditing exact normalized overlap across framework documents..."
	python3 scripts/analyze_framework_overlap.py

corpus-dedupe:
	@echo "[DATA] Generating corpus dedupe report..."
	python3 scripts/corpus_dedupe_report.py

build-registries:
	@echo "[DATA] Building artifact and experiment registries..."
	python3 scripts/build_registries.py

docs-index:
	@echo "[DOCS] Building documentation index registries..."
	python3 scripts/build_docs_index.py

claim-coverage:
	@echo "[DATA] Building claim coverage report..."
	python3 scripts/build_claim_coverage_report.py

critique-evidence:
	@echo "[DATA] Generating critique table from the evidence ledger..."
	python3 scripts/generate_critique_evidence_table.py

hypothesis-registry:
	@echo "[DOCS] Rendering the canonical hypothesis registry..."
	python3 scripts/build_hypothesis_registry_report.py

validate-clean-reproduction:
	@test -n "$(EVIDENCE_SOURCE_COMMIT)" || (echo "EVIDENCE_SOURCE_COMMIT is required" && exit 2)
	@echo "[VERIFY] Comparing clean-container outputs, source identity, and primary evidence..."
	python3 scripts/verify_clean_reproduction.py \
		--image reproduction-evidence-reproduction:latest \
		--source-commit "$(EVIDENCE_SOURCE_COMMIT)"

validate-hypothesis-promotions:
	@echo "[VERIFY] Enforcing independent reproduction before paper promotion..."
	python3 scripts/validate_hypothesis_promotions.py

validate-external-provenance:
	@echo "[VERIFY] Validating external provenance JSON files against schemas..."
	python3 scripts/validate_external_provenance_schemas.py

validate-registry-schemas:
	@echo "[VERIFY] Validating registry TOML/JSON files against schemas..."
	python3 scripts/validate_registry_schemas.py

parquet-audit:
	@echo "[DATA] Auditing parquet artifacts..."
	python3 scripts/parquet_audit.py

evidence-audits:
	@echo "[DATA] Regenerating computational evidence audits..."
	PYTHONPATH=src python3 scripts/generate_core_validation_results.py
	PYTHONPATH=src python3 scripts/audit_triad_selectors.py
	PYTHONPATH=src python3 experiments/quantum_lbm_stable_demo.py
	PYTHONPATH=src python3 scripts/analyze_retained_lbm.py
	PYTHONPATH=src python3 scripts/audit_lbm_root_order.py
	python3 scripts/parquet_audit.py

beta-plane-sweep:
	@echo "[EXPERIMENT] Running the preregistered decaying beta-plane sweep..."
	PYTHONPATH=src JAX_PLATFORMS=cpu python3 scripts/run_beta_plane_sweep.py --profile production

beta-plane-refinement:
	@echo "[EXPERIMENT] Running the amended shared-initial-condition refinement matrix..."
	PYTHONPATH=src JAX_PLATFORMS=cpu python3 scripts/run_beta_plane_sweep.py --profile refinement

beta-plane-controls:
	@echo "[EXPERIMENT] Running the preregistered beta-plane control package..."
	PYTHONPATH=src JAX_PLATFORMS=cpu python3 scripts/run_beta_plane_controls.py

lbm-evidence-figures:
	@echo "[FIGURES] Rendering LBM evidence with the local Matplotlib and font stack..."
	PYTHONPATH=src python3 scripts/analyze_retained_lbm.py --figure-root figures

pdf-text-quality-audit: check-pdf-deps
	@echo "[DATA] Auditing native PDF text with the local Poppler build..."
	python3 scripts/audit_pdf_text_quality.py

document-ocr-mineru:
	@echo "[OCR] Building the pinned MinerU CUDA image..."
	docker compose -f tools/document_ocr/compose.yaml build mineru
	@echo "[OCR] Decomposing manifest PDFs sequentially in automatic mode..."
	python3 scripts/run_mineru_manifest.py
	@echo "[OCR] Running forced OCR on the sparse comparison document..."
	docker compose -f tools/document_ocr/compose.yaml run --rm mineru 'mineru -p /workspace/source_materials/pdfs/Comment_on_the_Pais_Superforce_Theory.pdf -o /workspace/build/document_ocr/mineru -b hybrid-engine --effort high -m ocr --formula true --table true --image-analysis true'

document-ocr-tesseract:
	@echo "[OCR] Running the independent Tesseract comparison..."
	python3 scripts/run_tesseract_pdf_ocr.py source_materials/pdfs/Comment_on_the_Pais_Superforce_Theory.pdf --dpi 400 --page-segmentation-mode 1
	@echo "[OCR] Running Tesseract only on pages routed by the text-quality audit..."
	python3 scripts/run_tesseract_fallbacks.py

document-ocr-generate: document-ocr-mineru document-ocr-tesseract
	@echo "[OCR] MinerU and Tesseract outputs generated."

document-decomposition-index: check-pdf-deps
	@echo "[DATA] Indexing completed MinerU document decompositions..."
	python3 scripts/index_document_decomposition.py
	python3 scripts/compare_pdf_ocr_outputs.py

verify-offline:
	@echo "[VERIFY] Running offline integrity checks..."
	python3 scripts/validate_external_provenance_schemas.py
	python3 scripts/validate_registry_schemas.py
	python3 scripts/validate_hypothesis_promotions.py
	python3 scripts/verify_offline_integrity.py

check-pdf-deps:
	@echo "[CHECK] Verifying PDF evidence system dependencies..."
	@command -v pdfinfo > /dev/null || { echo "pdfinfo is required; install poppler-utils" >&2; exit 1; }
	@command -v pdftotext > /dev/null || { echo "pdftotext is required; install poppler-utils" >&2; exit 1; }

repro-refresh:
	@$(MAKE) normalize-corpus
	@$(MAKE) framework-decomposition
	@$(MAKE) framework-overlap
	@$(MAKE) corpus-dedupe
	@$(MAKE) evidence-audits
	@$(MAKE) critique-evidence
	@$(MAKE) hypothesis-registry
	@$(MAKE) build-registries
	@$(MAKE) docs-index
	@$(MAKE) claim-coverage
	@$(MAKE) verify-offline
	@echo "[SUCCESS] Offline reproducibility indexes refreshed."

reproducibility-indexes:
	@$(MAKE) normalize-corpus
	@$(MAKE) framework-decomposition
	@$(MAKE) framework-overlap
	@$(MAKE) corpus-dedupe
	@$(MAKE) critique-evidence
	@$(MAKE) hypothesis-registry
	@$(MAKE) build-registries
	@$(MAKE) docs-index
	@$(MAKE) claim-coverage
	@$(MAKE) verify-offline
	@echo "[SUCCESS] Deterministic reproducibility indexes refreshed."

archive-pdfs:
	@echo "[DATA] Archiving repository PDFs to ~/Documents/MathScienceCompendium/pdfs..."
	python3 scripts/archive_pdfs_to_documents.py

# ==============================================================================
# Full Pipeline
# ==============================================================================

cleanbuild: clean-all install lint check-types lint-latex run-highres run-unified figures test benchmark papers
	@echo "[SUCCESS] Clean build completed with zero warnings/errors."

# ==============================================================================
# LaTeX Paper Build
# ==============================================================================

papers: lint-latex
	@echo "[BUILD] Building critical review (halt-on-error)..."
	cd papers && latexmk -pdf -gg -interaction=nonstopmode -halt-on-error main.tex
	@! rg -n "(LaTeX Warning|Package .* Warning|pdfTeX warning|Overfull \\\\hbox|Overfull \\\\vbox|Underfull \\\\hbox|Underfull \\\\vbox)" papers/main.log || (echo "LaTeX emitted publication-blocking warnings." && exit 1)
	@! rg -n "Warning--" papers/main.blg || (echo "BibTeX emitted publication-blocking warnings." && exit 1)
	@$(MAKE) build-registries
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
	@echo "[CLEAN-ALL] Archiving PDFs before cleanup..."
	python3 scripts/archive_pdfs_to_documents.py
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
	@echo "  make lint         - Run ruff linter"
	@echo "  make check-types  - Run mypy static type checking"
	@echo "  make test         - Run full test suite"
	@echo "  make cleanbuild   - Full clean, install, QA, and PDF build"
	@echo ""
	@echo "REPRODUCIBILITY:"
	@echo "  make fetch-external   - Fetch/cache external sources and provenance"
	@echo "  make sync-super-force-analysis - Sync curated Super-Force-Analysis text/code assets"
	@echo "  make normalize-corpus - Convert .txt corpus files to JSON records"
	@echo "  make framework-decomposition - Chunk framework sources into traceable Markdown"
	@echo "  make framework-overlap - Audit exact normalized overlap across framework drafts"
	@echo "  make corpus-dedupe    - Emit focused dedupe report for normalized corpus"
	@echo "  make build-registries - Build TOML indexes for artifacts and experiments"
	@echo "  make docs-index       - Build docs registry and docs index markdown"
	@echo "  make claim-coverage   - Build claim/source coverage report from crosswalk policy"
	@echo "  make critique-evidence - Generate the paper critique table from its evidence ledger"
	@echo "  make validate-clean-reproduction - Verify clean results against source and primary evidence"
	@echo "  make validate-external-provenance - Validate data/external provenance JSON against schemas"
	@echo "  make validate-registry-schemas - Validate data/registry/*.toml and selected *.json against schemas"
	@echo "  make parquet-audit    - Audit parquet files and emit JSON summary"
	@echo "  make evidence-audits  - Regenerate core, LBM, root-order, and parquet audits"
	@echo "  make lbm-evidence-figures - Regenerate local-toolchain LBM publication figures"
	@echo "  make pdf-text-quality-audit - Regenerate the local Poppler text-quality audit"
	@echo "  make document-ocr-generate - Generate pinned MinerU and Tesseract OCR outputs"
	@echo "  make document-decomposition-index - Index completed MinerU and Tesseract outputs"
	@echo "  make verify-offline   - Run offline integrity checks"
	@echo "  make reproducibility-indexes - Refresh deterministic indexes without rerunning evidence"
	@echo "  make repro-refresh    - Run normalize + registries + audit + verification"
	@echo "  make archive-pdfs     - Copy all repo PDFs to ~/Documents before cleanup"
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
