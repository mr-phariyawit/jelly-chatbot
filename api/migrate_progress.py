
import os
import sqlalchemy
from sqlalchemy import create_engine, text

# Get DB URL from env
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set.")
    exit(1)

def migrate():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        try:
            print("Attempting to add 'indexing_progress' column to 'files' table...")
            conn.execute(text("ALTER TABLE files ADD COLUMN indexing_progress INTEGER DEFAULT 0;"))
            conn.commit()
            print("Success: Column added.")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("Info: Column 'indexing_progress' already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
