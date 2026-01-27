
import os
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
            print("Attempting to add 'is_approved' column to 'admin_users' table...")
            conn.execute(text("ALTER TABLE admin_users ADD COLUMN is_approved BOOLEAN DEFAULT FALSE;"))
            conn.commit()
            print("Success: Column added.")
            
            print("Setting existing users to approved...")
            conn.execute(text("UPDATE admin_users SET is_approved = TRUE;"))
            conn.commit()
            print("Success: Existing users approved.")
            
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                print("Info: Column 'is_approved' already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
