#!/usr/bin/env python3
"""
server.py — MCP Statute Server  (MCP 2.x / MCPServer API)
===========================================================
Exposes two MCP tools over stdio transport:

  1. search_applicable_laws(facts_summary, category, top_k?)
     → Returns the top-K statute sections most relevant to the
       citizen's grievance facts within the specified category.

  2. validate_notice_citations(draft_text)
     → Scans a drafted legal notice for section references and
       verifies every citation exists in the statute knowledge
       base.  Returns a ValidationReport with errors for any
       citation that does not match.

Anti-hallucination guarantee
----------------------------
Neither tool calls an LLM.  All statute text is loaded verbatim
from data/statutes.json.  The LLM (backend) is only allowed to
use citations returned by search_applicable_laws; validate_notice_citations
is the gatekeeper that enforces this constraint before a notice
is submitted to the law clinic queue.

Transport: stdio (spawned as subprocess by backend/mcp_client.py)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

# Ensure the package root is importable when invoked directly
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.mcpserver import MCPServer

from tools.statute_lookup import (
    VALID_CATEGORIES,
    search_applicable_laws as _search_applicable_laws,
    validate_notice_citations as _validate_notice_citations,
)

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

server = MCPServer(
    name="mcp-statute-server",
    version="0.1.0",
    description=(
        "Deterministic statute lookup for Legal Rights Navigator. "
        "All citations are verbatim from the statute knowledge base — "
        "never generated or hallucinated."
    ),
)


# ---------------------------------------------------------------------------
# Tool 1: search_applicable_laws
# ---------------------------------------------------------------------------

@server.tool(
    description=(
        "Search the statute knowledge base for sections applicable to a "
        "citizen's grievance. Returns verbatim statutory text — never "
        "generated or paraphrased. Use this tool to obtain all citations "
        "before drafting any legal notice. Do NOT draft citations from "
        "memory; always call this tool first.\n\n"
        f"Valid categories: {', '.join(sorted(VALID_CATEGORIES))}"
    ),
)
def search_applicable_laws(
    facts_summary: Annotated[
        str,
        "Plain-language summary of the grievance facts, e.g. 'employer withheld last month salary after termination without notice'.",
    ],
    category: Annotated[
        str,
        "Dispute category. Must be one of: unpaid_wages, consumer_fraud, security_deposit.",
    ],
    top_k: Annotated[
        int,
        "Number of most-relevant sections to return (default 5, max 15).",
    ] = 5,
) -> str:
    """
    Returns a JSON object with:
      - category: the queried category
      - query: the facts_summary
      - results_count: number of results returned
      - results: list of StatuteResult objects

    Each StatuteResult has:
      act, section, section_title, excerpt (verbatim ≤500 chars),
      relevance_score, notice_period_days, penalty, forum
    """
    facts_summary = facts_summary.strip()
    if not facts_summary:
        return json.dumps(
            {"error": "facts_summary is required and must not be empty."},
            ensure_ascii=False,
        )

    try:
        results = _search_applicable_laws(facts_summary, category, top_k=top_k)
    except ValueError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    payload = {
        "category": category,
        "query": facts_summary,
        "results_count": len(results),
        "results": results,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: validate_notice_citations
# ---------------------------------------------------------------------------

@server.tool(
    description=(
        "Scan a drafted legal notice for all section references "
        "(e.g. 'Section 35', 'Section 15(1)(a)', 'S. 38') and verify each "
        "one exists in the statute knowledge base. Returns a ValidationReport. "
        "If is_valid is false, the notice MUST NOT be submitted — fix all "
        "errors first to prevent hallucinated citations from reaching the citizen."
    ),
)
def validate_notice_citations(
    draft_text: Annotated[
        str,
        "The complete text of the drafted legal notice.",
    ],
) -> str:
    """
    Returns a JSON ValidationReport with:
      - is_valid: bool — True only when all detected citations are verified
      - valid_citations: list of verified citation strings with act name
      - errors: list of {citation, error, suggestion} for unknown sections
      - summary: human-readable summary string
    """
    draft_text = draft_text.strip()
    if not draft_text:
        return json.dumps(
            {"error": "draft_text is required and must not be empty."},
            ensure_ascii=False,
        )

    report = _validate_notice_citations(draft_text)
    return json.dumps(report, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    asyncio.run(server.run_stdio_async())
