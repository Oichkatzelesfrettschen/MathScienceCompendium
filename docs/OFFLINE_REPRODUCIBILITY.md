# Offline Reproducibility Guide

This repository is organized for deterministic offline checks and regeneration.

## Principles

- No network calls in tests.
- External sources are fetched only by scripts.
- All fetched artifacts require provenance metadata.
- Text corpus normalization is deterministic.
- Artifact and experiment registries are generated from on-disk state.

## Data Contracts

- `source_materials/frameworks/`: raw local text corpus.
- `source_materials/pdfs/`: cached research PDFs (when available).
- `source_materials/pdfs/extracted/`: extracted text from cached PDFs.
- `data/external/sources.toml`: fetch manifest for external sources.
- `data/external/PROVENANCE.json`: generated provenance lock record.
- `data/external/super_force_analysis/`: curated upstream text/code assets.
- `data/external/super_force_analysis/PROVENANCE.json`: provenance for curated Super-Force-Analysis sync lane.
- `data/normalized/corpus/`: normalized JSON records from raw `.txt` files.
- `data/normalized/frameworks/`: ASCII Markdown reading views, heading indexes,
  explicit-reference indexes, formula and table candidate indexes, and source-line
  chunks for retained framework texts.
- `data/registry/framework_document_decomposition.json`: source, chunk, and output
  hashes proving complete framework-document coverage.
- `data/registry/framework_overlap_audit.json`: exact normalized paragraph
  overlap, containment, and source-line occurrences across framework drafts.
- `data/registry/unified_framework_claims.json`: canonical statements, source
  anchors, evidence links, falsification tests, and integration dispositions.
- `data/registry/aligned_research_mineru_run.json`: per-source MinerU status plus
  source and primary-output hashes for the manifest-aligned PDF corpus.
- `data/registry/tesseract_fallback_run.json`: page-selective 400 DPI Tesseract
  outputs routed by the native-text quality audit.
- `docs/framework/UNIFIED_EVIDENCE_FRAMEWORK.md`: human-readable consolidated
  framework governed by the machine-readable claim ledger.
- `data/registry/*.toml`: generated indexes for corpus/artifacts/experiments.
- `data/registry/corpus_dedupe_report.toml`: focused duplicate tracking report for normalized corpus.
- `data/registry/claim_source_crosswalk.toml`: chapter-level claim anchors mapped to external source IDs.
- `data/registry/claim_coverage_report.toml`: machine-readable claim/source coverage metrics from crosswalk policy.
- `data/registry/docs_index.toml`: machine-readable index of `docs/`, `papers/sections/`, and `research/` text artifacts.
- `data/registry/parquet_audit.json`: parquet inventory and optional schema audit.
- `docs/DOCS_INDEX.md`: human-readable content index generated from `docs/`, `papers/sections/`, and `research/`.
- `schemas/registry/*.schema.json`: JSON schemas for TOML registries and selected JSON registry outputs.
- `schemas/external/*.schema.json`: JSON schemas for external provenance records.
- `docs/external_sources/*.md`: source index docs for each external ingestion lane.

## Regeneration Commands

Run `make repro-refresh` for the platform-independent corpus, registry, audit,
and integrity refresh used by CI. The native PDF text-quality audit is a
separate evidence-generation lane because Poppler extraction can differ across
platform builds:

- `make pdf-text-quality-audit`
- `make document-decomposition-index`

Both PDF evidence targets fail fast unless `pdfinfo` and `pdftotext` are
available. Review and commit their regenerated ledgers from the same declared
Poppler toolchain; do not use cross-platform byte equality as a quality test.

The underlying commands are:

- `python3 scripts/fetch_external_sources.py --manifest data/external/sources.toml --extract-text`
- `python3 scripts/sync_super_force_analysis_assets.py`
- `python3 scripts/normalize_txt_to_json.py`
- `python3 scripts/decompose_framework_documents.py`
- `python3 scripts/analyze_framework_overlap.py`
- `python3 scripts/run_mineru_manifest.py`
- `python3 scripts/audit_pdf_text_quality.py`
- `python3 scripts/run_tesseract_fallbacks.py`
- `python3 scripts/index_document_decomposition.py`
- `python3 scripts/corpus_dedupe_report.py`
- `python3 scripts/build_registries.py`
- `python3 scripts/build_docs_index.py`
- `python3 scripts/build_claim_coverage_report.py`
- `python3 scripts/validate_external_provenance_schemas.py`
- `python3 scripts/validate_registry_schemas.py`
- `python3 scripts/parquet_audit.py`
- `python3 scripts/verify_offline_integrity.py`
- `python3 scripts/archive_pdfs_to_documents.py`

## Verification Coverage

`scripts/verify_offline_integrity.py` enforces:

- no leaked absolute local filesystem paths in repo text artifacts;
- no unresolved explicit section stubs in targeted paper chapters;
- corpus registry consistency (`source_relpath` and `normalized_relpath` existence);
- external source manifest target structure;
- external source index coverage (`docs/external_sources/*_SOURCE_INDEX.md`);
- provenance completeness for fetched/synced assets (URL/hash/size/timestamps/files);
- claim-to-source crosswalk validity and coverage-policy thresholds (`claim_source_crosswalk.toml`);
- current policy floor: `min_unique_sources_per_chapter = 2` and per required volume-group prefix `min_claims_per_group = 2`, `min_unique_sources_per_group = 2`;
- claim/source coverage report generation and schema validity (`claim_coverage_report.toml`);
- docs index consistency (`docs_index.toml`) across `docs/`, `papers/sections/`, and `research/`;
- external provenance JSON schema validation (`data/external/PROVENANCE.json` plus lane `*/PROVENANCE.json`);
- schema validation for `data/registry/*.toml` and selected `data/registry/*.json` against `schemas/registry/*.schema.json`;
- optional archive index JSON validity when present.
- no tracked LaTeX build intermediates under `papers/`.
- no shadow Python package under `experiments/src`.

## Notes About PDFs

PDFs are considered first-class offline artifacts and are retained in-repo when available.
If relocation is ever needed, copy to `~/Documents/MathScienceCompendium/pdfs/` before removal.
Use `make archive-pdfs` (or `python3 scripts/archive_pdfs_to_documents.py`) to perform this safely.

## Evidence Retention Classes

| Repository surface | Retention class | Durable contract |
|---|---|---|
| `source_materials/frameworks/` and `source_materials/pdfs/` | raw exact-target evidence | Retain source bytes with provenance and hashes. |
| `data/external/` and `data/registry/` manifests | hash manifest | Retain and validate against live source and result bytes. |
| `scripts/`, `schemas/registry/`, and `tools/document_ocr/` | canonical generator or schema | Retain the executable regeneration and validation path. |
| `docs/framework/`, `papers/sections/`, and `papers/main.pdf` | synthesized truth surface | Retain the reviewed human-facing result and its source. |
| `data/normalized/corpus/`, `data/normalized/frameworks/`, extracted text, and paper figures | derived regenerable evidence view | Retain when it provides bounded offline review, with source hashes and generators. |
| `build/document_ocr/`, Python caches, and LaTeX intermediates | transient noise | Keep out of Git; regenerate from the canonical commands. |

The offline verifier rejects tracked LaTeX intermediates under `papers/`.
The source PDF, TeX source, generated tables and figures, bibliography source,
and final PDF remain durable. Files such as `.aux`, `.bbl`, `.blg`, `.toc`,
`.lof`, `.lot`, `.run.xml`, and `-blx.bib` remain build products governed by
`.gitignore`.

## CI Artifact Publication

The `reproducibility` GitHub Actions job uploads machine-readable review artifacts after `make repro-refresh`:

- `data/registry/claim_coverage_report.toml`
- `data/registry/docs_index.toml`
- `data/registry/corpus_dedupe_report.toml`
- `docs/DOCS_INDEX.md`

## Known Optional Dependencies

- `pyarrow` for parquet schema introspection.

`pdftotext` and `pdfinfo` are required by `make pdf-text-quality-audit` and
`make document-decomposition-index`, but not by `make repro-refresh` or
`make verify-offline`. The parquet audit still runs without `pyarrow`, but its
schema metadata is reduced.
