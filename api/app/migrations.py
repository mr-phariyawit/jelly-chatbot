
import sqlalchemy
from sqlalchemy import text, inspect
from database import engine

def run_migrations():
    """Run database migrations on startup."""
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # 1. Check admin_users.is_approved
        try:
            columns = [col['name'] for col in inspector.get_columns('admin_users')]
            if 'is_approved' not in columns:
                print("Adding 'is_approved' column to 'admin_users' table...")
                conn.execute(text("ALTER TABLE admin_users ADD COLUMN is_approved BOOLEAN DEFAULT FALSE;"))
                conn.execute(text("UPDATE admin_users SET is_approved = TRUE;"))
                conn.commit()
                print("Migration successful: Added 'is_approved' column.")
            else:
                print("Migration skipped: 'is_approved' column already exists.")
        except Exception as e:
            print(f"Migration error (is_approved): {e}")

        # 2. Check files.indexing_progress
        try:
            columns = [col['name'] for col in inspector.get_columns('files')]
            if 'indexing_progress' not in columns:
                print("Adding 'indexing_progress' column to 'files' table...")
                conn.execute(text("ALTER TABLE files ADD COLUMN indexing_progress INTEGER DEFAULT 0;"))
                conn.commit()
                print("Migration successful: Added 'indexing_progress' column.")
            else:
                print("Migration skipped: 'indexing_progress' column already exists.")
        except Exception as e:
            print(f"Migration error (indexing_progress): {e}")

        # 3. Check bots.trigger_names
        try:
            columns = [col['name'] for col in inspector.get_columns('bots')]
            if 'trigger_names' not in columns:
                print("Adding 'trigger_names' column to 'bots' table...")
                conn.execute(text("ALTER TABLE bots ADD COLUMN trigger_names TEXT;"))
                conn.commit()
                print("Migration successful: Added 'trigger_names' column.")
            else:
                print("Migration skipped: 'trigger_names' column already exists.")
        except Exception as e:
            print(f"Migration error (trigger_names): {e}")
