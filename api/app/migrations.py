
import sqlalchemy
from sqlalchemy import text
from database import engine

def run_migrations():
    """Run database migrations on startup."""
    with engine.connect() as conn:
        try:
            # Check if is_approved exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='admin_users' AND column_name='is_approved';"))
            if not result.fetchone():
                print("Adding 'is_approved' column to 'admin_users' table...")
                conn.execute(text("ALTER TABLE admin_users ADD COLUMN is_approved BOOLEAN DEFAULT FALSE;"))
                conn.execute(text("UPDATE admin_users SET is_approved = TRUE;"))
                conn.commit()
                print("Migration successful: Added 'is_approved' column.")
            else:
                print("Migration skipped: 'is_approved' column already exists.")
        except Exception as e:
            print(f"Migration error (is_approved): {e}")

        try:
            # Check if indexing_progress exists
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='files' AND column_name='indexing_progress';"))
            if not result.fetchone():
                print("Adding 'indexing_progress' column to 'files' table...")
                conn.execute(text("ALTER TABLE files ADD COLUMN indexing_progress INTEGER DEFAULT 0;"))
                conn.commit()
                print("Migration successful: Added 'indexing_progress' column.")
            else:
                print("Migration skipped: 'indexing_progress' column already exists.")
        except Exception as e:
            print(f"Migration error (indexing_progress): {e}")
