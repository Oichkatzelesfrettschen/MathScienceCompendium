#!/usr/bin/env python3
"""Record an explicitly reviewed local companion snapshot for PDF admission."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from assemble_learning_album import ROOT, git, sha256, source_dependencies
from prepare_learning_companion import MARKER, observe, validate_files


def record(snapshot: Path, destination: Path) -> None:
    snapshot = snapshot.resolve()
    destination = destination.resolve()
    if not destination.is_relative_to(ROOT) or destination.is_relative_to(snapshot):
        raise ValueError("Edition record must be inside this repository and outside the snapshot")
    marker = json.loads((snapshot / MARKER).read_text())
    if marker.get("before") != marker.get("after"):
        raise ValueError("Snapshot lacks matching before/after observations")
    if observe(Path(marker["source"])) != marker["before"]:
        raise ValueError("External source differs from the reviewed snapshot")
    validate_files(snapshot, marker["before"]["files"])
    if git(snapshot, "rev-parse", "HEAD") != marker["before"]["head"]:
        raise ValueError("Snapshot HEAD differs from its source observation")
    pdf = snapshot / "build/main.pdf"
    edition = {
        "schema_version": 1,
        "title": "Precalculus Through Problems of the Past",
        "revision": marker["before"]["head"],
        "working_tree": True,
        "pdf_sha256": sha256(pdf),
        "source_dependencies": source_dependencies(snapshot, pdf),
        "scope": "Identity of the explicitly reviewed working-edition PDF and recorder-listed local inputs. Mathematical, historical, visual, and learner evidence remain separate.",
    }
    destination.write_text(json.dumps(edition, indent=2) + "\n")
    print(f"Recorded {len(edition['source_dependencies'])} source inputs in {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/learning/precalculus_edition.json"
    )
    arguments = parser.parse_args()
    record(arguments.snapshot_root, arguments.output)


if __name__ == "__main__":
    main()
