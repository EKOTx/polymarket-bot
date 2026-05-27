"""
Database engine and session factory.
SQLite for dev, PostgreSQL for production — same codebase.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import settings


def _make_engine():
    kwargs: dict = {}
    if not settings.is_postgres:
        kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(settings.DATABASE_URL, **kwargs)

    # SQLite performance pragmas
    if not settings.is_postgres:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(conn, _):
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA synchronous=NORMAL")

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a DB session, closes on exit."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager version for non-FastAPI code."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Create all tables. Use Alembic for migrations in production."""
    from backend.app.models import user, market  # noqa: F401 — register models
    Base.metadata.create_all(bind=engine)
