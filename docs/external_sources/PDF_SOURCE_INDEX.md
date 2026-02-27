# PDF Source Index

Canonical manifest: `data/external/sources.toml`

This index tracks expected PDF sources used by the compendium.
The manifest is authoritative for fetch metadata and target paths.
For curated non-PDF context imports from Super-Force-Analysis, see:
`docs/external_sources/SUPER_FORCE_ANALYSIS_SOURCE_INDEX.md`.

## Process

1. Add/update source entries in `data/external/sources.toml`.
2. Run `python3 scripts/fetch_external_sources.py --extract-text`.
3. Commit updated `data/external/PROVENANCE.json` and extracted text outputs.

## Current Policy

- Keep PDFs in `source_materials/pdfs/` when available.
- Keep extracted text in `source_materials/pdfs/extracted/`.
- Avoid hardcoded absolute local paths in documentation.
