"""
test_pii_security.py — Security & Privacy Audit tests.

Coverage
--------
PII Masking (unit — no DB, no HTTP):
  1.  Phone numbers are masked (Indian mobile, +91 prefix, landline)
  2.  Aadhaar numbers are masked (plain 12-digit and 4-4-4 grouped)
  3.  PAN numbers are masked (AAAAA9999A)
  4.  Bank account numbers are masked (9–18 digits)
  5.  UPI IDs are masked
  6.  Email addresses are masked
  7.  Multiple distinct values in one call each get unique tokens
  8.  Repeated identical value gets the same token (dedup)
  9.  Unmasking exactly reverses masking (round-trip)
  10. Unmasking is idempotent on text with no tokens
  11. mask_dict masks all string leaf values in a nested dict
  12. mask_dict leaves non-string values (int, float, None) unchanged
  13. LLM prompt built from safe_facts never contains the original phone number
  14. LLM prompt built from safe_facts never contains the original Aadhaar number
  15. LLM prompt built from safe_facts never contains the original email
  16. Unmasked text after unmask_pii contains the original phone number again
  17. Token format is <<LABEL_N>> (no raw PII in token itself)
  18. Mixed PII text — all types masked in a single call
  19. Text with no PII is returned unchanged
  20. Empty string is handled gracefully

RBAC (HTTP integration via TestClient):
  21. Clinic verify endpoint rejects unauthenticated request (no token)
  22. Clinic verify endpoint rejects request with a forged/invalid token
  23. Clinic verify endpoint rejects request with a token signed with wrong key
  24. Clinic PDF download rejects unauthenticated request
  25. Clinic PDF download rejects invalid token
  26. Auth /me rejects unauthenticated request
  27. Auth /me rejects invalid token
  28. Intake endpoint is publicly accessible (no auth required)
  29. Notice generate endpoint is publicly accessible (no auth required)
  30. Reviewer with valid token can access clinic endpoint
"""
from __future__ import annotations

import json
import re

import pytest

# ── Import the module under test directly (no DB / HTTP needed for PII tests) ─
from app.services.pii_masker import mask_dict, mask_pii, unmask_pii


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

_TOKEN_RE = re.compile(r"<<[A-Z_]+_\d+>>")

def _fresh() -> dict[str, str]:
    """Return a fresh empty PII store."""
    return {}


# ═══════════════════════════════════════════════════════════════════════════════
# 1–10  Basic masking / unmasking correctness
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhoneMasking:
    def test_mobile_10_digit(self):
        store = _fresh()
        result = mask_pii("Call me at 9876543210 tomorrow.", store)
        assert "9876543210" not in result
        assert len(store) == 1

    def test_mobile_with_plus91_prefix(self):
        store = _fresh()
        result = mask_pii("My number is +91 9876543210.", store)
        assert "9876543210" not in result
        assert len(store) >= 1

    def test_mobile_with_91_no_space(self):
        store = _fresh()
        result = mask_pii("Contact: +919876543210", store)
        assert "9876543210" not in result

    def test_landline(self):
        store = _fresh()
        result = mask_pii("Office: 011-23456789", store)
        assert "23456789" not in result

    def test_phone_token_is_opaque(self):
        store = _fresh()
        result = mask_pii("9876543210", store)
        # The result must not contain the phone digits
        assert "9876543210" not in result
        # The result must look like a token
        assert _TOKEN_RE.search(result) is not None


class TestAadhaarMasking:
    def test_plain_12_digit(self):
        store = _fresh()
        result = mask_pii("Aadhaar: 234567890123", store)
        assert "234567890123" not in result
        assert len(store) >= 1

    def test_grouped_4_4_4(self):
        store = _fresh()
        result = mask_pii("ID: 2345 6789 0123", store)
        assert "2345 6789 0123" not in result

    def test_grouped_with_hyphens(self):
        store = _fresh()
        result = mask_pii("2345-6789-0123", store)
        assert "2345-6789-0123" not in result


class TestPanMasking:
    def test_pan_uppercase(self):
        store = _fresh()
        result = mask_pii("PAN: ABCDE1234F", store)
        assert "ABCDE1234F" not in result
        assert len(store) == 1

    def test_pan_in_sentence(self):
        store = _fresh()
        result = mask_pii("Tax ID is ABCDE1234F as per records.", store)
        assert "ABCDE1234F" not in result


class TestBankAccountMasking:
    def test_9_digit_account(self):
        store = _fresh()
        result = mask_pii("Account: 123456789", store)
        assert "123456789" not in result

    def test_18_digit_account(self):
        store = _fresh()
        result = mask_pii("Acc no: 123456789012345678", store)
        assert "123456789012345678" not in result

    def test_8_digit_not_masked(self):
        """8-digit numbers are below the bank-account threshold."""
        store = _fresh()
        result = mask_pii("PIN: 12345678", store)
        # 8 digits should NOT be captured as bank account
        # (threshold is 9 digits minimum)
        assert "BANK_ACCOUNT" not in result


class TestUpiMasking:
    def test_paytm_upi(self):
        store = _fresh()
        result = mask_pii("Pay to: sharma.priya@paytm", store)
        assert "sharma.priya@paytm" not in result
        assert len(store) == 1

    def test_okaxis_upi(self):
        store = _fresh()
        result = mask_pii("UPI: 9876543210@okaxis", store)
        assert "@okaxis" not in result

    def test_ybl_upi(self):
        store = _fresh()
        result = mask_pii("priya@ybl", store)
        assert "priya@ybl" not in result


class TestEmailMasking:
    def test_simple_email(self):
        store = _fresh()
        result = mask_pii("Email me at priya.sharma@example.com", store)
        assert "priya.sharma@example.com" not in result
        assert len(store) == 1

    def test_email_with_plus(self):
        store = _fresh()
        result = mask_pii("user+tag@domain.org", store)
        assert "user+tag@domain.org" not in result

    def test_email_with_subdomain(self):
        store = _fresh()
        result = mask_pii("admin@mail.clinic.test", store)
        assert "admin@mail.clinic.test" not in result


class TestMultipleValues:
    def test_two_phones_get_separate_tokens(self):
        store = _fresh()
        result = mask_pii("Buyer: 9111111111, Seller: 9222222222", store)
        assert "9111111111" not in result
        assert "9222222222" not in result
        # Two separate tokens
        assert len(store) >= 2

    def test_repeated_value_same_token(self):
        """The same phone number appearing twice must produce one token entry."""
        store = _fresh()
        result = mask_pii("9876543210 and again 9876543210", store)
        tokens = _TOKEN_RE.findall(result)
        # Both occurrences replaced but only one store entry
        assert len(store) == 1
        assert tokens[0] == tokens[1]

    def test_roundtrip_exact(self):
        original = "Name: Priya. Phone: 9876543210. Aadhaar: 2345 6789 0123."
        store = _fresh()
        masked = mask_pii(original, store)
        restored = unmask_pii(masked, store)
        assert restored == original

    def test_unmask_idempotent_on_clean_text(self):
        store = _fresh()
        text = "No PII here, just a normal sentence."
        assert unmask_pii(text, store) == text

    def test_empty_string(self):
        store = _fresh()
        assert mask_pii("", store) == ""
        assert unmask_pii("", store) == ""

    def test_no_pii_unchanged(self):
        store = _fresh()
        text = "The Consumer Protection Act 2019 applies here."
        result = mask_pii(text, store)
        assert result == text
        assert store == {}


class TestMaskDict:
    def test_string_values_masked(self):
        store = _fresh()
        data = {"phone": "9876543210", "name": "Priya Sharma"}
        safe = mask_dict(data, store)
        assert "9876543210" not in safe["phone"]
        # Name with no PII passes through unchanged
        assert safe["name"] == "Priya Sharma"

    def test_non_string_values_unchanged(self):
        store = _fresh()
        data = {"amount": 25000.0, "count": 3, "flag": None}
        safe = mask_dict(data, store)
        assert safe["amount"] == 25000.0
        assert safe["count"] == 3
        assert safe["flag"] is None

    def test_nested_dict_masked(self):
        store = _fresh()
        data = {"contact": {"email": "a@b.com", "phone": "9876543210"}}
        safe = mask_dict(data, store)
        assert "a@b.com" not in safe["contact"]["email"]
        assert "9876543210" not in safe["contact"]["phone"]

    def test_list_of_strings_masked(self):
        store = _fresh()
        data = {"phones": ["9111111111", "9222222222"]}
        safe = mask_dict(data, store)
        assert "9111111111" not in safe["phones"][0]
        assert "9222222222" not in safe["phones"][1]


class TestTokenFormat:
    def test_token_is_readable_label(self):
        store = _fresh()
        result = mask_pii("9876543210", store)
        token = _TOKEN_RE.search(result)
        assert token is not None
        inner = token.group(0)  # e.g. <<PHONE_1>>
        assert inner.startswith("<<")
        assert inner.endswith(">>")
        # Must not contain digits that look like the original number
        assert "9876543210" not in inner

    def test_phone_token_label(self):
        store = _fresh()
        result = mask_pii("9876543210", store)
        assert "<<PHONE_" in result

    def test_email_token_label(self):
        store = _fresh()
        result = mask_pii("user@example.com", store)
        assert "<<EMAIL_" in result

    def test_aadhaar_token_label(self):
        store = _fresh()
        result = mask_pii("234567890123", store)
        assert "<<AADHAAR_" in result

    def test_pan_token_label(self):
        store = _fresh()
        result = mask_pii("ABCDE1234F", store)
        assert "<<PAN_" in result


# ═══════════════════════════════════════════════════════════════════════════════
# 13–16  LLM prompt safety (integration with notice_service helpers)
# ═══════════════════════════════════════════════════════════════════════════════

class TestLlmPromptSafety:
    """
    Verify that the prompts built by notice_service never contain raw PII
    after masking is applied.  We test the helper functions directly so
    these are pure-Python, no HTTP / DB needed.
    """

    _SENSITIVE_FACTS = {
        "claimant_name": "Priya Sharma",
        "claimant_contact": "9876543210",        # mobile phone
        "respondent_contact": "quickmart@hdfc",  # UPI-style email
        "claimant_aadhaar": "2345 6789 0123",
        "claimant_email": "priya@example.com",
        "dispute_category": "consumer_fraud",
        "claim_amount_inr": 25000.0,
        "incident_date": "2024-03-15",
    }

    _STATUTES = [
        {
            "act": "Consumer Protection Act 2019",
            "section": "Section 35",
            "section_title": "Complaints to District Commission",
            "excerpt": "A complaint in relation to any goods sold...",
            "relevance_score": 0.9,
            "forum": "District Consumer Disputes Redressal Commission",
        }
    ]

    def _build_safe_prompt(self) -> tuple[str, dict[str, str]]:
        """Apply masking and build the notice prompt the same way notice_service does."""
        from app.services.pii_masker import mask_dict
        from app.services.notice_service import _build_notice_prompt

        store: dict[str, str] = {}
        safe_facts = mask_dict(self._SENSITIVE_FACTS, store)
        prompt = _build_notice_prompt(safe_facts, self._STATUTES)
        return prompt, store

    def test_phone_not_in_prompt(self):
        prompt, _ = self._build_safe_prompt()
        assert "9876543210" not in prompt

    def test_aadhaar_not_in_prompt(self):
        prompt, _ = self._build_safe_prompt()
        assert "2345 6789 0123" not in prompt
        assert "234567890123" not in prompt

    def test_email_not_in_prompt(self):
        prompt, _ = self._build_safe_prompt()
        assert "priya@example.com" not in prompt

    def test_upi_not_in_prompt(self):
        prompt, _ = self._build_safe_prompt()
        assert "quickmart@hdfc" not in prompt

    def test_tokens_present_in_prompt(self):
        """At least one <<TOKEN>> must appear to confirm masking ran."""
        prompt, store = self._build_safe_prompt()
        assert len(store) > 0
        assert _TOKEN_RE.search(prompt) is not None

    def test_unmask_restores_phone_in_output(self):
        _, store = self._build_safe_prompt()
        # Simulate LLM echoing tokens back
        fake_llm_output = "Call <<PHONE_1>> to resolve the matter."
        restored = unmask_pii(fake_llm_output, store)
        assert "9876543210" in restored

    def test_statute_names_not_affected(self):
        """Statute section numbers/act names must pass through masking unchanged."""
        prompt, _ = self._build_safe_prompt()
        assert "Consumer Protection Act 2019" in prompt
        assert "Section 35" in prompt


# ═══════════════════════════════════════════════════════════════════════════════
# 21–30  RBAC enforcement (HTTP integration via TestClient)
# ═══════════════════════════════════════════════════════════════════════════════

class TestClinicRbac:
    """Clinic endpoints must reject unauthenticated and forged tokens."""

    def _pending_case_and_notice(self, client):
        from app.db.store import get_case_store, get_notice_store
        from app.models.case import CaseRecord, LegalFacts
        from app.models.notice import LegalNotice, StatuteCitation

        facts = LegalFacts(
            claimant_name="Priya Sharma",
            respondent_name="QuickMart Pvt Ltd",
            incident_date="2024-03-15",
            claim_amount_inr=25000.0,
            evidence_summary="Receipts and screenshots",
            dispute_category="consumer_fraud",
        )
        case = CaseRecord(
            dispute_category="consumer_fraud",
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
            draft_body="LEGAL NOTICE\nUnder Section 35 of the CPA 2019...",
            plain_language_guide="Your rights...",
            citations=[citation],
            review_status="pending_clinic_review",
        )
        case.notice_id = notice.id
        get_case_store().put(case)
        get_notice_store().put(notice)
        return case.id, notice.id

    _APPROVED_BODY = (
        "LEGAL NOTICE\n\nTo: QuickMart Pvt Ltd\n\n"
        "Under Section 35 of the Consumer Protection Act 2019, "
        "you are hereby called upon to refund ₹25,000 within 30 days."
    )
    _VERIFY_PAYLOAD = {
        "reviewer_id": "student_001",
        "action": "approve",
        "edited_body": _APPROVED_BODY,
    }

    # ── No token ──────────────────────────────────────────────────────────

    def test_verify_no_token_rejected(self, client):
        case_id, _ = self._pending_case_and_notice(client)
        resp = client.patch(f"/api/clinic/verify/{case_id}", json=self._VERIFY_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_pdf_download_no_token_rejected(self, client):
        _, notice_id = self._pending_case_and_notice(client)
        resp = client.get(f"/api/clinic/notice/{notice_id}/pdf")
        assert resp.status_code in (401, 403)

    # ── Forged / invalid token ────────────────────────────────────────────

    def test_verify_forged_token_rejected(self, client):
        case_id, _ = self._pending_case_and_notice(client)
        resp = client.patch(
            f"/api/clinic/verify/{case_id}",
            json=self._VERIFY_PAYLOAD,
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        assert resp.status_code in (401, 403)

    def test_pdf_download_forged_token_rejected(self, client):
        _, notice_id = self._pending_case_and_notice(client)
        resp = client.get(
            f"/api/clinic/notice/{notice_id}/pdf",
            headers={"Authorization": "Bearer forgery.x.y"},
        )
        assert resp.status_code in (401, 403)

    def test_verify_wrong_secret_token_rejected(self, client):
        """A JWT signed with a *different* secret key must be rejected."""
        from jose import jwt
        import datetime, time

        payload = {
            "sub": "hacker",
            "exp": int(time.time()) + 3600,
        }
        bad_token = jwt.encode(payload, "wrong-secret-key-xyz", algorithm="HS256")
        case_id, _ = self._pending_case_and_notice(client)
        resp = client.patch(
            f"/api/clinic/verify/{case_id}",
            json=self._VERIFY_PAYLOAD,
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert resp.status_code in (401, 403)

    # ── Public endpoints unaffected ───────────────────────────────────────

    def test_intake_is_public(self, client):
        """The intake endpoint must NOT require authentication."""
        resp = client.post("/api/intake/message", json={
            "session_id": "test-session",
            "message": "I bought a defective mixer from QuickMart.",
            "language": "en",
        })
        # 200 (question) or 202 (facts collected) — anything but 401/403
        assert resp.status_code not in (401, 403)

    def test_notice_generate_is_public(self, client):
        """Notice generation must NOT require authentication."""
        # Use a non-existent case_id so it fails with 404/422 — NOT 401/403
        resp = client.post("/api/notice/generate", json={"case_id": "nonexistent-id"})
        assert resp.status_code not in (401, 403)

    # ── Valid token accepted ──────────────────────────────────────────────

    def test_verify_valid_token_accepted(self, client, auth_headers):
        case_id, _ = self._pending_case_and_notice(client)
        resp = client.patch(
            f"/api/clinic/verify/{case_id}",
            json=self._VERIFY_PAYLOAD,
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text

    def test_pdf_download_after_approve_valid_token(self, client, auth_headers):
        case_id, notice_id = self._pending_case_and_notice(client)
        client.patch(
            f"/api/clinic/verify/{case_id}",
            json=self._VERIFY_PAYLOAD,
            headers=auth_headers,
        )
        resp = client.get(f"/api/clinic/notice/{notice_id}/pdf", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"


class TestAuthMeRbac:
    """The /api/auth/me endpoint also enforces authentication."""

    def test_me_no_token_rejected(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code in (401, 403)

    def test_me_invalid_token_rejected(self, client):
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer garbage.garbage.garbage"},
        )
        assert resp.status_code in (401, 403)

    def test_me_valid_token_returns_profile(self, client, auth_token):
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "test_student"
        assert "hashed_password" not in data
