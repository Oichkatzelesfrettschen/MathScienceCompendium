#!/usr/bin/env python3
"""Resolve DOIs to download URLs via content negotiation and redirect handling.

Usage:
    python scripts/resolve_dois.py [--dry-run]

Reads DOI fields from data/external/sources.toml and resolves each to a
PDF download URL using the doi.org content negotiation API. Attempted
download is then delegated to fetch_external_sources logic.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-reuse-import]


REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "data" / "external" / "sources.toml"
DOI_BASE = "https://doi.org/"
RESOLVE_LOG = REPO_ROOT / "data" / "external" / "doi_resolutions.json"


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_doi(doi: str, timeout: int = 30) -> tuple[str | None, str]:
    """Resolve a DOI to its final redirect URL.

    Returns (resolved_url, status_message).
    Uses content negotiation requesting application/pdf first, then text/html.
    """
    for accept in ("application/pdf", "text/html"):
        url = f"{DOI_BASE}{doi}"
        req = urllib.request.Request(
            url,
            headers={
                "Accept": accept,
                "User-Agent": "MathScienceCompendium/1.0 (DOI resolver)",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                final_url = resp.url
                content_type = resp.headers.get("Content-Type", "")
                return final_url, f"ok (Accept:{accept}, CT:{content_type[:40]})"
        except urllib.error.HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308):
                location = exc.headers.get("Location")
                if location:
                    return location, f"redirect:{exc.code}"
            status = f"http_error:{exc.code}"
        except urllib.error.URLError as exc:
            status = f"url_error:{exc.reason}"
        except TimeoutError:
            return None, "timeout"
    return None, status  # type: ignore[return-value]


def load_doi_sources() -> list[dict]:
    if not MANIFEST.exists():
        return []
    data = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))
    return [s for s in data.get("sources", []) if any("doi.org" in u for u in s.get("urls", []))]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve DOIs to download URLs via content negotiation"
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    sources = load_doi_sources()
    if not sources:
        print("No DOI sources found in sources.toml (add doi.org URLs to entries).")
        return 0

    resolutions: list[dict] = []
    for source in sources:
        source_id = source.get("id", "unknown")
        doi_url = next((u for u in source.get("urls", []) if "doi.org" in u), None)
        if not doi_url:
            continue

        doi = doi_url.replace("https://doi.org/", "").replace("http://doi.org/", "")
        print(f"Resolving DOI {doi} ({source_id})...", end=" ", flush=True)

        if args.dry_run:
            print("(dry-run)")
            continue

        resolved_url, status = resolve_doi(doi, args.timeout)
        record = {
            "id": source_id,
            "doi": doi,
            "resolved_url": resolved_url,
            "status": status,
            "resolved_at_utc": now_utc_iso(),
        }
        resolutions.append(record)
        print(f"-> {resolved_url or 'FAILED'} ({status})")

    if not args.dry_run and resolutions:
        RESOLVE_LOG.parent.mkdir(parents=True, exist_ok=True)
        RESOLVE_LOG.write_text(
            json.dumps(
                {"generated_at_utc": now_utc_iso(), "resolutions": resolutions},
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nWrote: {RESOLVE_LOG.relative_to(REPO_ROOT)}")

    failed = [r for r in resolutions if r["resolved_url"] is None]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
