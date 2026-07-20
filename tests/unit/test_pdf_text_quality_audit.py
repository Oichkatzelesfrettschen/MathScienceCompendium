"""Unit tests for PDF text-quality routing policy."""

from scripts.audit_pdf_text_quality import classify_document, page_metrics
from scripts.run_tesseract_pdf_ocr import parse_page_spec


def test_page_metrics_routes_sparse_text_to_ocr():
    metrics = page_metrics("short page", minimum_nonspace_characters=20)
    assert metrics["ocr_recommended"]


def test_page_metrics_keeps_dense_native_text():
    metrics = page_metrics("word " * 100, minimum_nonspace_characters=250)
    assert not metrics["ocr_recommended"]


def test_replacement_character_routes_page_to_ocr():
    metrics = page_metrics("word " * 100 + "\ufffd", minimum_nonspace_characters=250)
    assert metrics["ocr_recommended"]


def test_document_classification_distinguishes_mixed_pages():
    page_rows = [
        {"ocr_recommended": False},
        {"ocr_recommended": True},
    ]
    assert classify_document(page_rows) == "native_text_mixed"


def test_page_spec_parses_sorted_unique_pages_and_ranges():
    assert parse_page_spec("7,2-4,3") == [2, 3, 4, 7]
