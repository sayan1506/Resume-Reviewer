from backend.db.supabase_storage import upload_pdf

try:
    with open("test.pdf", "rb") as f:
        url = upload_pdf(f, "test_resume.pdf")

    print("Supabase upload successful")
    print("File URL:", url)

except Exception as e:
    print("Supabase upload failed:", e)