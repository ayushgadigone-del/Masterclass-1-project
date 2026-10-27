"""
store.py — database-backed store with the same dict-like API as before.

The public interface is unchanged so all routers and services work without
modification:
    get(id) -> M | None
    put(obj) -> M
    list_all() -> list[M]
    filter(**kwargs) -> list[M]
    delete(id) -> bool

Internally this now uses SQLModel (SQLite for dev, Postgres for prod).
The Store translates between Pydantic models and SQLModel table rows via
JSON serialisation for complex nested fields (facts, citations, conversation).
"""
from __future__ import annotations

import json
import threading
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import settings

M = TypeVar("M", bound=BaseModel)


# ── Conversion helpers ────────────────────────────────────────────────────────

def _case_to_row(obj) -> "CaseTable":
    from app.db.sql_models import CaseTable
    return CaseTable(
        id=obj.id,
        dispute_category=obj.dispute_category,
        status=obj.status,
        facts_json=json.dumps(obj.facts.model_dump(mode="json"), default=str),
        conversation_json=json.dumps(obj.conversation_history, default=str),
        notice_id=obj.notice_id,
        settlement_id=obj.settlement_id,
        language=obj.language,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


def _row_to_case(row) -> "CaseRecord":
    from app.models.case import CaseRecord, LegalFacts
    facts = LegalFacts.model_validate(json.loads(row.facts_json))
    return CaseRecord(
        id=row.id,
        dispute_category=row.dispute_category,
        status=row.status,
        facts=facts,
        conversation_history=json.loads(row.conversation_json),
        notice_id=row.notice_id,
        settlement_id=row.settlement_id,
        language=row.language,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _notice_to_row(obj) -> "NoticeTable":
    from app.db.sql_models import NoticeTable
    return NoticeTable(
        id=obj.id,
        case_id=obj.case_id,
        draft_body=obj.draft_body,
        plain_language_guide=obj.plain_language_guide,
        citations_json=json.dumps(
            [c.model_dump(mode="json") for c in obj.citations], default=str
        ),
        review_status=obj.review_status,
        reviewer_id=obj.reviewer_id,
        reviewer_notes=obj.reviewer_notes,
        approved_body=obj.approved_body,
        pdf_path=obj.pdf_path,
        pdf_hash=obj.pdf_hash,
        settlement_token=obj.settlement_token,
        settlement_url=obj.settlement_url,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
    )


def _row_to_notice(row) -> "LegalNotice":
    from app.models.notice import LegalNotice, StatuteCitation
    citations = [StatuteCitation.model_validate(c) for c in json.loads(row.citations_json)]
    return LegalNotice(
        id=row.id,
        case_id=row.case_id,
        draft_body=row.draft_body,
        plain_language_guide=row.plain_language_guide,
        citations=citations,
        review_status=row.review_status,
        reviewer_id=row.reviewer_id,
        reviewer_notes=row.reviewer_notes,
        approved_body=row.approved_body,
        pdf_path=row.pdf_path,
        pdf_hash=row.pdf_hash,
        settlement_token=row.settlement_token,
        settlement_url=row.settlement_url,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _reviewer_to_row(obj) -> "ReviewerTable":
    from app.db.sql_models import ReviewerTable
    return ReviewerTable(
        id=obj.id,
        username=obj.username,
        hashed_password=obj.hashed_password,
        full_name=obj.full_name,
        email=obj.email,
        role=obj.role,
        is_active=obj.is_active,
        created_at=obj.created_at,
    )


def _row_to_reviewer(row) -> "ReviewerRecord":
    from app.models.reviewer import ReviewerRecord
    return ReviewerRecord(
        id=row.id,
        username=row.username,
        hashed_password=row.hashed_password,
        full_name=row.full_name,
        email=row.email,
        role=row.role,
        is_active=row.is_active,
        created_at=row.created_at,
    )


# ── Type registry ─────────────────────────────────────────────────────────────
# Maps Pydantic model class → (SQLModel table class, to_row fn, from_row fn)

def _get_registry():
    from app.db.sql_models import CaseTable, NoticeTable, ReviewerTable
    from app.models.case import CaseRecord
    from app.models.notice import LegalNotice
    from app.models.reviewer import ReviewerRecord

    return {
        CaseRecord: (CaseTable, _case_to_row, _row_to_case),
        LegalNotice: (NoticeTable, _notice_to_row, _row_to_notice),
        ReviewerRecord: (ReviewerTable, _reviewer_to_row, _row_to_reviewer),
    }


# ── Store ─────────────────────────────────────────────────────────────────────

class Store(Generic[M]):
    """
    Database-backed store with the same API as the old JSON-file store.
    Thread-safe: each operation opens and commits its own session.
    """

    def __init__(self, name: str, model_cls: type[M]) -> None:
        self._name = name
        self._model_cls = model_cls
        self._lock = threading.Lock()

    def _registry(self):
        reg = _get_registry()
        entry = reg.get(self._model_cls)
        if entry is None:
            raise TypeError(
                f"Store: no SQLModel table registered for {self._model_cls.__name__}"
            )
        return entry  # (TableClass, to_row, from_row)

    def _session(self) -> Session:
        from app.db.database import engine
        return Session(engine)

    # ── Public API (identical to old Store) ───────────────────────────────────

    def get(self, id: str) -> M | None:
        TableClass, _, from_row = self._registry()
        with self._lock, self._session() as session:
            row = session.get(TableClass, id)
            return from_row(row) if row is not None else None

    def put(self, obj: M) -> M:
        """Insert or replace by obj.id (upsert)."""
        TableClass, to_row, from_row = self._registry()
        with self._lock, self._session() as session:
            row = to_row(obj)
            existing = session.get(TableClass, obj.id)  # type: ignore[attr-defined]
            if existing is not None:
                # Update all columns
                for key, val in row.model_dump().items():
                    setattr(existing, key, val)
                session.add(existing)
            else:
                session.add(row)
            session.commit()
        return obj

    def list_all(self) -> list[M]:
        TableClass, _, from_row = self._registry()
        with self._lock, self._session() as session:
            rows = session.exec(select(TableClass)).all()
            return [from_row(r) for r in rows]

    def filter(self, **kwargs) -> list[M]:
        """Return objects whose attributes match all given kwargs (in-memory filter)."""
        all_items = self.list_all()
        return [
            obj for obj in all_items
            if all(getattr(obj, k, None) == v for k, v in kwargs.items())
        ]

    def delete(self, id: str) -> bool:
        TableClass, _, _ = self._registry()
        with self._lock, self._session() as session:
            row = session.get(TableClass, id)
            if row is not None:
                session.delete(row)
                session.commit()
                return True
        return False


# ── Module-level singletons ────────────────────────────────────────────────────

from app.models.case import CaseRecord
from app.models.notice import LegalNotice
from app.models.reviewer import ReviewerRecord

_case_store: Store[CaseRecord] | None = None
_notice_store: Store[LegalNotice] | None = None
_reviewer_store: Store[ReviewerRecord] | None = None


def get_case_store() -> Store[CaseRecord]:
    global _case_store
    if _case_store is None:
        _case_store = Store("cases", CaseRecord)
    return _case_store


def get_notice_store() -> Store[LegalNotice]:
    global _notice_store
    if _notice_store is None:
        _notice_store = Store("notices", LegalNotice)
    return _notice_store


def get_reviewer_store() -> Store[ReviewerRecord]:
    global _reviewer_store
    if _reviewer_store is None:
        _reviewer_store = Store("reviewers", ReviewerRecord)
    return _reviewer_store
