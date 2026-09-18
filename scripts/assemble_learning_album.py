#!/usr/bin/env python3
"""Publish separate admitted books with a cross-PDF route directory."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    FloatObject,
    NameObject,
    NumberObject,
    TextStringObject,
)
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from validate_learning_library import ROOT, validate_library


ROUTE_BODY_SIZE = 11
ROUTE_HEADING_SIZE = 12
ROUTE_LINE_HEIGHT = ROUTE_BODY_SIZE * 1.45
ROUTE_HEADING_GAP = 20


def heading_end_y(title: str, subtitle: str) -> float:
    width, height = A4
    title_lines = simpleSplit(title, "Helvetica-Bold", 23, width - 84)
    subtitle_lines = simpleSplit(subtitle, "Helvetica", 11, width - 84)
    return height - 66 - (len(title_lines) - 1) * 28 - 28 - len(subtitle_lines) * 15.95 - 18


def route_subtitle(route: dict[str, Any]) -> str:
    return (
        f"Purpose: {route['purpose']} Question: {route['question']} "
        f"Starting knowledge: {route['starting_knowledge']}"
    )


def lesson_lines(node: dict[str, Any], nodes: dict[str, Any]) -> list[str]:
    """Summarize the next learning decision and locate the deeper preparation."""
    required = ", ".join(nodes[item]["title"] for item in node["requires"]) or "Start here"
    paragraphs = [
        f"Question: {node['question']}",
        "Outcomes: " + "; ".join(node["outcomes"]),
        f"Required: {required}.",
        "",
        f"Readiness check: {node['readiness']['prompt']}",
        "Open the linked lesson for entry preparation, worked solutions, and next-step guidance. "
        "The matching lesson in index.html also supplies these details for every book.",
    ]
    return [
        line
        for paragraph in paragraphs
        for line in (
            simpleSplit(paragraph, "Helvetica", ROUTE_BODY_SIZE, A4[0] - 104) if paragraph else [""]
        )
    ]


def route_page_layout(route: dict[str, Any], nodes: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """Measure wrapped assessments, splitting long lessons across readable pages."""
    subtitle = route_subtitle(route)
    top = heading_end_y(route["title"], subtitle)
    bottom = 60
    line_height = ROUTE_LINE_HEIGHT
    if top - ROUTE_HEADING_GAP - line_height < bottom:
        raise ValueError(f"Route heading leaves no room for a lesson: {route['id']}")
    pages: list[list[dict[str, Any]]] = []
    page: list[dict[str, Any]] = []
    y = top
    for index, identifier in enumerate(route["nodes"], start=1):
        node = nodes[identifier]
        remaining = lesson_lines(node, nodes)
        continuation = False
        fresh_capacity = int((top - ROUTE_HEADING_GAP - bottom) // line_height)
        available_capacity = int((y - ROUTE_HEADING_GAP - bottom) // line_height)
        if page and available_capacity < len(remaining) <= fresh_capacity:
            pages.append(page)
            page = []
            y = top
        while remaining:
            capacity = int((y - ROUTE_HEADING_GAP - bottom) // line_height)
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
            y -= ROUTE_HEADING_GAP + len(portion) * line_height + 16
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
    return subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "-C", str(root), *arguments], text=True
    ).strip()


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


def navigation_pdf(path: Path, library: dict[str, Any], targets: dict[str, Any]) -> list[tuple]:
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
        "What should I learn next?",
        "Choose a purpose, check your starting skills, and follow a question.",
    )
    y = (
        paragraph(
            "Three connected books carry one journey from basic operations to "
            "careful advanced reasoning. Each keeps its own purpose and authorship. "
            "The directory and reading-route links open separate PDF books; "
            "their original tables of contents and PDF bookmarks remain available.",
            42,
            y,
            width - 84,
        )
        - 24
    )
    book_map = {book["id"]: book for book in library["books"]}
    for identifier, title, explanation in [
        (
            "precalc",
            "1. " + book_map[node_map["precalc"]["book"]]["title"],
            "Functions and their histories, visual constructions, guided operations, and exercises.",
        ),
        (
            "proof",
            "2. From Precalculus to Mathematical Physics",
            "Bridge lessons with definitions, worked derivations, historical sources, "
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
        document.roundRect(36, y - 69, width - 72, 88, 7, fill=1, stroke=0)
        jump(title, f"book:{node_map[identifier]['book']}", 48, y, 0, 12)
        paragraph(explanation, 48, y - 24, width - 96)
        y -= 102
    for route in library["routes"]:
        identifier = "route:" + route["id"]
        label = f"{route['purpose']}: {route['title']} (p. {targets[identifier]['page']})"
        for line in simpleSplit(label, "Helvetica-Bold", 9, width - 84):
            jump(line, identifier, 42, y, 0, 9)
            y -= 14
        y -= 4
    y -= 8
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
            "Lesson directory", "Open a separate book. The directory lists its PDF page number."
        )
        for node in library["nodes"][start : start + 18]:
            title = node["title"]
            while document.stringWidth(title, "Helvetica-Bold", 10) > width - 132:
                title = title[:-4] + "..."
            jump(title, node["id"], 42, y, page_number, 10)
            document.setFont("Helvetica", 10)
            document.setFillColor(ink)
            document.drawRightString(
                width - 42, y, f"{node['book']}: {targets[node['id']]['page']}"
            )
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
                route_subtitle(route),
            )
            for item in route_page:
                identifier = item["identifier"]
                node = node_map[identifier]
                title = f"{item['index']}. {node['title']}"
                if item["continuation"]:
                    title += " (continued)"
                while (
                    document.stringWidth(title, "Helvetica-Bold", ROUTE_HEADING_SIZE) > width - 104
                ):
                    title = title[:-4] + "..."
                y = item["y"]
                jump(title, identifier, 42, y, page_number, ROUTE_HEADING_SIZE)
                document.setFillColor(ink)
                document.setFont("Helvetica", ROUTE_BODY_SIZE)
                for line_number, line in enumerate(item["lines"]):
                    document.drawString(
                        52, y - ROUTE_HEADING_GAP - line_number * ROUTE_LINE_HEIGHT, line
                    )
            jump(
                "Return to lesson directory (navigation PDF p. 2)",
                "directory",
                42,
                34,
                page_number,
                9,
            )
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
    output = output.resolve()
    for source_root in source_roots.values():
        if output.is_relative_to(source_root):
            raise ValueError("Bundle output lies inside an external source checkout")
    revisions: dict[str, str] = {}
    readers: dict[str, PdfReader] = {}
    source_paths: dict[str, Path] = {}
    dependencies: dict[str, dict[str, str]] = {}
    targets: dict[str, Any] = {}
    books: list[dict[str, Any]] = []
    for book in library["books"]:
        identifier = book["id"]
        root = source_roots[identifier] if book.get("repository") else ROOT
        path = (root / book["pdf"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError(f"Book PDF escapes source checkout: {identifier}")
        if path.is_relative_to(output):
            raise ValueError("Bundle output overlaps an input PDF")
        if not path.is_file():
            raise ValueError(f"Missing built book: {path}")
        actual = git(root, "rev-parse", "HEAD")
        source_dependencies_map = source_dependencies(root, path)
        if book.get("repository"):
            if book.get("edition_manifest"):
                edition_path = (ROOT / book["edition_manifest"]).resolve()
                if not edition_path.is_relative_to(ROOT.resolve()):
                    raise ValueError("Edition manifest escapes repository")
                edition = json.loads(edition_path.read_text())
                if actual != edition["revision"]:
                    raise ValueError(f"{identifier}: revision differs from edition")
                if sha256(path) != edition["pdf_sha256"]:
                    raise ValueError(f"{identifier}: edition PDF hash differs")
                if source_dependencies_map != edition["source_dependencies"]:
                    raise ValueError(f"{identifier}: edition source hashes differ")
                if not edition.get("working_tree") and git(
                    root, "status", "--porcelain", "--untracked-files=no"
                ):
                    raise ValueError(f"{identifier}: tracked source has uncommitted changes")
            else:
                if actual != book["revision"]:
                    raise ValueError(f"{identifier} revision differs")
                if git(root, "status", "--porcelain", "--untracked-files=no"):
                    raise ValueError(f"{identifier}: tracked source has uncommitted changes")
        revisions[identifier] = actual
        dependencies[identifier] = source_dependencies_map
        source_paths[identifier] = path
        reader = PdfReader(path, strict=True)
        if not reader.pages:
            raise ValueError(f"Empty book: {path}")
        readers[identifier] = reader
        titles = outline_pages(reader)
        filename = identifier + ".pdf"
        targets[f"book:{identifier}"] = {
            "book": identifier,
            "file": filename,
            "page": 1,
            "title": book["title"],
        }
        for node in library["nodes"]:
            if node["book"] != identifier:
                continue
            title = node.get("pdf_title")
            pages = [0] if title is None else titles.get(normalize_title(title), [])
            if not pages:
                raise ValueError(f"Missing PDF destination for {node['id']}: {title}")
            if len(pages) != 1:
                raise ValueError(f"Ambiguous PDF destination for {node['id']}: {title}")
            targets[node["id"]] = {
                "book": identifier,
                "file": filename,
                "page": pages[0] + 1,
                "title": title or book["title"],
            }
        books.append(
            {
                "id": identifier,
                "file": filename,
                "pages": len(reader.pages),
                "pdf_sha256": sha256(path),
                "source_dependencies": source_dependencies_map,
                "revision": actual,
                "edition_manifest": book.get("edition_manifest"),
            }
        )
    targets["directory"] = {"file": "navigation.pdf", "page": 2, "title": "Album directory"}
    route_offset = 1 + (len(library["nodes"]) + 17) // 18
    node_map = {node["id"]: node for node in library["nodes"]}
    for route in library["routes"]:
        targets["route:" + route["id"]] = {
            "file": "navigation.pdf",
            "page": route_offset + 1,
            "title": route["title"],
        }
        route_offset += len(route_page_layout(route, node_map))
    managed_files = [book["file"] for book in books] + [
        "navigation.pending.pdf",
        "navigation.pdf",
        "index.html",
        "manifest.json",
    ]
    for filename in managed_files:
        candidate = output / filename
        if candidate.is_symlink() or (candidate.exists() and not candidate.is_file()):
            raise ValueError(f"Managed output must be a regular file: {candidate}")
    output.mkdir(parents=True, exist_ok=True)
    destination_root = output
    with tempfile.TemporaryDirectory(prefix=".album-stage-", dir=output) as staging:
        output = Path(staging)
        for book in books:
            shutil.copyfile(source_paths[book["id"]], output / book["file"])
            if sha256(output / book["file"]) != book["pdf_sha256"]:
                raise ValueError("Copied book hash differs")
        navigation = output / "navigation.pending.pdf"
        links = navigation_pdf(navigation, library, targets)
        writer = PdfWriter()
        writer.append(navigation, import_outline=True)
        if len(writer.pages) != navigation_page_count(library):
            raise ValueError("Navigation page count drifted")
        writer.add_outline_item("Album directory", 1)
        writer.add_outline_item("Reading routes", 1 + (len(library["nodes"]) + 17) // 18)
        for identifier, target in targets.items():
            if target["file"] == "navigation.pdf":
                writer.add_named_destination(identifier, target["page"] - 1)
                if identifier.startswith("route:"):
                    writer.add_outline_item(target["title"], target["page"] - 1)
        for page, rectangle, identifier in links:
            target = targets[identifier]
            if target["file"] == "navigation.pdf":
                action = DictionaryObject(
                    {
                        NameObject("/S"): NameObject("/GoTo"),
                        NameObject("/D"): TextStringObject(identifier),
                    }
                )
            else:
                action = DictionaryObject(
                    {
                        NameObject("/S"): NameObject("/GoToR"),
                        NameObject("/F"): TextStringObject(target["file"]),
                        NameObject("/D"): ArrayObject(
                            [NumberObject(target["page"] - 1), NameObject("/Fit")]
                        ),
                    }
                )
            writer.add_annotation(
                page,
                DictionaryObject(
                    {
                        NameObject("/Type"): NameObject("/Annot"),
                        NameObject("/Subtype"): NameObject("/Link"),
                        NameObject("/Rect"): ArrayObject(
                            [FloatObject(value) for value in rectangle]
                        ),
                        NameObject("/Border"): ArrayObject([NumberObject(0)] * 3),
                        NameObject("/A"): action,
                    }
                ),
            )
        destination = output / "navigation.pdf"
        writer.write(destination)
        check = PdfReader(destination, strict=True)
        for page, rectangle, identifier in links:
            matched = [
                annotation.get_object()
                for annotation in check.pages[page].get("/Annots", [])
                if all(
                    abs(float(value) - expected) < 0.001
                    for value, expected in zip(annotation.get_object()["/Rect"], rectangle)
                )
            ]
            target = targets[identifier]
            if len(matched) != 1:
                raise ValueError(f"Navigation destination failed: {identifier}")
            action = matched[0]["/A"]
            if target["file"] == "navigation.pdf":
                valid = (
                    action["/S"] == "/GoTo"
                    and action["/D"] == identifier
                    and check.get_destination_page_number(check.named_destinations[identifier])
                    == target["page"] - 1
                )
            else:
                valid = (
                    action["/S"] == "/GoToR"
                    and action["/F"] == target["file"]
                    and int(action["/D"][0]) == target["page"] - 1
                )
            if not valid:
                raise ValueError(f"Navigation destination failed: {identifier}")
        navigation.unlink()

        def escape(value: str) -> str:
            return html.escape(value, quote=True)

        node_map = {node["id"]: node for node in library["nodes"]}

        def node_link(identifier: str) -> str:
            return f'<a href="#{escape(identifier)}">{escape(node_map[identifier]["title"])}</a>'

        routes_html = []
        for route in library["routes"]:
            routes_html.append(
                f'<section id="route-{escape(route["id"])}"><h3>{escape(route["title"])}</h3>'
                f"<p><strong>Purpose:</strong> {escape(route['purpose'])}</p>"
                f"<p><strong>Question:</strong> {escape(route['question'])}</p>"
                f"<p><strong>Starting knowledge:</strong> {escape(route['starting_knowledge'])}</p>"
                "<ol>"
                + "".join(f"<li>{node_link(identifier)}</li>" for identifier in route["nodes"])
                + "</ol></section>"
            )
        lessons_html = []
        for node in library["nodes"]:
            target = targets[node["id"]]
            required = (
                ", ".join(node_link(identifier) for identifier in node["requires"]) or "Start here"
            )
            lessons_html.append(
                f'<section id="{escape(node["id"])}"><h3>{escape(node["title"])}</h3>'
                f"<p><strong>Question:</strong> {escape(node['question'])}</p>"
                f"<p><strong>Role:</strong> {escape(node['role'])}</p>"
                f'<p><a href="{escape(target["file"])}#page={target["page"]}">Open lesson PDF</a>'
                f" — {escape(target['book'])}, {escape(target['title'])}, PDF page {target['page']}.</p>"
                f"<p><strong>Required:</strong> {required}</p>"
                "<p><strong>Helpful background:</strong> "
                + escape("; ".join(node["helpful"]))
                + "</p>"
                "<h4>Learning outcomes</h4><ul>"
                + "".join(f"<li>{escape(outcome)}</li>" for outcome in node["outcomes"])
                + "</ul>"
                f"<h4>Entry check</h4><p>{escape(node['entry_check']['prompt'])}</p>"
                f"<details><summary>Entry solution and repair</summary>"
                f"<p>{escape(node['entry_check']['answer'])}</p>"
                f"<p>Repair: {node_link(node['entry_check']['repair'])}</p></details>"
                f"<h4>Practice</h4><p>{escape(node['assessment'])}</p>"
                f"<h4>Readiness check</h4><p>{escape(node['readiness']['prompt'])}</p>"
                f"<details><summary>Readiness solution</summary>"
                f"<p>{escape(node['readiness']['answer'])}</p></details>"
                f"<h4>Quick reference</h4><p><strong>Use:</strong> {escape(node['reference']['use'])}</p>"
                f"<p><strong>Watch:</strong> {escape(node['reference']['watch'])}</p>"
                "<h4>Next and why</h4><ul>"
                + "".join(
                    f"<li>{node_link(item['node'])}: {escape(item['why'])}</li>"
                    for item in node["next"]
                )
                + '</ul><p><a href="#routes">Return to routes</a></p></section>'
            )
        (output / "index.html").write_text(
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            "<title>What should I learn next?</title>"
            "<style>body{font:1.1rem/1.6 system-ui,sans-serif;max-width:70ch;margin:auto;padding:2rem;"
            "color:#18212b;background:white}a{color:#17365d}section{border-top:1px solid #667;"
            "margin-top:2rem;padding-top:1rem}details{padding:.5rem;border-left:3px solid #667}"
            "</style></head><body><main><h1>What should I learn next?</h1>"
            '<p>These books remain separate. Open <a href="navigation.pdf">the route guide PDF</a> '
            "to choose a journey. Return with your reader Back command or reopen index.html. "
            "When a reader ignores a PDF link, open the named file and use its printed PDF page locator.</p>"
            '<h2 id="routes">Choose a reading route</h2>'
            + "".join(routes_html)
            + "<h2>Lesson directory</h2>"
            + "".join(lessons_html)
            + "</main></body></html>\n"
        )
        manifest = {
            "schema_version": 2,
            "library_sha256": sha256(ROOT / "docs/learning/library.json"),
            "navigation_sha256": sha256(destination),
            "index_sha256": sha256(output / "index.html"),
            "pages": len(check.pages),
            "navigation_links_checked": len(links),
            "destinations": targets,
            "books": books,
            "scope": "Separate PDF identity and cross-file destination checks; reader support and factual audits are separate observations.",
        }
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        for filename in managed_files:
            staged = output / filename
            if staged.is_file():
                staged.replace(destination_root / filename)
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
