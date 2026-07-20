"""Tests for canonical text-corpus inclusion boundaries."""

from scripts.normalize_txt_to_json import should_include, to_toml


def test_retained_framework_text_is_included():
    assert should_include("source_materials/frameworks/example.txt")


def test_generated_build_text_is_excluded():
    assert not should_include("build/document_ocr/tesseract/page-0001.txt")


def test_generated_normalized_text_is_excluded():
    assert not should_include("data/normalized/example.txt")


def test_registry_toml_escapes_non_ascii_paths():
    payload = to_toml(
        [
            {
                "id": "aether",
                "source_relpath": "source_materials/frameworks/\u00c6ther.txt",
                "normalized_relpath": "data/normalized/aether.json",
                "category": "source_materials",
                "sha256": "0" * 64,
                "line_count": 1,
                "size_bytes": 1,
            }
        ]
    )
    payload.encode("ascii")
    assert "\\u00c6ther.txt" in payload
