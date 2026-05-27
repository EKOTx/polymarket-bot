"""
Database engine, session factory, and init.
Uses SQLite via SQLAlchemy 2.0 sync API.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from database.models import Base


def _get_db_url() -> str:
    raw = os.getenv("DATABASE_URL", "sqlite:///data/polymarket.db")
    # Ensure data/ directory exists for relative paths
    if raw.startswith("sqlite:///") and not raw.startswith("sqlite:////"):
        rel_path = raw.removeprefix("sqlite:///")
        Path(rel_path).parent.mkdir(parents=True, exist_ok=True)
    return raw


DATABASE_URL = _get_db_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable WAL mode and foreign keys for SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Create all tables if they don't exist."""
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    """
    Get a new DB session. Caller is responsible for closing.
    Use as context manager: `with get_session() as s:`
    """
    return SessionLocal()


def session_scope():
    """Context manager for a DB session with auto-commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
