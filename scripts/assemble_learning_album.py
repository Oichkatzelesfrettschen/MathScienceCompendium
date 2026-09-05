#!/usr/bin/env python3
"""Assemble pinned books with preserved links and executable reading routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Link
from pypdf.generic import NameObject
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from validate_learning_library import ROOT, validate_library


def heading_end_y(title: str, subtitle: str) -> float:
    width, height = A4
    title_lines = simpleSplit(title, "Helvetica-Bold", 23, width - 84)
    subtitle_lines = simpleSplit(subtitle, "Helvetica", 11, width - 84)
    return height - 66 - (len(title_lines) - 1) * 28 - 28 - len(subtitle_lines) * 15.95 - 18


def route_page_layout(route: dict[str, Any], nodes: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """Measure wrapped assessments, splitting long lessons across readable pages."""
    width, _ = A4
    subtitle = "Follow the prerequisites. Attempt each assessment before moving onward."
    top = heading_end_y(route["title"], subtitle)
    bottom = 60
    line_height = 9 * 1.45
    if top - 17 - line_height < bottom:
        raise ValueError(f"Route heading leaves no room for a lesson: {route['id']}")
    pages: list[list[dict[str, Any]]] = []
    page: list[dict[str, Any]] = []
    y = top
    for index, identifier in enumerate(route["nodes"], start=1):
        node = nodes[identifier]
        remaining = simpleSplit(node["assessment"], "Helvetica", 9, width - 104)
        continuation = False
        while remaining:
            capacity = int((y - 17 - bottom) // line_height)
            if capacity < 1:
                pages.append(page)
                page = []
                y = top
                continue
            portion, remaining = remaining[:capacity], remaining[capacity:]
            page.append(
                {
                    "identifier": identifier,
                    "index": index,
                    "continuation": continuation,
                    "y": y,
                    "lines": portion,
                }
            )
            y -= 17 + len(portion) * line_height + 13
            continuation = True
    if page:
        pages.append(page)
    return pages


def navigation_page_count(library: dict[str, Any]) -> int:
    directory_pages = (len(library["nodes"]) + 17) // 18
    nodes = {node["id"]: node for node in library["nodes"]}
    route_pages = sum(len(route_page_layout(route, nodes)) for route in library["routes"])
    return 1 + directory_pages + route_pages


def git(root: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *arguments], text=True).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_title(title: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKC", title).replace("\u2013", "-").replace("\u2014", "-").split()
    )


def outline_pages(reader: PdfReader) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}

    def visit(items: list[Any]) -> None:
        for item in items:
            if isinstance(item, list):
                visit(item)
            else:
                page = reader.get_destination_page_number(item)
                if page is not None:
                    result.setdefault(normalize_title(str(item["/Title"])), []).append(page)

    visit(reader.outline)
    return result


def source_dependencies(root: Path, pdf: Path) -> dict[str, str]:
    root = root.resolve()
    recorder = pdf.with_suffix(".fls")
    if not recorder.is_file():
        raise ValueError(f"Missing TeX input recorder: {recorder}")
    dependencies: dict[str, str] = {}
    lines = recorder.read_text().splitlines()
    directories = [Path(line[4:]) for line in lines if line.startswith("PWD ")]
    if not directories or not directories[0].resolve().is_relative_to(root):
        raise ValueError(f"Recorder working directory lies outside source checkout: {recorder}")
    working_directory = directories[0].resolve()
    relevant_suffixes = {
        ".tex",
        ".bib",
        ".bbl",
        ".ind",
        ".png",
        ".jpg",
        ".jpeg",
        ".pdf",
        ".eps",
        ".svg",
        ".dat",
        ".ist",
        ".sty",
        ".cls",
        ".bst",
    }

    def retain(source: Path) -> None:
        if not source.is_file():
            raise ValueError(f"Missing recorded source input: {source}")
        if source.stat().st_mtime_ns > pdf.stat().st_mtime_ns:
            raise ValueError(f"PDF is older than its input: {source}")
        dependencies[str(source.relative_to(root))] = sha256(source)

    for line in lines:
        if not line.startswith("INPUT "):
            continue
        source = Path(line[6:])
        source = (
            (working_directory / source).resolve() if not source.is_absolute() else source.resolve()
        )
        if source.is_relative_to(root) and source.suffix.lower() in relevant_suffixes:
            retain(source)
    bibliography_names: set[str] = set()
    auxiliary = pdf.with_suffix(".aux")
    if auxiliary.is_file():
        for group in re.findall(r"\\bibdata\{([^}]+)\}", auxiliary.read_text()):
            bibliography_names.update(name.strip() for name in group.split(","))
    latexmk_database = pdf.with_suffix(".fdb_latexmk")
    if latexmk_database.is_file():
        bibliography_names.update(
            re.findall(r'^\s*"([^"\n]+\.bib)"', latexmk_database.read_text(), flags=re.MULTILINE)
        )
    for name in sorted(bibliography_names):
        relative = Path(name if name.endswith(".bib") else name + ".bib")
        candidates = {
            (directory / relative).resolve() for directory in (working_directory, pdf.parent, root)
        }
        existing = {
            candidate
            for candidate in candidates
            if candidate.is_file() and candidate.is_relative_to(root)
        }
        if len(existing) != 1:
            raise ValueError(f"Bibliography origin must resolve to one local source: {name}")
        retain(existing.pop())
    if any(Path(name).suffix == ".bbl" for name in dependencies) and not bibliography_names:
        raise ValueError(f"Missing bibliography origin evidence for: {pdf}")
    if not dependencies:
        raise ValueError(f"Empty source dependency set: {pdf}")
    return dict(sorted(dependencies.items()))


def navigation_pdf(path: Path, library: dict[str, Any], targets: dict[str, int]) -> list[tuple]:
    document = canvas.Canvas(str(path), pagesize=A4, invariant=1)
    document.setTitle("Mathematics learning album: choose a route")
    document.setAuthor("Eirikr Hinngart")
    width, height = A4
    links: list[tuple] = []
    ink, navy, paper = map(HexColor, ["#18212B", "#17365D", "#F2F5F8"])
    node_map = {node["id"]: node for node in library["nodes"]}

    def paragraph(text: str, x: float, y: float, limit: float, size: int = 11) -> float:
        document.setFillColor(ink)
        document.setFont("Helvetica", size)
        for line in simpleSplit(text, "Helvetica", size, limit):
            document.drawString(x, y, line)
            y -= size * 1.45
        return y

    def heading(title: str, subtitle: str) -> float:
        document.setFillColor(navy)
        document.setFont("Helvetica-Bold", 23)
        y = height - 66
        title_lines = simpleSplit(title, "Helvetica-Bold", 23, width - 84)
        for title_line in title_lines:
            document.drawString(42, y, title_line)
            y -= 28
        return paragraph(subtitle, 42, y, width - 84) - 18

    def jump(label: str, identifier: str, x: float, y: float, page: int, size: int = 11) -> None:
        document.setFont("Helvetica-Bold", size)
        document.setFillColor(navy)
        document.drawString(x, y, label)
        extent = document.stringWidth(label, "Helvetica-Bold", size)
        links.append((page, (x - 2, y - 3, x + extent + 2, y + size + 2), identifier))

    y = heading(
        "A mathematics learning album",
        "Start with precalculus. Choose a question. Follow the prerequisites.",
    )
    y = (
        paragraph(
            "Three connected books carry one journey from basic operations to "
            "careful advanced reasoning. Each keeps its own purpose and authorship. "
            "The directory and reading-route links jump into the assembled books; "
            "their original tables of contents and PDF bookmarks remain available.",
            42,
            y,
            width - 84,
        )
        - 24
    )
    for identifier, title, explanation in [
        (
            "precalc",
            "1. A Precalculus Compendium",
            "Functions and their histories, visual constructions, guided operations, and exercises.",
        ),
        (
            "proof",
            "2. From Precalculus to Mathematical Physics",
            "Ten bridge chapters with definitions, worked derivations, historical sources, "
            "and three fully solved exercises per chapter.",
        ),
        (
            "review_evidence",
            "3. Claim, Evidence, and Falsification",
            "The advanced review asks what mathematics, computation, and physical evidence "
            "actually establish. Its negative results are part of the learning destination.",
        ),
    ]:
        document.setFillColor(paper)
        document.roundRect(36, y - 89, width - 72, 108, 7, fill=1, stroke=0)
        jump(title, f"book:{node_map[identifier]['book']}", 48, y, 0, 12)
        paragraph(explanation, 48, y - 24, width - 96)
        y -= 128
    paragraph(
        "A route is an invitation, not a claim of full-course mastery. Try the "
        "stated assessment before moving onward. Return to a worked example "
        "when an operation or prerequisite is unfamiliar.",
        42,
        y,
        width - 84,
    )
    document.showPage()
    page_number = 1
    for start in range(0, len(library["nodes"]), 18):
        y = heading(
            "Lesson directory", "Click a lesson title. Page numbers refer to this combined PDF."
        )
        for node in library["nodes"][start : start + 18]:
            title = node["title"]
            while document.stringWidth(title, "Helvetica-Bold", 10) > width - 132:
                title = title[:-4] + "..."
            jump(title, node["id"], 42, y, page_number, 10)
            document.setFont("Helvetica", 10)
            document.setFillColor(ink)
            document.drawRightString(width - 42, y, str(targets[node["id"]] + 1))
            y -= 32
        paragraph(
            "Use the PDF outline to return to the directory or reading routes. "
            "Each source book retains its own outline and internal links.",
            42,
            y - 8,
            width - 84,
        )
        document.showPage()
        page_number += 1
    for route in library["routes"]:
        for route_page in route_page_layout(route, node_map):
            heading(
                route["title"],
                "Follow the prerequisites. Attempt each assessment before moving onward.",
            )
            for item in route_page:
                identifier = item["identifier"]
                node = node_map[identifier]
                title = f"{item['index']}. {node['title']}"
                if item["continuation"]:
                    title += " (continued)"
                while document.stringWidth(title, "Helvetica-Bold", 10) > width - 104:
                    title = title[:-4] + "..."
                y = item["y"]
                jump(title, identifier, 42, y, page_number, 10)
                document.setFillColor(ink)
                document.setFont("Helvetica", 9)
                for line_number, line in enumerate(item["lines"]):
                    document.drawString(52, y - 17 - line_number * 9 * 1.45, line)
            document.showPage()
            page_number += 1
    document.save()
    return links


def assemble(
    library: dict[str, Any],
    precalc_root: Path,
    output: Path,
    additional_roots: dict[str, Path] | None = None,
) -> dict[str, Any]:
    source_roots = {
        "precalculus": precalc_root.resolve(),
        **{identifier: path.resolve() for identifier, path in (additional_roots or {}).items()},
    }
    errors = validate_library(library, root=ROOT, external_roots=source_roots)
    if errors:
        raise ValueError("; ".join(errors))
    revisions: dict[str, str] = {}
    for book in library["books"]:
        if not book.get("repository"):
            continue
        root = source_roots.get(book["id"])
        if root is None:
            raise ValueError(f"Missing external checkout: {book['id']}")
        actual = git(root, "rev-parse", "HEAD")
        if actual != book["revision"]:
            raise ValueError(
                f"{book['id']} revision differs: expected {book['revision']}, got {actual}"
            )
        if git(root, "status", "--porcelain", "--untracked-files=no"):
            raise ValueError(f"{book['id']}: tracked source has uncommitted changes")
        revisions[book["id"]] = actual
    output.mkdir(parents=True, exist_ok=True)
    readers: dict[str, PdfReader] = {}
    source_paths: dict[str, Path] = {}
    offsets: dict[str, int] = {}
    titles: dict[str, dict[str, list[int]]] = {}
    dependencies: dict[str, dict[str, str]] = {}
    offset = navigation_page_count(library)
    for book in library["books"]:
        root = source_roots[book["id"]] if book.get("repository") else ROOT
        path = root / book["pdf"]
        if not path.is_file():
            raise ValueError(f"Missing built book: {path}")
        source_paths[book["id"]] = path
        dependencies[book["id"]] = source_dependencies(root, path)
        reader = PdfReader(path, strict=True)
        if not reader.pages:
            raise ValueError(f"Empty book: {path}")
        readers[book["id"]] = reader
        offsets[book["id"]] = offset
        titles[book["id"]] = outline_pages(reader)
        offset += len(reader.pages)
    targets: dict[str, int] = {}
    for node in library["nodes"]:
        title = node.get("pdf_title")
        pages = [0] if title is None else titles[node["book"]].get(normalize_title(title), [])
        if not pages:
            raise ValueError(f"Missing PDF destination for {node['id']}: {title}")
        if len(pages) != 1:
            raise ValueError(f"Ambiguous PDF destination for {node['id']}: {title}")
        targets[node["id"]] = offsets[node["book"]] + pages[0]
    targets.update({f"book:{identifier}": page for identifier, page in offsets.items()})
    navigation = output / "navigation.pdf"
    links = navigation_pdf(navigation, library, targets)
    writer = PdfWriter()
    writer.append(navigation, import_outline=True)
    if len(writer.pages) != navigation_page_count(library):
        raise ValueError("Navigation page count drifted")
    writer.add_outline_item("Album directory", 1)
    writer.add_outline_item("Reading routes", 1 + (len(library["nodes"]) + 17) // 18)
    for book in library["books"]:
        writer.append(readers[book["id"]], outline_item=book["title"], import_outline=True)
    for page, rectangle, identifier in links:
        added = writer.add_annotation(
            page, Link(rect=rectangle, target_page_index=targets[identifier])
        )
        # Local explicit destinations require a page object, not a remote page number.
        added[NameObject("/Dest")][0] = writer.pages[targets[identifier]].indirect_reference
    writer.add_metadata({"/Title": "Mathematics Learning Album", "/Author": "Eirikr Hinngart"})
    destination = output / "album.pdf"
    temporary = output / "album.pending.pdf"
    writer.write(temporary)
    check = PdfReader(temporary, strict=True)
    if len(check.pages) != offset:
        raise ValueError("Assembled page count differs from input total")
    for page, rectangle, identifier in links:
        annotations = check.pages[page].get("/Annots", [])
        expected = targets[identifier]
        matched = [
            item.get_object()
            for item in annotations
            if len(item.get_object().get("/Rect", [])) == 4
            and all(
                abs(float(actual) - expected_coordinate) < 0.001
                for actual, expected_coordinate in zip(item.get_object()["/Rect"], rectangle)
            )
        ]
        if (
            len(matched) != 1
            or check.get_page_number(matched[0]["/Dest"][0].get_object()) != expected
        ):
            raise ValueError(f"Navigation destination failed: {identifier}")
    temporary.replace(destination)
    manifest = {
        "schema_version": 1,
        "library_sha256": sha256(ROOT / "docs/learning/library.json"),
        "album_sha256": sha256(destination),
        "pages": offset,
        "navigation_links_checked": len(links),
        "destinations": {key: value + 1 for key, value in targets.items()},
        "books": [
            {
                "id": book["id"],
                "pages": len(readers[book["id"]].pages),
                "pdf_sha256": sha256(source_paths[book["id"]]),
                "source_dependencies": dependencies[book["id"]],
                "revision": revisions[book["id"]]
                if book.get("repository")
                else git(ROOT, "rev-parse", "HEAD"),
            }
            for book in library["books"]
        ],
        "scope": "Assembly identity and navigation checks; factual audits are separate records.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--precalc-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "build/album")
    parser.add_argument("--book-root", action="append", default=[], metavar="ID=PATH")
    arguments = parser.parse_args()
    library = json.loads((ROOT / "docs/learning/library.json").read_text())
    additional_roots = {}
    for mapping in arguments.book_root:
        identifier, separator, path = mapping.partition("=")
        if not separator or not identifier or not path:
            parser.error("--book-root requires ID=PATH")
        additional_roots[identifier] = Path(path).expanduser().resolve()
    result = assemble(library, arguments.precalc_root.resolve(), arguments.output, additional_roots)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
