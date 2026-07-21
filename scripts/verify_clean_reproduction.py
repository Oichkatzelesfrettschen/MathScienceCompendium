#!/usr/bin/env python3
"""Verify clean-container results against primary evidence and source history."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path
from typing import Any, cast


REPO_ROOT = Path(__file__).resolve().parent.parent
REPRODUCTION_ROOT = REPO_ROOT / "data" / "reproduction"
RUN_LOG_RELPATH = "data/reproduction/docker_compose_run.log"
REQUIRED_SOURCE_PATHS = (
    "requirements-lock.txt",
    "pyproject.toml",
    "scripts/audit_triad_selectors.py",
    "scripts/run_beta_plane_controls.py",
    "scripts/run_beta_plane_sweep.py",
    "src/mathphysics/__init__.py",
    "src/mathphysics/beta_plane.py",
    "src/mathphysics/fourier_quotient.py",
    "src/mathphysics/triad_selectors.py",
    ".dockerignore",
    "tools/reproduction/Dockerfile",
    "tools/reproduction/compose.yaml",
    "tools/reproduction/build_exact_source_image.sh",
    "tools/reproduction/run_independent_reproduction.py",
    "scripts/verify_clean_reproduction.py",
    "scripts/validate_hypothesis_promotions.py",
    "schemas/registry/independent_reproduction_registry.schema.json",
    "schemas/registry/clean_reproduction_verification.schema.json",
    "schemas/registry/manuscript_result_claims.schema.json",
    "data/registry/manuscript_result_claims.json",
    "data/registry/e7_selector_preregistration.json",
    "data/registry/beta_plane_sweep_preregistration.json",
    "data/registry/beta_plane_refinement_protocol_amendment.json",
)
INPUT_PATHS = ("data/registry/lbm_evidence_audit.json",)
JSON_COMPARISONS = (
    (
        "triad_selector_audit",
        "data/registry/triad_selector_audit.json",
        "data/reproduction/triad_selector_audit.json",
    ),
    (
        "beta_plane_production",
        "data/registry/beta_plane_sweep_results.json",
        "data/reproduction/beta_plane_sweep_results.json",
    ),
    (
        "beta_plane_refinement",
        "data/registry/beta_plane_refinement_results.json",
        "data/reproduction/beta_plane_refinement_results.json",
    ),
    (
        "beta_plane_controls",
        "data/registry/beta_plane_control_results.json",
        "data/reproduction/beta_plane_control_results.json",
    ),
)
ARCHIVE_COMPARISONS = (
    (
        "beta_plane_production_arrays",
        "data/evidence/beta_plane/production_run_arrays.tar",
        "data/reproduction/beta_plane_production_arrays.tar",
    ),
    (
        "beta_plane_refinement_arrays",
        "data/evidence/beta_plane/refinement_run_arrays.tar",
        "data/reproduction/beta_plane_refinement_arrays.tar",
    ),
    (
        "beta_plane_control_arrays",
        "data/evidence/beta_plane/control_final_states.tar",
        "data/reproduction/beta_plane_control_arrays.tar",
    ),
)


def sha256_bytes(content: bytes) -> str:
    """Return a SHA-256 digest for bytes."""
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    """Return a SHA-256 digest for one file."""
    return sha256_bytes(path.read_bytes())


def run_bytes(command: list[str]) -> bytes:
    """Run a required command and return its standard output."""
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def load_json(relpath: str) -> dict[str, Any]:
    """Load one repository JSON object."""
    return cast(
        "dict[str, Any]",
        json.loads((REPO_ROOT / relpath).read_text(encoding="ascii")),
    )


def normalized_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove only expected primary-versus-reproduction provenance distinctions."""
    normalized = copy.deepcopy(payload)
    if "source_commit" in normalized:
        normalized["source_commit"] = "<execution-source-commit>"
    normalized.pop("execution_receipt", None)
    evidence_archive = normalized.get("evidence_archive")
    if isinstance(evidence_archive, dict) and "relpath" in evidence_archive:
        evidence_archive["relpath"] = "<independent-output-root>"
    return normalized


def parse_sha256_manifest(content: bytes, container_prefix: str) -> dict[str, str]:
    """Parse checksum output while preserving repository paths encoded as UTF-8."""
    records: dict[str, str] = {}
    for line in content.decode("utf-8").splitlines():
        digest, container_path = line.split(maxsplit=1)
        records[container_path.removeprefix(container_prefix)] = digest
    return records


def image_file_digests(image: str, relpaths: tuple[str, ...]) -> dict[str, str]:
    """Hash selected files retained inside the reproduction image."""
    container_paths = [f"/workspace/{relpath}" for relpath in relpaths]
    output = run_bytes(
        ["docker", "run", "--rm", "--entrypoint", "sha256sum", image, *container_paths]
    )
    return parse_sha256_manifest(output, "/workspace/")


def committed_tree_digests(source_commit: str) -> dict[str, str]:
    """Hash every regular file exported by the declared Git tree."""
    archive_bytes = run_bytes(["git", "archive", "--format=tar", source_commit])
    records: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            file_handle = archive.extractfile(member)
            if file_handle is None:
                raise ValueError(f"cannot read committed archive member {member.name}")
            records[member.name] = sha256_bytes(file_handle.read())
    return records


def image_tree_digests(image: str) -> dict[str, str]:
    """Read the complete source-tree manifest generated inside the image."""
    output = run_bytes(
        [
            "docker",
            "run",
            "--rm",
            "--entrypoint",
            "cat",
            image,
            "/evidence_source_tree.sha256",
        ]
    )
    return parse_sha256_manifest(output, "/workspace/")


def verify_environment_outputs(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Recompute every output digest declared by the clean container."""
    records: list[dict[str, Any]] = []
    for declared in report["outputs"]:
        relpath = declared["relpath"]
        path = REPO_ROOT / relpath
        actual_digest = sha256_file(path) if path.is_file() else None
        actual_size = path.stat().st_size if path.is_file() else None
        records.append(
            {
                "relpath": relpath,
                "declared_sha256": declared["sha256"],
                "actual_sha256": actual_digest,
                "declared_size_bytes": declared["size_bytes"],
                "actual_size_bytes": actual_size,
                "match": actual_digest == declared["sha256"]
                and actual_size == declared["size_bytes"],
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()

    environment_relpath = "data/reproduction/environment_report.json"
    environment_report = load_json(environment_relpath)
    if environment_report["source_commit"] != args.source_commit:
        raise ValueError("environment report source commit does not match the requested commit")

    image_inspect = json.loads(run_bytes(["docker", "image", "inspect", args.image]))[0]
    image_identity = {
        "schema_version": 1,
        "image_reference": args.image,
        "image_id": image_inspect["Id"],
        "repo_digests": image_inspect.get("RepoDigests", []),
        "architecture": image_inspect["Architecture"],
        "os": image_inspect["Os"],
        "created": image_inspect["Created"],
        "environment": image_inspect["Config"].get("Env", []),
    }
    image_identity_path = REPRODUCTION_ROOT / "image_identity.json"
    image_identity_path.write_text(
        json.dumps(image_identity, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )

    committed_digests = committed_tree_digests(args.source_commit)
    image_digests = image_tree_digests(args.image)
    source_records = [
        {
            "relpath": relpath,
            "committed_sha256": committed_digests.get(relpath),
            "image_sha256": image_digest,
            "match": committed_digests.get(relpath) == image_digest,
        }
        for relpath, image_digest in sorted(image_digests.items())
    ]
    missing_required_source_paths = sorted(set(REQUIRED_SOURCE_PATHS).difference(image_digests))
    unexpected_image_paths = sorted(set(image_digests).difference(committed_digests))

    image_input_digests = image_file_digests(args.image, INPUT_PATHS)
    primary_controls = load_json("data/registry/beta_plane_control_results.json")
    reproduction_controls = load_json("data/reproduction/beta_plane_control_results.json")
    input_records = []
    for relpath in INPUT_PATHS:
        host_digest = sha256_file(REPO_ROOT / relpath)
        primary_declared = primary_controls["retained_lbm_null_control"]["audit_sha256"]
        reproduction_declared = reproduction_controls["retained_lbm_null_control"]["audit_sha256"]
        input_records.append(
            {
                "relpath": relpath,
                "host_sha256": host_digest,
                "image_sha256": image_input_digests.get(relpath),
                "primary_declared_sha256": primary_declared,
                "reproduction_declared_sha256": reproduction_declared,
                "match": len(
                    {
                        host_digest,
                        image_input_digests.get(relpath),
                        primary_declared,
                        reproduction_declared,
                    }
                )
                == 1,
            }
        )

    json_records: list[dict[str, Any]] = []
    for comparison_id, primary_relpath, reproduction_relpath in JSON_COMPARISONS:
        primary_payload = load_json(primary_relpath)
        reproduction_payload = load_json(reproduction_relpath)
        primary_path = REPO_ROOT / primary_relpath
        reproduction_path = REPO_ROOT / reproduction_relpath
        json_records.append(
            {
                "comparison_id": comparison_id,
                "primary_relpath": primary_relpath,
                "reproduction_relpath": reproduction_relpath,
                "primary_sha256": sha256_file(primary_path),
                "reproduction_sha256": sha256_file(reproduction_path),
                "primary_source_commit": primary_payload.get("source_commit"),
                "reproduction_source_commit": reproduction_payload.get("source_commit"),
                "byte_identical": primary_path.read_bytes() == reproduction_path.read_bytes(),
                "normalized_json_identical": normalized_result(primary_payload)
                == normalized_result(reproduction_payload),
            }
        )

    archive_records: list[dict[str, Any]] = []
    for comparison_id, primary_relpath, reproduction_relpath in ARCHIVE_COMPARISONS:
        primary_digest = sha256_file(REPO_ROOT / primary_relpath)
        reproduction_digest = sha256_file(REPO_ROOT / reproduction_relpath)
        archive_records.append(
            {
                "comparison_id": comparison_id,
                "primary_relpath": primary_relpath,
                "reproduction_relpath": reproduction_relpath,
                "primary_sha256": primary_digest,
                "reproduction_sha256": reproduction_digest,
                "byte_identical": primary_digest == reproduction_digest,
            }
        )

    environment_records = verify_environment_outputs(environment_report)
    run_log_path = REPO_ROOT / RUN_LOG_RELPATH
    execution_receipts = environment_report.get("execution_receipts", {})
    expected_execution_receipts = {
        "production": {
            "fresh_execution_required": True,
            "work_root_existed_before": False,
            "resumed_count": 0,
            "pending_count": 540,
            "total_count": 540,
        },
        "refinement": {
            "fresh_execution_required": True,
            "work_root_existed_before": False,
            "resumed_count": 0,
            "pending_count": 48,
            "total_count": 48,
        },
    }
    cache_isolation = {
        "relpath": RUN_LOG_RELPATH,
        "sha256": sha256_file(run_log_path),
        "execution_receipts": execution_receipts,
        "expected_execution_receipts": expected_execution_receipts,
        "match": execution_receipts == expected_execution_receipts,
    }
    all_checks_passed = all(record["match"] for record in source_records)
    all_checks_passed &= not missing_required_source_paths
    all_checks_passed &= not unexpected_image_paths
    all_checks_passed &= all(record["match"] for record in input_records)
    all_checks_passed &= all(record["match"] for record in environment_records)
    all_checks_passed &= cache_isolation["match"]
    all_checks_passed &= all(record["normalized_json_identical"] for record in json_records)
    all_checks_passed &= all(record["byte_identical"] for record in archive_records)
    report = {
        "schema_version": 1,
        "source_commit": args.source_commit,
        "image_reference": args.image,
        "image_digest": image_identity["image_id"],
        "all_checks_passed": all_checks_passed,
        "environment_report": {
            "relpath": environment_relpath,
            "sha256": sha256_file(REPO_ROOT / environment_relpath),
        },
        "image_identity": {
            "relpath": str(image_identity_path.relative_to(REPO_ROOT)),
            "sha256": sha256_file(image_identity_path),
        },
        "source_identity": source_records,
        "source_tree_contract": {
            "image_file_count": len(image_digests),
            "committed_file_count": len(committed_digests),
            "missing_required_source_paths": missing_required_source_paths,
            "unexpected_image_paths": unexpected_image_paths,
            "all_image_files_match_commit": all(record["match"] for record in source_records),
        },
        "input_identity": input_records,
        "environment_outputs": environment_records,
        "cache_isolation": cache_isolation,
        "json_comparisons": json_records,
        "archive_comparisons": archive_records,
    }
    report_path = REPRODUCTION_ROOT / "verification_report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    print(f"Wrote {report_path.relative_to(REPO_ROOT)}")
    print(f"all_checks_passed={str(all_checks_passed).lower()}")
    return 0 if all_checks_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
