from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os

from models import Base


# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sessions.db")

# Create engine with appropriate configuration
connect_args = {}
# For PostgreSQL with Unix socket (Cloud Run), use psycopg2
if "postgresql" in DATABASE_URL:
    # Replace pg8000 with psycopg2 if present
    DATABASE_URL = DATABASE_URL.replace("postgresql+pg8000://", "postgresql://")
    print("Using PostgreSQL connection")
elif os.getenv("K_SERVICE"):
    # CRITICAL: Prevent data loss in Cloud Run
    raise RuntimeError(
        "CRITICAL ERROR: Attempting to use SQLite in Cloud Run environment (K_SERVICE). "
        "This will result in data loss. Setup DATABASE_URL to verify persistence."
    )

# Create engine with connection pooling for better performance
if "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args,
        pool_size=5,           # Number of permanent connections
        max_overflow=10,       # Extra connections when pool is full
        pool_timeout=30,       # Wait time for available connection
        pool_recycle=1800,     # Recycle connections every 30 minutes
        pool_pre_ping=True,    # Verify connection before use
    )
else:
    engine = create_engine(DATABASE_URL, connect_args=connect_args)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
    # Enable pgvector if using PostgreSQL
    if engine.dialect.name == 'postgresql':
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
                print("Enabled pgvector extension")
        except Exception as e:
            print(f"Warning: Failed to enable pgvector extension: {e}")

    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def migrate_db():
    """Run database migrations safely."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            # 1. Add status column to files table
            try:
                conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT 'pending';"))
                conn.commit()
                print("Migration: Added status column to files table")
            except Exception as e:
                print(f"Migration warning (status column): {e}")

            # 2. Add gcs_uri column to files table
            try:
                conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS gcs_uri VARCHAR;"))
                conn.commit()
                print("Migration: Added gcs_uri column to files table")
            except Exception as e:
                print(f"Migration warning (files.gcs_uri column): {e}")

            # 3. Add gcs_uri column to messages table
            try:
                conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS gcs_uri VARCHAR;"))
                conn.commit()
                print("Migration: Added gcs_uri column to messages table")
            except Exception as e:
                print(f"Migration warning (messages.gcs_uri column): {e}")

            # 4. Add size_bytes column to messages table
            try:
                conn.execute(text("ALTER TABLE messages ADD COLUMN IF NOT EXISTS size_bytes INTEGER DEFAULT 0;"))
                conn.commit()
                print("Migration: Added size_bytes column to messages table")
            except Exception as e:
                print(f"Migration warning (messages.size_bytes column): {e}")

            # 5. Add indexing_progress column to files table
            try:
                conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS indexing_progress INTEGER DEFAULT 0;"))
                conn.commit()
                print("Migration: Added indexing_progress column to files table")
            except Exception as e:
                print(f"Migration warning (files.indexing_progress column): {e}")

            # 3. Create bot_logs table if not exists (Manual fallback for create_all)
            try:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS bot_logs (
                        id VARCHAR PRIMARY KEY,
                        bot_id VARCHAR NOT NULL,
                        level VARCHAR DEFAULT 'INFO',
                        event_type VARCHAR NOT NULL,
                        message TEXT NOT NULL,
                        log_metadata TEXT,
                        created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() at time zone 'utc'),
                        FOREIGN KEY (bot_id) REFERENCES bots(id)
                    );
                """))
                conn.commit()
                print("Migration: Verified bot_logs table")
            except Exception as e:
                print(f"Migration warning (bot_logs table): {e}")
                
    except Exception as e:
        print(f"Migration failed completely (DB Connection?): {e}")
