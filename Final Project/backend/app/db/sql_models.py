"""
sql_models.py — SQLModel table definitions (SQLite dev / Postgres prod).

These are the persistent database representations. They mirror the Pydantic
models in app/models/ but use SQLModel's table=True so SQLAlchemy manages the
schema.

Relationship to Pydantic models:
  CaseTable     ↔  app.models.case.CaseRecord
  NoticeTable   ↔  app.models.notice.LegalNotice
  ReviewerTable ↔  app.models.reviewer.ReviewerRecord

The Store class in store.py converts between these table rows and the Pydantic
models transparently so routers and services never touch SQLAlchemy directly.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import Column, Field, SQLModel, Text


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid4())


# ── CaseTable ─────────────────────────────────────────────────────────────────

class CaseTable(SQLModel, table=True):
    __tablename__ = "cases"

    id: str = Field(default_factory=_uuid, primary_key=True)
    dispute_category: str
    status: str = "intake_in_progress"

    # LegalFacts and conversation_history are stored as JSON text
    facts_json: str = Field(default="{}", sa_column=Column(Text))
    conversation_json: str = Field(default="[]", sa_column=Column(Text))

    notice_id: Optional[str] = None
    settlement_id: Optional[str] = None
    language: str = "en"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ── NoticeTable ───────────────────────────────────────────────────────────────

class NoticeTable(SQLModel, table=True):
    __tablename__ = "notices"

    id: str = Field(default_factory=_uuid, primary_key=True)
    case_id: str = Field(index=True)
    draft_body: str = Field(sa_column=Column(Text))
    plain_language_guide: str = Field(default="", sa_column=Column(Text))

    # Citations stored as JSON array text
    citations_json: str = Field(default="[]", sa_column=Column(Text))

    review_status: str = "auto_drafted"
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = Field(default=None, sa_column=Column(Text))
    approved_body: Optional[str] = Field(default=None, sa_column=Column(Text))
    pdf_path: Optional[str] = None
    pdf_hash: Optional[str] = None
    settlement_token: Optional[str] = Field(default=None, sa_column=Column(Text))
    settlement_url: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ── ReviewerTable ─────────────────────────────────────────────────────────────

class ReviewerTable(SQLModel, table=True):
    __tablename__ = "reviewers"

    id: str = Field(default_factory=_uuid, primary_key=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: str
    email: str
    role: str = "student"
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)
