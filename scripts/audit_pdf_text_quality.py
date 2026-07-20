#!/usr/bin/env python3
"""Audit page-level native text coverage for the retained PDF corpus."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF_ROOT = REPO_ROOT / "source_materials" / "pdfs"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "pdf_text_quality_audit.json"
DEFAULT_MINIMUM_NONSPACE_CHARACTERS = 250


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def pdf_page_count(pdf_path: Path) -> int:
    result = run_command(["pdfinfo", str(pdf_path)])
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"pdfinfo did not report a page count for {pdf_path}")
    return int(match.group(1))


def extract_native_page_text(pdf_path: Path, page_number: int) -> str:
    result = run_command(
        [
            "pdftotext",
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-layout",
            str(pdf_path),
            "-",
        ]
    )
    return result.stdout


def page_metrics(text: str, minimum_nonspace_characters: int) -> dict[str, Any]:
    nonspace_characters = sum(not character.isspace() for character in text)
    replacement_characters = text.count("\ufffd")
    words = re.findall(r"[A-Za-z0-9]+", text)
    return {
        "nonspace_characters": nonspace_characters,
        "word_count": len(words),
        "replacement_characters": replacement_characters,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "ocr_recommended": (
            nonspace_characters < minimum_nonspace_characters or replacement_characters > 0
        ),
    }


def classify_document(page_rows: list[dict[str, Any]]) -> str:
    ocr_page_count = sum(bool(row["ocr_recommended"]) for row in page_rows)
    if ocr_page_count == 0:
        return "native_text_complete"
    if ocr_page_count == len(page_rows):
        return "ocr_required"
    return "native_text_mixed"


def audit_pdf(pdf_path: Path, minimum_nonspace_characters: int) -> dict[str, Any]:
    page_rows = []
    for page_number in range(1, pdf_page_count(pdf_path) + 1):
        page_text = extract_native_page_text(pdf_path, page_number)
        page_rows.append(
            {
                "page": page_number,
                **page_metrics(page_text, minimum_nonspace_characters),
            }
        )
    return {
        "source_relpath": pdf_path.relative_to(REPO_ROOT).as_posix(),
        "source_sha256": sha256_file(pdf_path),
        "size_bytes": pdf_path.stat().st_size,
        "page_count": len(page_rows),
        "native_nonspace_characters": sum(int(row["nonspace_characters"]) for row in page_rows),
        "pages_recommended_for_ocr": [
            int(row["page"]) for row in page_rows if row["ocr_recommended"]
        ],
        "classification": classify_document(page_rows),
        "pages": page_rows,
    }


def build_audit(pdf_root: Path, minimum_nonspace_characters: int) -> dict[str, Any]:
    pdf_paths = sorted(pdf_root.glob("*.pdf"))
    documents = [audit_pdf(path, minimum_nonspace_characters) for path in pdf_paths]
    return {
        "schema_version": 1,
        "generator": "scripts/audit_pdf_text_quality.py",
        "policy": {
            "minimum_nonspace_characters_per_page": minimum_nonspace_characters,
            "replacement_character_limit": 0,
            "purpose": "route sparse native text to OCR without replacing good embedded text",
        },
        "document_count": len(documents),
        "page_count": sum(int(document["page_count"]) for document in documents),
        "documents": documents,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-root", type=Path, default=DEFAULT_PDF_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--minimum-nonspace-characters",
        type=int,
        default=DEFAULT_MINIMUM_NONSPACE_CHARACTERS,
    )
    arguments = parser.parse_args()

    if arguments.minimum_nonspace_characters <= 0:
        parser.error("--minimum-nonspace-characters must be positive")
    pdf_root = arguments.pdf_root
    if not pdf_root.is_absolute():
        pdf_root = REPO_ROOT / pdf_root
    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path

    audit = build_audit(pdf_root, arguments.minimum_nonspace_characters)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(
        f"Wrote {output_path.relative_to(REPO_ROOT)} "
        f"({audit['document_count']} documents, {audit['page_count']} pages)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
