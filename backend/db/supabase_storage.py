from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_pdf(file, filename):

    file_bytes = file.read()

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=filename,
        file=file_bytes,
        file_options={"content-type": "application/pdf"}
    )

    file_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"

    return file_url