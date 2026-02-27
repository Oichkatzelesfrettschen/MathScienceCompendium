#!/usr/bin/env python3
"""Batch download arXiv papers with rate limiting and provenance tracking.

Usage:
    python scripts/fetch_arxiv.py [--dry-run] [--delay 3]

Reads arXiv IDs from data/external/sources.toml (entries with arxiv_id field)
and downloads PDFs to source_materials/pdfs/ with SHA-256 provenance.

Rate limiting: defaults to 3 seconds between requests to respect arXiv policy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-reuse-import]


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "data" / "external" / "sources.toml"
PROVENANCE = REPO_ROOT / "data" / "external" / "PROVENANCE.json"
PDF_DIR = REPO_ROOT / "source_materials" / "pdfs"
ARXIV_PDF_BASE = "https://arxiv.org/pdf/"

# arXiv rate limit: minimum delay between requests in seconds
ARXIV_MIN_DELAY = 3.0


@dataclass
class ArxivResult:
    arxiv_id: str
    target_path: str
    status: str
    sha256: str | None
    size_bytes: int | None
    fetched_at_utc: str
    url: str | None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_pdf(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(5) == b"%PDF-"
    except OSError:
        return False


def fetch_arxiv_pdf(
    arxiv_id: str,
    target: Path,
    timeout: int = 60,
) -> tuple[bool, str]:
    url = f"{ARXIV_PDF_BASE}{arxiv_id}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "MathScienceCompendium/1.0 "
                "(automated academic fetch; +https://github.com/fetch-info)"
            ),
        },
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            data = resp.read()
        if not data.startswith(b"%PDF-"):
            return False, "not_pdf_payload"
        target.write_bytes(data)
        return True, url
    except urllib.error.HTTPError as exc:
        return False, f"http_error:{exc.code}"
    except urllib.error.URLError as exc:
        return False, f"url_error:{exc.reason}"
    except TimeoutError:
        return False, "timeout"


def load_arxiv_sources() -> list[dict]:
    if not MANIFEST.exists():
        print(f"Manifest not found: {MANIFEST}", file=sys.stderr)
        return []
    data = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    return [s for s in data.get("sources", []) if s.get("arxiv_id")]


def update_provenance(results: list[ArxivResult]) -> None:
    existing: dict = {}
    if PROVENANCE.exists():
        payload = json.loads(PROVENANCE.read_text(encoding="utf-8"))
        existing = {r["id"]: r for r in payload.get("results", []) if "id" in r}

    for r in results:
        entry = asdict(r)
        entry["id"] = f"arxiv_{r.arxiv_id.replace('.', '_').replace('/', '_')}"
        existing[entry["id"]] = entry

    PROVENANCE.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE.write_text(
        json.dumps(
            {
                "manifest": str(MANIFEST.relative_to(REPO_ROOT)),
                "generated_at_utc": now_utc_iso(),
                "results": sorted(existing.values(), key=lambda x: x.get("id", "")),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch download arXiv PDFs with rate limiting"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be downloaded without fetching",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=ARXIV_MIN_DELAY,
        help=f"Seconds between requests (default: {ARXIV_MIN_DELAY})",
    )
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if file exists",
    )
    args = parser.parse_args()

    sources = load_arxiv_sources()
    if not sources:
        print("No arXiv sources found in sources.toml (add arxiv_id field to entries).")
        return 0

    results: list[ArxivResult] = []
    for i, source in enumerate(sources):
        arxiv_id: str = source["arxiv_id"]
        filename = f"arxiv_{arxiv_id.replace('/', '_')}.pdf"
        target = PDF_DIR / filename

        print(f"[{i+1}/{len(sources)}] arXiv:{arxiv_id} -> {target.name}", end=" ")

        if args.dry_run:
            print("(dry-run)")
            continue

        if target.exists() and not args.force:
            sha = sha256_file(target)
            size = target.stat().st_size
            print(f"[exists] sha256={sha[:16]}...")
            results.append(
                ArxivResult(
                    arxiv_id=arxiv_id,
                    target_path=str(target.relative_to(REPO_ROOT)),
                    status="exists",
                    sha256=sha,
                    size_bytes=size,
                    fetched_at_utc=now_utc_iso(),
                    url=None,
                )
            )
            continue

        ok, detail = fetch_arxiv_pdf(arxiv_id, target, args.timeout)
        if ok:
            sha = sha256_file(target)
            size = target.stat().st_size
            print(f"[downloaded] {size/1024:.0f} KB sha256={sha[:16]}...")
            results.append(
                ArxivResult(
                    arxiv_id=arxiv_id,
                    target_path=str(target.relative_to(REPO_ROOT)),
                    status="downloaded",
                    sha256=sha,
                    size_bytes=size,
                    fetched_at_utc=now_utc_iso(),
                    url=detail,
                )
            )
        else:
            print(f"[failed] {detail}")
            results.append(
                ArxivResult(
                    arxiv_id=arxiv_id,
                    target_path=str(target.relative_to(REPO_ROOT)),
                    status="failed",
                    sha256=None,
                    size_bytes=None,
                    fetched_at_utc=now_utc_iso(),
                    url=detail,
                )
            )

        if i < len(sources) - 1:
            time.sleep(args.delay)

    if not args.dry_run:
        update_provenance(results)
        print(f"\nUpdated provenance: {PROVENANCE.relative_to(REPO_ROOT)}")

    failed = [r for r in results if r.status == "failed"]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
