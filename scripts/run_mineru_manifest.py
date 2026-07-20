#!/usr/bin/env python3
"""Run pinned MinerU sequentially for every PDF in the external-source manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "data" / "external" / "sources.toml"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "build" / "document_ocr" / "mineru_corpus"
DEFAULT_RUN_REGISTRY = REPO_ROOT / "data" / "registry" / "aligned_research_mineru_run.json"
COMPOSE_RELPATH = "tools/document_ocr/compose.yaml"
MINERU_VERSION = "3.4.4"
BACKEND = "hybrid-engine"
EFFORT = "high"
MODE = "auto"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def expected_outputs(pdf_path: Path, output_root: Path) -> dict[str, Path]:
    stem = pdf_path.stem
    output_directory = output_root / stem / "hybrid_auto"
    return {
        "markdown": output_directory / f"{stem}.md",
        "content_list": output_directory / f"{stem}_content_list.json",
        "content_list_v2": output_directory / f"{stem}_content_list_v2.json",
        "middle": output_directory / f"{stem}_middle.json",
        "model": output_directory / f"{stem}_model.json",
        "layout_pdf": output_directory / f"{stem}_layout.pdf",
        "origin_pdf": output_directory / f"{stem}_origin.pdf",
    }


def outputs_complete(outputs: dict[str, Path]) -> bool:
    return all(path.is_file() and path.stat().st_size > 0 for path in outputs.values())


def output_records(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for role, path in sorted(outputs.items()):
        if not path.is_file():
            continue
        records.append(
            {
                "role": role,
                "relpath": str(path.relative_to(REPO_ROOT)),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return records


def command_for(pdf_path: Path, output_root: Path) -> list[str]:
    container_pdf = Path("/workspace") / pdf_path.relative_to(REPO_ROOT)
    container_output = Path("/workspace") / output_root.relative_to(REPO_ROOT)
    mineru_command = (
        f"mineru -p {container_pdf} -o {container_output} "
        f"-b {BACKEND} --effort {EFFORT} -m {MODE} "
        "--formula true --table true --image-analysis true"
    )
    return [
        "docker",
        "compose",
        "-f",
        COMPOSE_RELPATH,
        "run",
        "--rm",
        "mineru",
        mineru_command,
    ]


def process_source(source: dict[str, Any], output_root: Path, force: bool) -> dict[str, Any]:
    source_id = str(source["id"])
    pdf_path = REPO_ROOT / str(source["target_relpath"])
    outputs = expected_outputs(pdf_path, output_root)
    base_record: dict[str, Any] = {
        "source_id": source_id,
        "source_relpath": str(pdf_path.relative_to(REPO_ROOT)),
        "source_sha256": sha256_file(pdf_path),
        "source_size_bytes": pdf_path.stat().st_size,
    }
    if outputs_complete(outputs) and not force:
        print(f"[complete] {source_id}", flush=True)
        return {**base_record, "status": "complete", "outputs": output_records(outputs)}

    print(f"[running] {source_id}", flush=True)
    result = subprocess.run(command_for(pdf_path, output_root), check=False)
    status = "generated" if result.returncode == 0 and outputs_complete(outputs) else "failed"
    print(f"[{status}] {source_id} returncode={result.returncode}", flush=True)
    return {
        **base_record,
        "status": status,
        "returncode": result.returncode,
        "outputs": output_records(outputs),
    }


def load_pdf_sources(manifest_path: Path) -> list[dict[str, Any]]:
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    sources: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source in manifest.get("sources", []):
        source_id = str(source["id"])
        if source_id in seen_ids:
            raise ValueError(f"duplicate source id: {source_id}")
        seen_ids.add(source_id)
        target_path = REPO_ROOT / str(source["target_relpath"])
        if target_path.suffix.lower() != ".pdf":
            continue
        if not target_path.is_file():
            raise FileNotFoundError(f"missing manifest PDF: {target_path}")
        sources.append(source)
    return sources


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--run-registry", type=Path, default=DEFAULT_RUN_REGISTRY)
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()

    manifest_path = arguments.manifest.resolve()
    output_root = arguments.output_root.resolve()
    run_registry = arguments.run_registry.resolve()
    records = [
        process_source(source, output_root, arguments.force)
        for source in load_pdf_sources(manifest_path)
    ]
    payload = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/run_mineru_manifest.py",
        "manifest_relpath": str(manifest_path.relative_to(REPO_ROOT)),
        "manifest_sha256": sha256_file(manifest_path),
        "engine": {
            "name": "MinerU",
            "version": MINERU_VERSION,
            "backend": BACKEND,
            "effort": EFFORT,
            "mode": MODE,
            "formula": True,
            "table": True,
            "image_analysis": True,
            "execution": "sequential docker compose containers",
        },
        "source_count": len(records),
        "complete_count": sum(record["status"] in {"complete", "generated"} for record in records),
        "failed_count": sum(record["status"] == "failed" for record in records),
        "sources": records,
    }
    run_registry.parent.mkdir(parents=True, exist_ok=True)
    run_registry.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )
    print(f"Wrote {run_registry.relative_to(REPO_ROOT)}", flush=True)
    return 1 if payload["failed_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
