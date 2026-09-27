"""Engine and session factory for the SQLite metadata/audit database."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base

SessionFactory = sessionmaker[Session]


def make_session_factory(sqlite_path: Path) -> SessionFactory:
    """Create the database file (and tables) if needed and return a session factory."""
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{sqlite_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)
