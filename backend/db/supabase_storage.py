from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_pdf(file_bytes: bytes, filename: str) -> str:
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=filename,
        file=file_bytes,
        file_options={"content-type": "application/pdf"}
    )

    # Use the SDK's URL builder instead of manual string construction
    file_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)

    return file_url