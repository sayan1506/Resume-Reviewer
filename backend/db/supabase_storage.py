from supabase import create_client
import os
from urllib.parse import urlparse, unquote
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


def extract_object_path(file_url: str) -> str:
    """Derive the storage object path (relative to the bucket) from a stored file URL.

    Stored URLs look like
    https://<project>.supabase.co/storage/v1/object/public/<bucket>/<object>,
    so we slice everything after the bucket segment. Falls back to the last path
    segment for any unexpected URL shape.
    """
    path = urlparse(file_url).path
    marker = f"/{SUPABASE_BUCKET}/"
    idx = path.find(marker)
    if idx != -1:
        return unquote(path[idx + len(marker):])
    return unquote(path.rsplit("/", 1)[-1])


def create_signed_url(object_path: str, expires_in: int = 300) -> str:
    """Generate a short-lived signed URL for a private-bucket object."""
    result = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(
        path=object_path,
        expires_in=expires_in,
    )
    # SDK key has varied across versions ("signedURL" vs "signedUrl")
    return result.get("signedURL") or result.get("signedUrl")