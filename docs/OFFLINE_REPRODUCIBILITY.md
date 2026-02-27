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

- `python3 scripts/fetch_external_sources.py --manifest data/external/sources.toml --extract-text`
- `python3 scripts/sync_super_force_analysis_assets.py`
- `python3 scripts/normalize_txt_to_json.py`
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

## Notes About PDFs

PDFs are considered first-class offline artifacts and are retained in-repo when available.
If relocation is ever needed, copy to `~/Documents/MathScienceCompendium/pdfs/` before removal.
Use `make archive-pdfs` (or `python3 scripts/archive_pdfs_to_documents.py`) to perform this safely.

## CI Artifact Publication

The `reproducibility` GitHub Actions job uploads machine-readable review artifacts after `make repro-refresh`:

- `data/registry/claim_coverage_report.toml`
- `data/registry/docs_index.toml`
- `data/registry/corpus_dedupe_report.toml`
- `docs/DOCS_INDEX.md`

## Known Optional Dependencies

- `pdftotext` for PDF text extraction.
- `pyarrow` for parquet schema introspection.

The pipeline still runs without these dependencies, but metadata detail is reduced.
