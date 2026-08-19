from fastapi import UploadFile, HTTPException

PDF_MAGIC = b"%PDF-"


def validate_pdf(file: UploadFile):
    """Verify the upload is really a PDF by inspecting its header bytes.

    We deliberately do NOT gate on ``file.content_type``. Mobile file pickers
    (Google Drive, the Android Files app, scanner apps) routinely report an
    empty type or ``application/octet-stream`` for a perfectly valid PDF, so
    trusting that header made mobile uploads fail intermittently. The magic
    bytes are authoritative and cannot be spoofed by a picker quirk.
    """
    header = file.file.read(len(PDF_MAGIC))
    file.file.seek(0)  # rewind so the service can still read the whole stream

    if not header:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if header != PDF_MAGIC:
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
