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
    print(f"Using PostgreSQL connection")
elif os.getenv("K_SERVICE"):
    # CRITICAL: Prevent data loss in Cloud Run
    raise RuntimeError(
        "CRITICAL ERROR: Attempting to use SQLite in Cloud Run environment (K_SERVICE). "
        "This will result in data loss. Setup DATABASE_URL to verify persistence."
    )

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
