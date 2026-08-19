"""Unit tests for validate_pdf, which gates resume uploads.

Regression coverage for the mobile-upload bug: validation used to compare
``file.content_type`` against "application/pdf", but mobile file pickers often
report an empty or generic MIME type for a valid PDF, so uploads failed at
random depending on which picker the user chose.
"""

import io

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from utils.file_validator import validate_pdf

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def make_upload(data: bytes, content_type: str | None = None) -> UploadFile:
    """Build an UploadFile, optionally with a specific reported content type."""
    headers = Headers({"content-type": content_type}) if content_type else None
    return UploadFile(file=io.BytesIO(data), filename="resume.pdf", headers=headers)


def test_accepts_valid_pdf():
    """A real PDF with the correct content type passes."""
    validate_pdf(make_upload(MINIMAL_PDF, "application/pdf"))


@pytest.mark.parametrize(
    "content_type",
    [
        None,                        # picker reported nothing at all
        "",                          # blank type
        "application/octet-stream",  # Android Files / Drive generic fallback
        "application/x-pdf",         # some scanner apps
        "text/plain",                # misdetected by the OS
    ],
)
def test_accepts_valid_pdf_regardless_of_reported_content_type(content_type):
    """The mobile bug: a valid PDF must pass even when the MIME type is wrong.

    This is the core regression guard — every one of these previously 400'd.
    """
    validate_pdf(make_upload(MINIMAL_PDF, content_type))


def test_rejects_non_pdf_even_when_labelled_as_pdf():
    """Content wins over the label, so a spoofed content type is still rejected."""
    with pytest.raises(HTTPException) as exc:
        validate_pdf(make_upload(b"GIF89a this is not a pdf", "application/pdf"))

    assert exc.value.status_code == 400
    assert exc.value.detail == "Only PDF files allowed"


def test_rejects_empty_file():
    """An empty upload reports that specifically rather than 'not a PDF'."""
    with pytest.raises(HTTPException) as exc:
        validate_pdf(make_upload(b"", "application/pdf"))

    assert exc.value.status_code == 400
    assert exc.value.detail == "Uploaded file is empty"


def test_rejects_file_shorter_than_the_magic_prefix():
    """A truncated header must not slip through as a partial match."""
    with pytest.raises(HTTPException) as exc:
        validate_pdf(make_upload(b"%PD", "application/pdf"))

    assert exc.value.status_code == 400
    assert exc.value.detail == "Only PDF files allowed"


def test_rewinds_stream_so_the_service_still_reads_full_content():
    """validate_pdf consumes bytes to inspect them, so it must seek back to 0.

    Without the rewind the upload would silently lose its first 5 bytes and the
    stored PDF would be corrupt.
    """
    upload = make_upload(MINIMAL_PDF, "application/pdf")

    validate_pdf(upload)

    assert upload.file.read() == MINIMAL_PDF
