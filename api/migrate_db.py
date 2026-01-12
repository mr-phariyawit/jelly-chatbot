
import os
import sqlalchemy
from sqlalchemy import create_engine, text

# Get DB URL from env or use default (same as main.py)
# Note: In Cloud Run, this is set. Locally, we might need to set it or rely on valid default.
# For this script, we assume the user has the env var set or we use the cloud sql proxy one if available.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set.")
    exit(1)

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            print("Attempting to add 'description' column to 'files' table...")
            conn.execute(text("ALTER TABLE files ADD COLUMN description TEXT;"))
            conn.commit()
            print("Success: Column added.")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("Info: Column 'description' already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
