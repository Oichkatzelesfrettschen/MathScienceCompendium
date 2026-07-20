#!/usr/bin/env python3
"""Verify SHA-256 checksums of all cached PDFs against PROVENANCE.json.

Usage:
    python scripts/verify_checksums.py [--strict]

Exit codes:
    0  All files present and checksums match
    1  One or more files missing or checksum mismatch

--strict also fails on files listed as 'failed' or 'missing_url' in provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = REPO_ROOT / "data" / "external" / "PROVENANCE.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify SHA-256 checksums of cached PDFs against PROVENANCE.json"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on missing/failed entries in addition to checksum mismatches",
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=PROVENANCE,
    )
    args = parser.parse_args()

    provenance_path: Path = args.provenance
    if not provenance_path.is_absolute():
        provenance_path = REPO_ROOT / provenance_path

    if not provenance_path.exists():
        print(f"ERROR: Provenance file not found: {provenance_path}", file=sys.stderr)
        return 1

    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    results = payload.get("results", [])

    if not results:
        print("WARNING: No entries in provenance file.")
        return 0

    ok_count = 0
    mismatch_count = 0
    missing_count = 0
    skip_count = 0
    errors: list[str] = []

    for entry in results:
        entry_id = entry.get("id", entry.get("arxiv_id", "unknown"))
        status = entry.get("status", "unknown")
        relpath = entry.get("target_relpath") or entry.get("target_path")
        recorded_sha = entry.get("sha256")

        if status in ("failed", "missing_url", "not_pdf_payload"):
            skip_count += 1
            if args.strict:
                errors.append(f"SKIP  {entry_id}: status={status}")
            else:
                print(f"  SKIP  {entry_id}: status={status} (not downloaded)")
            continue

        if not relpath or not recorded_sha:
            skip_count += 1
            print(f"  SKIP  {entry_id}: no relpath or sha256 in provenance")
            continue

        path = REPO_ROOT / relpath
        if not path.exists():
            missing_count += 1
            errors.append(f"MISSING {entry_id}: {relpath}")
            continue

        actual_sha = sha256_file(path)
        if actual_sha == recorded_sha:
            ok_count += 1
            print(f"  OK    {entry_id}: {recorded_sha[:16]}...")
        else:
            mismatch_count += 1
            errors.append(
                f"MISMATCH {entry_id}: recorded={recorded_sha[:16]}... actual={actual_sha[:16]}..."
            )

    print(
        f"\nSummary: {ok_count} OK, {mismatch_count} mismatch, "
        f"{missing_count} missing, {skip_count} skipped"
    )

    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  {err}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
