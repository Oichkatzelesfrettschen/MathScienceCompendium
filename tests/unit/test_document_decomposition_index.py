"""Tests for document-decomposition indexing helpers."""

from pathlib import Path

import pytest
from scripts.index_document_decomposition import build_audit, resolve_repo_path, sha256_file


def test_sha256_file_tracks_content(tmp_path: Path):
    first_path = tmp_path / "first.txt"
    second_path = tmp_path / "second.txt"
    first_path.write_bytes(b"same")
    second_path.write_bytes(b"same")
    assert sha256_file(first_path) == sha256_file(second_path)
    second_path.write_bytes(b"different")
    assert sha256_file(first_path) != sha256_file(second_path)


def test_resolve_repo_path_preserves_absolute_path(tmp_path: Path):
    assert resolve_repo_path(tmp_path) == tmp_path


def test_build_audit_rejects_failed_mineru_registry(tmp_path: Path):
    run_registry = tmp_path / "run.json"
    run_registry.write_text('{"failed_count": 1}\n', encoding="ascii")
    with pytest.raises(ValueError, match="failed sources"):
        build_audit(tmp_path / "pdfs", tmp_path / "outputs", run_registry)
