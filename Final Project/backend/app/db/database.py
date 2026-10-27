"""
database.py — SQLModel engine and session factory.

Dev:  SQLite  (no extra setup required)
Prod: Postgres (set DATABASE_URL=postgresql+psycopg2://user:pass@host/db)

All models register themselves on the shared metadata via SQLModel.
Call `create_db_and_tables()` once at app startup (in lifespan).
"""
from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
# connect_args only used for SQLite — ignored by Postgres.
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    echo=False,
)


def create_db_and_tables() -> None:
    """Create all tables from registered SQLModel metadata (idempotent)."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency — yields a database session."""
    with Session(engine) as session:
        yield session
