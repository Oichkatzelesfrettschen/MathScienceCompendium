"""Tests for OCR comparison metrics."""

from scripts.compare_pdf_ocr_outputs import sha256_bytes, text_metrics


def test_text_metrics_count_words_lines_and_nonspace():
    metrics = text_metrics("alpha beta\n123\n")
    assert metrics["word_tokens"] == 3
    assert metrics["line_count"] == 2
    assert metrics["nonspace_characters"] == 12


def test_sha256_bytes_is_deterministic():
    assert sha256_bytes(b"evidence") == sha256_bytes(b"evidence")
    assert sha256_bytes(b"evidence") != sha256_bytes(b"claim")
