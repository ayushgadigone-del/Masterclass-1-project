"""
test_server_tools.py
--------------------
Integration-style tests for the MCP tool functions registered in server.py.

In MCP 2.x (MCPServer), @server.tool()-decorated functions are plain Python
functions — they can be called directly without starting a stdio server.
These tests import the decorated functions from server.py and call them
synchronously to verify correct JSON payloads are returned.

Coverage:
  search_applicable_laws tool function
    - Valid request returns results list with metadata
    - Empty facts_summary returns error JSON (not exception)
    - Invalid category returns error JSON (not exception)
    - top_k is forwarded correctly
    - All three categories return results

  validate_notice_citations tool function
    - Valid citation → is_valid=True in returned JSON
    - Hallucinated section → is_valid=False in returned JSON
    - Error entries have required fields
    - Empty draft_text → error JSON (not exception)
    - Draft with no citations → is_valid=True
    - Multiple hallucinated sections → all appear in errors
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the tool functions directly — they are plain callables in MCP 2.x
from server import search_applicable_laws, validate_notice_citations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(raw: str) -> dict:
    """Parse the JSON string returned by a tool function."""
    return json.loads(raw)


# ---------------------------------------------------------------------------
# search_applicable_laws
# ---------------------------------------------------------------------------

class TestSearchApplicableLaws:
    def test_valid_request_returns_results_list(self):
        raw = search_applicable_laws(
            "employer did not pay wages after termination",
            "unpaid_wages",
        )
        payload = _parse(raw)
        assert "results" in payload
        assert isinstance(payload["results"], list)
        assert len(payload["results"]) > 0

    def test_payload_contains_metadata(self):
        raw = search_applicable_laws(
            "defective goods refund denied",
            "consumer_fraud",
            top_k=3,
        )
        payload = _parse(raw)
        assert payload["category"] == "consumer_fraud"
        assert payload["results_count"] <= 3
        assert payload["results_count"] == len(payload["results"])

    def test_empty_facts_summary_returns_error(self):
        raw = search_applicable_laws("   ", "unpaid_wages")
        payload = _parse(raw)
        assert "error" in payload

    def test_invalid_category_returns_error_not_exception(self):
        raw = search_applicable_laws("some facts", "fake_category")
        payload = _parse(raw)
        assert "error" in payload
        assert "Invalid category" in payload["error"]

    def test_security_deposit_category_returns_results(self):
        raw = search_applicable_laws(
            "landlord kept deposit after vacating flat",
            "security_deposit",
            top_k=5,
        )
        payload = _parse(raw)
        assert payload["results_count"] > 0

    def test_result_items_have_forum_field(self):
        raw = search_applicable_laws("wages unpaid", "unpaid_wages", top_k=2)
        payload = _parse(raw)
        for item in payload["results"]:
            assert "forum" in item, "Each result must include the 'forum' field"

    def test_result_items_have_notice_period_and_penalty(self):
        raw = search_applicable_laws("wages delayed", "unpaid_wages", top_k=5)
        payload = _parse(raw)
        for item in payload["results"]:
            assert "notice_period_days" in item
            assert "penalty" in item

    def test_top_k_1_returns_one_result(self):
        raw = search_applicable_laws("wages", "unpaid_wages", top_k=1)
        payload = _parse(raw)
        assert payload["results_count"] == 1

    def test_all_three_categories_return_results(self):
        queries = {
            "unpaid_wages": "employer withheld last month salary",
            "consumer_fraud": "defective product refund denied",
            "security_deposit": "landlord refused to return deposit",
        }
        for category, query in queries.items():
            raw = search_applicable_laws(query, category)
            payload = _parse(raw)
            assert payload["results_count"] > 0, f"No results for {category}"


# ---------------------------------------------------------------------------
# validate_notice_citations
# ---------------------------------------------------------------------------

class TestValidateNoticeCitations:
    def test_valid_citation_returns_is_valid_true(self):
        draft = (
            "Under Section 35 of the Consumer Protection Act 2019, "
            "we hereby submit this complaint to the District Commission."
        )
        report = _parse(validate_notice_citations(draft))
        assert report["is_valid"] is True
        assert report["errors"] == []

    def test_hallucinated_section_returns_is_valid_false(self):
        draft = (
            "Section 999 of the Consumer Protection Act 2019 clearly states "
            "that the seller must refund within 3 days."
        )
        report = _parse(validate_notice_citations(draft))
        assert report["is_valid"] is False
        assert len(report["errors"]) >= 1

    def test_error_entry_has_required_fields(self):
        draft = "As per Section 777 of the Payment of Wages Act 1936."
        report = _parse(validate_notice_citations(draft))
        assert report["is_valid"] is False
        err = report["errors"][0]
        assert "citation" in err
        assert "error" in err
        assert "suggestion" in err

    def test_empty_draft_returns_error_payload(self):
        raw = validate_notice_citations("")
        payload = _parse(raw)
        assert "error" in payload

    def test_draft_with_no_sections_is_valid(self):
        draft = "This is a letter requesting resolution of our dispute amicably."
        report = _parse(validate_notice_citations(draft))
        assert report["is_valid"] is True
        assert report["valid_citations"] == []
        assert report["errors"] == []

    def test_multiple_hallucinated_sections_all_in_errors(self):
        draft = (
            "Section 100, Section 200, and Section 300 of the "
            "Model Tenancy Act 2021 are all relevant here."
        )
        report = _parse(validate_notice_citations(draft))
        assert report["is_valid"] is False
        assert len(report["errors"]) == 3

    def test_section_107_tenancy_is_valid(self):
        draft = (
            "Under Section 107 of the Model Tenancy Act 2021, "
            "the landlord is liable to pay interest at 8% on the unreturned deposit."
        )
        report = _parse(validate_notice_citations(draft))
        assert report["is_valid"] is True

    def test_summary_present_in_all_responses(self):
        cases = [
            "Section 5 of the Payment of Wages Act 1936.",
            "Section 999 is fake.",
            "No citations here.",
        ]
        for draft in cases:
            report = _parse(validate_notice_citations(draft))
            assert "summary" in report, f"No summary in report for: {draft!r}"

    def test_section_45_irc_is_valid(self):
        draft = (
            "Under Section 45 of the Industrial Relations Code 2020, "
            "wages must be paid within two working days of termination."
        )
        report = _parse(validate_notice_citations(draft))
        assert report["is_valid"] is True

    def test_mix_valid_and_invalid_returns_partial_error(self):
        draft = (
            "Under Section 35 of the Consumer Protection Act 2019 "
            "and Section 888 of the same Act, we file this complaint."
        )
        report = _parse(validate_notice_citations(draft))
        assert report["is_valid"] is False
        assert len(report["valid_citations"]) == 1
        assert len(report["errors"]) == 1
        assert "888" in report["errors"][0]["citation"]
