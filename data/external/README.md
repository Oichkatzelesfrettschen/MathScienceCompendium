# External Sources Cache

This directory stores external source artifacts needed by the project.

Rules:
- Artifacts are cached locally for offline reuse.
- Every artifact must have provenance (URL, timestamp, hash, size).
- Do not place network calls in tests.
- Keep filenames stable and ASCII.

Files:
- `sources.toml`: desired external sources and fetch metadata.
- `PROVENANCE.json`: generated lock-style record after fetch.
