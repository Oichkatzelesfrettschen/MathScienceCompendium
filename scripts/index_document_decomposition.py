#!/usr/bin/env python3
"""Index MinerU document decompositions with source and output provenance."""

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
DEFAULT_DECOMPOSITION_ROOT = REPO_ROOT / "build" / "document_ocr" / "mineru_corpus"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "document_decomposition_audit.json"
DEFAULT_RUN_MANIFEST = (
    REPO_ROOT / "data" / "registry" / "aligned_research_mineru_run.json"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as input_file:
        for chunk in iter(lambda: input_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_page_count(path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"pdfinfo did not report pages for {path}")
    return int(match.group(1))


def document_record(pdf_path: Path, decomposition_root: Path) -> dict[str, Any]:
    document_root = decomposition_root / pdf_path.stem
    markdown_candidates = sorted(document_root.glob(f"*/{pdf_path.stem}.md"))
    content_list_candidates = sorted(
        document_root.glob(f"*/{pdf_path.stem}_content_list.json")
    )
    if len(markdown_candidates) != 1:
        raise ValueError(
            f"expected one MinerU Markdown output for {pdf_path.name}, "
            f"found {len(markdown_candidates)}"
        )
    if len(content_list_candidates) != 1:
        raise ValueError(
            f"expected one MinerU content list for {pdf_path.name}, "
            f"found {len(content_list_candidates)}"
        )
    markdown_path = markdown_candidates[0]
    content_list_path = content_list_candidates[0]
    markdown_text = markdown_path.read_text(encoding="utf-8", errors="replace")
    content_list = json.loads(content_list_path.read_text(encoding="utf-8"))
    if not isinstance(content_list, list):
        raise ValueError(f"MinerU content list is not an array: {content_list_path}")
    content_type_counts: dict[str, int] = {}
    for item in content_list:
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            raise ValueError(f"MinerU content item lacks a type: {content_list_path}")
        item_type = item["type"]
        content_type_counts[item_type] = content_type_counts.get(item_type, 0) + 1
    artifacts = [path for path in document_root.rglob("*") if path.is_file()]
    return {
        "source_relpath": pdf_path.relative_to(REPO_ROOT).as_posix(),
        "source_sha256": sha256_file(pdf_path),
        "page_count": pdf_page_count(pdf_path),
        "markdown_relpath": markdown_path.relative_to(REPO_ROOT).as_posix(),
        "markdown_sha256": sha256_file(markdown_path),
        "markdown_bytes": markdown_path.stat().st_size,
        "markdown_nonspace_characters": len(re.sub(r"\s", "", markdown_text)),
        "content_list_relpath": content_list_path.relative_to(REPO_ROOT).as_posix(),
        "content_list_sha256": sha256_file(content_list_path),
        "content_item_count": len(content_list),
        "content_type_counts": dict(sorted(content_type_counts.items())),
        "artifact_file_count": len(artifacts),
        "artifact_bytes": sum(path.stat().st_size for path in artifacts),
    }


def build_audit(
    pdf_root: Path,
    decomposition_root: Path,
    run_manifest_path: Path,
) -> dict[str, Any]:
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    if run_manifest.get("failed_count") != 0:
        raise ValueError("MinerU run registry contains failed sources")
    pdf_paths = sorted(pdf_root.glob("*.pdf"))
    run_source_paths = {
        str(source["source_relpath"])
        for source in run_manifest.get("sources", [])
        if isinstance(source, dict) and source.get("status") in {"complete", "generated"}
    }
    live_source_paths = {path.relative_to(REPO_ROOT).as_posix() for path in pdf_paths}
    if run_source_paths != live_source_paths:
        missing = sorted(live_source_paths - run_source_paths)
        extra = sorted(run_source_paths - live_source_paths)
        raise ValueError(
            f"MinerU run registry does not match the live PDF corpus: "
            f"missing={missing}, extra={extra}"
        )
    engine = run_manifest["engine"]
    documents = [document_record(pdf_path, decomposition_root) for pdf_path in pdf_paths]
    content_type_counts: dict[str, int] = {}
    for document in documents:
        for item_type, count in document["content_type_counts"].items():
            content_type_counts[item_type] = content_type_counts.get(item_type, 0) + count
    return {
        "schema_version": 1,
        "generator": "scripts/index_document_decomposition.py",
        "run_manifest": {
            "relpath": run_manifest_path.relative_to(REPO_ROOT).as_posix(),
            "sha256": sha256_file(run_manifest_path),
        },
        "engine": {
            "name": engine["name"],
            "version": engine["version"],
            "backend": engine["backend"],
            "effort": engine["effort"],
            "mode": engine["mode"],
            "formula": engine["formula"],
            "table": engine["table"],
            "image_analysis": engine["image_analysis"],
        },
        "document_count": len(documents),
        "page_count": sum(document["page_count"] for document in documents),
        "content_type_counts": dict(sorted(content_type_counts.items())),
        "documents": documents,
    }


def resolve_repo_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-root", type=Path, default=DEFAULT_PDF_ROOT)
    parser.add_argument("--decomposition-root", type=Path, default=DEFAULT_DECOMPOSITION_ROOT)
    parser.add_argument("--run-manifest", type=Path, default=DEFAULT_RUN_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    audit = build_audit(
        resolve_repo_path(arguments.pdf_root),
        resolve_repo_path(arguments.decomposition_root),
        resolve_repo_path(arguments.run_manifest),
    )
    output_path = resolve_repo_path(arguments.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(audit, indent=2, sort_keys=True, allow_nan=False, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(
        f"Wrote {output_path.relative_to(REPO_ROOT)} "
        f"({audit['document_count']} documents, {audit['page_count']} pages)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
