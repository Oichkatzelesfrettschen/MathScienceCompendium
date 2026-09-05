#!/usr/bin/env python3
"""Validate book ownership, real lesson sources, prerequisites, and ordered routes."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def validate_library(
    data: dict[str, Any],
    root: Path = ROOT,
    external_roots: dict[str, Path] | None = None,
) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    external_roots = external_roots or {}
    if data.get("schema_version") != 1:
        errors.append("Unsupported library schema")
    books = data.get("books", [])
    nodes = data.get("nodes", [])
    routes = data.get("routes", [])
    for name, records in [("book", books), ("node", nodes), ("route", routes)]:
        identifiers = [item.get("id") for item in records]
        if not identifiers or len(set(identifiers)) != len(identifiers):
            errors.append(f"Empty or duplicate {name} identifiers")
        if any(
            not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z_]*", value)
            for value in identifiers
        ):
            errors.append(f"Invalid {name} identifier")
    book_map = {item["id"]: item for item in books}
    node_map = {item["id"]: item for item in nodes}
    for book in books:
        if book.get("repository") and not re.fullmatch(r"[0-9a-f]{40}", book.get("revision", "")):
            errors.append(f"{book['id']}: external book needs exact commit")
    for node in nodes:
        identifier = node["id"]
        if node.get("book") not in book_map:
            errors.append(f"{identifier}: unknown book")
            continue
        relative = Path(node.get("source", ""))
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"{identifier}: source escapes book")
        else:
            external = bool(book_map[node["book"]].get("repository"))
            source_root = external_roots.get(node["book"]) if external else root
            if source_root is not None:
                source_root = source_root.resolve()
                source = (source_root / relative).resolve()
                if not source.is_relative_to(source_root):
                    errors.append(f"{identifier}: source escapes book through resolved path")
                elif not source.is_file():
                    errors.append(f"{identifier}: missing source {relative}")
                elif node.get("pdf_title") and node["pdf_title"] not in source.read_text():
                    errors.append(f"{identifier}: heading absent from source")
        if not isinstance(node.get("assessment"), str) or not node["assessment"].strip():
            errors.append(f"{identifier}: missing assessment")
        for prerequisite in node.get("requires", []):
            if prerequisite not in node_map:
                errors.append(f"{identifier}: unknown prerequisite {prerequisite}")
    active: set[str] = set()
    complete: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in active:
            errors.append(f"{identifier}: prerequisite cycle")
            return
        if identifier in complete or identifier not in node_map:
            return
        active.add(identifier)
        for prerequisite in node_map[identifier].get("requires", []):
            visit(prerequisite)
        active.remove(identifier)
        complete.add(identifier)

    for identifier in node_map:
        visit(identifier)
    used: set[str] = set()
    for route in routes:
        if not route.get("nodes"):
            errors.append(f"{route['id']}: empty route")
        seen: set[str] = set()
        for identifier in route.get("nodes", []):
            if identifier not in node_map:
                errors.append(f"{route['id']}: unknown node {identifier}")
                continue
            if identifier in seen:
                errors.append(f"{route['id']}: repeated node {identifier}")
            missing = set(node_map[identifier].get("requires", [])) - seen
            if missing:
                errors.append(f"{route['id']}: {identifier} precedes {sorted(missing)}")
            seen.add(identifier)
        used.update(seen)
    if set(node_map) - used:
        errors.append(f"Unreachable lessons: {sorted(set(node_map) - used)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=ROOT / "docs/learning/library.json")
    arguments = parser.parse_args()
    data = json.loads(arguments.library.read_text())
    errors = validate_library(data)
    for error in errors:
        print(error)
    print(
        f"Library: {len(data['books'])} books, {len(data['nodes'])} lessons, "
        f"{len(data['routes'])} routes, {len(errors)} findings"
    )
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
