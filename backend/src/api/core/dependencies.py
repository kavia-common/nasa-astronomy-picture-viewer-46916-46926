from typing import Generator
from sqlalchemy.orm import Session
from src.api.db import get_db

# Keep a reference for shutdown cleanup if needed
_last_session: Session | None = None

# PUBLIC_INTERFACE
def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency to provide a SQLAlchemy session to request handlers.

    Yields:
        Session: Active database session.
    """
    global _last_session
    for db in get_db():
        _last_session = db
        yield db


def close_db_session() -> None:
    """
    Close the last opened database session if still open.
    """
    global _last_session
    try:
        if _last_session is not None:
            _last_session.close()
    finally:
        _last_session = None
