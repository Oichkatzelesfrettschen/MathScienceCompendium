#!/usr/bin/env python3
"""Generate a focused duplicate report for normalized corpus and registry."""

from __future__ import annotations

import json
import tomllib
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "data" / "registry" / "corpus_index.toml"
REPORT_PATH = REPO_ROOT / "data" / "registry" / "corpus_dedupe_report.toml"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def write_report(
    docs: list[dict[str, object]],
    duplicate_groups: list[list[dict[str, object]]],
    hash_mismatches: list[str],
) -> None:
    duplicate_documents = sum(len(group) for group in duplicate_groups)
    status = "clean" if not duplicate_groups and not hash_mismatches else "attention_required"

    lines: list[str] = []
    lines.append('generated_by = "scripts/corpus_dedupe_report.py"')
    lines.append(f'generated_at_utc = "{now_utc_iso()}"')
    lines.append(f'registry_relpath = "{REGISTRY_PATH.relative_to(REPO_ROOT).as_posix()}"')
    lines.append(f"documents_total = {len(docs)}")
    lines.append(f"exact_duplicate_groups = {len(duplicate_groups)}")
    lines.append(f"exact_duplicate_documents = {duplicate_documents}")
    lines.append(f"hash_mismatch_count = {len(hash_mismatches)}")
    lines.append(f'status = "{status}"')
    lines.append(
        'reconciliation_actions = ["Excluded generated *.egg-info/*.txt files from normalization.", "Excluded generated data/external/fetch_traces/*.txt files from normalization.", "Removed stale normalized JSON files that no longer map to corpus index entries."]'
    )
    lines.append("")

    for mismatch in hash_mismatches:
        lines.append("[[hash_mismatches]]")
        lines.append(f'message = "{toml_escape(mismatch)}"')
        lines.append("")

    for group in duplicate_groups:
        canonical = sorted(group, key=lambda d: str(d["source_relpath"]))[0]
        lines.append("[[duplicate_groups]]")
        lines.append(f'sha256 = "{canonical["sha256"]}"')
        lines.append(f"count = {len(group)}")
        lines.append(f'canonical_source_relpath = "{canonical["source_relpath"]}"')
        lines.append('recommended_action = "Keep canonical source and mark remaining entries as duplicates in claims/evidence docs if retained intentionally."')
        source_paths = ", ".join(f'"{toml_escape(str(item["source_relpath"]))}"' for item in sorted(group, key=lambda d: str(d["source_relpath"])))
        normalized_paths = ", ".join(
            f'"{toml_escape(str(item["normalized_relpath"]))}"' for item in sorted(group, key=lambda d: str(d["normalized_relpath"]))
        )
        lines.append(f"source_relpaths = [{source_paths}]")
        lines.append(f"normalized_relpaths = [{normalized_paths}]")
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    data = tomllib.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    docs = data.get("documents", [])
    if not isinstance(docs, list):
        raise SystemExit("Invalid corpus registry format: expected [[documents]] list")

    by_sha: dict[str, list[dict[str, object]]] = defaultdict(list)
    hash_mismatches: list[str] = []

    for doc in docs:
        sha = str(doc.get("sha256", ""))
        source_relpath = str(doc.get("source_relpath", ""))
        normalized_relpath = str(doc.get("normalized_relpath", ""))
        if not sha or not source_relpath or not normalized_relpath:
            hash_mismatches.append(f"registry entry missing required fields: {doc}")
            continue

        normalized_path = REPO_ROOT / normalized_relpath
        if not normalized_path.exists():
            hash_mismatches.append(f"normalized file missing: {normalized_relpath}")
            continue

        record = json.loads(normalized_path.read_text(encoding="utf-8"))
        record_sha = str(record.get("sha256", ""))
        if record_sha != sha:
            hash_mismatches.append(
                f"sha mismatch for {source_relpath}: registry={sha} normalized={record_sha}"
            )
        by_sha[sha].append(doc)

    duplicate_groups = [group for group in by_sha.values() if len(group) > 1]
    duplicate_groups.sort(key=lambda group: (-len(group), str(group[0]["sha256"])))

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_report(docs=docs, duplicate_groups=duplicate_groups, hash_mismatches=hash_mismatches)

    print(f"Wrote dedupe report: {REPORT_PATH.relative_to(REPO_ROOT).as_posix()}")
    print(f"Documents analyzed: {len(docs)}")
    print(f"Exact duplicate groups: {len(duplicate_groups)}")
    print(f"Hash mismatches: {len(hash_mismatches)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
