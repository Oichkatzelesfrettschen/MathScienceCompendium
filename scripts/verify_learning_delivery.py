#!/usr/bin/env python3
"""Reopen delivered PDFs, verify destinations, and render inspection inputs.

Run from the repository root after make album, learning-largeprint, and
learning-grayscale. Rendering supplies inputs for visual review; it does
not measure learner outcomes or certify the rendered layout.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def outline_page(document: fitz.Document, title: str) -> int:
    matches = [row[2] for row in document.get_toc() if row[1] == title]
    require(len(matches) == 1, f"Expected one outline destination: {title}")
    return matches[0]


def main() -> None:
    render_root = Path("build/learning/visual-review")
    render_root.mkdir(parents=True, exist_ok=True)
    pdf_paths = {
        "bridge": Path("build/learning/main.pdf"),
        "navigation": Path("build/album/navigation.pdf"),
        "review": Path("papers/main.pdf"),
        "largeprint": Path("build/learning/largeprint/largeprint.pdf"),
        "grayscale": Path("build/learning/main-grayscale.pdf"),
    }
    documents = {name: fitz.open(path) for name, path in pdf_paths.items()}
    manifest = json.loads(Path("build/album/manifest.json").read_text())
    library = json.loads(Path("docs/learning/library.json").read_text())
    matrix_page = manifest["destinations"]["matrix_maps"]["page"]
    complex_page = manifest["destinations"]["complex_numbers"]["page"]
    hypothesis_page = manifest["destinations"]["review_hypotheses"]["page"]
    samples = {
        "bridge": [
            matrix_page,
            matrix_page + 1,
            complex_page + 1,
            manifest["destinations"]["quantum"]["page"],
            outline_page(documents["bridge"], "Readiness solutions"),
        ],
        "navigation": [
            1,
            manifest["destinations"]["route:symmetry"]["page"],
            manifest["destinations"]["route:claims"]["page"],
        ],
        "review": [
            manifest["destinations"]["review_evidence"]["page"],
            hypothesis_page,
            hypothesis_page + 1,
        ],
        "largeprint": [
            outline_page(documents["largeprint"], "From balanced equations to matrix maps") + 1,
            outline_page(
                documents["largeprint"], "Complex numbers: multiplication, length, and conjugation"
            )
            + 1,
        ],
        "grayscale": [matrix_page + 1],
    }
    for name, document in documents.items():
        for page_number in samples[name]:
            require(1 <= page_number <= len(document), f"Invalid sample in {name}")
            document[page_number - 1].get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False).save(
                render_root / f"delivered-{name}-{page_number}.png"
            )
        if name not in ("bridge", "navigation"):
            continue
        for start in range(0, len(document), 20):
            sheet = Image.new("RGB", (1000, 1550), "white")
            draw = ImageDraw.Draw(sheet)
            for offset in range(min(20, len(document) - start)):
                pixmap = document[start + offset].get_pixmap(
                    matrix=fitz.Matrix(0.36, 0.36), alpha=False
                )
                thumbnail = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                thumbnail.thumbnail((240, 280))
                column_offset, row_offset = offset % 4 * 250, offset // 4 * 310
                sheet.paste(thumbnail, (column_offset, row_offset + 20))
                draw.text(
                    (column_offset + 8, row_offset + 3),
                    f"{name} page {start + offset + 1}",
                    fill="black",
                )
            sheet.save(render_root / f"delivered-{name}-sheet-{start + 1}.png")
    navigation = documents["navigation"]
    remote_links = local_links = 0
    for page in navigation:
        for link in page.get_links():
            require(page.rect.contains(link["from"]), f"Annotation outside page: {link}")
            if link["kind"] == fitz.LINK_GOTOR:
                target = (pdf_paths["navigation"].parent / link["file"]).resolve()
                require(
                    target.parent == pdf_paths["navigation"].parent.resolve(),
                    f"Remote target escapes bundle: {target}",
                )
                with fitz.open(target) as target_document:
                    require(
                        0 <= link["page"] < len(target_document), f"Invalid destination: {link}"
                    )
                remote_links += 1
            elif link["kind"] in (fitz.LINK_GOTO, fitz.LINK_NAMED):
                require(0 <= link["page"] < len(navigation), f"Invalid local destination: {link}")
                local_links += 1
            else:
                require(link["kind"] == fitz.LINK_URI, f"Unexpected link action: {link}")
    for book in manifest["books"]:
        book_path = Path("build/album") / (book["id"] + ".pdf")
        require(
            hashlib.sha256(book_path.read_bytes()).hexdigest() == book["pdf_sha256"],
            f"Copied PDF identity differs: {book_path}",
        )
    record = {
        "schema_version": 1,
        "focused_test_command": ".venv/bin/python -m pytest --noconftest -q -o addopts='' tests/unit/test_learning*.py",
        "bounded_original_learning_checks": len(
            json.loads(Path("build/learning/examples.json").read_text())["checks"]
        ),
        "library_nodes": len(library["nodes"]),
        "routes": len(library["routes"]),
        "navigation_pymupdf_remote_links": remote_links,
        "navigation_pymupdf_local_links": local_links,
        "pdfs": {
            name: {
                "path": str(path),
                "pages": len(documents[name]),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "full_page_samples_rendered": samples[name],
            }
            for name, path in pdf_paths.items()
        },
        "contact_sheets_rendered": {
            name: f"all {len(documents[name])} pages" for name in ("bridge", "navigation")
        },
        "full_page_render_dpi": 100.8,
        "scope": "PDF object navigation and artifact identity checks; rendered samples require visual inspection. Human learner outcomes and universal reader compatibility are separate evidence.",
    }
    Path("build/learning/validation.json").write_text(json.dumps(record, indent=2) + "\n")
    for document in documents.values():
        document.close()
    print(f"Independent reader links: {remote_links} cross-file; {local_links} local")


if __name__ == "__main__":
    main()
