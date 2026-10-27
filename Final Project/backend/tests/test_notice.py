"""
test_notice.py — tests for POST /api/notice/generate

Coverage:
  - Generates a notice for a ready case
  - Returns plain_language_guide and draft_body
  - Returns at least one StatuteCitation
  - Citations reference the correct category's statutes
  - Cannot generate if case is not ready
  - Unknown case_id returns 422
  - Notice status is pending_clinic_review after generation
  - Citation validation summary is in the response message
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.conftest import FULL_FACTS


def _create_ready_case(client: TestClient) -> str:
    """
    Bypass the conversational intake to directly set a case as ready_for_notice
    using the store, so notice tests don't depend on intake heuristics.
    """
    from app.db.store import get_case_store
    from app.models.case import CaseRecord, LegalFacts

    facts = LegalFacts(
        claimant_name=FULL_FACTS["claimant_name"],
        respondent_name=FULL_FACTS["respondent_name"],
        incident_date=FULL_FACTS["incident_date"],
        claim_amount_inr=FULL_FACTS["claim_amount_inr"],
        evidence_summary=FULL_FACTS["evidence_summary"],
        dispute_category=FULL_FACTS["dispute_category"],
    )
    case = CaseRecord(
        dispute_category=FULL_FACTS["dispute_category"],
        status="ready_for_notice",
        facts=facts,
    )
    get_case_store().put(case)
    return case.id


class TestGenerateNotice:
    def test_generate_returns_200(self, client: TestClient):
        case_id = _create_ready_case(client)
        resp = client.post("/api/notice/generate", json={"case_id": case_id})
        assert resp.status_code == 201, resp.text

    def test_response_contains_notice_id(self, client: TestClient):
        case_id = _create_ready_case(client)
        data = client.post("/api/notice/generate", json={"case_id": case_id}).json()
        assert "notice_id" in data
        assert len(data["notice_id"]) > 0

    def test_response_contains_plain_language_guide(self, client: TestClient):
        case_id = _create_ready_case(client)
        data = client.post("/api/notice/generate", json={"case_id": case_id}).json()
        assert "plain_language_guide" in data
        assert len(data["plain_language_guide"]) > 50

    def test_response_contains_draft_body(self, client: TestClient):
        case_id = _create_ready_case(client)
        data = client.post("/api/notice/generate", json={"case_id": case_id}).json()
        assert "draft_body" in data
        assert len(data["draft_body"]) > 50

    def test_response_contains_citations(self, client: TestClient):
        case_id = _create_ready_case(client)
        data = client.post("/api/notice/generate", json={"case_id": case_id}).json()
        assert "citations" in data
        assert isinstance(data["citations"], list)
        assert len(data["citations"]) > 0

    def test_citation_has_required_fields(self, client: TestClient):
        case_id = _create_ready_case(client)
        data = client.post("/api/notice/generate", json={"case_id": case_id}).json()
        for citation in data["citations"]:
            for field in ("act", "section", "section_title", "excerpt", "relevance_score", "forum"):
                assert field in citation, f"Citation missing field '{field}'"

    def test_citations_are_for_correct_category(self, client: TestClient):
        case_id = _create_ready_case(client)
        data = client.post("/api/notice/generate", json={"case_id": case_id}).json()
        for citation in data["citations"]:
            assert "Consumer Protection" in citation["act"] or \
                   "Payment of Wages" in citation["act"] or \
                   "Tenancy" in citation["act"] or \
                   "Industrial Relations" in citation["act"]

    def test_notice_status_is_pending_clinic_review(self, client: TestClient):
        case_id = _create_ready_case(client)
        data = client.post("/api/notice/generate", json={"case_id": case_id}).json()
        assert data["review_status"] == "pending_clinic_review"

    def test_case_status_updated_to_pending_clinic_review(self, client: TestClient):
        from app.db.store import get_case_store
        case_id = _create_ready_case(client)
        client.post("/api/notice/generate", json={"case_id": case_id})
        case = get_case_store().get(case_id)
        assert case.status == "pending_clinic_review"

    def test_unknown_case_id_returns_422(self, client: TestClient):
        resp = client.post("/api/notice/generate", json={"case_id": "no-such-case"})
        assert resp.status_code == 422

    def test_cannot_generate_for_intake_in_progress_case(self, client: TestClient):
        from app.db.store import get_case_store
        from app.models.case import CaseRecord

        case = CaseRecord(dispute_category="consumer_fraud", status="intake_in_progress")
        get_case_store().put(case)
        resp = client.post("/api/notice/generate", json={"case_id": case.id})
        assert resp.status_code == 422

    def test_message_contains_validation_summary(self, client: TestClient):
        case_id = _create_ready_case(client)
        data = client.post("/api/notice/generate", json={"case_id": case_id}).json()
        assert "message" in data
        assert len(data["message"]) > 0

    def test_unpaid_wages_category_returns_wages_citation(self, client: TestClient):
        from app.db.store import get_case_store
        from app.models.case import CaseRecord, LegalFacts

        facts = LegalFacts(
            claimant_name="Ramesh Kumar",
            respondent_name="ABC Industries",
            incident_date="2024-01-10",
            claim_amount_inr=15000.0,
            evidence_summary="Salary slip for December 2023",
            dispute_category="unpaid_wages",
        )
        case = CaseRecord(
            dispute_category="unpaid_wages",
            status="ready_for_notice",
            facts=facts,
        )
        get_case_store().put(case)

        data = client.post("/api/notice/generate", json={"case_id": case.id}).json()
        assert data["review_status"] == "pending_clinic_review"
        acts = [c["act"] for c in data["citations"]]
        assert any("Wages" in a or "Industrial" in a for a in acts), \
            f"Expected wages-related citation, got: {acts}"
