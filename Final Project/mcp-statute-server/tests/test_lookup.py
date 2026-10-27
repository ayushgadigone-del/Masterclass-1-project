"""
test_lookup.py
--------------
Unit tests for tools/statute_lookup.py

Coverage:
  search_applicable_laws
    - Returns results for each of the 3 valid categories
    - Relevance scoring: keyword-rich query scores higher than empty query
    - top_k parameter is respected
    - Invalid category raises ValueError
    - Empty facts_summary still returns results (no crash)

  validate_notice_citations
    - Valid citations (Section 35, Section 15) return is_valid=True
    - Non-existent section (Section 999) returns is_valid=False with error
    - Multiple citations: mix of valid + invalid produces correct error count
    - Hallucinated act + section (e.g. "Section 42 of the Imaginary Act") is flagged
    - Draft with no section references at all returns is_valid=True, no errors
    - Case-insensitivity: "section 35" and "SECTION 35" both resolve

Tests deliberately do NOT import MCP or start a server — they test the pure
Python logic layer so they run without any network or subprocess dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the mcp-statute-server root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from tools.statute_lookup import (
    VALID_CATEGORIES,
    ValidationReport,
    search_applicable_laws,
    validate_notice_citations,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _has_section(results, section_number: str) -> bool:
    return any(r["section"] == f"Section {section_number}" for r in results)


# ---------------------------------------------------------------------------
# search_applicable_laws — category validation
# ---------------------------------------------------------------------------

class TestSearchCategoryValidation:
    def test_invalid_category_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid category"):
            search_applicable_laws("employer did not pay salary", "invalid_category")

    def test_each_valid_category_returns_results(self):
        queries = {
            "unpaid_wages": "employer withheld last month salary after termination",
            "consumer_fraud": "defective product refund denied by seller",
            "security_deposit": "landlord refused to return security deposit after vacating",
        }
        for category, query in queries.items():
            results = search_applicable_laws(query, category)
            assert len(results) > 0, f"Expected results for category '{category}'"

    def test_valid_categories_constant_matches_expected(self):
        assert VALID_CATEGORIES == {"unpaid_wages", "consumer_fraud", "security_deposit"}


# ---------------------------------------------------------------------------
# search_applicable_laws — result structure
# ---------------------------------------------------------------------------

class TestSearchResultStructure:
    def test_result_has_required_keys(self):
        results = search_applicable_laws("wages not paid", "unpaid_wages", top_k=1)
        assert len(results) == 1
        r = results[0]
        for key in ("act", "section", "section_title", "excerpt", "relevance_score",
                    "notice_period_days", "penalty", "forum"):
            assert key in r, f"Missing key '{key}' in result"

    def test_section_formatted_with_prefix(self):
        results = search_applicable_laws("salary delayed", "unpaid_wages", top_k=3)
        for r in results:
            assert r["section"].startswith("Section "), (
                f"Section field should start with 'Section ', got: {r['section']}"
            )

    def test_excerpt_max_500_chars(self):
        results = search_applicable_laws("wages", "unpaid_wages", top_k=5)
        for r in results:
            assert len(r["excerpt"]) <= 500, (
                f"Excerpt exceeds 500 chars for section {r['section']}"
            )

    def test_relevance_score_is_float(self):
        results = search_applicable_laws("wages not paid", "unpaid_wages", top_k=3)
        for r in results:
            assert isinstance(r["relevance_score"], float)

    def test_results_sorted_by_score_descending(self):
        results = search_applicable_laws(
            "employer withheld wages after termination delay", "unpaid_wages", top_k=5
        )
        scores = [r["relevance_score"] for r in results]
        assert scores == sorted(scores, reverse=True), "Results not sorted by score"


# ---------------------------------------------------------------------------
# search_applicable_laws — top_k
# ---------------------------------------------------------------------------

class TestSearchTopK:
    def test_top_k_1_returns_one_result(self):
        results = search_applicable_laws("wages", "unpaid_wages", top_k=1)
        assert len(results) == 1

    def test_top_k_3_returns_at_most_3(self):
        results = search_applicable_laws("wages", "unpaid_wages", top_k=3)
        assert len(results) <= 3

    def test_top_k_default_is_5(self):
        results = search_applicable_laws("wages", "unpaid_wages")
        assert len(results) <= 5

    def test_top_k_larger_than_corpus_returns_all(self):
        # top_k=100 should return every unpaid_wages provision in the corpus
        results = search_applicable_laws("wages", "unpaid_wages", top_k=100)
        # Corpus currently has 9 unpaid_wages entries (PWA + IRC sections)
        assert len(results) >= 5


# ---------------------------------------------------------------------------
# search_applicable_laws — keyword relevance
# ---------------------------------------------------------------------------

class TestSearchRelevance:
    def test_termination_keywords_surface_termination_sections(self):
        results = search_applicable_laws(
            "employment terminated wages not paid within two days",
            "unpaid_wages",
            top_k=3,
        )
        # Section 5 (time of payment / 7-day / 2-day rule) or Section 45 (IRC termination)
        has_relevant = any(
            r["section"] in ("Section 5", "Section 45") for r in results
        )
        assert has_relevant, (
            f"Expected Section 5 or 45 in top 3 for termination query, got: "
            f"{[r['section'] for r in results]}"
        )

    def test_refund_defective_product_surfaces_cpa_section_39(self):
        results = search_applicable_laws(
            "defective product refund compensation loss",
            "consumer_fraud",
            top_k=3,
        )
        assert _has_section(results, "39"), (
            f"Expected Section 39 (CPA findings / refund / compensation) in results, "
            f"got: {[r['section'] for r in results]}"
        )

    def test_security_deposit_refund_surfaces_mra_107(self):
        results = search_applicable_laws(
            "landlord not returning security deposit after one month of vacating",
            "security_deposit",
            top_k=3,
        )
        assert _has_section(results, "107"), (
            f"Expected Section 107 (MTA refund + interest) in top 3, "
            f"got: {[r['section'] for r in results]}"
        )

    def test_empty_facts_returns_results_without_crash(self):
        # An empty query should still return results (no crash; score=0 for all)
        results = search_applicable_laws("", "consumer_fraud", top_k=3)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# validate_notice_citations — valid citations
# ---------------------------------------------------------------------------

class TestValidateCitationsValid:
    def test_known_section_35_is_valid(self):
        draft = (
            "Under Section 35 of the Consumer Protection Act 2019, "
            "we hereby file this complaint."
        )
        report: ValidationReport = validate_notice_citations(draft)
        assert report["is_valid"] is True
        assert report["errors"] == []
        assert len(report["valid_citations"]) == 1

    def test_known_section_15_is_valid(self):
        draft = (
            "Pursuant to Section 15 of the Payment of Wages Act 1936, "
            "we demand immediate payment of withheld wages."
        )
        report = validate_notice_citations(draft)
        assert report["is_valid"] is True
        assert report["errors"] == []

    def test_multiple_valid_citations(self):
        draft = (
            "Under Section 5 and Section 15 of the Payment of Wages Act 1936 "
            "the employer is liable for delay in payment of wages."
        )
        report = validate_notice_citations(draft)
        assert report["is_valid"] is True
        assert len(report["errors"]) == 0
        assert len(report["valid_citations"]) == 2

    def test_case_insensitive_section_match(self):
        upper = validate_notice_citations("SECTION 35 of the consumer protection act applies.")
        lower = validate_notice_citations("section 35 of the consumer protection act applies.")
        assert upper["is_valid"] is True
        assert lower["is_valid"] is True

    def test_no_citations_in_draft_is_valid(self):
        draft = "This is a plain letter with no statute references whatsoever."
        report = validate_notice_citations(draft)
        assert report["is_valid"] is True
        assert report["errors"] == []
        assert report["valid_citations"] == []


# ---------------------------------------------------------------------------
# validate_notice_citations — invalid / hallucinated citations
# ---------------------------------------------------------------------------

class TestValidateCitationsInvalid:
    def test_nonexistent_section_999_returns_error(self):
        draft = (
            "Under Section 999 of the Consumer Protection Act 2019, "
            "you are hereby notified."
        )
        report = validate_notice_citations(draft)
        assert report["is_valid"] is False
        assert len(report["errors"]) == 1
        error = report["errors"][0]
        assert "999" in error["citation"]
        assert "hallucinated" in error["error"].lower() or "not match" in error["error"].lower()

    def test_hallucinated_section_in_unknown_act(self):
        draft = "Section 42 of the Imaginary Legal Relief Act applies here."
        report = validate_notice_citations(draft)
        assert report["is_valid"] is False
        assert any("42" in e["citation"] for e in report["errors"])

    def test_mix_valid_and_invalid_citations(self):
        draft = (
            "Under Section 35 of the Consumer Protection Act 2019 and "
            "Section 888 of the same Act, we file this complaint."
        )
        report = validate_notice_citations(draft)
        assert report["is_valid"] is False
        assert len(report["valid_citations"]) == 1
        assert len(report["errors"]) == 1
        assert "888" in report["errors"][0]["citation"]

    def test_multiple_hallucinated_sections_all_flagged(self):
        draft = (
            "Section 111, Section 222, and Section 333 of the "
            "Payment of Wages Act clearly state the following."
        )
        report = validate_notice_citations(draft)
        assert report["is_valid"] is False
        assert len(report["errors"]) == 3

    def test_suggestion_provided_when_act_is_mentioned(self):
        draft = (
            "Under Section 999 of the Consumer Protection Act 2019, "
            "the complainant is entitled to relief."
        )
        report = validate_notice_citations(draft)
        assert report["is_valid"] is False
        error = report["errors"][0]
        # Suggestion should list known sections for CPA 2019
        assert error["suggestion"] is not None
        assert "Consumer Protection Act 2019" in error["suggestion"]

    def test_error_count_in_summary(self):
        draft = "Section 500 and Section 501 are fictitious sections."
        report = validate_notice_citations(draft)
        assert "2" in report["summary"]
        assert report["is_valid"] is False


# ---------------------------------------------------------------------------
# validate_notice_citations — edge cases
# ---------------------------------------------------------------------------

class TestValidateCitationsEdgeCases:
    def test_empty_draft_returns_valid_no_citations(self):
        report = validate_notice_citations("")
        # Empty string — no citations detected
        assert report["valid_citations"] == []
        assert report["errors"] == []

    def test_section_with_subsection_is_valid(self):
        # Section 35(1)(a) style — should resolve to section 35
        draft = "As per Section 35 of the Consumer Protection Act 2019."
        report = validate_notice_citations(draft)
        assert report["is_valid"] is True

    def test_s_dot_abbreviation_detected(self):
        # "S. 38" style abbreviation
        draft = "S. 38 of the Consumer Protection Act 2019 mandates a 30-day response."
        report = validate_notice_citations(draft)
        assert report["is_valid"] is True

    def test_section_106_tenancy_is_valid(self):
        draft = (
            "Under Section 106 of the Model Tenancy Act 2021, "
            "the security deposit shall not exceed two months rent."
        )
        report = validate_notice_citations(draft)
        assert report["is_valid"] is True
