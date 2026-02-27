# Repository Harmonization Plan

## Scope

This plan defines a top-down, offline-first structure for:
- text-heavy research corpus,
- external PDF artifacts,
- experiment outputs (including parquet),
- embedded explorers and generated artifacts,
- deterministic rebuild and verification.

The plan assumes no network in tests and reproducible regeneration from scripts.

## Rescope Update (2026-02-12)

Current focus is now explicitly split into two operational lanes:
- Lane A: core corpus/data reproducibility (`normalize -> dedupe -> registries -> parquet audit -> verify`).
- Lane B: external-source ingestion with provenance (`fetch_external_sources` + curated upstream syncs).

Completed outcomes in this rescope:
- corpus dedupe report is clean (`data/registry/corpus_dedupe_report.toml`).
- manifest URL coverage is complete (no `missing_url` entries in `data/external/sources.toml`).
- external PDF fetch lane is fully green (10/10 downloaded, extracted, and provenance-locked).
- curated `Super-Force-Analysis` context assets are synced by commit-pinned source URLs into:
  - `data/external/super_force_analysis/`
  - `data/external/super_force_analysis/PROVENANCE.json`

Next-step queue (prioritized):
1. Continue curated claim-anchor expansion:
- add additional chapter anchors before raising `min_claims_per_chapter`.
2. Add registry changelog snapshots:
- emit timestamped reproducibility snapshots for cross-PR drift review.

Completed in this pass:
1. Added source-index coverage verifier:
- every external dataset lane is now required to have `docs/external_sources/*_SOURCE_INDEX.md`.
2. Added provenance completeness verifier:
- downloaded/synced assets are checked for URL/hash/size/timestamp and file existence.
3. Added claims-linkage layer:
- machine-readable chapter claim anchors now live in `data/registry/claim_source_crosswalk.toml`.
4. Added docs indexing lane:
- generated `data/registry/docs_index.toml` plus `docs/DOCS_INDEX.md`.
5. Added CI reproducibility guard:
- `.github/workflows/ci.yml` now runs `make repro-refresh` and fails on uncommitted index drift in reproducibility artifacts.
6. Expanded docs indexing scope:
- `data/registry/docs_index.toml` and `docs/DOCS_INDEX.md` now index `docs/`, `papers/sections/`, and `research/` with category partitioning.
7. Added schema validation gate for registry TOML:
- `scripts/validate_registry_schemas.py` validates `data/registry/*.toml` against `schemas/registry/*.schema.json`, including semantic count checks.
8. Extended schema validation to JSON registries:
- `scripts/validate_registry_schemas.py` now validates `parquet_audit.json` (required) and `pdf_archive_index.json` (when present) with schema + semantic count checks.
9. Added claim-lane coverage policy enforcement:
- `claim_source_crosswalk.toml` now includes `coverage_policy` thresholds and `verify_offline_integrity.py` enforces per-chapter and per-volume-group minimum linkage coverage.
10. Added external provenance schema validation lane:
- `scripts/validate_external_provenance_schemas.py` validates `data/external/PROVENANCE.json` and lane `data/external/*/PROVENANCE.json` files against `schemas/external/*.schema.json`.
11. Added claim coverage report artifact:
- `scripts/build_claim_coverage_report.py` emits `data/registry/claim_coverage_report.toml` with chapter/group coverage status and unknown-source metrics.
12. Tightened coverage policy thresholds:
- `claim_source_crosswalk.toml` now requires at least two unique sources per covered chapter and at least two claims/sources per required chapter-group prefix.
13. Added CI artifact publication for reproducibility outputs:
- `.github/workflows/ci.yml` now uploads `claim_coverage_report.toml`, `docs_index.toml`, `corpus_dedupe_report.toml`, and `docs/DOCS_INDEX.md` from the reproducibility job.

## Repository Composition Snapshot

Current file type counts (excluding `.git`, virtualenv, and caches):
- `.py`: 80
- `.json`: 58
- `.txt`: 52
- `.md`: 23
- `.tex`: 18
- `.parquet`: 6
- `.toml`: 5
- `.pdf`: 2
- total tracked/working files in scan: 272

Notable unique assets:
- interactive explorers: `figures/e8_exceptional_interactive.html`, `figures/lie_algebras_explorer.html`
- experiment snapshots: `results/*.parquet`
- external-source manifest lane: `data/external/sources.toml` + `data/external/PROVENANCE.json`
- normalized corpus lane: `data/normalized/corpus/*.json`
- generated indexes: `data/registry/*.toml` and `data/registry/*.json`

## Format Decision Matrix

### JSON
Benefits:
- strict machine parseability and broad tooling.
- ideal for normalized corpus records and schema-validated artifacts.
- easiest to hash and compare deterministically.

Detriments:
- verbose for hand editing.
- weak native comments.

Use in this repo:
- normalized corpus files (`data/normalized/corpus/*.json`)
- provenance and audit outputs (`PROVENANCE.json`, parquet audit, archive index)
- schema contracts (`schemas/*.json`)

### TOML
Benefits:
- readable key/value and table structure.
- good for registry-style metadata and manifests.
- stable for human-maintained indexes.

Detriments:
- less suited for deeply nested complex records.
- mixed parser support compared to JSON in some ecosystems.

Use in this repo:
- source manifest (`data/external/sources.toml`)
- generated registries (`data/registry/*.toml`)

### YAML
Benefits:
- concise for rich nested configs.
- supports comments and multi-line text well.

Detriments:
- whitespace sensitivity and parser variability.
- less deterministic in style unless heavily normalized.

Use in this repo:
- keep minimal and optional.
- avoid as primary registry or normalized data format.

### Decision

Use both JSON and TOML in a modular split:
- JSON for normalized/generated machine artifacts.
- TOML for human-facing manifests and registries.
- YAML only where already required by external tooling.

## Target Build Hierarchy

1. Source Layer
- `source_materials/frameworks/*.txt`
- `source_materials/pdfs/*.pdf`
- `source_materials/pdfs/extracted/*.txt`

2. External Fetch Layer
- `data/external/sources.toml` declares authoritative targets.
- `scripts/fetch_external_sources.py` fetches and records provenance.
- `data/external/PROVENANCE.json` is the machine lock record.

3. Normalization Layer
- `scripts/normalize_txt_to_json.py` converts `.txt` corpus into deterministic JSON.
- output: `data/normalized/corpus/*.json`
- registry: `data/registry/corpus_index.toml`

4. Artifact and Experiment Registry Layer
- `scripts/build_registries.py` creates:
  - `data/registry/artifacts_index.toml`
  - `data/registry/experiments_index.toml`
- `scripts/build_docs_index.py` creates:
  - `data/registry/docs_index.toml`
  - `docs/DOCS_INDEX.md`
- `scripts/validate_registry_schemas.py` validates:
  - `artifacts_index.toml`
  - `claim_coverage_report.toml`
  - `experiments_index.toml`
  - `corpus_index.toml`
  - `corpus_dedupe_report.toml`
  - `claim_source_crosswalk.toml`
  - `docs_index.toml`
  - `parquet_audit.json` (required)
  - `pdf_archive_index.json` (optional, validated when present)
- `scripts/parquet_audit.py` creates:
  - `data/registry/parquet_audit.json`
- `scripts/build_claim_coverage_report.py` creates:
  - `data/registry/claim_coverage_report.toml`

5. Verification Layer
- `scripts/verify_offline_integrity.py` checks:
  - absolute path leakage,
  - unresolved section stubs,
  - corpus index consistency,
  - manifest target structure,
  - external source index coverage,
  - external provenance completeness,
  - claim-to-source crosswalk integrity,
  - docs index consistency,
  - provenance JSON validity,
  - PDF archive index integrity.
- `scripts/validate_registry_schemas.py` enforces schema conformance for TOML registries and cross-field count consistency.
- claim crosswalk coverage policy enforces minimum source-linkage per chapter and required chapter-group prefixes.
- `scripts/validate_external_provenance_schemas.py` enforces schema + count/file consistency for external provenance JSON lanes.

6. Preservation Layer (PDF safety)
- `scripts/archive_pdfs_to_documents.py` copies repository PDFs to:
  - `~/Documents/MathScienceCompendium/pdfs`
- `data/registry/pdf_archive_index.json` records copied hashes and paths.
- `make clean-all` runs archive first, then cleanup.

## Already Applied in This Phase

- path drift fixes for old absolute home-directory references.
- replacement of explicit LaTeX section stubs with structured skeletons:
  - `papers/sections/vol2_ch6_string_theory.tex`
  - `papers/sections/vol2_ch7_quantum_gravity.tex`
  - `papers/sections/appendix_data.tex`
- experiment script portability fixes:
  - `experiments/genesis_integration.py`
  - `experiments/quantum_lbm_stable_demo.py`
- offline pipeline targets added to `Makefile`.
- PDF retention policy documented and automated archive flow added.

## Consolidation and Dedup Plan

Phase A: Inventory and Canonicalization
- freeze canonical source roots (`source_materials`, `research`, `experiments`, `papers`).
- keep generated machine outputs under `data/normalized` and `data/registry`.

Phase B: Regeneration Contracts
- regenerate via:
  - `make fetch-external`
  - `make repro-refresh`
- ensure outputs are deterministic and path-stable.

Phase C: Duplicate and Drift Control
- compare hashes in normalized corpus index to detect duplicated text payloads.
- flag duplicate external entries by URL + checksum in provenance.
- enforce relative path policy in docs and scripts.

Phase D: Quality Gate Hardening
- require `make verify-offline` in CI/local pre-merge lane.
- keep tests offline and scripts deterministic.

## Acceptance Criteria

- no absolute local paths in text artifacts.
- no unresolved explicit section stubs in targeted paper sections.
- corpus JSON and TOML registries regenerate cleanly.
- parquet audit output generated and parseable.
- PDF archive index generated and valid.
- all current PDFs preserved in both repo and `~/Documents` mirror.
