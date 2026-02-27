#!/usr/bin/env python3
"""Fetch external artifacts from a TOML manifest with provenance tracking.

This script is intentionally script-only (not test) to keep test runs offline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "data" / "external" / "sources.toml"
DEFAULT_PROVENANCE = REPO_ROOT / "data" / "external" / "PROVENANCE.json"
TRACE_DIR = REPO_ROOT / "data" / "external" / "fetch_traces"


@dataclass
class FetchResult:
    id: str
    target_relpath: str
    status: str
    source_url: str | None
    size_bytes: int | None
    sha256: str | None
    extract_text_relpath: str | None
    fetched_at_utc: str
    notes: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def is_pdf_file(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(5) == b"%PDF-"
    except OSError:
        return False


def write_trace(source_id: str, text: str) -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    (TRACE_DIR / f"{source_id}.txt").write_text(text, encoding="utf-8")


def clear_trace(source_id: str) -> None:
    trace_path = TRACE_DIR / f"{source_id}.txt"
    if trace_path.exists():
        trace_path.unlink()


def download_url(url: str, target: Path, timeout: int) -> tuple[bool, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "MathScienceCompendiumFetcher/1.0 (+offline-reproducible-cache)",
            "Accept": "application/pdf,application/octet-stream,*/*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            ensure_parent(target)
            with target.open("wb") as out:
                shutil.copyfileobj(resp, out)
        if target.suffix.lower() == ".pdf" and not is_pdf_file(target):
            try:
                target.unlink()
            except OSError:
                pass
            return False, "not_pdf_payload"
        return True, "ok"
    except urllib.error.HTTPError as exc:
        return False, f"http_error:{exc.code}"
    except urllib.error.URLError as exc:
        return False, f"url_error:{exc.reason}"
    except TimeoutError:
        return False, "timeout"


def maybe_extract_text(pdf_path: Path, txt_path: Path) -> tuple[bool, str]:
    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        return False, "pdftotext_not_found"

    ensure_parent(txt_path)
    try:
        subprocess.run([pdftotext, str(pdf_path), str(txt_path)], check=True)
    except subprocess.CalledProcessError as exc:
        return False, f"pdftotext_failed:{exc.returncode}"
    return True, "ok"


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    if "sources" not in data or not isinstance(data["sources"], list):
        raise ValueError("Manifest must contain a [[sources]] list")
    return data


def process_source(
    source: dict[str, Any],
    force: bool,
    timeout: int,
    extract_text: bool,
) -> FetchResult:
    source_id = str(source["id"])
    target_relpath = str(source["target_relpath"])
    target = REPO_ROOT / target_relpath
    urls = list(source.get("urls", []))
    extract_text_relpath = source.get("extract_text_relpath")
    notes = str(source.get("notes", ""))

    fetched_at = now_utc_iso()

    if target.exists() and not force:
        clear_trace(source_id)
        sha = sha256_file(target)
        size = target.stat().st_size
        if extract_text and extract_text_relpath:
            txt_path = REPO_ROOT / str(extract_text_relpath)
            maybe_extract_text(target, txt_path)
        return FetchResult(
            id=source_id,
            target_relpath=target_relpath,
            status="exists",
            source_url=None,
            size_bytes=size,
            sha256=sha,
            extract_text_relpath=str(extract_text_relpath) if extract_text_relpath else None,
            fetched_at_utc=fetched_at,
            notes=notes,
        )

    if not urls:
        write_trace(source_id, "No URLs configured for source. Update data/external/sources.toml.")
        return FetchResult(
            id=source_id,
            target_relpath=target_relpath,
            status="missing_url",
            source_url=None,
            size_bytes=None,
            sha256=None,
            extract_text_relpath=str(extract_text_relpath) if extract_text_relpath else None,
            fetched_at_utc=fetched_at,
            notes=notes,
        )

    for url in urls:
        ok, msg = download_url(str(url), target, timeout)
        if ok:
            clear_trace(source_id)
            sha = sha256_file(target)
            size = target.stat().st_size
            if extract_text and extract_text_relpath and target.suffix.lower() == ".pdf":
                txt_path = REPO_ROOT / str(extract_text_relpath)
                maybe_extract_text(target, txt_path)
            return FetchResult(
                id=source_id,
                target_relpath=target_relpath,
                status="downloaded",
                source_url=str(url),
                size_bytes=size,
                sha256=sha,
                extract_text_relpath=str(extract_text_relpath) if extract_text_relpath else None,
                fetched_at_utc=fetched_at,
                notes=notes,
            )
        write_trace(source_id, f"Failed URL: {url}\nReason: {msg}\n")

    return FetchResult(
        id=source_id,
        target_relpath=target_relpath,
        status="failed",
        source_url=None,
        size_bytes=None,
        sha256=None,
        extract_text_relpath=str(extract_text_relpath) if extract_text_relpath else None,
        fetched_at_utc=fetched_at,
        notes=notes,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch external sources with provenance")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--force", action="store_true", help="Re-download even if target exists")
    parser.add_argument("--extract-text", action="store_true", help="Run pdftotext for PDFs")
    args = parser.parse_args()

    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = REPO_ROOT / manifest_path
    provenance_path = args.provenance
    if not provenance_path.is_absolute():
        provenance_path = REPO_ROOT / provenance_path

    manifest = load_manifest(manifest_path)
    results: list[dict[str, Any]] = []
    for source in manifest["sources"]:
        result = process_source(source, args.force, args.timeout, args.extract_text)
        results.append(result.__dict__)
        print(f"[{result.status}] {result.id} -> {result.target_relpath}")

    ensure_parent(provenance_path)
    payload = {
        "manifest": str(manifest_path.relative_to(REPO_ROOT)),
        "generated_at_utc": now_utc_iso(),
        "results": sorted(results, key=lambda r: r["id"]),
    }
    provenance_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote provenance: {provenance_path.relative_to(REPO_ROOT)}")

    failed = [r for r in results if r["status"] in {"failed"}]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
