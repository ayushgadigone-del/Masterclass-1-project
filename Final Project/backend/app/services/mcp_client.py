"""
mcp_client.py — synchronous client for the mcp-statute-server subprocess.

Instead of the full MCP stdio protocol (which requires an async event loop
and the mcp library), we call the statute lookup logic **directly** by
importing the module.  This keeps the backend dependency-free from the mcp
package while reusing the exact same tested logic.

If the MCP server is deployed as a separate process (e.g. in Docker), swap
the import for an HTTP call to the server's SSE/HTTP endpoint.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add the mcp-statute-server root to sys.path so we can import its modules
_MCP_ROOT = Path(__file__).parent.parent.parent.parent / "mcp-statute-server"
if str(_MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(_MCP_ROOT))

from tools.statute_lookup import (
    StatuteResult,
    ValidationReport,
    search_applicable_laws,
    validate_notice_citations,
)


def call_search_applicable_laws(
    facts_summary: str,
    category: str,
    top_k: int = 5,
) -> list[StatuteResult]:
    """
    Retrieve statute sections relevant to the citizen's grievance.

    Parameters
    ----------
    facts_summary : str
        Plain-language summary of the grievance facts.
    category : str
        "unpaid_wages" | "consumer_fraud" | "security_deposit"
    top_k : int
        Max number of sections to return.

    Returns
    -------
    list[StatuteResult]
        Sorted by relevance_score descending.  All text verbatim from statutes.json.

    Raises
    ------
    ValueError
        If category is not one of the three valid values.
    """
    return search_applicable_laws(facts_summary, category, top_k=top_k)


def call_validate_notice_citations(draft_text: str) -> ValidationReport:
    """
    Scan a drafted notice for section references and verify each one exists.

    Returns a ValidationReport with is_valid, valid_citations, errors, summary.
    """
    return validate_notice_citations(draft_text)


# Category mapping: SPEC uses different names in some places
CATEGORY_ALIASES: dict[str, str] = {
    "consumer_protection": "consumer_fraud",
    "payment_of_wages": "unpaid_wages",
    "tenancy": "security_deposit",
    # pass-through
    "consumer_fraud": "consumer_fraud",
    "unpaid_wages": "unpaid_wages",
    "security_deposit": "security_deposit",
}


def normalise_category(raw: str) -> str:
    """Map SPEC dispute_category names to MCP category names."""
    return CATEGORY_ALIASES.get(raw, raw)
