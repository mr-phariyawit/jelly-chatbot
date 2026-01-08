from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os
from google.cloud.sql.connector import Connector, IPTypes
import pg8000

from models import Base

# Configuration
# Configuration
INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

# Try to extract from DATABASE_URL if individual vars are missing
if os.getenv("DATABASE_URL") and not (DB_USER and DB_PASS and DB_NAME):
    try:
        from sqlalchemy.engine.url import make_url
        url = make_url(os.getenv("DATABASE_URL"))
        DB_USER = url.username or DB_USER or "postgres"
        DB_PASS = url.password or DB_PASS
        DB_NAME = url.database or DB_NAME or "session_db"
        print(f"Extracted credentials from DATABASE_URL for user: {DB_USER}")
    except Exception as e:
        print(f"Failed to parse DATABASE_URL: {e}")

# Defaults
DB_USER = DB_USER or "postgres"
DB_PASS = DB_PASS or "ChangeMe123!"
DB_NAME = DB_NAME or "session_db"

# Initialize Connector
connector = None

def getconn():
    """Create database connection using the Connector."""
    global connector
    if connector is None:
        connector = Connector()
    
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        ip_type=IPTypes.PUBLIC,
    )
    return conn

# Create SessionLocal factory
if INSTANCE_CONNECTION_NAME:
    # Cloud SQL Connection
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
else:
    # SQLite fallback for local development
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sessions.db")
    connect_args = {}
    if DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables."""
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
