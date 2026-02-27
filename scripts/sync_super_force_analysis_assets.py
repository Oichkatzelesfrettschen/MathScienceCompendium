#!/usr/bin/env python3
"""Sync curated text/code assets from Super-Force-Analysis with provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "data" / "external" / "super_force_analysis"
PROVENANCE_PATH = OUT_DIR / "PROVENANCE.json"

DEFAULT_REPO = "ConsciousEnergy/Super-Force-Analysis"
DEFAULT_REF = "afbde0996d58bde0dbc7dbcf254810b3c289db31"

CURATED_ASSETS = [
    ("LICENSE.md", "LICENSE.upstream.md"),
    ("README.md", "README.upstream.md"),
    ("Dimensional_Analysis_Results.md", "Dimensional_Analysis_Results.md"),
    ("Experimental_Designs.md", "Experimental_Designs.md"),
    ("Literature_Review.md", "Literature_Review.md"),
    ("Super_Force_Dimensional_Analysis.py", "Super_Force_Dimensional_Analysis.py"),
    ("Simulations_&_Modeling", "Simulations_and_Modeling.md"),
]


@dataclass(frozen=True)
class SyncedAsset:
    upstream_path: str
    local_relpath: str
    source_url: str
    sha256: str
    size_bytes: int


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_raw_url(repo: str, ref: str, upstream_path: str) -> str:
    quoted_path = urllib.parse.quote(upstream_path, safe="/")
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{quoted_path}"


def fetch_bytes(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "MathScienceCompendium/1.0 super-force sync"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def normalize_text_payload(payload: bytes) -> bytes:
    text = payload.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    if not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


def sync_assets(repo: str, ref: str, timeout: int) -> list[SyncedAsset]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[SyncedAsset] = []

    for upstream_path, local_name in CURATED_ASSETS:
        source_url = build_raw_url(repo, ref, upstream_path)
        payload = fetch_bytes(source_url, timeout=timeout)
        payload = normalize_text_payload(payload)

        local_path = OUT_DIR / local_name
        local_path.write_bytes(payload)

        relpath = local_path.relative_to(REPO_ROOT).as_posix()
        results.append(
            SyncedAsset(
                upstream_path=upstream_path,
                local_relpath=relpath,
                source_url=source_url,
                sha256=sha256_bytes(payload),
                size_bytes=len(payload),
            )
        )
        print(f"[synced] {upstream_path} -> {relpath}")

    return results


def write_provenance(repo: str, ref: str, assets: list[SyncedAsset]) -> None:
    payload = {
        "generated_by": "scripts/sync_super_force_analysis_assets.py",
        "generated_at_utc": now_utc_iso(),
        "upstream_repo": repo,
        "upstream_ref": ref,
        "asset_count": len(assets),
        "assets": [
            {
                "upstream_path": asset.upstream_path,
                "local_relpath": asset.local_relpath,
                "source_url": asset.source_url,
                "sha256": asset.sha256,
                "size_bytes": asset.size_bytes,
            }
            for asset in assets
        ],
    }
    PROVENANCE_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote provenance: {PROVENANCE_PATH.relative_to(REPO_ROOT).as_posix()}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync curated Super-Force-Analysis assets.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repository owner/name")
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git commit SHA or ref to sync from")
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout in seconds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    assets = sync_assets(repo=args.repo, ref=args.ref, timeout=args.timeout)
    write_provenance(repo=args.repo, ref=args.ref, assets=assets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
