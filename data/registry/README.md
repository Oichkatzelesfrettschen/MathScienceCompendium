# Registry Files

Registry files are generated TOML indexes used by build and validation scripts.

Generated outputs:
- `corpus_index.toml`: mapping from raw text files to normalized JSON records.
- `artifacts_index.toml`: figures, papers, and result artifact metadata.
- `experiments_index.toml`: experiment outputs and run metadata.
- `docs_index.toml`: indexed content metadata for docs, paper sections, and research corpus.
- `claim_source_crosswalk.toml`: chapter-level claim anchors mapped to external source IDs.
- `claim_coverage_report.toml`: policy-based claim/source coverage metrics for tracked chapters/groups.
- `corpus_dedupe_report.toml`: duplicate and hash-mismatch report for normalized corpus.

Validation:
- `scripts/validate_registry_schemas.py` validates all `data/registry/*.toml` files and
  selected `data/registry/*.json` files against `schemas/registry/*.schema.json`.

Do not hand-edit generated sections; regenerate using scripts.
