#!/usr/bin/env python3
"""Build a working-source companion snapshot while checking its source boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


MARKER = ".companion-snapshot.json"


def git(root: Path, *arguments: str) -> bytes:
    return subprocess.check_output(
        ["git", "-c", "core.fsmonitor=false", "-C", str(root), *arguments],
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )


def observe(root: Path) -> dict:
    paths = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    hashes = {}
    for raw_path in sorted(set(paths.split(b"\0")) - {b""}):
        relative = os.fsdecode(raw_path)
        path = root / relative
        if relative.split("/")[0] in {".git", "build"}:
            continue
        if path.is_symlink():
            hashes[relative] = {"symlink": str(path.readlink())}
        elif path.is_file():
            hashes[relative] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        elif path.exists():
            raise ValueError(f"Unsupported source entry: {relative}")
        else:
            hashes[relative] = {"deleted": True}
    return {
        "head": git(root, "rev-parse", "HEAD").decode().strip(),
        "status": git(root, "status", "--porcelain=v1", "--untracked-files=all").decode(),
        "index": git(root, "ls-files", "--stage", "-z").decode(),
        "refs": git(root, "for-each-ref", "--format=%(refname) %(objectname)").decode(),
        "files": hashes,
    }


def validate_files(root: Path, files: dict) -> None:
    actual_paths = {
        os.fsdecode(path)
        for path in git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split(
            b"\0"
        )
        if path
    }
    unexpected = {
        path
        for path in actual_paths
        if path not in files and path != MARKER and path.split("/")[0] != "build"
    }
    if unexpected:
        raise ValueError(
            f"Unexpected snapshot sources {sorted(unexpected)}; choose a fresh --output"
        )
    for relative, expected in files.items():
        path = root / relative
        if expected.get("deleted"):
            valid = not path.exists() and not path.is_symlink()
        elif "symlink" in expected:
            valid = path.is_symlink() and str(path.readlink()) == expected["symlink"]
        else:
            valid = (
                path.is_file()
                and not path.is_symlink()
                and hashlib.sha256(path.read_bytes()).hexdigest() == expected["sha256"]
            )
        if not valid:
            raise ValueError(f"Snapshot differs at {relative}; choose a fresh --output")


def prepare(source: Path, output: Path, prepare_only: bool = False) -> None:
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    if output == source or source in output.parents:
        raise ValueError("Output must be outside the external source root")
    before = observe(source)
    owned = False
    try:
        if output.exists():
            marker = output / MARKER
            if not marker.is_file():
                raise ValueError("Existing output lacks ownership marker; choose a fresh --output")
            recorded = json.loads(marker.read_text())
            if recorded["source"] != str(source) or recorded["before"] != before:
                raise ValueError("Source snapshot changed; choose a fresh --output")
            if git(output, "rev-parse", "HEAD").decode().strip() != before["head"]:
                raise ValueError("Snapshot HEAD changed; choose a fresh --output")
            validate_files(output, before["files"])
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--no-hardlinks", "--no-checkout", str(source), str(output)],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(output), "checkout", "--detach", before["head"]], check=True
            )
            for relative, entry in before["files"].items():
                destination = output / relative
                # Refuse ancestor symlinks, which could redirect writes outside the snapshot.
                for ancestor in destination.parents:
                    if ancestor == output:
                        break
                    if ancestor.is_symlink():
                        raise ValueError(f"Symlink ancestor in snapshot: {relative}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.is_symlink() or destination.is_file():
                    destination.unlink()
                if entry.get("deleted"):
                    continue
                if "symlink" in entry:
                    target = (destination.parent / entry["symlink"]).resolve()
                    if target != output and output not in target.parents:
                        raise ValueError(f"External symlink target: {relative}")
                    destination.symlink_to(entry["symlink"])
                else:
                    destination.write_bytes((source / relative).read_bytes())
                    destination.chmod((source / relative).stat().st_mode & 0o777)
            validate_files(output, before["files"])
            (output / MARKER).write_text(
                json.dumps({"source": str(source), "before": before}, indent=2) + "\n"
            )
        owned = True
        if not prepare_only:
            environment = os.environ.copy()
            environment["TEXMFVAR"] = str(output / "build" / "texmf-var")
            subprocess.run(["make", "pdf"], cwd=output, env=environment, check=True)
            validate_files(output, before["files"])
    finally:
        after = observe(source)
        if before != after:
            raise RuntimeError("External source measurements changed during snapshot preparation")
        if owned:
            (output / MARKER).write_text(
                json.dumps({"source": str(source), "before": before, "after": after}, indent=2)
                + "\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path("~/Github/precalc_paper"))
    parser.add_argument("--output", type=Path, default=Path("build/companion-source"))
    parser.add_argument("--prepare-only", action="store_true")
    arguments = parser.parse_args()
    prepare(arguments.source_root, arguments.output, arguments.prepare_only)


if __name__ == "__main__":
    main()
