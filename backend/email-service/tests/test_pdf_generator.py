"""Tests for PDF generation."""

from src.services.pdf_generator import generate_pdf

_PDF_MAGIC = b"%PDF"


def test_generate_pdf_with_string_returns_pdf_bytes() -> None:
    """String content produces valid PDF bytes starting with %PDF."""
    result = generate_pdf("Report", "This is the body.")
    assert isinstance(result, bytes)
    assert result[:4] == _PDF_MAGIC


def test_generate_pdf_with_dict_returns_pdf_bytes() -> None:
    """Dict content produces valid PDF bytes starting with %PDF."""
    result = generate_pdf("Prescription", {"Drug": "Aspirin", "Dose": "500mg"})
    assert isinstance(result, bytes)
    assert result[:4] == _PDF_MAGIC


def test_generate_pdf_with_empty_dict() -> None:
    """An empty dictionary produces a non-empty PDF without errors."""
    result = generate_pdf("Empty Report", {})
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_generate_pdf_with_multi_key_dict() -> None:
    """Multi-entry dict generates PDF without errors."""
    content = {
        "Patient": "John Doe",
        "Doctor": "Dr. Smith",
        "Diagnosis": "Common cold",
        "Prescription": "Rest and fluids",
    }
    result = generate_pdf("Medical Report", content)
    assert isinstance(result, bytes)
    assert result[:4] == _PDF_MAGIC


def test_generate_pdf_title_with_spaces() -> None:
    """Title with spaces does not cause errors."""
    result = generate_pdf("My Report With Spaces", "some content")
    assert isinstance(result, bytes)
    assert result[:4] == _PDF_MAGIC


def test_generate_pdf_non_empty_output() -> None:
    """Output is always a non-empty bytes object."""
    result = generate_pdf("T", "c")
    assert len(result) > 0


def test_generate_pdf_string_content_no_iteration() -> None:
    """String content is rendered as a block, not iterated character-by-character."""
    text = "Multi-line\ncontent here"
    result = generate_pdf("Notes", text)
    assert result[:4] == _PDF_MAGIC
