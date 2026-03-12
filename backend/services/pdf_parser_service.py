from fastapi import HTTPException
import requests
from utils.pdf_parser import extract_text_from_pdf


def parse_resume_service(file_url: str):

    response = requests.get(file_url)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to download PDF")

    pdf_bytes = response.content

    text = extract_text_from_pdf(pdf_bytes)

    return text