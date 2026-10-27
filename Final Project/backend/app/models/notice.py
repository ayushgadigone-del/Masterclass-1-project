"""
notice.py — Pydantic models for legal notice generation and review.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class StatuteCitation(BaseModel):
    act: str
    section: str                  # e.g. "Section 35"
    section_title: str
    excerpt: str                  # verbatim statutory text ≤ 500 chars
    relevance_score: float
    notice_period_days: int | None = None
    penalty: str | None = None
    forum: str


class LegalNotice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    case_id: str
    draft_body: str               # formal notice prose (plain text / Markdown)
    plain_language_guide: str     # citizen-facing action guide
    citations: list[StatuteCitation] = Field(default_factory=list)
    review_status: Literal[
        "auto_drafted",
        "pending_clinic_review",
        "under_review",
        "approved",
        "rejected",
        "sent",
    ] = "auto_drafted"
    reviewer_id: str | None = None
    reviewer_notes: str | None = None
    approved_body: str | None = None
    pdf_path: str | None = None
    pdf_hash: str | None = None           # SHA-256 of the PDF bytes
    settlement_token: str | None = None   # JWT signed token for respondent URL
    settlement_url: str | None = None     # full URL sent to respondent
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


# ── Request / Response DTOs ────────────────────────────────────────────────────

class NoticeGenerateRequest(BaseModel):
    case_id: str = Field(description="Case ID for which to generate the notice.")


class NoticeGenerateResponse(BaseModel):
    case_id: str
    notice_id: str
    review_status: str
    plain_language_guide: str
    draft_body: str
    citations: list[StatuteCitation]
    message: str


class ClinicVerifyRequest(BaseModel):
    reviewer_id: str = Field(description="Law clinic student ID.")
    action: Literal["approve", "reject"] = Field(
        description="'approve' finalises the notice; 'reject' returns it."
    )
    edited_body: str | None = Field(
        default=None,
        description="Edited notice body. Required when action='approve'.",
    )
    reviewer_notes: str | None = Field(
        default=None,
        description="Optional review notes.",
    )


class ClinicVerifyResponse(BaseModel):
    case_id: str
    notice_id: str
    review_status: str
    pdf_path: str | None = None
    pdf_hash: str | None = None
    settlement_url: str | None = None
    message: str
