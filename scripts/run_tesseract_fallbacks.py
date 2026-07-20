#!/usr/bin/env python3
"""OCR only pages routed to Tesseract by the native-text quality audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_tesseract_pdf_ocr import ocr_pdf, sha256_file, tesseract_version


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AUDIT = REPO_ROOT / "data" / "registry" / "pdf_text_quality_audit.json"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "build" / "document_ocr" / "tesseract_fallbacks"
DEFAULT_REGISTRY = REPO_ROOT / "data" / "registry" / "tesseract_fallback_run.json"


def build_run(
    audit_path: Path,
    output_root: Path,
    dpi: int,
    page_segmentation_mode: int,
) -> dict[str, object]:
    audit = json.loads(audit_path.read_text(encoding="ascii"))
    records: list[dict[str, object]] = []
    for document in audit["documents"]:
        selected_pages = list(document["pages_recommended_for_ocr"])
        if not selected_pages:
            continue
        pdf_path = REPO_ROOT / document["source_relpath"]
        manifest_path = ocr_pdf(
            pdf_path,
            output_root,
            dpi,
            page_segmentation_mode,
            selected_pages,
        )
        records.append(
            {
                "source_relpath": document["source_relpath"],
                "source_sha256": document["source_sha256"],
                "selected_pages": selected_pages,
                "manifest_relpath": manifest_path.relative_to(REPO_ROOT).as_posix(),
                "manifest_sha256": sha256_file(manifest_path),
            }
        )
    return {
        "schema_version": 1,
        "generator": "scripts/run_tesseract_fallbacks.py",
        "quality_audit_relpath": audit_path.relative_to(REPO_ROOT).as_posix(),
        "quality_audit_sha256": sha256_file(audit_path),
        "engine_version": tesseract_version(),
        "dpi": dpi,
        "page_segmentation_mode": page_segmentation_mode,
        "document_count": len(records),
        "page_count": sum(len(record["selected_pages"]) for record in records),
        "documents": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--dpi", type=int, default=400)
    parser.add_argument("--page-segmentation-mode", type=int, default=1)
    arguments = parser.parse_args()
    if arguments.dpi <= 0:
        parser.error("--dpi must be positive")
    audit_path = arguments.audit.resolve()
    output_root = arguments.output_root.resolve()
    registry_path = arguments.registry.resolve()
    payload = build_run(
        audit_path,
        output_root,
        arguments.dpi,
        arguments.page_segmentation_mode,
    )
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(
        f"Wrote {registry_path.relative_to(REPO_ROOT)} "
        f"({payload['document_count']} documents, {payload['page_count']} pages)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
