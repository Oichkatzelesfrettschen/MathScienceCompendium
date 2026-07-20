#!/usr/bin/env python3
"""Build a machine-readable claim coverage report from claim-source crosswalk."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import tomllib


if __package__:
    from .reproducible_time import generated_at_utc
else:
    from reproducible_time import generated_at_utc


REPO_ROOT = Path(__file__).resolve().parent.parent
CROSSWALK_PATH = REPO_ROOT / "data" / "registry" / "claim_source_crosswalk.toml"
SOURCES_PATH = REPO_ROOT / "data" / "external" / "sources.toml"
OUT_PATH = REPO_ROOT / "data" / "registry" / "claim_coverage_report.toml"


def toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def toml_string_array(values: list[str]) -> str:
    escaped = [f'"{toml_escape(item)}"' for item in values]
    return "[" + ", ".join(escaped) + "]"


def read_positive_int(raw: object, default_value: int) -> int:
    if isinstance(raw, int) and raw >= 1:
        return raw
    return default_value


def main() -> int:
    crosswalk = tomllib.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))
    sources_manifest = tomllib.loads(SOURCES_PATH.read_text(encoding="utf-8"))

    known_source_ids = {
        str(entry.get("id", "")).strip()
        for entry in sources_manifest.get("sources", [])
        if str(entry.get("id", "")).strip()
    }

    coverage_policy = crosswalk.get("coverage_policy", {})
    if not isinstance(coverage_policy, dict):
        coverage_policy = {}

    min_claims_per_chapter = read_positive_int(coverage_policy.get("min_claims_per_chapter"), 1)
    min_unique_sources_per_chapter = read_positive_int(
        coverage_policy.get("min_unique_sources_per_chapter"),
        1,
    )
    min_claims_per_group = read_positive_int(coverage_policy.get("min_claims_per_group"), 1)
    min_unique_sources_per_group = read_positive_int(
        coverage_policy.get("min_unique_sources_per_group"),
        1,
    )

    raw_prefixes = coverage_policy.get("required_chapter_group_prefixes", [])
    group_prefixes: list[str] = []
    if isinstance(raw_prefixes, list):
        for value in raw_prefixes:
            cleaned = str(value).strip()
            if cleaned:
                group_prefixes.append(cleaned)
    if not group_prefixes:
        group_prefixes = ["papers/sections/"]

    claims = crosswalk.get("claims", [])
    if not isinstance(claims, list):
        claims = []

    chapter_claim_ids: dict[str, list[str]] = defaultdict(list)
    chapter_source_ids: dict[str, set[str]] = defaultdict(set)
    unknown_source_ids: set[str] = set()

    for claim in claims:
        if not isinstance(claim, dict):
            continue

        claim_id = str(claim.get("claim_id", "")).strip()
        chapter_relpath = str(claim.get("chapter_relpath", "")).strip()
        source_ids = claim.get("source_ids", [])

        if not chapter_relpath:
            continue

        if claim_id:
            chapter_claim_ids[chapter_relpath].append(claim_id)

        if isinstance(source_ids, list):
            for source_id in source_ids:
                source_id_str = str(source_id).strip()
                if not source_id_str:
                    continue
                chapter_source_ids[chapter_relpath].add(source_id_str)
                if source_id_str not in known_source_ids:
                    unknown_source_ids.add(source_id_str)

    chapter_rows: list[dict[str, object]] = []
    all_sources: set[str] = set()

    for chapter_relpath in sorted(chapter_claim_ids):
        claim_ids = sorted(set(chapter_claim_ids[chapter_relpath]))
        source_ids = sorted(chapter_source_ids[chapter_relpath])
        all_sources.update(source_ids)

        claims_count = len(claim_ids)
        unique_sources_count = len(source_ids)
        status = "pass"
        if claims_count < min_claims_per_chapter:
            status = "fail"
        if unique_sources_count < min_unique_sources_per_chapter:
            status = "fail"

        chapter_rows.append(
            {
                "chapter_relpath": chapter_relpath,
                "claims_count": claims_count,
                "unique_sources_count": unique_sources_count,
                "claim_ids": claim_ids,
                "source_ids": source_ids,
                "status": status,
            }
        )

    group_rows: list[dict[str, object]] = []
    for prefix in group_prefixes:
        matching_chapters = [
            row for row in chapter_rows if str(row["chapter_relpath"]).startswith(prefix)
        ]
        group_claims_count = sum(int(row["claims_count"]) for row in matching_chapters)

        group_sources: set[str] = set()
        for row in matching_chapters:
            group_sources.update(str(source_id) for source_id in row["source_ids"])

        group_status = "pass"
        if len(matching_chapters) == 0:
            group_status = "fail"
        if group_claims_count < min_claims_per_group:
            group_status = "fail"
        if len(group_sources) < min_unique_sources_per_group:
            group_status = "fail"

        group_rows.append(
            {
                "group_prefix": prefix,
                "chapters_covered": len(matching_chapters),
                "claims_count": group_claims_count,
                "unique_sources_count": len(group_sources),
                "source_ids": sorted(group_sources),
                "status": group_status,
            }
        )

    overall_status = "pass"
    if unknown_source_ids:
        overall_status = "fail"
    if any(str(row["status"]) != "pass" for row in chapter_rows):
        overall_status = "fail"
    if any(str(row["status"]) != "pass" for row in group_rows):
        overall_status = "fail"

    lines: list[str] = []
    lines.append('generated_by = "scripts/build_claim_coverage_report.py"')
    lines.append(f'generated_at_utc = "{generated_at_utc()}"')
    lines.append(f'crosswalk_relpath = "{CROSSWALK_PATH.relative_to(REPO_ROOT).as_posix()}"')
    lines.append(f'sources_manifest_relpath = "{SOURCES_PATH.relative_to(REPO_ROOT).as_posix()}"')
    lines.append(f"claims_total = {len(claims)}")
    lines.append(f"chapters_with_claims = {len(chapter_rows)}")
    lines.append(f"groups_tracked = {len(group_rows)}")
    lines.append(f"unique_sources_total = {len(all_sources)}")
    lines.append(f"unknown_source_id_count = {len(unknown_source_ids)}")
    lines.append(f"unknown_source_ids = {toml_string_array(sorted(unknown_source_ids))}")
    lines.append(f'overall_status = "{overall_status}"')
    lines.append("")

    lines.append("[coverage_policy]")
    lines.append(f"min_claims_per_chapter = {min_claims_per_chapter}")
    lines.append(f"min_unique_sources_per_chapter = {min_unique_sources_per_chapter}")
    lines.append(f"min_claims_per_group = {min_claims_per_group}")
    lines.append(f"min_unique_sources_per_group = {min_unique_sources_per_group}")
    lines.append(f"required_chapter_group_prefixes = {toml_string_array(group_prefixes)}")
    lines.append("")

    for row in chapter_rows:
        lines.append("[[chapter_coverage]]")
        lines.append(f'chapter_relpath = "{toml_escape(str(row["chapter_relpath"]))}"')
        lines.append(f"claims_count = {row['claims_count']}")
        lines.append(f"unique_sources_count = {row['unique_sources_count']}")
        lines.append(f"claim_ids = {toml_string_array(list(row['claim_ids']))}")
        lines.append(f"source_ids = {toml_string_array(list(row['source_ids']))}")
        lines.append(f'status = "{row["status"]}"')
        lines.append("")

    for row in group_rows:
        lines.append("[[group_coverage]]")
        lines.append(f'group_prefix = "{toml_escape(str(row["group_prefix"]))}"')
        lines.append(f"chapters_covered = {row['chapters_covered']}")
        lines.append(f"claims_count = {row['claims_count']}")
        lines.append(f"unique_sources_count = {row['unique_sources_count']}")
        lines.append(f"source_ids = {toml_string_array(list(row['source_ids']))}")
        lines.append(f'status = "{row["status"]}"')
        lines.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    print(f"Wrote claim coverage report: {OUT_PATH.relative_to(REPO_ROOT).as_posix()}")
    print(f"Claims analyzed: {len(claims)}")
    print(f"Chapters with claims: {len(chapter_rows)}")
    print(f"Overall status: {overall_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
