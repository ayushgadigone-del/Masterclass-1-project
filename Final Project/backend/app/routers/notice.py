"""
notice.py — POST /api/notice/generate

Triggers legal notice generation for a case whose status is
'ready_for_notice'.  Calls the MCP statute tools, invokes the LLM
with a citation-constrained prompt, and sets the case status to
'pending_clinic_review'.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.models.notice import NoticeGenerateRequest, NoticeGenerateResponse
from app.services.notice_service import generate_notice

router = APIRouter(prefix="/api/notice", tags=["notice"])


@router.post(
    "/generate",
    response_model=NoticeGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a legal notice for a case",
    description=(
        "Calls `search_applicable_laws` on the MCP statute server, then uses the "
        "LLM to draft a formal Legal Notice and a plain-language Action Guide. "
        "All statute citations in the draft are verified by `validate_notice_citations` "
        "before the notice is queued. Sets case status to `pending_clinic_review`.\n\n"
        "Requires `case_id` with status `ready_for_notice` or `clinic_rejected`."
    ),
)
def post_generate_notice(body: NoticeGenerateRequest) -> NoticeGenerateResponse:
    try:
        return generate_notice(body.case_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
