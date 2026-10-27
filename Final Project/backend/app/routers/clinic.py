"""
clinic.py — PATCH /api/clinic/verify/{case_id}

Allows a law clinic student to approve or reject a drafted notice.

On APPROVE:
  - Stores the reviewed/edited notice body
  - Generates a PDF with a SHA-256 verification hash
  - Creates a unique JWT-signed settlement URL for the respondent
  - Updates case status to 'clinic_approved'

On REJECT:
  - Records reviewer notes
  - Sets notice status back to 'rejected'
  - Sets case status to 'clinic_rejected' (citizen can re-submit)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.db.store import get_case_store, get_notice_store
from app.models.notice import ClinicVerifyRequest, ClinicVerifyResponse
from app.models.reviewer import ReviewerRecord
from app.routers.auth import get_current_reviewer
from app.services.pdf_service import approve_and_generate

router = APIRouter(prefix="/api/clinic", tags=["clinic"])


@router.patch(
    "/verify/{case_id}",
    response_model=ClinicVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Law clinic student approves or rejects a drafted notice",
    description=(
        "On **approve**: validates the edited body, renders a PDF with a "
        "SHA-256 verification hash, and generates a unique settlement URL "
        "for the respondent.\n\n"
        "On **reject**: records reviewer notes and returns the case to the "
        "citizen for corrections.\n\n"
        "Requires the case to have a notice in `pending_clinic_review` status."
    ),
)
def patch_verify_notice(
    case_id: str,
    body: ClinicVerifyRequest,
    reviewer: ReviewerRecord = Depends(get_current_reviewer),
) -> ClinicVerifyResponse:
    case_store = get_case_store()
    notice_store = get_notice_store()

    case = case_store.get(case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case '{case_id}' not found.",
        )

    if not case.notice_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No notice exists for this case yet. Call POST /api/notice/generate first.",
        )

    notice = notice_store.get(case.notice_id)
    if notice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notice '{case.notice_id}' not found.",
        )

    if notice.review_status not in ("pending_clinic_review", "auto_drafted", "under_review"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Notice is in status '{notice.review_status}' and cannot be reviewed. "
                "Only notices in pending_clinic_review / auto_drafted / under_review can be verified."
            ),
        )

    # ── REJECT ────────────────────────────────────────────────────────────
    if body.action == "reject":
        notice.review_status = "rejected"
        notice.reviewer_id = body.reviewer_id
        notice.reviewer_notes = body.reviewer_notes
        notice.touch()
        notice_store.put(notice)

        case.status = "clinic_rejected"
        case.touch()
        case_store.put(case)

        return ClinicVerifyResponse(
            case_id=case_id,
            notice_id=notice.id,
            review_status="rejected",
            message=(
                "Notice rejected. "
                + (f"Reviewer notes: {body.reviewer_notes}" if body.reviewer_notes else "")
            ),
        )

    # ── APPROVE ───────────────────────────────────────────────────────────
    if not body.edited_body:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="edited_body is required when action='approve'.",
        )

    try:
        pdf_path, pdf_hash, settlement_token, settlement_url = approve_and_generate(
            notice, body.edited_body
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {exc}",
        )

    notice.review_status = "approved"
    notice.reviewer_id = body.reviewer_id
    notice.reviewer_notes = body.reviewer_notes
    notice.approved_body = body.edited_body
    notice.pdf_path = pdf_path
    notice.pdf_hash = pdf_hash
    notice.settlement_token = settlement_token
    notice.settlement_url = settlement_url
    notice.touch()
    notice_store.put(notice)

    case.status = "clinic_approved"
    case.touch()
    case_store.put(case)

    return ClinicVerifyResponse(
        case_id=case_id,
        notice_id=notice.id,
        review_status="approved",
        pdf_path=pdf_path,
        pdf_hash=pdf_hash,
        settlement_url=settlement_url,
        message=(
            f"Notice approved and PDF generated. "
            f"SHA-256: {pdf_hash[:16]}… "
            f"Settlement URL created for respondent."
        ),
    )


@router.get(
    "/notice/{notice_id}/pdf",
    summary="Download the approved notice PDF",
    description="Returns the PDF file for a clinic-approved notice.",
)
def get_notice_pdf(
    notice_id: str,
    reviewer: ReviewerRecord = Depends(get_current_reviewer),
):
    notice_store = get_notice_store()
    notice = notice_store.get(notice_id)
    if notice is None:
        raise HTTPException(status_code=404, detail="Notice not found.")
    if not notice.pdf_path:
        raise HTTPException(
            status_code=404,
            detail="PDF not yet generated. Notice must be approved first.",
        )
    return FileResponse(
        notice.pdf_path,
        media_type="application/pdf",
        filename=f"legal_notice_{notice_id}.pdf",
    )
