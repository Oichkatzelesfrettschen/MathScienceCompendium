#!/usr/bin/env python3
"""Audit parquet outputs and emit a deterministic JSON report."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "data" / "registry" / "parquet_audit.json"


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


def parquet_schema_info(path: Path) -> dict[str, Any]:
    # Optional dependency: pyarrow. Fall back gracefully.
    try:
        import pyarrow.parquet as pq  # type: ignore
    except Exception:
        return {
            "schema_available": False,
            "reason": "pyarrow_unavailable",
        }

    try:
        pf = pq.ParquetFile(path)
    except Exception as exc:
        return {
            "schema_available": False,
            "reason": f"parquet_read_error:{exc}",
        }

    schema = pf.schema_arrow
    fields = []
    for field in schema:
        fields.append({"name": field.name, "type": str(field.type)})

    return {
        "schema_available": True,
        "num_row_groups": pf.num_row_groups,
        "num_rows": pf.metadata.num_rows if pf.metadata is not None else None,
        "num_columns": len(schema),
        "fields": fields,
    }


def main() -> int:
    parquet_paths = sorted(p for p in REPO_ROOT.rglob("*.parquet") if p.is_file())

    records = []
    for path in parquet_paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        record = {
            "relpath": rel,
            "size_bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        record.update(parquet_schema_info(path))
        records.append(record)

    payload = {
        "generated_by": "scripts/parquet_audit.py",
        "generated_at_utc": now_utc_iso(),
        "parquet_count": len(records),
        "records": records,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {OUT_PATH.relative_to(REPO_ROOT)} ({len(records)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
