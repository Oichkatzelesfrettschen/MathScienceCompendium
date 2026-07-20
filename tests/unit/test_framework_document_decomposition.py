"""Tests for traceable framework-document decomposition."""

from __future__ import annotations

import json
from collections import Counter

from scripts.decompose_framework_documents import (
    REPO_ROOT,
    ascii_text,
    chunk_ranges,
    detect_headings,
    extract_references,
    extract_structural_blocks,
    normalize_ascii_reading_view,
    select_document_title,
)


def test_ascii_text_transliterates_math_and_marks_unknown_codepoints():
    unknown: Counter[str] = Counter()
    source = "field \u03c6 approaches \u221e beside \u2603 and \x01\n"
    converted = ascii_text(source, unknown)
    assert converted == "field phi approaches infinity beside [U+2603] and [U+0001]\n"
    assert unknown == Counter({"[U+0001]": 1, "[U+2603]": 1})
    converted.encode("ascii")


def test_ascii_reading_view_removes_line_end_padding_and_eof_fanout():
    source = "first line   \nsecond line\t\n\n\n"

    assert normalize_ascii_reading_view(source) == "first line\nsecond line\n"


def test_detect_headings_recognizes_supported_document_styles():
    lines = [
        "## Document: foundations ##\n",
        "\n",
        "SECTION 1: METHODS\n",
        "\n",
        "Introduction\n",
        "------------\n",
        "1.1 Reproducible Evidence\n",
    ]
    headings = detect_headings(lines)
    assert [heading["line"] for heading in headings] == [1, 3, 5, 7]
    assert headings[0]["title"] == "Document: foundations"


def test_document_title_prefers_explicit_framework_identity():
    lines = [
        "----------------\n",
        "Aether Framework Draft v.1\n",
        "Revision 2\n",
        "----------------\n",
    ]
    assert select_document_title(lines, detect_headings(lines), "fallback") == (
        "Aether Framework Draft v.1"
    )


def test_chunk_ranges_cover_every_line_without_overlap():
    ranges = chunk_ranges(1000, [1, 350, 750], max_lines=400)
    assert ranges == [(1, 349), (350, 749), (750, 1000)]
    assert [line for start, end in ranges for line in range(start, end + 1)] == list(range(1, 1001))


def test_extract_references_retains_line_provenance():
    lines = [
        "References\n",
        "----------\n",
        "Doe, Example result, doi:10.1000/example.1\n",
        "See https://arxiv.org/abs/1111.4064 for context.\n",
    ]
    headings = detect_headings(lines)
    references = extract_references(lines, headings)
    kinds = {record["kind"] for record in references}
    assert {"doi", "url", "arxiv", "bibliography_line"} <= kinds
    assert all(record["source_line"] >= 1 for record in references)


def test_extract_structural_blocks_separates_formula_table_and_code_candidates():
    lines = [
        "energy = mass * c^2\n",
        "| term | value |\n",
        "```python\n",
        "plain prose\n",
    ]
    blocks = extract_structural_blocks(lines)
    assert [record["source_line"] for record in blocks["formula_candidates"]] == [1]
    assert [record["source_line"] for record in blocks["table_row_candidates"]] == [2]
    assert [record["source_line"] for record in blocks["code_fences"]] == [3]


def test_live_registry_covers_all_framework_sources_contiguously():
    registry_path = REPO_ROOT / "data/registry/framework_document_decomposition.json"
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    source_paths = sorted((REPO_ROOT / "source_materials/frameworks").glob("*.txt"))
    assert registry["document_count"] == len(source_paths) == 8
    assert (REPO_ROOT / registry["index_relpath"]).read_bytes().isascii()

    for document in registry["documents"]:
        expected_start = 1
        for chunk in document["chunks"]:
            assert chunk["source_line_start"] == expected_start
            markdown_path = REPO_ROOT / chunk["markdown_relpath"]
            assert markdown_path.read_bytes().isascii()
            expected_start = chunk["source_line_end"] + 1
        assert expected_start == document["line_count"] + 1
        structure_path = REPO_ROOT / document["structure_index_relpath"]
        assert structure_path.read_bytes().isascii()
