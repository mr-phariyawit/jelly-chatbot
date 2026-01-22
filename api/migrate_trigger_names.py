"""
Migration script to add trigger_names column to bots table
Run this script to add support for group chat trigger names
Compatible with both SQLite (local) and PostgreSQL (production)
"""
from database import engine
from sqlalchemy import text, inspect

def migrate():
    """Add trigger_names column if it doesn't exist"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('bots')]
    
    if 'trigger_names' in columns:
        print("✅ Column trigger_names already exists. Nothing to do.")
        return
    
    with engine.connect() as conn:
        try:
            # Simple ALTER TABLE works for both SQLite and PostgreSQL
            conn.execute(text("ALTER TABLE bots ADD COLUMN trigger_names TEXT"))
            conn.commit()
            print("✅ Migration complete: Added trigger_names column to bots table")
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()
