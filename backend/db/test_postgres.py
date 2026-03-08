from backend.db.postgres import engine

try:
    conn = engine.connect()
    print("PostgreSQL connection successful")
    conn.close()
except Exception as e:
    print("PostgreSQL connection failed:", e)