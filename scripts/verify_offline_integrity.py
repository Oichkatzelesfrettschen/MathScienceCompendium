#!/usr/bin/env python3
"""Offline integrity checks for reproducibility and repository hygiene."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING


try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


REPO_ROOT = Path(__file__).resolve().parent.parent

TEXT_EXTENSIONS = {".md", ".txt", ".tex", ".py", ".toml", ".yml", ".yaml", ".ini", ".json"}
GENERATED_CACHE_DIRECTORIES = {
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
ABSOLUTE_PATH_PATTERNS = [
    re.compile(r"(?<![A-Za-z0-9_./:-])(/home/[^\s`\"']+)"),
    re.compile(
        r"(?<![A-Za-z0-9_./:-])"
        r"([A-Za-z]:\\(?:(?:[^\\\s`\"']+\\)+[^\\\s`\"']+|"
        r"[^\\\s`\"']+\.[A-Za-z0-9]{1,8}))"
    ),
    re.compile(r"file://[^\s`\"']+"),
]

STUB_FILES = [
    "papers/sections/vol2_ch6_string_theory.tex",
    "papers/sections/vol2_ch7_quantum_gravity.tex",
    "papers/sections/appendix_data.tex",
]

SHADOW_EXPERIMENT_PATHS = [
    "experiments/setup.py",
]

LATEX_INTERMEDIATE_SUFFIXES = {
    ".aux",
    ".bbl",
    ".blg",
    ".lof",
    ".lot",
    ".toc",
}


def classify_tracked_latex_intermediates(paths: Iterable[str]) -> list[str]:
    """Return tracked LaTeX build products that must remain regenerable."""
    return sorted(
        path
        for path in paths
        if path.startswith("papers/")
        and (
            Path(path).suffix in LATEX_INTERMEDIATE_SUFFIXES
            or path.endswith(".run.xml")
            or path.endswith("-blx.bib")
        )
    )


def check_no_tracked_latex_intermediates() -> list[str]:
    """Reject ignored LaTeX intermediates that leaked into Git history."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--", "papers"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"unable to enumerate tracked paper files: {exc}"]

    tracked_intermediates = classify_tracked_latex_intermediates(result.stdout.splitlines())
    return [
        f"tracked LaTeX intermediate must be removed from Git: {path}"
        for path in tracked_intermediates
    ]


def check_no_shadow_experiment_package() -> list[str]:
    """Keep experiments on the canonical src/mathphysics implementation."""
    shadow_sources = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "experiments" / "src").rglob("*.py")
    )
    return [
        f"shadow experiment package must be reconciled into src/mathphysics: {path}"
        for path in [
            *(path for path in SHADOW_EXPERIMENT_PATHS if (REPO_ROOT / path).exists()),
            *shadow_sources,
        ]
    ]


def check_no_absolute_local_paths() -> list[str]:
    failures: list[str] = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or GENERATED_CACHE_DIRECTORIES.intersection(path.parts):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == "scripts/verify_offline_integrity.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        searchable_values = [text]
        if path.suffix.lower() == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                pass
            else:
                searchable_values = list(iter_json_strings(payload))
        path_found = False
        for searchable_value in searchable_values:
            for pattern in ABSOLUTE_PATH_PATTERNS:
                match = pattern.search(searchable_value)
                if match:
                    failures.append(f"absolute local path '{match.group(0)}' found in {rel}")
                    path_found = True
                    break
            if path_found:
                break
    return failures


def iter_json_strings(value: object) -> Iterator[str]:
    """Yield decoded string leaves from a JSON-compatible value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_json_strings(key)
            yield from iter_json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_json_strings(item)


def check_stub_files_resolved() -> list[str]:
    failures: list[str] = []
    for rel in STUB_FILES:
        path = REPO_ROOT / rel
        if not path.exists():
            failures.append(f"stub file missing: {rel}")
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        lowered = content.lower()
        if "to be developed" in lowered or "chapter stub" in lowered:
            failures.append(f"stub marker still present: {rel}")
    return failures


def check_corpus_registry() -> list[str]:
    failures: list[str] = []
    registry_path = REPO_ROOT / "data/registry/corpus_index.toml"
    if not registry_path.exists():
        return ["missing registry: data/registry/corpus_index.toml"]

    data = tomllib.loads(registry_path.read_text(encoding="utf-8"))
    documents = data.get("documents", [])
    if not isinstance(documents, list):
        return ["invalid corpus_index.toml structure"]

    for doc in documents:
        source = REPO_ROOT / str(doc["source_relpath"])
        normalized = REPO_ROOT / str(doc["normalized_relpath"])
        if not source.exists():
            failures.append(f"missing source file in corpus registry: {doc['source_relpath']}")
        else:
            source_bytes = source.read_bytes()
            source_text = source_bytes.decode("utf-8", errors="strict")
            actual_sha256 = hashlib.sha256(source_bytes).hexdigest()
            actual_line_count = source_text.count("\n") + (0 if source_text == "" else 1)
            if str(doc.get("source_relpath", "")).startswith("build/"):
                failures.append(
                    f"generated build file admitted to corpus registry: {doc['source_relpath']}"
                )
            if doc.get("sha256") != actual_sha256:
                failures.append(
                    f"corpus source SHA-256 mismatch for {doc['source_relpath']}: "
                    f"registry={doc.get('sha256')} live={actual_sha256}"
                )
            if doc.get("size_bytes") != len(source_bytes):
                failures.append(
                    f"corpus source size mismatch for {doc['source_relpath']}: "
                    f"registry={doc.get('size_bytes')} live={len(source_bytes)}"
                )
            if doc.get("line_count") != actual_line_count:
                failures.append(
                    f"corpus source line-count mismatch for {doc['source_relpath']}: "
                    f"registry={doc.get('line_count')} live={actual_line_count}"
                )
        if not normalized.exists():
            failures.append(
                f"missing normalized file in corpus registry: {doc['normalized_relpath']}"
            )
        else:
            try:
                normalized_record = json.loads(normalized.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                failures.append(
                    f"invalid normalized corpus JSON {doc['normalized_relpath']}: {exc}"
                )
                continue
            for field_name in ("source_relpath", "sha256", "size_bytes", "line_count"):
                if normalized_record.get(field_name) != doc.get(field_name):
                    failures.append(
                        f"normalized corpus metadata mismatch for {doc['normalized_relpath']}: "
                        f"field={field_name} registry={doc.get(field_name)!r} "
                        f"normalized={normalized_record.get(field_name)!r}"
                    )

    return failures


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        while chunk := file_handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def check_artifact_registry_contents() -> list[str]:
    """Verify that identity registries describe the live repository bytes."""
    failures: list[str] = []
    registry_specs = (
        ("data/registry/artifacts_index.toml", "artifacts"),
        ("data/registry/experiments_index.toml", "experiments"),
    )

    for registry_relpath, table_name in registry_specs:
        registry_path = REPO_ROOT / registry_relpath
        if not registry_path.exists():
            failures.append(f"missing registry: {registry_relpath}")
            continue
        registry = tomllib.loads(registry_path.read_text(encoding="utf-8"))
        entries = registry.get(table_name, [])
        if not isinstance(entries, list):
            failures.append(f"invalid {registry_relpath}: {table_name} must be a list")
            continue

        for entry in entries:
            relpath = str(entry.get("relpath", "")).strip()
            if not relpath:
                failures.append(f"{registry_relpath}: entry missing relpath")
                continue
            artifact_path = REPO_ROOT / relpath
            if not artifact_path.is_file():
                failures.append(f"{registry_relpath}: missing indexed file: {relpath}")
                continue
            expected_size = entry.get("size_bytes")
            actual_size = artifact_path.stat().st_size
            if expected_size != actual_size:
                failures.append(
                    f"{registry_relpath}: size mismatch for {relpath}: "
                    f"registry={expected_size} live={actual_size}"
                )
            expected_sha256 = str(entry.get("sha256", "")).strip()
            actual_sha256 = sha256_file(artifact_path)
            if expected_sha256 != actual_sha256:
                failures.append(
                    f"{registry_relpath}: SHA-256 mismatch for {relpath}: "
                    f"registry={expected_sha256} live={actual_sha256}"
                )

    return failures


def check_external_manifest_targets() -> list[str]:
    failures: list[str] = []
    manifest = REPO_ROOT / "data/external/sources.toml"
    if not manifest.exists():
        return ["missing manifest: data/external/sources.toml"]

    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    for source in data.get("sources", []):
        rel = str(source.get("target_relpath", "")).strip()
        if not rel:
            failures.append(f"source missing target_relpath: {source.get('id', '<unknown>')}")
            continue
        # Target file may legitimately be absent before fetch; only validate parent directory exists.
        parent = (REPO_ROOT / rel).parent
        if not parent.exists():
            failures.append(
                f"target parent directory missing for {source.get('id')}: {parent.relative_to(REPO_ROOT).as_posix()}"
            )
    return failures


def check_provenance_json_valid() -> list[str]:
    provenance = REPO_ROOT / "data/external/PROVENANCE.json"
    if not provenance.exists():
        return []
    try:
        json.loads(provenance.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON in data/external/PROVENANCE.json: {exc}"]
    return []


def check_pdf_archive_index() -> list[str]:
    failures: list[str] = []
    archive_index = REPO_ROOT / "data/registry/pdf_archive_index.json"
    if not archive_index.exists():
        return []

    try:
        data = json.loads(archive_index.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON in data/registry/pdf_archive_index.json: {exc}"]

    items = data.get("items")
    if not isinstance(items, list):
        return ["invalid structure in data/registry/pdf_archive_index.json: items must be a list"]

    for item in items:
        source_relpath = str(item.get("source_relpath", "")).strip()
        if not source_relpath:
            failures.append("pdf archive item missing source_relpath")
            continue
        if not source_relpath.lower().endswith(".pdf"):
            failures.append(f"pdf archive item is not a PDF: {source_relpath}")
            continue
        source_file = REPO_ROOT / source_relpath
        if not source_file.exists():
            failures.append(f"pdf archive source missing from repository: {source_relpath}")
    return failures


def check_external_source_index_coverage() -> list[str]:
    failures: list[str] = []
    docs_dir = REPO_ROOT / "docs" / "external_sources"
    data_external = REPO_ROOT / "data" / "external"

    expected_indexes = {"PDF_SOURCE_INDEX.md"}
    for subdir in sorted(data_external.iterdir()):
        if not subdir.is_dir():
            continue
        if subdir.name in {"fetch_traces"}:
            continue
        provenance_path = subdir / "PROVENANCE.json"
        if provenance_path.exists():
            expected_indexes.add(f"{subdir.name.upper()}_SOURCE_INDEX.md")

    for index_name in sorted(expected_indexes):
        index_path = docs_dir / index_name
        if not index_path.exists():
            failures.append(
                f"missing external source index doc: docs/external_sources/{index_name}"
            )
    return failures


def check_external_provenance_completeness() -> list[str]:
    failures: list[str] = []
    provenance_files = [REPO_ROOT / "data" / "external" / "PROVENANCE.json"]
    provenance_files.extend(sorted((REPO_ROOT / "data" / "external").glob("*/PROVENANCE.json")))

    for provenance_path in provenance_files:
        if not provenance_path.exists():
            continue
        rel_provenance = provenance_path.relative_to(REPO_ROOT).as_posix()

        try:
            data = json.loads(provenance_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"invalid JSON in {rel_provenance}: {exc}")
            continue

        if "results" in data:
            results = data.get("results")
            if not isinstance(results, list):
                failures.append(f"invalid structure in {rel_provenance}: results must be a list")
                continue
            for result in results:
                result_id = str(result.get("id", "<unknown>"))
                status = str(result.get("status", "")).strip()
                fetched_at = str(result.get("fetched_at_utc", "")).strip()
                if not fetched_at:
                    failures.append(
                        f"{rel_provenance}: missing fetched_at_utc for source {result_id}"
                    )
                if status in {"downloaded", "exists"}:
                    sha = str(result.get("sha256", "")).strip()
                    size = result.get("size_bytes")
                    if not sha:
                        failures.append(f"{rel_provenance}: missing sha256 for source {result_id}")
                    if not isinstance(size, int) or size <= 0:
                        failures.append(
                            f"{rel_provenance}: invalid size_bytes for source {result_id}"
                        )
                if status == "downloaded":
                    source_url = str(result.get("source_url", "")).strip()
                    if not source_url:
                        failures.append(
                            f"{rel_provenance}: missing source_url for downloaded source {result_id}"
                        )
                target_relpath = str(result.get("target_relpath", "")).strip()
                if target_relpath and status in {"downloaded", "exists"}:
                    target_path = REPO_ROOT / target_relpath
                    if not target_path.exists():
                        failures.append(
                            f"{rel_provenance}: missing target file for {result_id}: {target_relpath}"
                        )

        if "assets" in data:
            assets = data.get("assets")
            if not isinstance(assets, list):
                failures.append(f"invalid structure in {rel_provenance}: assets must be a list")
                continue
            generated_at = str(data.get("generated_at_utc", "")).strip()
            if not generated_at:
                failures.append(f"{rel_provenance}: missing generated_at_utc")
            for asset in assets:
                upstream_path = str(asset.get("upstream_path", "<unknown>"))
                local_relpath = str(asset.get("local_relpath", "")).strip()
                source_url = str(asset.get("source_url", "")).strip()
                sha = str(asset.get("sha256", "")).strip()
                size = asset.get("size_bytes")
                if not local_relpath:
                    failures.append(
                        f"{rel_provenance}: missing local_relpath for upstream asset {upstream_path}"
                    )
                    continue
                if not source_url:
                    failures.append(
                        f"{rel_provenance}: missing source_url for asset {local_relpath}"
                    )
                if not sha:
                    failures.append(f"{rel_provenance}: missing sha256 for asset {local_relpath}")
                if not isinstance(size, int) or size <= 0:
                    failures.append(
                        f"{rel_provenance}: invalid size_bytes for asset {local_relpath}"
                    )
                local_path = REPO_ROOT / local_relpath
                if not local_path.exists():
                    failures.append(f"{rel_provenance}: local asset missing: {local_relpath}")

    return failures


def check_claim_source_crosswalk() -> list[str]:
    failures: list[str] = []
    crosswalk_path = REPO_ROOT / "data" / "registry" / "claim_source_crosswalk.toml"
    manifest_path = REPO_ROOT / "data" / "external" / "sources.toml"

    if not crosswalk_path.exists():
        return ["missing registry: data/registry/claim_source_crosswalk.toml"]
    if not manifest_path.exists():
        return ["missing manifest: data/external/sources.toml"]

    crosswalk = tomllib.loads(crosswalk_path.read_text(encoding="utf-8"))
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    known_source_ids = {str(item.get("id", "")).strip() for item in manifest.get("sources", [])}

    main_tex_path = REPO_ROOT / "papers" / "main.tex"
    if not main_tex_path.exists():
        failures.append("missing active paper assembly: papers/main.tex")
        active_sections: set[str] = set()
    else:
        main_tex = main_tex_path.read_text(encoding="utf-8", errors="replace")
        active_sections = {
            f"papers/{section_relpath}.tex"
            for section_relpath in re.findall(r"\\input\{([^}]+)\}", main_tex)
        }

    coverage_policy = crosswalk.get("coverage_policy", {})
    if not isinstance(coverage_policy, dict):
        failures.append("claim_source_crosswalk.toml coverage_policy must be a table")
        coverage_policy = {}

    def read_minimum(field_name: str, default_value: int) -> int:
        value = coverage_policy.get(field_name, default_value)
        if not isinstance(value, int) or value < 1:
            failures.append(
                f"claim_source_crosswalk.toml coverage_policy.{field_name} must be an integer >= 1"
            )
            return default_value
        return value

    min_claims_per_chapter = read_minimum("min_claims_per_chapter", 1)
    min_unique_sources_per_chapter = read_minimum("min_unique_sources_per_chapter", 1)
    min_claims_per_group = read_minimum("min_claims_per_group", 1)
    min_unique_sources_per_group = read_minimum("min_unique_sources_per_group", 1)

    raw_group_prefixes = coverage_policy.get("required_chapter_group_prefixes", [])
    group_prefixes: list[str] = []
    if not isinstance(raw_group_prefixes, list):
        failures.append(
            "claim_source_crosswalk.toml coverage_policy.required_chapter_group_prefixes must be a list"
        )
    else:
        for value in raw_group_prefixes:
            prefix = str(value).strip()
            if not prefix:
                failures.append(
                    "claim_source_crosswalk.toml coverage_policy.required_chapter_group_prefixes must not contain empty values"
                )
                continue
            group_prefixes.append(prefix)

    claims = crosswalk.get("claims", [])
    if not isinstance(claims, list):
        return ["invalid claim_source_crosswalk.toml structure: expected [[claims]] list"]

    seen_claim_ids: set[str] = set()
    chapter_claim_counts: dict[str, int] = defaultdict(int)
    chapter_unique_sources: dict[str, set[str]] = defaultdict(set)
    group_claim_counts: dict[str, int] = defaultdict(int)
    group_unique_sources: dict[str, set[str]] = defaultdict(set)

    for claim in claims:
        claim_id = str(claim.get("claim_id", "")).strip()
        chapter_relpath = str(claim.get("chapter_relpath", "")).strip()
        source_ids = claim.get("source_ids", [])
        if not claim_id:
            failures.append("claim_source_crosswalk.toml entry missing claim_id")
            continue
        if claim_id in seen_claim_ids:
            failures.append(f"duplicate claim_id in claim_source_crosswalk.toml: {claim_id}")
        seen_claim_ids.add(claim_id)

        if not chapter_relpath:
            failures.append(f"claim {claim_id} missing chapter_relpath")
        else:
            chapter_path = REPO_ROOT / chapter_relpath
            if not chapter_path.exists():
                failures.append(
                    f"claim {claim_id} references missing chapter file: {chapter_relpath}"
                )
            elif chapter_relpath not in active_sections:
                failures.append(
                    f"claim {claim_id} references a section outside papers/main.tex: "
                    f"{chapter_relpath}"
                )

        if not isinstance(source_ids, list) or not source_ids:
            failures.append(f"claim {claim_id} must define non-empty source_ids list")
            continue

        cleaned_source_ids: list[str] = []
        for source_id in source_ids:
            source_id_str = str(source_id).strip()
            if source_id_str not in known_source_ids:
                failures.append(f"claim {claim_id} references unknown source_id: {source_id_str}")
                continue
            cleaned_source_ids.append(source_id_str)

        if chapter_relpath:
            chapter_claim_counts[chapter_relpath] += 1
            chapter_unique_sources[chapter_relpath].update(cleaned_source_ids)
            for prefix in group_prefixes:
                if chapter_relpath.startswith(prefix):
                    group_claim_counts[prefix] += 1
                    group_unique_sources[prefix].update(cleaned_source_ids)

    for chapter_relpath in sorted(chapter_claim_counts):
        claims_count = chapter_claim_counts[chapter_relpath]
        unique_sources_count = len(chapter_unique_sources[chapter_relpath])
        if claims_count < min_claims_per_chapter:
            failures.append(
                f"claim coverage below minimum for chapter {chapter_relpath}: "
                f"claims={claims_count} min={min_claims_per_chapter}"
            )
        if unique_sources_count < min_unique_sources_per_chapter:
            failures.append(
                f"source coverage below minimum for chapter {chapter_relpath}: "
                f"unique_sources={unique_sources_count} min={min_unique_sources_per_chapter}"
            )

    for prefix in group_prefixes:
        matched_chapters = [
            chapter for chapter in chapter_claim_counts if chapter.startswith(prefix)
        ]
        if not matched_chapters:
            failures.append(
                f"no chapter coverage found for required chapter group prefix: {prefix}"
            )
            continue
        claims_count = group_claim_counts[prefix]
        unique_sources_count = len(group_unique_sources[prefix])
        if claims_count < min_claims_per_group:
            failures.append(
                f"claim coverage below minimum for chapter group {prefix}: "
                f"claims={claims_count} min={min_claims_per_group}"
            )
        if unique_sources_count < min_unique_sources_per_group:
            failures.append(
                f"source coverage below minimum for chapter group {prefix}: "
                f"unique_sources={unique_sources_count} min={min_unique_sources_per_group}"
            )

    return failures


def check_docs_index() -> list[str]:
    failures: list[str] = []
    docs_index_path = REPO_ROOT / "data" / "registry" / "docs_index.toml"
    if not docs_index_path.exists():
        return ["missing registry: data/registry/docs_index.toml"]

    data = tomllib.loads(docs_index_path.read_text(encoding="utf-8"))
    documents = data.get("documents", [])
    if not isinstance(documents, list):
        return ["invalid docs_index.toml structure: expected [[documents]] list"]

    documents_total = data.get("documents_total")
    if not isinstance(documents_total, int):
        failures.append("docs_index.toml missing integer documents_total")
    elif documents_total != len(documents):
        failures.append(
            f"docs_index.toml documents_total mismatch: header={documents_total} actual={len(documents)}"
        )

    seen_ids: set[str] = set()
    coverage = {
        "docs/": False,
        "papers/sections/": False,
        "research/": False,
    }

    for item in documents:
        item_id = str(item.get("id", "")).strip()
        relpath = str(item.get("relpath", "")).strip()
        category = str(item.get("category", "")).strip()
        if not item_id:
            failures.append("docs_index.toml entry missing id")
        elif item_id in seen_ids:
            failures.append(f"docs_index.toml contains duplicate id: {item_id}")
        seen_ids.add(item_id)
        if not relpath:
            failures.append("docs_index.toml entry missing relpath")
            continue
        if not category:
            failures.append(f"docs_index.toml entry missing category for relpath: {relpath}")
        if not (REPO_ROOT / relpath).exists():
            failures.append(f"docs_index.toml references missing file: {relpath}")
        for prefix in coverage:
            if relpath.startswith(prefix):
                coverage[prefix] = True

    for prefix, present in coverage.items():
        if not present:
            failures.append(f"docs_index.toml missing required coverage for scope: {prefix}")
    return failures


def main() -> int:
    checks = [
        check_no_tracked_latex_intermediates,
        check_no_shadow_experiment_package,
        check_no_absolute_local_paths,
        check_stub_files_resolved,
        check_corpus_registry,
        check_artifact_registry_contents,
        check_external_manifest_targets,
        check_external_source_index_coverage,
        check_external_provenance_completeness,
        check_provenance_json_valid,
        check_pdf_archive_index,
        check_claim_source_crosswalk,
        check_docs_index,
    ]

    failures: list[str] = []
    for check in checks:
        failures.extend(check())

    if failures:
        print("Offline integrity check FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Offline integrity check PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
