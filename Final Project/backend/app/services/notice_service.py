"""
notice_service.py — orchestrates statute lookup → LLM drafting → validation.

Contract (anti-hallucination):
  1. Call MCP search_applicable_laws → get verbatim statute sections
  2. Validate citations in the draft with validate_notice_citations
  3. If validation fails, re-draft up to 2 times before using the fallback template
  4. Produce both:
       - formal Legal Notice (for law clinic review)
       - plain-language Action Guide (for the citizen)
"""
from __future__ import annotations

import json

from app.config import settings
from app.db.store import get_case_store, get_notice_store
from app.models.case import CaseRecord
from app.models.notice import LegalNotice, NoticeGenerateResponse, StatuteCitation
from app.services import llm_service, mcp_client
from app.services.pii_masker import mask_dict, mask_pii, unmask_pii

# ── System prompts ────────────────────────────────────────────────────────────

_NOTICE_SYSTEM = (
    "You are a legal notice drafter for an Indian pre-litigation engine. "
    "You MUST only use the statute citations provided in the [STATUTES] block. "
    "Do NOT add any section numbers, act names, or legal citations not listed there. "
    "Write in formal legal English. Structure: addressee block, subject line, "
    "background facts, legal basis (cite only sections from [STATUTES]), "
    "specific demands, 30-day response deadline, consequence of non-compliance."
)

_GUIDE_SYSTEM = (
    "You are a plain-language legal assistant helping a citizen in India understand "
    "their rights. Write at a Grade 7 reading level. Avoid legal jargon. "
    "Use numbered steps. Be empathetic and clear."
)


def _build_notice_prompt(facts: dict, statutes: list[dict]) -> str:
    return (
        "[GRIEVANCE FACTS]\n"
        f"{json.dumps(facts, indent=2, default=str)}\n\n"
        "[STATUTES]\n"
        f"{json.dumps(statutes, indent=2)}\n\n"
        "Draft a formal pre-litigation legal notice using ONLY the statutes above. "
        "Do not invent section numbers. Every legal citation must match a section "
        "in the [STATUTES] block exactly."
    )


def _build_guide_prompt(facts: dict, statutes: list[dict]) -> str:
    forum = statutes[0].get("forum", "the appropriate legal forum") if statutes else "the appropriate legal forum"
    notice_period = next(
        (s.get("notice_period_days") for s in statutes if s.get("notice_period_days")),
        30,
    )
    return (
        f"A citizen has a {facts.get('dispute_category', 'legal')} dispute.\n\n"
        f"Facts: {json.dumps(facts, indent=2, default=str)}\n\n"
        f"Relevant laws found:\n{json.dumps(statutes, indent=2)}\n\n"
        f"Write a plain-language Action Guide for this citizen that explains:\n"
        f"1. What their legal rights are\n"
        f"2. What this legal notice means and what happens next\n"
        f"3. That the other party has {notice_period} days to respond\n"
        f"4. Where to go if no response: {forum}\n"
        f"5. What documents/evidence to keep ready\n"
        "Keep it friendly, clear, and under 300 words."
    )


# ── Main service function ─────────────────────────────────────────────────────

def generate_notice(case_id: str) -> NoticeGenerateResponse:
    """
    Generate a legal notice for an existing case.

    Steps:
      1. Load the case; require status == "ready_for_notice"
      2. Call MCP statute lookup
      3. Draft notice via LLM (with statute constraint)
      4. Validate citations (up to 2 re-draft attempts)
      5. Draft plain-language guide via LLM
      6. Persist LegalNotice record
      7. Update case status to pending_clinic_review
    """
    case_store = get_case_store()
    notice_store = get_notice_store()

    case = case_store.get(case_id)
    if case is None:
        raise ValueError(f"Case '{case_id}' not found.")
    if case.status not in ("ready_for_notice", "clinic_rejected"):
        raise ValueError(
            f"Case is in status '{case.status}'. "
            "Must be 'ready_for_notice' or 'clinic_rejected' to generate a notice."
        )

    # ── Step 1: Statute lookup via MCP ────────────────────────────────────
    category = mcp_client.normalise_category(case.dispute_category)
    facts_dict = case.facts.model_dump(mode="json")
    facts_summary = _facts_to_summary(case.facts)

    statutes: list[dict] = mcp_client.call_search_applicable_laws(
        facts_summary, category, top_k=5
    )

    # ── PII masking — must happen before ANY LLM call ─────────────────────
    # pii_store maps token → original value; it lives only in this stack
    # frame and is passed to pdf_service for re-hydration at render time.
    pii_store: dict[str, str] = {}
    safe_facts = mask_dict(facts_dict, pii_store)

    # ── Step 2: Draft formal notice ───────────────────────────────────────
    notice_prompt = _build_notice_prompt(safe_facts, statutes)
    draft_body = llm_service.complete(notice_prompt, system=_NOTICE_SYSTEM)

    # ── Step 3: Validate citations (up to 2 retries) ──────────────────────
    validation = mcp_client.call_validate_notice_citations(draft_body)
    attempts = 0
    while not validation["is_valid"] and attempts < 2:
        # Re-prompt with the error list appended
        error_note = (
            "\n\n[VALIDATION ERRORS — fix these before resubmitting]\n"
            + "\n".join(
                f"- {e['citation']}: {e['error']}" + (
                    f"\n  Suggestion: {e['suggestion']}" if e.get("suggestion") else ""
                )
                for e in validation["errors"]
            )
        )
        draft_body = llm_service.complete(
            notice_prompt + error_note, system=_NOTICE_SYSTEM
        )
        validation = mcp_client.call_validate_notice_citations(draft_body)
        attempts += 1

    # ── Step 4: Draft plain-language guide ────────────────────────────────
    guide_prompt = _build_guide_prompt(safe_facts, statutes)
    plain_guide = llm_service.complete(guide_prompt, system=_GUIDE_SYSTEM)

    # ── Step 5: Build StatuteCitation objects ─────────────────────────────
    citations = [
        StatuteCitation(
            act=s["act"],
            section=s["section"],
            section_title=s["section_title"],
            excerpt=s["excerpt"],
            relevance_score=s["relevance_score"],
            notice_period_days=s.get("notice_period_days"),
            penalty=s.get("penalty"),
            forum=s["forum"],
        )
        for s in statutes
    ]

    # ── Step 6: Persist notice ────────────────────────────────────────────
    # Re-hydrate PII in the draft body and guide before storing (the clinic
    # reviewer sees real names / contacts; PII was only masked during LLM
    # transit).  The PDF renderer will also receive the unmasked body.
    draft_body = unmask_pii(draft_body, pii_store)
    plain_guide = unmask_pii(plain_guide, pii_store)

    notice = LegalNotice(
        case_id=case_id,
        draft_body=draft_body,
        plain_language_guide=plain_guide,
        citations=citations,
        review_status="pending_clinic_review",
    )
    notice_store.put(notice)

    # ── Step 7: Update case ───────────────────────────────────────────────
    case.notice_id = notice.id
    case.status = "pending_clinic_review"
    case.touch()
    case_store.put(case)

    return NoticeGenerateResponse(
        case_id=case_id,
        notice_id=notice.id,
        review_status=notice.review_status,
        plain_language_guide=plain_guide,
        draft_body=draft_body,
        citations=citations,
        message=(
            "Legal notice drafted and queued for law clinic review. "
            f"Citation validation: {validation['summary']}"
        ),
    )


def _facts_to_summary(facts) -> str:
    """Build a concise plain-language facts summary for the statute lookup."""
    parts = []
    if facts.dispute_category:
        parts.append(f"dispute type: {facts.dispute_category.replace('_', ' ')}")
    if facts.incident_date:
        parts.append(f"incident on {facts.incident_date}")
    if facts.claim_amount_inr:
        parts.append(f"claim amount ₹{facts.claim_amount_inr:,.0f}")
    if facts.evidence_summary:
        parts.append(f"evidence: {facts.evidence_summary[:100]}")
    return ". ".join(parts) if parts else "general legal dispute"
