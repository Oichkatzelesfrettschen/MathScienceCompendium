# Scientific Document OCR Environment

This environment pins MinerU 3.4.4 for formula-aware and layout-aware PDF
decomposition on an NVIDIA GPU. The image uses the CUDA 13 build of vLLM
0.21.0 and downloads the complete MinerU model set during the image build.

Build the image:

```sh
docker compose -f tools/document_ocr/compose.yaml build mineru
```

Verify GPU access and the MinerU version:

```sh
docker compose -f tools/document_ocr/compose.yaml run --rm mineru \\
  'nvidia-smi && mineru --version'
```

Run the high-effort parser sequentially over the provenance manifest:

```sh
python3 scripts/run_mineru_manifest.py
```

The sequential runner starts an isolated `docker compose` container per PDF,
validates the complete MinerU output set, skips complete papers, and records
source and output hashes. This avoids resource contention from a directory-wide
concurrent invocation.

The repository entrypoint runs the complete corpus, the forced-OCR comparison
sample, and Tesseract:

```sh
make document-ocr-generate
make document-decomposition-index
```

Generated OCR trees live under ignored `build/document_ocr/` paths. The retained
`data/registry/document_ocr_run_manifest.json` records the container image ID,
pinned base image, commands, modes, and Tesseract manifest hash.
`data/registry/document_decomposition_audit.json` records every MinerU output
hash, while `data/registry/pdf_ocr_visual_review.json` records the page-level
selection rubric. Tesseract is an independent fallback; it never replaces
embedded text or MinerU output automatically.

`data/registry/aligned_research_mineru_run.json` proves the complete seven-file
primary output set for every manifest PDF. After the native-text quality audit,
`python3 scripts/run_tesseract_fallbacks.py` renders only the pages routed for a
fallback comparison and records them in
`data/registry/tesseract_fallback_run.json`.
