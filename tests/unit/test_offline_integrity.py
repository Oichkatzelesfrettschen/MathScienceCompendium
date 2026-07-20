from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

from scripts import verify_offline_integrity


if TYPE_CHECKING:
    from pathlib import Path


def write_registry(path: Path, table_name: str, artifact_relpath: str, payload: bytes) -> None:
    digest = hashlib.sha256(payload).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                'generated_by = "test"',
                'generated_at_utc = "2026-07-18T00:00:00+00:00"',
                "",
                f"[[{table_name}]]",
                f'relpath = "{artifact_relpath}"',
                'kind = "test_artifact"',
                f"size_bytes = {len(payload)}",
                f'sha256 = "{digest}"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_artifact_registry_contents_detects_live_byte_drift(
    tmp_path: Path,
    monkeypatch,
) -> None:
    artifact_relpath = "results/example.bin"
    artifact_path = tmp_path / artifact_relpath
    artifact_path.parent.mkdir(parents=True)
    payload = b"canonical evidence"
    artifact_path.write_bytes(payload)

    write_registry(
        tmp_path / "data/registry/artifacts_index.toml",
        "artifacts",
        artifact_relpath,
        payload,
    )
    write_registry(
        tmp_path / "data/registry/experiments_index.toml",
        "experiments",
        artifact_relpath,
        payload,
    )
    monkeypatch.setattr(verify_offline_integrity, "REPO_ROOT", tmp_path)

    assert verify_offline_integrity.check_artifact_registry_contents() == []

    artifact_path.write_bytes(b"changed evidence")
    failures = verify_offline_integrity.check_artifact_registry_contents()

    assert any("size mismatch" in failure for failure in failures)
    assert any("SHA-256 mismatch" in failure for failure in failures)


def test_artifact_registry_contents_rejects_missing_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    payload = b"missing evidence"
    artifact_relpath = "results/missing.bin"
    write_registry(
        tmp_path / "data/registry/artifacts_index.toml",
        "artifacts",
        artifact_relpath,
        payload,
    )
    write_registry(
        tmp_path / "data/registry/experiments_index.toml",
        "experiments",
        artifact_relpath,
        payload,
    )
    monkeypatch.setattr(verify_offline_integrity, "REPO_ROOT", tmp_path)

    failures = verify_offline_integrity.check_artifact_registry_contents()

    assert len(failures) == 2
    assert all("missing indexed file" in failure for failure in failures)


def test_corpus_registry_detects_stale_source_hash(tmp_path: Path, monkeypatch) -> None:
    source_relpath = "source_materials/frameworks/example.txt"
    normalized_relpath = "data/normalized/corpus/example.json"
    source_path = tmp_path / source_relpath
    source_path.parent.mkdir(parents=True)
    source_payload = b"first line\nsecond line\n"
    source_path.write_bytes(source_payload)
    digest = hashlib.sha256(source_payload).hexdigest()

    normalized_path = tmp_path / normalized_relpath
    normalized_path.parent.mkdir(parents=True)
    normalized_path.write_text(
        json.dumps(
            {
                "source_relpath": source_relpath,
                "sha256": digest,
                "size_bytes": len(source_payload),
                "line_count": 3,
            }
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "data/registry/corpus_index.toml"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        "\n".join(
            [
                "[[documents]]",
                f'source_relpath = "{source_relpath}"',
                f'normalized_relpath = "{normalized_relpath}"',
                f'sha256 = "{digest}"',
                f"size_bytes = {len(source_payload)}",
                "line_count = 3",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verify_offline_integrity, "REPO_ROOT", tmp_path)

    assert verify_offline_integrity.check_corpus_registry() == []
    source_path.write_text("changed\n", encoding="utf-8")

    failures = verify_offline_integrity.check_corpus_registry()
    assert any("SHA-256 mismatch" in failure for failure in failures)
    assert any("size mismatch" in failure for failure in failures)


def test_corpus_registry_rejects_generated_build_sources(tmp_path: Path, monkeypatch) -> None:
    source_relpath = "build/document_ocr/page.txt"
    normalized_relpath = "data/normalized/corpus/page.json"
    payload = b"generated\n"
    digest = hashlib.sha256(payload).hexdigest()
    source_path = tmp_path / source_relpath
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(payload)
    normalized_path = tmp_path / normalized_relpath
    normalized_path.parent.mkdir(parents=True)
    normalized_path.write_text(
        json.dumps(
            {
                "source_relpath": source_relpath,
                "sha256": digest,
                "size_bytes": len(payload),
                "line_count": 2,
            }
        ),
        encoding="utf-8",
    )
    registry_path = tmp_path / "data/registry/corpus_index.toml"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        "\n".join(
            [
                "[[documents]]",
                f'source_relpath = "{source_relpath}"',
                f'normalized_relpath = "{normalized_relpath}"',
                f'sha256 = "{digest}"',
                f"size_bytes = {len(payload)}",
                "line_count = 2",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(verify_offline_integrity, "REPO_ROOT", tmp_path)

    failures = verify_offline_integrity.check_corpus_registry()
    assert any("generated build file admitted" in failure for failure in failures)


def test_absolute_path_check_ignores_generated_caches(tmp_path: Path, monkeypatch) -> None:
    fixture_absolute_path = "/" + "home/example/typeshed/file.pyi"
    cache_path = tmp_path / ".mypy_cache" / "entry.json"
    cache_path.parent.mkdir(parents=True)
    cache_path.write_text(
        json.dumps({"path": fixture_absolute_path}) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(verify_offline_integrity, "REPO_ROOT", tmp_path)

    assert verify_offline_integrity.check_no_absolute_local_paths() == []

    document_path = tmp_path / "docs" / "bad.json"
    document_path.parent.mkdir(parents=True)
    document_path.write_text(
        json.dumps({"path": fixture_absolute_path}) + "\n", encoding="utf-8"
    )
    failures = verify_offline_integrity.check_no_absolute_local_paths()
    assert any("docs/bad.json" in failure for failure in failures)


def test_absolute_path_check_distinguishes_latex_commands_from_windows_paths(
    tmp_path: Path, monkeypatch
) -> None:
    documents = tmp_path / "docs"
    documents.mkdir(parents=True)
    (documents / "formula.json").write_text(
        json.dumps({"formula": r"S:\tau"}) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(verify_offline_integrity, "REPO_ROOT", tmp_path)
    assert verify_offline_integrity.check_no_absolute_local_paths() == []

    windows_path = "C:" + "\\Users\\researcher\\paper.pdf"
    (documents / "windows-path.json").write_text(
        json.dumps({"path": windows_path}) + "\n",
        encoding="utf-8",
    )
    failures = verify_offline_integrity.check_no_absolute_local_paths()
    assert any("docs/windows-path.json" in failure for failure in failures)


def test_tracked_latex_intermediate_classification() -> None:
    tracked_paths = [
        "papers/main.pdf",
        "papers/main.tex",
        "papers/main.aux",
        "papers/main.bbl",
        "papers/main.run.xml",
        "papers/main-blx.bib",
        "papers/sections/review_scope_method.tex",
        "docs/example.aux",
    ]

    assert verify_offline_integrity.classify_tracked_latex_intermediates(
        tracked_paths
    ) == [
        "papers/main-blx.bib",
        "papers/main.aux",
        "papers/main.bbl",
        "papers/main.run.xml",
    ]
