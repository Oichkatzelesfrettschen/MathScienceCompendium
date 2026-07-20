#!/usr/bin/env python3
"""Decompose retained framework text into traceable ASCII Markdown chunks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE_ROOT = REPO_ROOT / "source_materials" / "frameworks"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "data" / "normalized" / "frameworks"
DEFAULT_REGISTRY = REPO_ROOT / "data" / "registry" / "framework_document_decomposition.json"
DEFAULT_MAX_LINES = 400
MIN_HEADING_ALIGNED_LINES = 250

ATX_HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")
EXPLICIT_HEADING = re.compile(
    r"^\s*(?:chapter|section|part|phase|appendix|document)\b[^\n]{0,180}$",
    flags=re.IGNORECASE,
)
NUMBERED_HEADING = re.compile(r"^\s*(?:\d+(?:\.\d+){0,4}|[IVXLCDM]+)[.):]?\s+[A-Z][^\n]{1,150}$")
UNDERLINE = re.compile(r"^\s*[=-]{3,}\s*$")
URL_PATTERN = re.compile(r"https?://[^\s)>}\]]+")
DOI_PATTERN = re.compile(r"(?:doi:\s*|https?://doi\.org/)(10\.\d{4,9}/[^\s)>}\]]+)", re.I)
ARXIV_PATTERN = re.compile(r"(?:arXiv:)?(\d{4}\.\d{4,5})(?:v\d+)?", re.I)
ISBN_PATTERN = re.compile(r"ISBN(?:-1[03])?:?\s*([0-9Xx -]{10,20})", re.I)
FORMULA_PATTERN = re.compile(
    r"(?:=|\\(?:frac|sum|int|mathcal|mathbb|begin|end|left|right)|[\u2200-\u22ff])"
)

DIRECT_REPLACEMENTS = {
    "\u0002": "fi",
    "\u0003": "fl",
    "\u00a0": " ",
    "\u00b0": " degrees",
    "\u00b1": "+/-",
    "\u00b2": "^2",
    "\u00b3": "^3",
    "\u00b7": "*",
    "\u00b6": "[PARAGRAPH]",
    "\u00bb": ">",
    "\u00d7": "*",
    "\u00f7": "/",
    "\u00c6": "AE",
    "\u00e6": "ae",
    "\u00f8": "o",
    "\u0141": "L",
    "\u0152": "OE",
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "--",
    "\u2015": "--",
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2022": "-",
    "\u2026": "...",
    "\u2039": "<",
    "\u2032": "'",
    "\u2033": '"',
    "\u2044": "/",
    "\u207b": "^-",
    "\u2190": "<-",
    "\u2192": "->",
    "\u2194": "<->",
    "\u21d2": "=>",
    "\u2202": "partial",
    "\u2207": "nabla",
    "\u2208": "in",
    "\u220f": "product",
    "\u2211": "sum",
    "\u2212": "-",
    "\u221d": "proportional to",
    "\u221a": "sqrt",
    "\u221e": "infinity",
    "\u222b": "integral",
    "\u2248": "approximately",
    "\u2260": "!=",
    "\u2264": "<=",
    "\u2265": ">=",
    "\u25a1": "box",
    "\u25cf": "-",
    "\u27e8": "<",
    "\u27e9": ">",
    "\u02c7": "^",
    "\u210f": "hbar",
}

GREEK_REPLACEMENTS = {
    "\u0393": "Gamma",
    "\u0394": "Delta",
    "\u0398": "Theta",
    "\u039b": "Lambda",
    "\u039e": "Xi",
    "\u03a0": "Pi",
    "\u03a3": "Sigma",
    "\u03a6": "Phi",
    "\u03a8": "Psi",
    "\u03a9": "Omega",
    "\u03b1": "alpha",
    "\u03b2": "beta",
    "\u03b3": "gamma",
    "\u03b4": "delta",
    "\u03b5": "epsilon",
    "\u03b6": "zeta",
    "\u03b7": "eta",
    "\u03b8": "theta",
    "\u03b9": "iota",
    "\u03ba": "kappa",
    "\u03bb": "lambda",
    "\u03bc": "mu",
    "\u03bd": "nu",
    "\u03be": "xi",
    "\u03c0": "pi",
    "\u03c1": "rho",
    "\u03c3": "sigma",
    "\u03c4": "tau",
    "\u03c5": "upsilon",
    "\u03c6": "phi",
    "\u03c7": "chi",
    "\u03c8": "psi",
    "\u03c9": "omega",
}

SUBSCRIPT_REPLACEMENTS = {
    "\u2080": "_0",
    "\u2081": "_1",
    "\u2082": "_2",
    "\u2083": "_3",
    "\u2084": "_4",
    "\u2085": "_5",
    "\u2086": "_6",
    "\u2087": "_7",
    "\u2088": "_8",
    "\u2089": "_9",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def ascii_text(text: str, unknown: Counter[str] | None = None) -> str:
    """Return a deterministic ASCII reading view without silent character loss."""
    output: list[str] = []
    replacements = DIRECT_REPLACEMENTS | GREEK_REPLACEMENTS | SUBSCRIPT_REPLACEMENTS
    for character in text:
        codepoint = ord(character)
        if character in "\n\t" or 32 <= codepoint <= 126:
            output.append(character)
            continue
        replacement = replacements.get(character)
        if replacement is not None:
            output.append(replacement)
            continue
        if codepoint < 32 or codepoint == 127:
            token = f"[U+{codepoint:04X}]"
            output.append(token)
            if unknown is not None:
                unknown[token] += 1
            continue
        normalized = unicodedata.normalize("NFKD", character)
        ascii_normalized = normalized.encode("ascii", errors="ignore").decode("ascii")
        if ascii_normalized:
            output.append(ascii_normalized)
            continue
        if unicodedata.category(character) == "Mn":
            continue
        token = f"[U+{codepoint:04X}]"
        output.append(token)
        if unknown is not None:
            unknown[token] += 1
    result = "".join(output)
    result.encode("ascii")
    return result


def normalize_ascii_reading_view(
    text: str,
    unknown: Counter[str] | None = None,
) -> str:
    """Render ASCII prose without source line-end padding or EOF fanout."""
    lines = [line.rstrip() for line in ascii_text(text, unknown).splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + ("\n" if lines else "")


def slugify(value: str) -> str:
    normalized = ascii_text(value).lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "document"


def is_all_caps_heading(line: str) -> bool:
    stripped = ascii_text(line).strip()
    if not 3 <= len(stripped) <= 160 or stripped.startswith(("-", "*")):
        return False
    if re.fullmatch(r"(?:\[U\+[A-F0-9]{4,6}\]\s*)+", stripped):
        return False
    letters = [character for character in stripped if character.isalpha()]
    return len(letters) >= 4 and all(character.isupper() for character in letters)


def heading_for_line(lines: list[str], index: int) -> str | None:
    stripped = lines[index].strip()
    if not stripped:
        return None
    match = ATX_HEADING.match(stripped)
    if match:
        title: str | None = ascii_text(match.group(2)).strip()
    elif (
        index + 1 < len(lines)
        and UNDERLINE.match(lines[index + 1])
        and len(stripped) <= 180
        and not UNDERLINE.match(stripped)
    ):
        title = ascii_text(stripped).strip(" #-\t")
    else:
        title = None
    converted = ascii_text(stripped).strip()
    if (title is None and EXPLICIT_HEADING.match(converted)) or (
        title is None and NUMBERED_HEADING.match(converted) and not converted.endswith(".")
    ):
        title = converted.strip(" #-")
    elif title is None and converted.lower() in {
        "abstract",
        "introduction",
        "conclusion",
        "conclusions",
        "references",
        "bibliography",
        "acknowledgments",
        "acknowledgements",
    }:
        title = converted
    elif title is None and is_all_caps_heading(stripped):
        title = converted.strip(" #-")
    return title


def detect_headings(lines: list[str]) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    for index in range(len(lines)):
        title = heading_for_line(lines, index)
        if title:
            headings.append({"line": index + 1, "title": title[:200]})
    return headings


def select_document_title(
    source_lines: list[str], headings: list[dict[str, Any]], fallback: str
) -> str:
    candidates: list[str] = []
    for line in source_lines[:20]:
        converted = ascii_text(line).strip()
        if not converted or UNDERLINE.match(converted):
            continue
        match = ATX_HEADING.match(converted)
        candidate = match.group(2).strip() if match else converted.strip(" #-").strip()
        if candidate:
            candidates.append(candidate)
    for candidate in candidates:
        if candidate.lower().startswith("title:"):
            return candidate.split(":", maxsplit=1)[1].strip()[:200]
    for candidate in candidates:
        if "framework draft" in candidate.lower() or candidate.startswith("The Unified Model:"):
            return candidate[:200]
    for candidate in candidates:
        if len(candidate) <= 120 and not candidate.lower().startswith("note:"):
            return candidate[:200]
    if headings:
        return str(headings[0]["title"])[:200]
    return ascii_text(fallback)[:200]


def chunk_ranges(
    line_count: int,
    heading_lines: list[int],
    max_lines: int = DEFAULT_MAX_LINES,
) -> list[tuple[int, int]]:
    """Return contiguous one-based ranges, preferring nearby heading boundaries."""
    if line_count == 0:
        return []
    heading_indexes = sorted({line - 1 for line in heading_lines if 1 < line <= line_count})
    ranges: list[tuple[int, int]] = []
    start_index = 0
    while start_index < line_count:
        target_end = min(start_index + max_lines, line_count)
        if target_end < line_count:
            preferred = [
                index
                for index in heading_indexes
                if start_index + MIN_HEADING_ALIGNED_LINES <= index <= target_end
            ]
            end_index = preferred[-1] if preferred else target_end
        else:
            end_index = target_end
        if end_index <= start_index:
            end_index = min(start_index + max_lines, line_count)
        ranges.append((start_index + 1, end_index))
        start_index = end_index
    return ranges


def extract_references(lines: list[str], headings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, int]] = set()

    def add(kind: str, value: str, line_number: int, context: str) -> None:
        key = (kind, value, line_number)
        if key in seen:
            return
        seen.add(key)
        records.append(
            {
                "kind": kind,
                "value": ascii_text(value)[:500],
                "source_line": line_number,
                "context": ascii_text(context.strip())[:500],
            }
        )

    for line_number, line in enumerate(lines, start=1):
        for match in DOI_PATTERN.finditer(line):
            add("doi", match.group(1).rstrip(".,;"), line_number, line)
        for match in URL_PATTERN.finditer(line):
            add("url", match.group(0).rstrip(".,;"), line_number, line)
        for match in ARXIV_PATTERN.finditer(line):
            add("arxiv", match.group(1), line_number, line)
        for match in ISBN_PATTERN.finditer(line):
            add("isbn", re.sub(r"\s+", "", match.group(1)), line_number, line)

    heading_lines = [int(heading["line"]) for heading in headings]
    for heading in headings:
        title = str(heading["title"]).lower()
        if "reference" not in title and "bibliograph" not in title:
            continue
        start = int(heading["line"]) + 1
        later = [line for line in heading_lines if line > start]
        end = later[0] - 1 if later else len(lines)
        for line_number in range(start, end + 1):
            context = lines[line_number - 1].strip()
            if len(context) >= 20 and not UNDERLINE.match(context):
                add("bibliography_line", context, line_number, context)

    return sorted(records, key=lambda record: (record["source_line"], record["kind"]))


def extract_structural_blocks(lines: list[str]) -> dict[str, list[dict[str, Any]]]:
    formulas: list[dict[str, Any]] = []
    table_rows: list[dict[str, Any]] = []
    code_fences: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or UNDERLINE.match(stripped):
            continue
        source_line_sha256 = sha256_bytes(line.encode("utf-8"))
        record = {
            "source_line": line_number,
            "source_line_sha256": source_line_sha256,
            "source_text": stripped,
            "ascii_text": ascii_text(stripped),
        }
        if FORMULA_PATTERN.search(stripped):
            formulas.append(record)
        if stripped.count("|") >= 2:
            table_rows.append(record)
        if stripped.startswith("```"):
            code_fences.append(record)
    return {
        "formula_candidates": formulas,
        "table_row_candidates": table_rows,
        "code_fences": code_fences,
    }


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def render_chunk(
    document_id: str,
    source_relpath: str,
    source_sha256: str,
    source_lines: list[str],
    line_start: int,
    line_end: int,
    chunk_id: str,
    source_chunk_sha256: str,
    unknown: Counter[str],
) -> str:
    source_text = "".join(source_lines[line_start - 1 : line_end])
    normalized = normalize_ascii_reading_view(source_text, unknown)
    header = [
        "---",
        "schema_version: 1",
        f"document_id: {yaml_string(document_id)}",
        f"chunk_id: {yaml_string(chunk_id)}",
        f"source_relpath: {yaml_string(source_relpath)}",
        f"source_sha256: {yaml_string(source_sha256)}",
        f"source_line_start: {line_start}",
        f"source_line_end: {line_end}",
        f"source_chunk_sha256: {yaml_string(source_chunk_sha256)}",
        "normalization: ascii-reading-view-v1",
        "---",
        "",
        f"# {document_id}: lines {line_start}-{line_end}",
        "",
    ]
    return "\n".join(header) + normalized


def render_document_index(document: dict[str, Any]) -> str:
    lines = [
        "---",
        "schema_version: 1",
        f"document_id: {yaml_string(str(document['id']))}",
        f"source_relpath: {yaml_string(str(document['source_relpath']))}",
        f"source_sha256: {yaml_string(str(document['source_sha256']))}",
        "normalization: ascii-reading-view-v1",
        "---",
        "",
        f"# {document['title']}",
        "",
        "The retained source bytes are authoritative. These Markdown files are an",
        "ASCII reading view. Every chunk records its exact source-line range and",
        "the SHA-256 digest of the corresponding UTF-8 source slice.",
        "",
        "## Chunks",
        "",
        "| Chunk | Source lines | Headings | Markdown |",
        "|---|---:|---:|---|",
    ]
    for chunk in document["chunks"]:
        chunk_name = Path(str(chunk["markdown_relpath"])).name
        lines.append(
            f"| {chunk['id']} | {chunk['source_line_start']}-{chunk['source_line_end']} "
            f"| {chunk['heading_count']} | [{chunk_name}]({chunk_name}) |"
        )
    lines.extend(["", "## Heading index", "", "| Source line | Heading |", "|---:|---|"])
    for heading in document["headings"]:
        escaped_title = str(heading["title"]).replace("|", "\\|")
        lines.append(f"| {heading['line']} | {escaped_title} |")
    lines.extend(
        [
            "",
            "## Explicit references",
            "",
            f"See [references.json]({Path(str(document['reference_index_relpath'])).name}) "
            f"for {document['reference_count']} extracted identifiers or bibliography lines.",
            "",
            "## Structural blocks",
            "",
            f"See [structure.json]({Path(str(document['structure_index_relpath'])).name}) "
            f"for {document['formula_candidate_count']} formula candidates, "
            f"{document['table_row_candidate_count']} table-row candidates, and "
            f"{document['code_fence_count']} code fences.",
            "",
        ]
    )
    result = "\n".join(lines)
    result.encode("ascii")
    return result


def render_corpus_index(documents: list[dict[str, Any]]) -> str:
    lines = [
        "# Framework Document Decomposition",
        "",
        "The retained UTF-8 files under source_materials/frameworks are authoritative.",
        "This directory supplies bounded ASCII reading views and separately indexed",
        "headings, explicit references, formulas, table rows, and code fences.",
        "",
        "| Document | Lines | Chunks | Headings | References | Formulas | Tables | Unknown tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for document in documents:
        lines.append(
            f"| [{document['title']}]({document['id']}/README.md) | "
            f"{document['line_count']} | {document['chunk_count']} | "
            f"{document['heading_count']} | {document['reference_count']} | "
            f"{document['formula_candidate_count']} | "
            f"{document['table_row_candidate_count']} | "
            f"{document['unknown_unicode_count']} |"
        )
    lines.append("")
    result = "\n".join(lines)
    result.encode("ascii")
    return result


def relative_to_repo(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def decompose_document(
    source_path: Path,
    output_root: Path,
    max_lines: int,
) -> tuple[dict[str, Any], set[Path]]:
    source_bytes = source_path.read_bytes()
    source_text = source_bytes.decode("utf-8", errors="strict")
    source_lines = source_text.splitlines(keepends=True)
    if source_text and not source_lines:
        source_lines = [source_text]
    source_relpath = relative_to_repo(source_path)
    source_sha256 = sha256_bytes(source_bytes)
    document_id = slugify(source_path.stem)
    document_root = output_root / document_id
    document_root.mkdir(parents=True, exist_ok=True)

    headings = detect_headings(source_lines)
    ranges = chunk_ranges(
        len(source_lines),
        [int(heading["line"]) for heading in headings],
        max_lines=max_lines,
    )
    unknown: Counter[str] = Counter()
    chunks: list[dict[str, Any]] = []
    expected_paths: set[Path] = set()

    for chunk_number, (line_start, line_end) in enumerate(ranges, start=1):
        chunk_id = f"{document_id}-{chunk_number:04d}"
        chunk_filename = f"{chunk_number:04d}-lines-{line_start:06d}-{line_end:06d}.md"
        chunk_path = document_root / chunk_filename
        source_slice = "".join(source_lines[line_start - 1 : line_end]).encode("utf-8")
        source_chunk_sha256 = sha256_bytes(source_slice)
        chunk_markdown = render_chunk(
            document_id,
            source_relpath,
            source_sha256,
            source_lines,
            line_start,
            line_end,
            chunk_id,
            source_chunk_sha256,
            unknown,
        )
        chunk_path.write_text(chunk_markdown, encoding="ascii")
        expected_paths.add(chunk_path)
        heading_count = sum(line_start <= int(heading["line"]) <= line_end for heading in headings)
        chunks.append(
            {
                "id": chunk_id,
                "source_line_start": line_start,
                "source_line_end": line_end,
                "source_chunk_sha256": source_chunk_sha256,
                "markdown_relpath": relative_to_repo(chunk_path),
                "markdown_sha256": sha256_file(chunk_path),
                "markdown_bytes": chunk_path.stat().st_size,
                "heading_count": heading_count,
            }
        )

    references = extract_references(source_lines, headings)
    reference_path = document_root / "references.json"
    reference_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "document_id": document_id,
                "source_relpath": source_relpath,
                "source_sha256": source_sha256,
                "references": references,
            },
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n",
        encoding="ascii",
    )
    expected_paths.add(reference_path)

    structural_blocks = extract_structural_blocks(source_lines)
    structure_path = document_root / "structure.json"
    structure_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "document_id": document_id,
                "source_relpath": source_relpath,
                "source_sha256": source_sha256,
                **structural_blocks,
            },
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
        + "\n",
        encoding="ascii",
    )
    expected_paths.add(structure_path)

    document: dict[str, Any] = {
        "id": document_id,
        "title": select_document_title(source_lines, headings, source_path.stem),
        "source_relpath": source_relpath,
        "source_sha256": source_sha256,
        "source_bytes": len(source_bytes),
        "line_count": len(source_lines),
        "chunk_count": len(chunks),
        "heading_count": len(headings),
        "reference_count": len(references),
        "formula_candidate_count": len(structural_blocks["formula_candidates"]),
        "table_row_candidate_count": len(structural_blocks["table_row_candidates"]),
        "code_fence_count": len(structural_blocks["code_fences"]),
        "unknown_unicode_count": sum(unknown.values()),
        "unknown_unicode": [
            {"token": token, "count": count} for token, count in sorted(unknown.items())
        ],
        "index_relpath": "",
        "index_sha256": "",
        "reference_index_relpath": relative_to_repo(reference_path),
        "reference_index_sha256": sha256_file(reference_path),
        "structure_index_relpath": relative_to_repo(structure_path),
        "structure_index_sha256": sha256_file(structure_path),
        "headings": headings,
        "chunks": chunks,
    }
    index_path = document_root / "README.md"
    document["index_relpath"] = relative_to_repo(index_path)
    index_path.write_text(render_document_index(document), encoding="ascii")
    document["index_sha256"] = sha256_file(index_path)
    expected_paths.add(index_path)
    return document, expected_paths


def build_registry(source_root: Path, output_root: Path, max_lines: int) -> dict[str, Any]:
    source_paths = sorted(source_root.glob("*.txt"))
    documents: list[dict[str, Any]] = []
    expected_paths: set[Path] = set()
    for source_path in source_paths:
        document, document_paths = decompose_document(source_path, output_root, max_lines)
        documents.append(document)
        expected_paths.update(document_paths)

    index_path = output_root / "README.md"
    index_path.write_text(render_corpus_index(documents), encoding="ascii")
    expected_paths.add(index_path)

    if output_root.exists():
        for existing_path in sorted(output_root.rglob("*"), reverse=True):
            if existing_path.is_file() and existing_path not in expected_paths:
                existing_path.unlink()
            elif existing_path.is_dir() and not any(existing_path.iterdir()):
                existing_path.rmdir()

    return {
        "schema_version": 1,
        "generator": "scripts/decompose_framework_documents.py",
        "index_relpath": relative_to_repo(index_path),
        "index_sha256": sha256_file(index_path),
        "policy": {
            "source_authority": "retained UTF-8 source bytes",
            "reading_view": "ASCII transliteration with explicit unknown-codepoint tokens",
            "max_source_lines_per_chunk": max_lines,
            "heading_alignment_minimum_lines": MIN_HEADING_ALIGNED_LINES,
        },
        "document_count": len(documents),
        "source_line_count": sum(int(document["line_count"]) for document in documents),
        "chunk_count": sum(int(document["chunk_count"]) for document in documents),
        "heading_count": sum(int(document["heading_count"]) for document in documents),
        "reference_count": sum(int(document["reference_count"]) for document in documents),
        "formula_candidate_count": sum(
            int(document["formula_candidate_count"]) for document in documents
        ),
        "table_row_candidate_count": sum(
            int(document["table_row_candidate_count"]) for document in documents
        ),
        "code_fence_count": sum(int(document["code_fence_count"]) for document in documents),
        "documents": documents,
    }


def resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    arguments = parser.parse_args()
    if arguments.max_lines < MIN_HEADING_ALIGNED_LINES:
        parser.error(f"--max-lines must be at least {MIN_HEADING_ALIGNED_LINES}")

    source_root = resolve_repo_path(arguments.source_root)
    output_root = resolve_repo_path(arguments.output_root)
    registry_path = resolve_repo_path(arguments.registry)
    output_root.mkdir(parents=True, exist_ok=True)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry = build_registry(source_root, output_root, arguments.max_lines)
    registry_path.write_text(
        json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(
        f"Wrote {relative_to_repo(registry_path)} "
        f"({registry['document_count']} documents, {registry['chunk_count']} chunks, "
        f"{registry['source_line_count']} source lines)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
