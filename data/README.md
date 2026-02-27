# Data Layout

This repository uses an offline-first data architecture.

Principles:
- All network fetches happen in scripts, never in tests.
- Cached artifacts must include provenance metadata.
- Normalized machine-readable documents are generated deterministically.
- Raw source files are preserved.

Directory contract:
- `data/external/`: downloaded external artifacts and provenance manifests.
- `data/normalized/`: deterministic JSON produced from raw source text.
- `data/registry/`: TOML indexes for corpus, artifacts, and experiments.

Reproducibility flow:
1. Fetch external sources from `data/external/sources.toml`.
2. Normalize text corpus into `data/normalized/corpus/`.
3. Build registries in `data/registry/`.
4. Run offline verifiers.

Suggested command sequence:
- `python3 scripts/fetch_external_sources.py --manifest data/external/sources.toml`
- `python3 scripts/normalize_txt_to_json.py`
- `python3 scripts/build_registries.py`
- `python3 scripts/verify_offline_integrity.py`
