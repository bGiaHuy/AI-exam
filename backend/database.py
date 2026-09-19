"""
================================================================================
DATABASE ENGINE & SESSION MANAGEMENT (SQLITE 3 + WAL MODE)
================================================================================
Enforces WAL mode & Foreign Keys per AGENTS.md specs.
Provides get_db FastAPI dependency with strict session cleanup.
================================================================================
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

# Database path resolution: stores cheating_system.db in project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "cheating_system.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# SQLite Engine with multi-thread access for FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Enforce WAL mode & Foreign Keys on every connection pool per AGENTS.md Rule 7
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI dependency for database session management.
    Ensures connection is closed after request lifecycle to prevent dangling locks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
