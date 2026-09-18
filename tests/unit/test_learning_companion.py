"""Exercise companion snapshots using local repositories and a trivial build."""

import importlib.util
import subprocess
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/prepare_learning_companion.py"
SPEC = importlib.util.spec_from_file_location("learning_companion", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
companion = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(companion)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    root = tmp_path / "external"
    root.mkdir()
    for arguments in [
        ["init"],
        ["config", "user.email", "fixture@example.invalid"],
        ["config", "user.name", "Fixture"],
    ]:
        subprocess.run(["git", "-C", str(root), *arguments], check=True, capture_output=True)
    (root / "lesson.tex").write_text("committed\n")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "Initial"], check=True)
    (root / "lesson.tex").write_text("working\n")
    (root / "new.tex").write_text("new\n")
    return root


def test_overlay_reuse_and_preservation(source: Path, tmp_path: Path) -> None:
    output = tmp_path / "snapshot"
    before = companion.observe(source)
    companion.prepare(source, output, prepare_only=True)
    assert (output / "lesson.tex").read_text() == "working\n"
    assert (output / "new.tex").read_text() == "new\n"
    companion.prepare(source, output, prepare_only=True)
    assert companion.observe(source) == before
    (output / "lesson.tex").write_text("unrelated edit\n")
    with pytest.raises(ValueError, match="fresh --output"):
        companion.prepare(source, output, prepare_only=True)
    assert (output / "lesson.tex").read_text() == "unrelated edit\n"


def test_reject_unsafe_and_stale_outputs(source: Path, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        companion.prepare(source, source / "snapshot", prepare_only=True)
    with pytest.raises(ValueError, match="ownership"):
        companion.prepare(source, tmp_path, prepare_only=True)
    output = tmp_path / "snapshot"
    companion.prepare(source, output, prepare_only=True)
    marker = (output / companion.MARKER).read_bytes()
    (source / "new.tex").write_text("changed\n")
    with pytest.raises(ValueError, match="changed"):
        companion.prepare(source, output, prepare_only=True)
    assert (output / companion.MARKER).read_bytes() == marker


def test_build_boundary(source: Path, tmp_path: Path) -> None:
    (source / "Makefile").write_text(
        "pdf:\n\tmkdir -p build\n\tprintf '%s' \"$$TEXMFVAR\" > build/cache-location\n"
    )
    before = companion.observe(source)
    output = tmp_path / "snapshot"
    companion.prepare(source, output)
    assert (output / "build/cache-location").read_text() == str(output / "build/texmf-var")
    assert companion.observe(source) == before
    assert not (source / "build").exists()
