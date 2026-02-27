# PDF Source Cache

This directory stores research PDFs used by the compendium.

Policy:
- Keep PDFs when available for offline reproducibility.
- Populate this directory via `scripts/fetch_external_sources.py` and `data/external/sources.toml`.
- Keep extracted text in `source_materials/pdfs/extracted/`.
- Before any removal or relocation, archive copies with `make archive-pdfs` to `~/Documents/MathScienceCompendium/pdfs/`.

If PDFs are unavailable, keep the manifest entries and provenance notes so fetch can be retried later.
