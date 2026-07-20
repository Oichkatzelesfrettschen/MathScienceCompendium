#!/usr/bin/env python3
"""Measure exact normalized overlap across retained framework documents."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


try:
    from scripts.decompose_framework_documents import REPO_ROOT, ascii_text
except ModuleNotFoundError:
    from decompose_framework_documents import REPO_ROOT, ascii_text


DEFAULT_DECOMPOSITION_REGISTRY = (
    REPO_ROOT / "data" / "registry" / "framework_document_decomposition.json"
)
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "framework_overlap_audit.json"
DEFAULT_REPORT = REPO_ROOT / "docs" / "framework" / "FRAMEWORK_OVERLAP_AUDIT.md"
MIN_BLOCK_CHARACTERS = 80
EXCERPT_CHARACTERS = 240


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def normalize_block(text: str) -> str:
    converted = ascii_text(text).lower()
    converted = re.sub(r"\[u\+[0-9a-f]{4,6}\]", " ", converted)
    converted = re.sub(r"[^a-z0-9]+", " ", converted)
    return " ".join(converted.split())


def extract_blocks(lines: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    start_index: int | None = None
    buffered_lines: list[str] = []

    def emit(end_index: int) -> None:
        nonlocal start_index, buffered_lines
        if start_index is None:
            return
        source_text = "".join(buffered_lines).strip()
        normalized = normalize_block(source_text)
        if len(normalized) >= MIN_BLOCK_CHARACTERS:
            blocks.append(
                {
                    "source_line_start": start_index + 1,
                    "source_line_end": end_index,
                    "normalized_characters": len(normalized),
                    "normalized_sha256": sha256_text(normalized),
                    "excerpt": ascii_text(source_text)[:EXCERPT_CHARACTERS].replace("\n", " "),
                }
            )
        start_index = None
        buffered_lines = []

    for index, line in enumerate(lines):
        if line.strip():
            if start_index is None:
                start_index = index
            buffered_lines.append(line)
        else:
            emit(index)
    emit(len(lines))
    return blocks


def ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def pairwise_records(
    document_hashes: dict[str, set[str]],
    heading_hashes: dict[str, set[str]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    document_ids = sorted(document_hashes)
    for left_index, left_id in enumerate(document_ids):
        for right_id in document_ids[left_index + 1 :]:
            left = document_hashes[left_id]
            right = document_hashes[right_id]
            shared = left & right
            union = left | right
            left_headings = heading_hashes[left_id]
            right_headings = heading_hashes[right_id]
            shared_headings = left_headings & right_headings
            heading_union = left_headings | right_headings
            records.append(
                {
                    "left_document_id": left_id,
                    "right_document_id": right_id,
                    "shared_block_count": len(shared),
                    "block_jaccard": ratio(len(shared), len(union)),
                    "left_block_containment": ratio(len(shared), len(left)),
                    "right_block_containment": ratio(len(shared), len(right)),
                    "shared_heading_count": len(shared_headings),
                    "heading_jaccard": ratio(len(shared_headings), len(heading_union)),
                }
            )
    return sorted(
        records,
        key=lambda record: (
            -max(record["left_block_containment"], record["right_block_containment"]),
            -record["shared_block_count"],
            record["left_document_id"],
            record["right_document_id"],
        ),
    )


def build_audit(registry_path: Path) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="ascii"))
    occurrences_by_hash: dict[str, list[dict[str, Any]]] = defaultdict(list)
    block_characters: dict[str, int] = {}
    block_excerpts: dict[str, str] = {}
    document_hashes: dict[str, set[str]] = {}
    heading_hashes: dict[str, set[str]] = {}
    documents: list[dict[str, Any]] = []

    for document in registry["documents"]:
        document_id = document["id"]
        source_path = REPO_ROOT / document["source_relpath"]
        lines = source_path.read_text(encoding="utf-8").splitlines(keepends=True)
        blocks = extract_blocks(lines)
        hashes = {block["normalized_sha256"] for block in blocks}
        document_hashes[document_id] = hashes
        normalized_headings = {
            normalize_block(heading["title"])
            for heading in document["headings"]
            if len(normalize_block(heading["title"])) >= 12
        }
        heading_hashes[document_id] = {sha256_text(value) for value in normalized_headings}
        for block in blocks:
            block_hash = block["normalized_sha256"]
            block_characters[block_hash] = block["normalized_characters"]
            block_excerpts[block_hash] = block["excerpt"]
            occurrences_by_hash[block_hash].append(
                {
                    "document_id": document_id,
                    "source_line_start": block["source_line_start"],
                    "source_line_end": block["source_line_end"],
                }
            )
        documents.append(
            {
                "id": document_id,
                "title": document["title"],
                "source_relpath": document["source_relpath"],
                "source_sha256": document["source_sha256"],
                "eligible_block_occurrences": len(blocks),
                "unique_block_hashes": len(hashes),
                "duplicate_occurrences_within_document": len(blocks) - len(hashes),
                "unique_heading_hashes": len(heading_hashes[document_id]),
            }
        )

    duplicate_groups: list[dict[str, Any]] = []
    for block_hash, occurrences in occurrences_by_hash.items():
        if len(occurrences) < 2:
            continue
        document_ids = sorted({occurrence["document_id"] for occurrence in occurrences})
        duplicate_groups.append(
            {
                "normalized_sha256": block_hash,
                "normalized_characters": block_characters[block_hash],
                "occurrence_count": len(occurrences),
                "document_count": len(document_ids),
                "document_ids": document_ids,
                "cross_document": len(document_ids) > 1,
                "excerpt": block_excerpts[block_hash],
                "occurrences": sorted(
                    occurrences,
                    key=lambda occurrence: (
                        occurrence["document_id"],
                        occurrence["source_line_start"],
                    ),
                ),
            }
        )
    duplicate_groups.sort(
        key=lambda group: (
            -group["normalized_characters"] * (group["occurrence_count"] - 1),
            group["normalized_sha256"],
        )
    )

    return {
        "schema_version": 1,
        "generator": "scripts/analyze_framework_overlap.py",
        "normalization": {
            "id": "ascii-lowercase-alphanumeric-whitespace-v1",
            "minimum_block_characters": MIN_BLOCK_CHARACTERS,
            "block_boundary": "blank-line-delimited paragraph",
        },
        "source_registry_relpath": str(registry_path.relative_to(REPO_ROOT)),
        "source_registry_sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest(),
        "document_count": len(documents),
        "documents": documents,
        "duplicate_group_count": len(duplicate_groups),
        "cross_document_duplicate_group_count": sum(
            1 for group in duplicate_groups if group["cross_document"]
        ),
        "duplicate_groups": duplicate_groups,
        "pairwise_overlap": pairwise_records(document_hashes, heading_hashes),
    }


def render_report(audit: dict[str, Any]) -> str:
    lines = [
        "# Framework Overlap Audit",
        "",
        "This report measures exact normalized paragraph overlap. It does not infer",
        "semantic equivalence. Every occurrence retains its source document and line range.",
        "",
        "## Document Summary",
        "",
        "| Document | Blocks | Unique | Repeated | Headings |",
        "|---|---:|---:|---:|---:|",
    ]
    for document in audit["documents"]:
        lines.append(
            f"| {document['id']} | {document['eligible_block_occurrences']} | "
            f"{document['unique_block_hashes']} | "
            f"{document['duplicate_occurrences_within_document']} | "
            f"{document['unique_heading_hashes']} |"
        )
    lines.extend(
        [
            "",
            "## Pairwise Overlap",
            "",
            "Containment is shared unique blocks divided by one document's unique blocks.",
            "",
            "| Left | Right | Shared blocks | Left containment | Right containment | Shared headings |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for record in audit["pairwise_overlap"]:
        lines.append(
            f"| {record['left_document_id']} | {record['right_document_id']} | "
            f"{record['shared_block_count']} | {record['left_block_containment']:.3f} | "
            f"{record['right_block_containment']:.3f} | {record['shared_heading_count']} |"
        )
    lines.extend(
        [
            "",
            "## Largest Exact Duplicate Groups",
            "",
            "| Characters | Occurrences | Documents | Excerpt |",
            "|---:|---:|---:|---|",
        ]
    )
    for group in audit["duplicate_groups"][:40]:
        excerpt = group["excerpt"].replace("|", "\\|")
        lines.append(
            f"| {group['normalized_characters']} | {group['occurrence_count']} | "
            f"{group['document_count']} | {excerpt} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "Exact overlap is safe to collapse into one canonical span with aliases.",
            "Heading overlap only nominates semantic-review candidates. It does not",
            "authorize merging equations, definitions, or physical claims.",
            "",
        ]
    )
    report = "\n".join(lines)
    report.encode("ascii")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_DECOMPOSITION_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    arguments = parser.parse_args()

    audit = build_audit(arguments.registry.resolve())
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.report.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    arguments.report.write_text(render_report(audit), encoding="ascii")
    print(f"Wrote {arguments.output.relative_to(REPO_ROOT)}")
    print(f"Wrote {arguments.report.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
