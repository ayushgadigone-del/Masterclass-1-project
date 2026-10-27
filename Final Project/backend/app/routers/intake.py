"""
intake.py — POST /api/intake/message

Accepts a citizen's plain-language or voice-transcribed message.
Extracts mandatory legal facts, asks follow-up questions for missing
fields, and signals when all facts are collected.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.models.case import IntakeMessage, IntakeResponse
from app.services.intake_service import process_intake_message

router = APIRouter(prefix="/api/intake", tags=["intake"])


@router.post(
    "/message",
    response_model=IntakeResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a citizen intake message",
    description=(
        "Accepts a plain-language or voice-transcribed message from the citizen. "
        "Extracts structured legal facts, identifies missing mandatory fields "
        "(claimant_name, respondent_name, incident_date, claim_amount_inr, "
        "evidence_summary), and returns either a follow-up question or a "
        "'ready_for_notice' status when all facts are collected.\n\n"
        "**Multilingual:** pass the ISO 639-1 language code in `language`; "
        "follow-up questions are in English by default (i18n can be added).\n\n"
        "**New case:** omit `case_id` and provide `dispute_category`.\n"
        "**Continue case:** provide `case_id`; `dispute_category` is ignored."
    ),
)
def post_intake_message(body: IntakeMessage) -> IntakeResponse:
    try:
        return process_intake_message(body)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
