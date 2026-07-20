#!/usr/bin/env python3
"""Build artifact and experiment registries in TOML format."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_DIR = REPO_ROOT / "data" / "registry"
ARTIFACTS_TOML = REGISTRY_DIR / "artifacts_index.toml"
EXPERIMENTS_TOML = REGISTRY_DIR / "experiments_index.toml"

ARTIFACT_SCAN_ROOTS = [
    "figures",
    "experiments/figures",
    "results",
    "papers",
    "source_materials/pdfs",
]

PAPER_ARTIFACTS = {"papers/main.pdf"}

EXPERIMENT_SCAN_PATTERNS = [
    "results/*.parquet",
    "experiments/*results*.json",
    "experiments/results/*.json",
    "experiments/data/*.json",
]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def infer_kind(rel: str) -> str:
    if rel.endswith(".parquet"):
        return "result_snapshot"
    if rel.endswith(".pdf"):
        return "paper_or_source_pdf"
    if rel.endswith(".html"):
        return "interactive_artifact"
    if rel.endswith(".png"):
        return "figure"
    if rel.endswith(".json"):
        return "experiment_json"
    return "artifact"


def include_artifact(relpath: str) -> bool:
    """Keep retained artifacts while excluding sources and build intermediates."""
    if relpath.startswith("papers/"):
        return relpath in PAPER_ARTIFACTS
    if relpath.startswith("source_materials/pdfs/"):
        return relpath.lower().endswith(".pdf")
    return True


def to_toml_table(name: str, rows: list[dict[str, str | int]]) -> str:
    out: list[str] = []
    out.append('generated_by = "scripts/build_registries.py"')
    out.append(f'generated_at_utc = "{now_utc_iso()}"')
    out.append("")
    for row in rows:
        out.append(f"[[{name}]]")
        for key in sorted(row.keys()):
            value = row[key]
            if isinstance(value, int):
                out.append(f"{key} = {value}")
            else:
                out.append(f'{key} = "{value}"')
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def build_artifacts() -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    for root_rel in ARTIFACT_SCAN_ROOTS:
        root = REPO_ROOT / root_rel
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if not include_artifact(rel):
                continue
            rows.append(
                {
                    "relpath": rel,
                    "kind": infer_kind(rel),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return rows


def build_experiments() -> list[dict[str, str | int]]:
    seen: set[str] = set()
    rows: list[dict[str, str | int]] = []
    for pattern in EXPERIMENT_SCAN_PATTERNS:
        for path in sorted(REPO_ROOT.glob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            rows.append(
                {
                    "relpath": rel,
                    "kind": infer_kind(rel),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    return rows


def main() -> int:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)

    artifact_rows = build_artifacts()
    experiment_rows = build_experiments()

    ARTIFACTS_TOML.write_text(to_toml_table("artifacts", artifact_rows), encoding="utf-8")
    EXPERIMENTS_TOML.write_text(to_toml_table("experiments", experiment_rows), encoding="utf-8")

    print(f"Wrote {ARTIFACTS_TOML.relative_to(REPO_ROOT)} ({len(artifact_rows)} rows)")
    print(f"Wrote {EXPERIMENTS_TOML.relative_to(REPO_ROOT)} ({len(experiment_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
