#!/usr/bin/env python3
"""Normalize all repository .txt files into deterministic JSON records."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "normalized" / "corpus"
REGISTRY = REPO_ROOT / "data" / "registry" / "corpus_index.toml"

EXCLUDED_PREFIXES = {
    ".git/",
    "build/",
    "data/normalized/",
    "data/external/fetch_traces/",
    "venv/",
    ".venv/",
}
EXCLUDED_SUBSTRINGS = {
    ".egg-info/",
}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slug_from_relpath(relpath: str) -> str:
    base = relpath.removesuffix(".txt")
    slug = base.replace("/", "__").replace(" ", "_")
    slug = slug.replace(".", "_")
    return slug.lower()


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:200]
    return ""


def category_for(relpath: str) -> str:
    parts = relpath.split("/")
    return parts[0] if parts else "repo"


def should_include(relpath: str) -> bool:
    for prefix in EXCLUDED_PREFIXES:
        if relpath.startswith(prefix):
            return False
    for marker in EXCLUDED_SUBSTRINGS:
        if marker in relpath:
            return False
    return relpath.endswith(".txt")


def to_toml(entries: list[dict[str, str | int]]) -> str:
    lines: list[str] = []
    lines.append('generated_by = "scripts/normalize_txt_to_json.py"')
    lines.append(f'generated_at_utc = "{now_utc_iso()}"')
    lines.append("")
    for entry in entries:
        lines.append("[[documents]]")
        lines.append(f"id = {json.dumps(entry['id'], ensure_ascii=True)}")
        lines.append(f"source_relpath = {json.dumps(entry['source_relpath'], ensure_ascii=True)}")
        lines.append(
            f"normalized_relpath = {json.dumps(entry['normalized_relpath'], ensure_ascii=True)}"
        )
        lines.append(f"category = {json.dumps(entry['category'], ensure_ascii=True)}")
        lines.append(f"sha256 = {json.dumps(entry['sha256'], ensure_ascii=True)}")
        lines.append(f"line_count = {entry['line_count']}")
        lines.append(f"size_bytes = {entry['size_bytes']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)

    txt_paths: list[Path] = []
    for path in REPO_ROOT.rglob("*.txt"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if should_include(rel):
            txt_paths.append(path)

    txt_paths.sort(key=lambda p: p.relative_to(REPO_ROOT).as_posix())

    entries: list[dict[str, str | int]] = []
    seen_output_paths: set[Path] = set()

    for txt_path in txt_paths:
        rel = txt_path.relative_to(REPO_ROOT).as_posix()
        text = txt_path.read_text(encoding="utf-8", errors="replace")
        doc_id = slug_from_relpath(rel)
        out_path = OUT_DIR / f"{doc_id}.json"

        # Resolve rare collisions deterministically.
        suffix = 1
        while out_path in seen_output_paths:
            out_path = OUT_DIR / f"{doc_id}_{suffix}.json"
            suffix += 1
        seen_output_paths.add(out_path)

        line_count = text.count("\n") + (0 if text == "" else 1)
        record = {
            "id": out_path.stem,
            "source_relpath": rel,
            "category": category_for(rel),
            "title": first_nonempty_line(text),
            "generated_at_utc": now_utc_iso(),
            "sha256": sha256_text(text),
            "size_bytes": len(text.encode("utf-8")),
            "line_count": line_count,
            "content": text,
        }
        out_path.write_text(
            json.dumps(record, indent=2, sort_keys=True, ensure_ascii=True),
            encoding="utf-8",
        )

        entries.append(
            {
                "id": record["id"],
                "source_relpath": rel,
                "normalized_relpath": out_path.relative_to(REPO_ROOT).as_posix(),
                "category": record["category"],
                "sha256": record["sha256"],
                "line_count": line_count,
                "size_bytes": record["size_bytes"],
            }
        )

    REGISTRY.write_text(to_toml(entries), encoding="utf-8")

    removed_stale = 0
    valid_outputs = {entry["normalized_relpath"] for entry in entries}
    for existing_json in OUT_DIR.glob("*.json"):
        rel = existing_json.relative_to(REPO_ROOT).as_posix()
        if rel not in valid_outputs:
            existing_json.unlink()
            removed_stale += 1

    print(f"Normalized {len(entries)} txt files into {OUT_DIR.relative_to(REPO_ROOT)}")
    print(f"Wrote registry: {REGISTRY.relative_to(REPO_ROOT)}")
    print(f"Removed stale normalized JSON files: {removed_stale}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
