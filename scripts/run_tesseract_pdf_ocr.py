#!/usr/bin/env python3
"""Render PDF pages and run a traceable Tesseract OCR baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "build" / "document_ocr" / "tesseract"


def run_command(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def page_count(pdf_path: Path) -> int:
    result = run_command(["pdfinfo", str(pdf_path)])
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"pdfinfo did not report a page count for {pdf_path}")
    return int(match.group(1))


def tesseract_version() -> str:
    result = run_command(["tesseract", "--version"])
    return result.stdout.splitlines()[0]


def parse_page_spec(page_spec: str) -> list[int]:
    """Parse a comma-separated one-based page and range specification."""
    selected_pages: set[int] = set()
    for raw_token in page_spec.split(","):
        token = raw_token.strip()
        if not token:
            raise ValueError("empty page token")
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start <= 0 or end < start:
                raise ValueError(f"invalid page range: {token}")
            selected_pages.update(range(start, end + 1))
        else:
            page_number = int(token)
            if page_number <= 0:
                raise ValueError(f"invalid page number: {token}")
            selected_pages.add(page_number)
    return sorted(selected_pages)


def ocr_pdf(
    pdf_path: Path,
    output_root: Path,
    dpi: int,
    page_segmentation_mode: int,
    page_numbers: list[int] | None = None,
) -> Path:
    document_output = output_root / pdf_path.stem
    pages_output = document_output / "pages"
    pages_output.mkdir(parents=True, exist_ok=True)
    page_rows = []
    source_page_count = page_count(pdf_path)
    selected_pages = list(range(1, source_page_count + 1)) if page_numbers is None else page_numbers
    if not selected_pages:
        raise ValueError("at least one page must be selected")
    if any(page_number > source_page_count for page_number in selected_pages):
        raise ValueError(f"selected page exceeds {source_page_count}-page source: {selected_pages}")

    with tempfile.TemporaryDirectory(prefix="mathscience-tesseract-") as temporary_directory:
        temporary_root = Path(temporary_directory)
        for page_number in selected_pages:
            image_base = temporary_root / f"page-{page_number:04d}"
            run_command(
                [
                    "pdftoppm",
                    "-f",
                    str(page_number),
                    "-l",
                    str(page_number),
                    "-singlefile",
                    "-r",
                    str(dpi),
                    "-png",
                    str(pdf_path),
                    str(image_base),
                ]
            )
            output_base = pages_output / f"page-{page_number:04d}"
            run_command(
                [
                    "tesseract",
                    str(image_base.with_suffix(".png")),
                    str(output_base),
                    "--dpi",
                    str(dpi),
                    "--psm",
                    str(page_segmentation_mode),
                    "-l",
                    "eng",
                ]
            )
            output_text_path = output_base.with_suffix(".txt")
            page_rows.append(
                {
                    "page": page_number,
                    "output_relpath": output_text_path.relative_to(REPO_ROOT).as_posix(),
                    "output_sha256": sha256_file(output_text_path),
                    "output_bytes": output_text_path.stat().st_size,
                }
            )

    manifest = {
        "schema_version": 1,
        "engine": "tesseract",
        "engine_version": tesseract_version(),
        "source_relpath": pdf_path.relative_to(REPO_ROOT).as_posix(),
        "source_sha256": sha256_file(pdf_path),
        "source_page_count": source_page_count,
        "selection": "all" if page_numbers is None else "explicit",
        "dpi": dpi,
        "page_segmentation_mode": page_segmentation_mode,
        "language": "eng",
        "pages": page_rows,
    }
    manifest_path = document_output / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, nargs="+")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--dpi", type=int, default=400)
    parser.add_argument("--page-segmentation-mode", type=int, default=1)
    parser.add_argument(
        "--pages",
        help="one-based comma-separated pages or ranges, for example 1,3,5-7",
    )
    arguments = parser.parse_args()

    if arguments.dpi <= 0:
        parser.error("--dpi must be positive")
    try:
        page_numbers = parse_page_spec(arguments.pages) if arguments.pages else None
    except ValueError as error:
        parser.error(str(error))
    output_root = arguments.output_root
    if not output_root.is_absolute():
        output_root = REPO_ROOT / output_root

    for input_path in arguments.pdf:
        pdf_path = input_path if input_path.is_absolute() else REPO_ROOT / input_path
        manifest_path = ocr_pdf(
            pdf_path,
            output_root,
            arguments.dpi,
            arguments.page_segmentation_mode,
            page_numbers,
        )
        print(f"Wrote {manifest_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
