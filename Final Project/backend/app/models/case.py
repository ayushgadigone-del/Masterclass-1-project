"""
case.py — Pydantic models for the citizen intake / case lifecycle.

A "Case" is the central record that tracks a citizen grievance from
first message through settlement.  The intake flow is conversational:
the citizen sends messages until all mandatory facts are collected.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Enums / literals ──────────────────────────────────────────────────────────

DisputeCategory = Literal["unpaid_wages", "consumer_fraud", "security_deposit"]

CaseStatus = Literal[
    "intake_in_progress",       # collecting mandatory facts
    "ready_for_notice",         # all facts collected, awaiting generation
    "notice_drafted",           # LLM draft produced, auto-validated
    "pending_clinic_review",    # submitted to law clinic queue
    "clinic_approved",          # reviewer approved
    "clinic_rejected",          # reviewer rejected — returned to citizen
    "notice_sent",              # PDF dispatched to respondent
    "settlement_open",          # respondent has the settlement URL
    "settled",
    "escalated",
]

MANDATORY_FIELDS = (
    "claimant_name",
    "respondent_name",
    "incident_date",
    "claim_amount_inr",
    "evidence_summary",
)


# ── Intake message ────────────────────────────────────────────────────────────

class IntakeMessage(BaseModel):
    """Single message from the citizen in the conversational intake flow."""
    case_id: str | None = Field(
        default=None,
        description="Existing case ID to continue. Omit to start a new case.",
    )
    message: str = Field(
        description="Citizen's plain-language text or voice transcript.",
        min_length=1,
    )
    dispute_category: DisputeCategory | None = Field(
        default=None,
        description="Required on first message. Subsequent messages inherit it.",
    )
    language: str = Field(
        default="en",
        description="ISO 639-1 language code of the message (e.g. 'en', 'hi', 'ta').",
    )


class IntakeResponse(BaseModel):
    """Response to a citizen intake message."""
    case_id: str
    status: CaseStatus
    follow_up_question: str | None = Field(
        default=None,
        description=(
            "Plain-language question asking for the next missing mandatory fact. "
            "None when all facts are collected."
        ),
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        description="Mandatory fields still outstanding.",
    )
    collected_facts: dict = Field(
        default_factory=dict,
        description="Facts extracted so far (PII-scrubbed for logging).",
    )
    message: str = Field(
        description="Plain-language status message for the citizen.",
    )


# ── Collected legal facts ─────────────────────────────────────────────────────

class LegalFacts(BaseModel):
    """
    Structured facts extracted from the citizen's intake messages.
    All fields are optional until collection is complete.
    """
    claimant_name: str | None = None
    respondent_name: str | None = None
    incident_date: date | None = None
    claim_amount_inr: float | None = None
    evidence_summary: str | None = None

    # Optional enrichment fields
    dispute_category: DisputeCategory | None = None
    claimant_contact: str | None = None
    respondent_contact: str | None = None
    location: str | None = None
    additional_context: str | None = None

    def missing_mandatory(self) -> list[str]:
        """Return list of mandatory field names that are still None."""
        missing = []
        for field in MANDATORY_FIELDS:
            if getattr(self, field) is None:
                missing.append(field)
        return missing

    def is_complete(self) -> bool:
        return len(self.missing_mandatory()) == 0


# ── Case record ───────────────────────────────────────────────────────────────

class CaseRecord(BaseModel):
    """Persistent record of a citizen's case."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    dispute_category: DisputeCategory
    status: CaseStatus = "intake_in_progress"
    facts: LegalFacts = Field(default_factory=LegalFacts)
    conversation_history: list[dict] = Field(
        default_factory=list,
        description="List of {role, content} dicts for LLM context.",
    )
    notice_id: str | None = None
    settlement_id: str | None = None
    language: str = "en"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
