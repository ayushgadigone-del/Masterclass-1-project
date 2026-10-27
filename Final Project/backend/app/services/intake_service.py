"""
intake_service.py — conversational intake: extract facts, ask follow-up questions.

Flow:
  1. Citizen sends a message (possibly multilingual).
  2. We run a lightweight regex + keyword extraction to pull structured facts
     from the text (no LLM needed for simple patterns).
  3. We compare extracted facts against MANDATORY_FIELDS to find what's missing.
  4. If something is missing → return a plain-language follow-up question.
  5. If all mandatory facts are collected → set case status to ready_for_notice.

The LLM is only used for free-text extraction of complex fields (incident_date
from natural language, claim amount parsing).  PII fields (names, contacts) are
extracted by regex to ensure they never appear in LLM prompts.
"""
from __future__ import annotations

import re
from datetime import date, datetime

from app.models.case import (
    CaseRecord,
    IntakeMessage,
    IntakeResponse,
    LegalFacts,
    MANDATORY_FIELDS,
)
from app.db.store import get_case_store

# ── Follow-up question templates ──────────────────────────────────────────────
# Plain language, designed to be readable at a Grade 6 level.
_FOLLOW_UP: dict[str, str] = {
    "claimant_name": (
        "Could you please tell me your full name as it should appear on the legal notice?"
    ),
    "respondent_name": (
        "What is the full name (or company name) of the person or organisation "
        "you have a dispute with?"
    ),
    "incident_date": (
        "On what date did the incident or problem occur? "
        "(For example: 15 March 2024, or 15/03/2024)"
    ),
    "claim_amount_inr": (
        "What is the total amount of money you are claiming, in Indian Rupees (₹)? "
        "(For example: ₹25,000)"
    ),
    "evidence_summary": (
        "Briefly describe any evidence you have — such as bills, receipts, "
        "messages, photos, or witness names."
    ),
}

# ── Regex extractors ──────────────────────────────────────────────────────────

_DATE_RE = re.compile(
    r"\b(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})\b"
    r"|\b(\d{1,2})\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|"
    r"may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?)\s+(\d{2,4})\b",
    re.IGNORECASE,
)

_AMOUNT_RE = re.compile(
    r"(?:rs\.?|inr|₹)\s*([\d,]+(?:\.\d{1,2})?)"
    r"|(\d[\d,]*(?:\.\d{1,2})?)\s*(?:rs\.?|inr|rupees?)",
    re.IGNORECASE,
)

_MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _parse_date(text: str) -> date | None:
    for m in _DATE_RE.finditer(text):
        try:
            if m.group(1):  # DD/MM/YYYY or DD-MM-YYYY
                d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                y = y + 2000 if y < 100 else y
                return date(y, mo, d)
            elif m.group(4):  # DD Month YYYY
                d = int(m.group(4))
                mo = _MONTH_MAP[m.group(5).lower()[:3]]
                y = int(m.group(6))
                y = y + 2000 if y < 100 else y
                return date(y, mo, d)
        except ValueError:
            continue
    return None


def _parse_amount(text: str) -> float | None:
    for m in _AMOUNT_RE.finditer(text):
        raw = (m.group(1) or m.group(2) or "").replace(",", "")
        try:
            return float(raw)
        except ValueError:
            continue
    return None


def _extract_name(text: str, hint_words: tuple[str, ...]) -> str | None:
    """
    Heuristic: if the text contains a hint word followed by a capitalised
    name-like token(s), extract it.  Used for claimant/respondent names.
    """
    pattern = (
        r"(?:" + "|".join(re.escape(w) for w in hint_words) + r")"
        r"\s+(?:is\s+|am\s+|:?\s*)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})"
    )
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _extract_facts_from_text(text: str, existing: LegalFacts) -> LegalFacts:
    """
    Pull structured facts from a raw message, merging with existing facts.
    Only overwrites a field if it was None before.
    """
    updated = existing.model_copy()

    if updated.incident_date is None:
        d = _parse_date(text)
        if d:
            updated.incident_date = d

    if updated.claim_amount_inr is None:
        amount = _parse_amount(text)
        if amount is not None:
            updated.claim_amount_inr = amount

    if updated.claimant_name is None:
        name = _extract_name(
            text,
            ("my name is", "i am", "name:", "claimant", "complainant", "applicant"),
        )
        if name:
            updated.claimant_name = name

    if updated.respondent_name is None:
        name = _extract_name(
            text,
            ("against", "respondent", "company", "employer", "landlord",
             "seller", "vendor", "opposite party", "defendant"),
        )
        if name:
            updated.respondent_name = name

    # evidence_summary: if message mentions evidence keywords, use the whole
    # message as the evidence summary (citizen will refine it)
    if updated.evidence_summary is None:
        evidence_keywords = (
            "receipt", "bill", "invoice", "screenshot", "message", "photo",
            "witness", "proof", "contract", "agreement", "document", "email",
        )
        if any(kw in text.lower() for kw in evidence_keywords):
            updated.evidence_summary = text[:500]  # cap at 500 chars

    return updated


# ── Main service function ─────────────────────────────────────────────────────

def process_intake_message(msg: IntakeMessage) -> IntakeResponse:
    """
    Process one citizen intake message.

    - Creates or retrieves the CaseRecord
    - Extracts structured facts from the message text
    - Determines missing mandatory fields
    - Returns a follow-up question or signals readiness for notice generation
    """
    store = get_case_store()

    # ── Load or create case ────────────────────────────────────────────────
    if msg.case_id:
        case = store.get(msg.case_id)
        if case is None:
            raise ValueError(f"Case '{msg.case_id}' not found.")
    else:
        if not msg.dispute_category:
            raise ValueError(
                "dispute_category is required when starting a new case. "
                "Must be one of: unpaid_wages, consumer_fraud, security_deposit."
            )
        case = CaseRecord(
            dispute_category=msg.dispute_category,
            language=msg.language,
        )
        # Pre-populate category in facts
        case.facts.dispute_category = msg.dispute_category

    # ── Append message to conversation history ────────────────────────────
    case.conversation_history.append({"role": "user", "content": msg.message})

    # ── Extract facts from this message ───────────────────────────────────
    case.facts = _extract_facts_from_text(msg.message, case.facts)

    # ── Determine missing fields ──────────────────────────────────────────
    missing = case.facts.missing_mandatory()

    # ── Build response ────────────────────────────────────────────────────
    if missing:
        follow_up_field = missing[0]
        follow_up_q = _FOLLOW_UP[follow_up_field]
        case.status = "intake_in_progress"
        status_message = (
            f"Thank you. I still need a few more details to prepare your legal notice. "
            f"{len(missing)} field(s) remaining."
        )
        # Append the follow-up question to conversation history
        case.conversation_history.append(
            {"role": "assistant", "content": follow_up_q}
        )
    else:
        follow_up_q = None
        case.status = "ready_for_notice"
        status_message = (
            "All details collected. Your legal notice is ready to be generated. "
            "Call POST /api/notice/generate with your case_id to proceed."
        )
        case.conversation_history.append(
            {"role": "assistant", "content": status_message}
        )

    case.touch()
    store.put(case)

    # Scrub PII from the returned collected_facts view
    safe_facts = {
        "dispute_category": case.facts.dispute_category,
        "incident_date": str(case.facts.incident_date) if case.facts.incident_date else None,
        "claim_amount_inr": case.facts.claim_amount_inr,
        "evidence_summary": (
            (case.facts.evidence_summary or "")[:50] + "…"
            if case.facts.evidence_summary
            else None
        ),
        "fields_collected": [
            f for f in MANDATORY_FIELDS if getattr(case.facts, f) is not None
        ],
    }

    return IntakeResponse(
        case_id=case.id,
        status=case.status,
        follow_up_question=follow_up_q,
        missing_fields=missing,
        collected_facts=safe_facts,
        message=status_message,
    )
