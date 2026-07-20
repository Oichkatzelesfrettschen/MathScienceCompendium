#!/usr/bin/env python3
"""Record traceable metrics for native, MinerU, and Tesseract PDF text."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF = REPO_ROOT / "source_materials" / "pdfs" / "Comment_on_the_Pais_Superforce_Theory.pdf"
DEFAULT_MINERU = (
    REPO_ROOT
    / "build"
    / "document_ocr"
    / "mineru"
    / "Comment_on_the_Pais_Superforce_Theory"
    / "hybrid_ocr"
    / "Comment_on_the_Pais_Superforce_Theory.md"
)
DEFAULT_TESSERACT_MANIFEST = (
    REPO_ROOT
    / "build"
    / "document_ocr"
    / "tesseract"
    / "Comment_on_the_Pais_Superforce_Theory"
    / "manifest.json"
)
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "pdf_ocr_comparison.json"
DEFAULT_RUN_MANIFEST = REPO_ROOT / "data" / "registry" / "document_ocr_run_manifest.json"
DEFAULT_VISUAL_REVIEW = REPO_ROOT / "data" / "registry" / "pdf_ocr_visual_review.json"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def text_metrics(text: str) -> dict[str, int]:
    return {
        "bytes_utf8": len(text.encode("utf-8")),
        "characters": len(text),
        "nonspace_characters": len(re.sub(r"\s", "", text)),
        "word_tokens": len(re.findall(r"[A-Za-z0-9]+", text)),
        "line_count": len(text.splitlines()),
    }


def resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def path_record(path: Path, text: str) -> dict[str, Any]:
    return {
        "source_relpath": path.relative_to(REPO_ROOT).as_posix(),
        "source_sha256": sha256_bytes(path.read_bytes()),
        **text_metrics(text),
    }


def native_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout


def tesseract_text(manifest_path: Path) -> tuple[str, dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    page_text = []
    for page in manifest["pages"]:
        page_path = REPO_ROOT / page["output_relpath"]
        page_text.append(page_path.read_text(encoding="utf-8", errors="replace"))
    return "\n\f\n".join(page_text), manifest


def build_comparison(
    pdf_path: Path,
    mineru_path: Path,
    tesseract_manifest_path: Path,
    run_manifest_path: Path,
    visual_review_path: Path,
) -> dict[str, Any]:
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    visual_review = json.loads(visual_review_path.read_text(encoding="utf-8"))
    mineru_config = run_manifest["mineru"]
    native = native_text(pdf_path)
    mineru = mineru_path.read_text(encoding="utf-8", errors="replace")
    tesseract, tesseract_manifest = tesseract_text(tesseract_manifest_path)
    return {
        "schema_version": 1,
        "generator": "scripts/compare_pdf_ocr_outputs.py",
        "provenance": {
            "run_manifest_relpath": run_manifest_path.relative_to(REPO_ROOT).as_posix(),
            "run_manifest_sha256": sha256_bytes(run_manifest_path.read_bytes()),
            "visual_review_relpath": visual_review_path.relative_to(REPO_ROOT).as_posix(),
            "visual_review_sha256": sha256_bytes(visual_review_path.read_bytes()),
        },
        "source_pdf": {
            "relpath": pdf_path.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_bytes(pdf_path.read_bytes()),
        },
        "outputs": {
            "native_pdftotext_layout": {
                "engine": "pdftotext -layout",
                **text_metrics(native),
            },
            "mineru_high_effort_hybrid_forced_ocr": {
                "engine": (
                    f"{mineru_config['name']} {mineru_config['version']} "
                    f"{mineru_config['backend']}, effort {mineru_config['effort']}, "
                    f"mode {mineru_config['forced_ocr_sample']['mode']}"
                ),
                **path_record(mineru_path, mineru),
                "markdown_display_math_blocks": len(re.findall(r"\$\$", mineru)) // 2,
                "markdown_image_references": len(re.findall(r"!\[.*?\]\(", mineru)),
            },
            "tesseract_400_dpi_psm_1": {
                "engine": tesseract_manifest["engine_version"],
                "manifest_relpath": tesseract_manifest_path.relative_to(REPO_ROOT).as_posix(),
                "manifest_sha256": sha256_bytes(tesseract_manifest_path.read_bytes()),
                "page_count": len(tesseract_manifest["pages"]),
                **text_metrics(tesseract),
            },
        },
        "selection": visual_review["selection"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--mineru", type=Path, default=DEFAULT_MINERU)
    parser.add_argument("--tesseract-manifest", type=Path, default=DEFAULT_TESSERACT_MANIFEST)
    parser.add_argument("--run-manifest", type=Path, default=DEFAULT_RUN_MANIFEST)
    parser.add_argument("--visual-review", type=Path, default=DEFAULT_VISUAL_REVIEW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    pdf_path = resolve_repo_path(arguments.pdf)
    mineru_path = resolve_repo_path(arguments.mineru)
    tesseract_manifest_path = resolve_repo_path(arguments.tesseract_manifest)
    run_manifest_path = resolve_repo_path(arguments.run_manifest)
    visual_review_path = resolve_repo_path(arguments.visual_review)
    output_path = resolve_repo_path(arguments.output)

    comparison = build_comparison(
        pdf_path,
        mineru_path,
        tesseract_manifest_path,
        run_manifest_path,
        visual_review_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(comparison, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(f"Wrote {output_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
