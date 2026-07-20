#!/usr/bin/env python3
"""Archive repository PDFs to ~/Documents before cleanup operations."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from collections.abc import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_INDEX = REPO_ROOT / "data" / "registry" / "pdf_archive_index.json"


@dataclass(frozen=True)
class ArchiveResult:
    source_relpath: str
    destination_relpath: str
    action: str
    sha256: str
    bytes: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_repo_pdfs(repo_root: Path) -> Iterable[Path]:
    for path in repo_root.rglob("*.pdf"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        yield path


def archive_pdf(source: Path, repo_root: Path, dest_root: Path, dry_run: bool) -> ArchiveResult:
    rel = source.relative_to(repo_root)
    dest = dest_root / rel
    source_hash = sha256_file(source)
    source_size = source.stat().st_size

    if dest.exists():
        dest_hash = sha256_file(dest)
        if dest_hash == source_hash:
            return ArchiveResult(
                source_relpath=rel.as_posix(),
                destination_relpath=rel.as_posix(),
                action="kept_existing",
                sha256=source_hash,
                bytes=source_size,
            )

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)

    return ArchiveResult(
        source_relpath=rel.as_posix(),
        destination_relpath=rel.as_posix(),
        action="copied" if not dry_run else "would_copy",
        sha256=source_hash,
        bytes=source_size,
    )


def display_destination_root(path: Path) -> str:
    text = path.as_posix()
    home = Path.home().as_posix()
    if text == home:
        return "~"
    if text.startswith(home + "/"):
        return "~" + text[len(home) :]
    if path.is_absolute():
        return f"<absolute:{path.name or 'root'}>"
    return text


def write_archive_index(results: list[ArchiveResult], dest_root: Path, dry_run: bool) -> None:
    payload = {
        "destination_root": display_destination_root(dest_root),
        "dry_run": dry_run,
        "pdf_count": len(results),
        "items": [
            {
                "source_relpath": item.source_relpath,
                "destination_relpath": item.destination_relpath,
                "action": item.action,
                "sha256": item.sha256,
                "bytes": item.bytes,
            }
            for item in results
        ],
    }
    ARCHIVE_INDEX.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_INDEX.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive repository PDFs to a Documents cache.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root (default: script parent parent)",
    )
    parser.add_argument(
        "--dest-root",
        type=Path,
        default=Path("~/Documents/MathScienceCompendium/pdfs"),
        help="Destination directory (default: ~/Documents/MathScienceCompendium/pdfs)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show planned actions without copying files."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    dest_root = args.dest_root.expanduser().resolve()

    results: list[ArchiveResult] = []
    for pdf in sorted(iter_repo_pdfs(repo_root)):
        results.append(archive_pdf(pdf, repo_root, dest_root, args.dry_run))

    write_archive_index(results, dest_root, args.dry_run)

    copied = sum(1 for item in results if item.action in {"copied", "would_copy"})
    kept = sum(1 for item in results if item.action == "kept_existing")
    mode = "dry-run" if args.dry_run else "live"
    print(f"[archive-pdfs] mode={mode} total={len(results)} copied={copied} kept_existing={kept}")
    print(f"[archive-pdfs] destination_root={dest_root}")
    print(f"[archive-pdfs] index={ARCHIVE_INDEX.relative_to(repo_root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
