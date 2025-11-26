from __future__ import annotations

from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.api.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


_engine = None
_SessionLocal: Optional[sessionmaker[Session]] = None


def _create_engine():
    settings = get_settings()
    db_url = settings.database_url
    connect_args = {}
    if db_url.startswith("sqlite"):
        # Needed for SQLite in multi-threaded contexts
        connect_args = {"check_same_thread": False}
    engine = create_engine(db_url, echo=False, future=True, connect_args=connect_args)
    if db_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()
    return engine


# PUBLIC_INTERFACE
def init_db() -> None:
    """
    Initialize database engine, session factory, and create all tables.
    """
    global _engine, _SessionLocal
    if _engine is None:
        _engine = _create_engine()
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)
        # Import models and create tables
        from src.api.models import APODCache  # noqa: F401
        Base.metadata.create_all(bind=_engine)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """
    Yield a new SQLAlchemy Session.

    Yields:
        Session: SQLAlchemy session bound to the application engine.
    """
    if _SessionLocal is None:
        init_db()
        # After init_db, _SessionLocal is guaranteed to be set
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
