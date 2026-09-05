"""Exercise real PDF assembly, retained links, and pinned-source failure paths."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest


pytest.importorskip("pypdf")
pytest.importorskip("reportlab")
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "album_assembly", ROOT / "scripts/assemble_learning_album.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def create_pdf(root: Path, title: str) -> None:
    (root / "source.tex").write_text(title)
    document = canvas.Canvas(str(root / "book.pdf"))
    document.bookmarkPage("start")
    document.addOutlineEntry(title, "start")
    document.drawString(50, 750, title)
    document.linkURL("https://example.org/source", (50, 700, 200, 720))
    document.showPage()
    document.drawString(50, 750, "Return to the opening page")
    document.linkAbsolute("Opening", "start", (50, 700, 250, 725))
    document.showPage()
    document.save()
    (root / "book.fls").write_text(f"PWD {root}\nINPUT source.tex\n")


@pytest.fixture
def fixture_album(tmp_path, monkeypatch):
    root = tmp_path / "album"
    external = tmp_path / "external"
    root.mkdir()
    external.mkdir()
    for directory in (root, external):
        subprocess.run(["git", "init", "-q", str(directory)], check=True)
        (directory / ".gitignore").write_text("*.pdf\n*.fls\n")
    create_pdf(root, "Local book")
    create_pdf(external, "External book")
    for directory in (root, external):
        subprocess.run(["git", "-C", str(directory), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(directory),
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )
    revision = MODULE.git(external, "rev-parse", "HEAD")
    library = {
        "schema_version": 1,
        "books": [
            {
                "id": "precalculus",
                "title": "External book",
                "entry": "source.tex",
                "pdf": "book.pdf",
                "repository": "https://example.org/book",
                "revision": revision,
            },
            {"id": "bridge", "title": "Local book", "entry": "source.tex", "pdf": "book.pdf"},
        ],
        "nodes": [
            {
                "id": "precalc",
                "title": "External book",
                "book": "precalculus",
                "source": "source.tex",
                "pdf_title": None,
                "requires": [],
                "assessment": "Compute.",
            },
            {
                "id": "proof",
                "title": "Local book",
                "book": "bridge",
                "source": "source.tex",
                "pdf_title": "Local book",
                "requires": ["precalc"],
                "assessment": "Prove.",
            },
            {
                "id": "review_evidence",
                "title": "Local book",
                "book": "bridge",
                "source": "source.tex",
                "pdf_title": "Local book",
                "requires": ["proof"],
                "assessment": "Compare.",
            },
        ],
        "routes": [
            {
                "id": "route",
                "title": "Fixture route",
                "nodes": ["precalc", "proof", "review_evidence"],
            }
        ],
    }
    manifest = root / "docs/learning/library.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(json.dumps(library))
    monkeypatch.setattr(MODULE, "ROOT", root)
    return root, external, library


def test_roundtrip_preserves_links_and_routes(fixture_album):
    root, external, library = fixture_album
    result = MODULE.assemble(library, external, root / "output")
    reader = PdfReader(root / "output/album.pdf")
    assert len(reader.pages) == result["pages"] == 7
    assert result["navigation_links_checked"] == 9
    assert result["destinations"]["proof"] == 6
    assert reader.pages[-2]["/Annots"][0].get_object()["/A"]["/URI"] == "https://example.org/source"


def test_internal_links_stay_with_their_source_book(fixture_album):
    root, external, library = fixture_album
    MODULE.assemble(library, external, root / "output")
    reader = PdfReader(root / "output/album.pdf")
    for source_page, expected_destination in ((4, 3), (6, 5)):
        destination = reader.pages[source_page]["/Annots"][0].get_object()["/Dest"]
        assert reader.get_page_number(destination[0].get_object()) == expected_destination


def test_wrong_revision_and_dirty_source_fail(fixture_album):
    root, external, library = fixture_album
    revision = library["books"][0]["revision"]
    library["books"][0]["revision"] = "0" * 40
    with pytest.raises(ValueError, match="revision differs"):
        MODULE.assemble(library, external, root / "output")
    library["books"][0]["revision"] = revision
    (external / "source.tex").write_text("modified")
    with pytest.raises(ValueError, match="uncommitted"):
        MODULE.assemble(library, external, root / "output")


def test_stale_pdf_and_missing_recorder_fail(fixture_album):
    root, external, library = fixture_album
    (root / "book.fls").unlink()
    with pytest.raises(ValueError, match="input recorder"):
        MODULE.assemble(library, external, root / "output")
    (root / "book.fls").write_text(f"PWD {root}\nINPUT source.tex\n")
    time.sleep(0.01)
    (root / "source.tex").write_text("Local book with newer source")
    with pytest.raises(ValueError, match="older than its input"):
        MODULE.assemble(library, external, root / "output")


def test_recorded_bibliography_tracks_origin_and_rejects_staleness(fixture_album):
    root, _, _ = fixture_album
    (root / "references.bib").write_text("@book{sample,title={Sample}}")
    (root / "book.bbl").write_text("Sample bibliography")
    (root / "book.aux").write_text(r"\bibdata{references}" + "\n")
    create_pdf(root, "Local book")
    with (root / "book.fls").open("a") as recorder:
        recorder.write("INPUT book.bbl\n")
    dependencies = MODULE.source_dependencies(root, root / "book.pdf")
    assert "book.bbl" in dependencies
    assert "references.bib" in dependencies
    time.sleep(0.01)
    (root / "references.bib").write_text("@book{sample,title={Corrected title}}")
    with pytest.raises(ValueError, match="older than its input"):
        MODULE.source_dependencies(root, root / "book.pdf")


def test_recorded_missing_input_and_missing_bibliography_origin_fail(fixture_album):
    root, _, _ = fixture_album
    with (root / "book.fls").open("a") as recorder:
        recorder.write("INPUT removed-figure.png\n")
    with pytest.raises(ValueError, match="Missing recorded source input"):
        MODULE.source_dependencies(root, root / "book.pdf")
    (root / "book.bbl").write_text("Sample bibliography")
    create_pdf(root, "Local book")
    with (root / "book.fls").open("a") as recorder:
        recorder.write("INPUT book.bbl\n")
    with pytest.raises(ValueError, match="Missing bibliography origin"):
        MODULE.source_dependencies(root, root / "book.pdf")


def test_latexmk_bibliography_origin_is_retained(fixture_album):
    root, _, _ = fixture_album
    (root / "references.bib").write_text("@book{sample,title={Sample}}")
    (root / "book.bbl").write_text("Sample bibliography")
    (root / "book.fdb_latexmk").write_text('  "references.bib" 100 200 "checksum" ""\n')
    create_pdf(root, "Local book")
    with (root / "book.fls").open("a") as recorder:
        recorder.write("INPUT book.bbl\n")
    assert "references.bib" in MODULE.source_dependencies(root, root / "book.pdf")


def test_missing_external_lesson_source_is_rejected(fixture_album):
    root, external, library = fixture_album
    library["nodes"][0]["source"] = "missing-external-lesson.tex"
    with pytest.raises(ValueError, match="missing source"):
        MODULE.assemble(library, external, root / "output")


def test_assessments_paginate_by_measured_height(fixture_album):
    root, external, library = fixture_album
    for node in library["nodes"]:
        node["assessment"] = "Explain each assumption and justify the complete calculation. " * 180
    node_map = {node["id"]: node for node in library["nodes"]}
    pages = MODULE.route_page_layout(library["routes"][0], node_map)
    assert len(pages) > 3
    for page in pages:
        for item in page:
            assert item["y"] - 17 - (len(item["lines"]) - 1) * 9 * 1.45 >= 60
    for node in library["nodes"]:
        actual_lines = [
            line
            for page in pages
            for item in page
            if item["identifier"] == node["id"]
            for line in item["lines"]
        ]
        expected_lines = MODULE.simpleSplit(node["assessment"], "Helvetica", 9, MODULE.A4[0] - 104)
        assert actual_lines == expected_lines
    result = MODULE.assemble(library, external, root / "output")
    reader = PdfReader(root / "output/album.pdf")
    assert len(reader.pages) == MODULE.navigation_page_count(library) + 4
    assert result["destinations"]["precalc"] == MODULE.navigation_page_count(library) + 1
    for page in reader.pages[: MODULE.navigation_page_count(library)]:
        for annotation in page.get("/Annots", []):
            assert float(annotation.get_object()["/Rect"][1]) >= 0


def create_pdf_with_duplicate_outlines(root: Path) -> None:
    (root / "source.tex").write_text("Local book and Worked example")
    document = canvas.Canvas(str(root / "book.pdf"))
    for index in range(2):
        document.bookmarkPage(f"page{index}")
        if index == 0:
            document.bookmarkPage("local-start")
            document.addOutlineEntry("Local book", "local-start")
        document.addOutlineEntry("Worked example", f"page{index}")
        document.drawString(50, 750, "Worked example")
        document.showPage()
    document.save()
    (root / "book.fls").write_text(f"PWD {root}\nINPUT source.tex\n")


def test_only_referenced_ambiguous_outline_titles_are_rejected(fixture_album):
    root, external, library = fixture_album
    create_pdf_with_duplicate_outlines(root)
    MODULE.assemble(library, external, root / "output")
    library["nodes"][1]["pdf_title"] = "Worked example"
    with pytest.raises(ValueError, match="Ambiguous PDF destination"):
        MODULE.assemble(library, external, root / "ambiguous-output")


def test_additional_external_book_keeps_source_and_internal_destination(fixture_album):
    root, external, library = fixture_album
    extra_book = dict(library["books"][0], id="another_book", title="Another external book")
    library["books"].append(extra_book)
    library["nodes"].append(
        {
            "id": "another_lesson",
            "title": "Another lesson",
            "book": "another_book",
            "source": "source.tex",
            "pdf_title": "External book",
            "requires": ["precalc"],
            "assessment": "Compute the same example through another source book.",
        }
    )
    library["routes"][0]["nodes"].append("another_lesson")
    result = MODULE.assemble(
        library, external, root / "output", additional_roots={"another_book": external}
    )
    reader = PdfReader(root / "output/album.pdf")
    destination = reader.pages[-1]["/Annots"][0].get_object()["/Dest"]
    assert reader.get_page_number(destination[0].get_object()) == len(reader.pages) - 2
    assert result["destinations"]["another_lesson"] == len(reader.pages) - 1
    assert result["books"][-1]["source_dependencies"] == {
        "source.tex": MODULE.sha256(external / "source.tex")
    }


def test_duplicate_pdf_dictionary_keys_fail_source_admission(fixture_album):
    root, external, library = fixture_album
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
        b"/Group << /S /Transparency >> /Group << /S /Transparency >> >>",
    ]
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, content in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{number} 0 obj\n".encode() + content + b"\nendobj\n")
    cross_reference = len(document)
    document.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode())
    document.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{cross_reference}\n%%EOF\n".encode()
    )
    (root / "book.pdf").write_bytes(document)
    with pytest.raises(PdfReadError, match="Multiple definitions"):
        MODULE.assemble(library, external, root / "output")
