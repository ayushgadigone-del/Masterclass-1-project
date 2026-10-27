"""
test_clinic.py — tests for PATCH /api/clinic/verify/{case_id} and auth

Coverage:
  Auth:
    - Register returns 201 with reviewer profile
    - Duplicate username returns 409
    - Login returns JWT access_token
    - Wrong password returns 401
    - /me with valid token returns profile
    - /me without token returns 403
    - Clinic endpoints return 403 without token
  Clinic (authenticated):
    - Approve: returns approved status, pdf_path, pdf_hash, settlement_url
    - Approve: PDF file is written to disk
    - Approve: SHA-256 hash is a valid 64-char hex string
    - Approve: settlement_url contains the case_id
    - Approve: case status updated to clinic_approved
    - Reject: returns rejected status, records reviewer_notes
    - Reject: case status updated to clinic_rejected
    - Approve without edited_body returns 422
    - Verify on non-existent case returns 404
    - Verify when no notice exists returns 422
    - Cannot verify an already-approved notice (status guard)
    - PDF download endpoint returns 200 with correct content-type
"""
from __future__ import annotations

import re
import pytest
from fastapi.testclient import TestClient

from tests.conftest import FULL_FACTS


def _create_pending_case_and_notice(client: TestClient) -> tuple[str, str]:
    """
    Directly insert a case + notice in pending_clinic_review state.
    Returns (case_id, notice_id).
    """
    from app.db.store import get_case_store, get_notice_store
    from app.models.case import CaseRecord, LegalFacts
    from app.models.notice import LegalNotice, StatuteCitation

    facts = LegalFacts(**{k: FULL_FACTS[k] for k in (
        "claimant_name", "respondent_name", "incident_date",
        "claim_amount_inr", "evidence_summary", "dispute_category",
    )})
    case = CaseRecord(
        dispute_category=FULL_FACTS["dispute_category"],
        status="pending_clinic_review",
        facts=facts,
    )

    citation = StatuteCitation(
        act="Consumer Protection Act 2019",
        section="Section 35",
        section_title="Complaints to District Commission",
        excerpt="A complaint in relation to any goods sold...",
        relevance_score=0.85,
        forum="District Consumer Disputes Redressal Commission",
    )
    notice = LegalNotice(
        case_id=case.id,
        draft_body=(
            "LEGAL NOTICE\n\n"
            "To: QuickMart Pvt Ltd\n\n"
            "Under Section 35 of the Consumer Protection Act 2019, "
            "you are hereby notified that Priya Sharma has filed a complaint "
            "regarding a defective product purchased on 15 March 2024 "
            "for ₹25,000. You are required to respond within 30 days."
        ),
        plain_language_guide="Your rights under consumer law...",
        citations=[citation],
        review_status="pending_clinic_review",
    )
    case.notice_id = notice.id

    get_case_store().put(case)
    get_notice_store().put(notice)
    return case.id, notice.id


_SAMPLE_APPROVED_BODY = (
    "LEGAL NOTICE\n\n"
    "To: QuickMart Pvt Ltd\n\n"
    "Under Section 35 of the Consumer Protection Act 2019, "
    "you are hereby called upon to refund ₹25,000 within 30 days "
    "of this notice.\n\n"
    "Signed,\nPriya Sharma"
)


# ── Auth tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_returns_201(self, client: TestClient):
        resp = client.post("/api/auth/register", json={
            "username": "newstudent",
            "password": "password123",
            "full_name": "New Student",
            "email": "new@clinic.test",
            "role": "student",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newstudent"
        assert "hashed_password" not in data

    def test_duplicate_username_returns_409(self, client: TestClient):
        payload = {
            "username": "dupuser",
            "password": "password123",
            "full_name": "Dup User",
            "email": "dup@clinic.test",
            "role": "student",
        }
        client.post("/api/auth/register", json=payload)
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 409

    def test_login_returns_access_token(self, client: TestClient, auth_token: str):
        assert len(auth_token) > 20
        # token is a dot-separated JWT
        assert auth_token.count(".") == 2

    def test_wrong_password_returns_401(self, client: TestClient, auth_token: str):
        # First register happened via auth_token fixture
        resp = client.post("/api/auth/login", json={
            "username": "test_student",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_me_with_valid_token(self, client: TestClient, auth_token: str):
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
        assert resp.status_code == 200
        assert resp.json()["username"] == "test_student"

    def test_me_without_token_is_rejected(self, client: TestClient):
        # FastAPI HTTPBearer returns 403 when no credentials are provided
        resp = client.get("/api/auth/me")
        assert resp.status_code in (401, 403)

    def test_clinic_without_token_is_rejected(self, client: TestClient):
        case_id, _ = _create_pending_case_and_notice(client)
        resp = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "x",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        })
        assert resp.status_code in (401, 403)

    def test_clinic_with_invalid_token_is_rejected(self, client: TestClient):
        case_id, _ = _create_pending_case_and_notice(client)
        resp = client.patch(
            f"/api/clinic/verify/{case_id}",
            json={"reviewer_id": "x", "action": "approve", "edited_body": _SAMPLE_APPROVED_BODY},
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        assert resp.status_code in (401, 403)


# ── Clinic tests (authenticated) ──────────────────────────────────────────────

class TestApprove:
    def test_approve_returns_200(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        resp = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers)
        assert resp.status_code == 200, resp.text

    def test_approve_review_status_is_approved(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        data = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers).json()
        assert data["review_status"] == "approved"

    def test_approve_returns_pdf_path(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        data = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers).json()
        assert data.get("pdf_path") is not None
        assert data["pdf_path"].endswith(".pdf")

    def test_approve_pdf_file_written_to_disk(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        data = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers).json()
        import os
        assert os.path.isfile(data["pdf_path"]), \
            f"PDF file not found at: {data['pdf_path']}"

    def test_approve_pdf_hash_is_sha256_hex(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        data = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers).json()
        assert data.get("pdf_hash") is not None
        assert re.fullmatch(r"[0-9a-f]{64}", data["pdf_hash"]), \
            f"pdf_hash is not a valid SHA-256 hex: {data['pdf_hash']}"

    def test_approve_settlement_url_contains_case_id(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        data = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers).json()
        assert data.get("settlement_url") is not None
        assert case_id in data["settlement_url"]

    def test_approve_settlement_url_contains_token(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        data = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers).json()
        assert "token=" in data["settlement_url"]

    def test_approve_case_status_updated(self, client: TestClient, auth_headers: dict):
        from app.db.store import get_case_store
        case_id, _ = _create_pending_case_and_notice(client)
        client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers)
        case = get_case_store().get(case_id)
        assert case.status == "clinic_approved"

    def test_approve_without_edited_body_returns_422(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        resp = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_approve_persists_reviewer_id(self, client: TestClient, auth_headers: dict):
        from app.db.store import get_notice_store
        case_id, notice_id = _create_pending_case_and_notice(client)
        client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_007",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers)
        notice = get_notice_store().get(notice_id)
        assert notice.reviewer_id == "student_007"


class TestReject:
    def test_reject_returns_200(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        resp = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_002",
            "action": "reject",
            "reviewer_notes": "Missing claimant address. Please add.",
        }, headers=auth_headers)
        assert resp.status_code == 200

    def test_reject_review_status_is_rejected(self, client: TestClient, auth_headers: dict):
        case_id, _ = _create_pending_case_and_notice(client)
        data = client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_002",
            "action": "reject",
        }, headers=auth_headers).json()
        assert data["review_status"] == "rejected"

    def test_reject_case_status_is_clinic_rejected(self, client: TestClient, auth_headers: dict):
        from app.db.store import get_case_store
        case_id, _ = _create_pending_case_and_notice(client)
        client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_002",
            "action": "reject",
            "reviewer_notes": "Needs revision",
        }, headers=auth_headers)
        case = get_case_store().get(case_id)
        assert case.status == "clinic_rejected"

    def test_reject_persists_reviewer_notes(self, client: TestClient, auth_headers: dict):
        from app.db.store import get_notice_store
        case_id, notice_id = _create_pending_case_and_notice(client)
        client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_002",
            "action": "reject",
            "reviewer_notes": "Citation incomplete",
        }, headers=auth_headers)
        notice = get_notice_store().get(notice_id)
        assert notice.reviewer_notes == "Citation incomplete"

    def test_reject_no_pdf_generated(self, client: TestClient, auth_headers: dict):
        from app.db.store import get_notice_store
        case_id, notice_id = _create_pending_case_and_notice(client)
        client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_002",
            "action": "reject",
        }, headers=auth_headers)
        notice = get_notice_store().get(notice_id)
        assert notice.pdf_path is None


class TestEdgeCases:
    def test_nonexistent_case_returns_404(self, client: TestClient, auth_headers: dict):
        resp = client.patch("/api/clinic/verify/no-such-case", json={
            "reviewer_id": "x",
            "action": "approve",
            "edited_body": "body",
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_case_with_no_notice_returns_422(self, client: TestClient, auth_headers: dict):
        from app.db.store import get_case_store
        from app.models.case import CaseRecord

        case = CaseRecord(dispute_category="consumer_fraud", status="pending_clinic_review")
        get_case_store().put(case)
        resp = client.patch(f"/api/clinic/verify/{case.id}", json={
            "reviewer_id": "x",
            "action": "approve",
            "edited_body": "body",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_already_approved_notice_cannot_be_re_reviewed(self, client: TestClient, auth_headers: dict):
        from app.db.store import get_case_store, get_notice_store
        from app.models.case import CaseRecord
        from app.models.notice import LegalNotice

        case = CaseRecord(dispute_category="consumer_fraud", status="clinic_approved")
        notice = LegalNotice(
            case_id=case.id,
            draft_body="body",
            plain_language_guide="guide",
            review_status="approved",
        )
        case.notice_id = notice.id
        get_case_store().put(case)
        get_notice_store().put(notice)

        resp = client.patch(f"/api/clinic/verify/{case.id}", json={
            "reviewer_id": "x",
            "action": "approve",
            "edited_body": "new body",
        }, headers=auth_headers)
        assert resp.status_code == 422


class TestPdfDownload:
    def test_download_approved_pdf(self, client: TestClient, auth_headers: dict):
        case_id, notice_id = _create_pending_case_and_notice(client)
        client.patch(f"/api/clinic/verify/{case_id}", json={
            "reviewer_id": "student_001",
            "action": "approve",
            "edited_body": _SAMPLE_APPROVED_BODY,
        }, headers=auth_headers)
        resp = client.get(f"/api/clinic/notice/{notice_id}/pdf", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    def test_download_unapproved_notice_returns_404(self, client: TestClient, auth_headers: dict):
        _, notice_id = _create_pending_case_and_notice(client)
        resp = client.get(f"/api/clinic/notice/{notice_id}/pdf", headers=auth_headers)
        assert resp.status_code == 404

    def test_download_unknown_notice_returns_404(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/clinic/notice/no-such-notice/pdf", headers=auth_headers)
        assert resp.status_code == 404
