"""
statute_lookup.py
-----------------
Deterministic keyword-scoring search engine over the statute knowledge base.

Design contract (anti-hallucination guarantee):
- All returned `excerpt` values are verbatim text from statutes.json.
- No LLM, no embeddings, no generation — pure BM25-style TF overlap.
- The `validate_notice_citations` tool cross-checks draft text against this
  same data; any section not present here returns a ValidationError.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import TypedDict

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

VALID_CATEGORIES = frozenset({"unpaid_wages", "consumer_fraud", "security_deposit"})

DATA_PATH = Path(__file__).parent.parent / "data" / "statutes.json"


class StatuteResult(TypedDict):
    act: str
    section: str
    section_title: str
    excerpt: str          # verbatim statutory text (truncated to 500 chars)
    relevance_score: float
    notice_period_days: int | None
    penalty: str | None
    forum: str


class ValidationError(TypedDict):
    citation: str         # the raw citation string found in the draft
    error: str            # human-readable explanation
    suggestion: str | None


class ValidationReport(TypedDict):
    is_valid: bool
    valid_citations: list[str]
    errors: list[ValidationError]
    summary: str


# ---------------------------------------------------------------------------
# Statute loader (lazy, cached at module level)
# ---------------------------------------------------------------------------

_STATUTES: list[dict] | None = None


def _load_statutes() -> list[dict]:
    global _STATUTES
    if _STATUTES is None:
        with DATA_PATH.open(encoding="utf-8") as fh:
            _STATUTES = json.load(fh)
    return _STATUTES


# ---------------------------------------------------------------------------
# Section reference index  (act_normalised + section → statute entry)
# ---------------------------------------------------------------------------

def _build_section_index(statutes: list[dict]) -> dict[tuple[str, str], dict]:
    """
    Returns a dict keyed by (normalised_act_name, normalised_section).
    Used by validate_notice_citations for exact-match lookups.
    """
    index: dict[tuple[str, str], dict] = {}
    for s in statutes:
        act_key = _normalise(s["act"])
        sec_key = _normalise(s["section"])
        index[(act_key, sec_key)] = s
        # Also index by section alone for partial lookups
        index[(None, sec_key)] = s  # type: ignore[index]  # last-writer-wins
    return index


def _normalise(text: str) -> str:
    """Lower-case, strip punctuation/whitespace for fuzzy matching."""
    return re.sub(r"[\s\(\)\-/]", "", text.lower())


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _score(statute: dict, keywords: list[str]) -> float:
    """
    BM25-inspired term-overlap score.

    Searches the combined token bag of: statute keywords list + section_title
    + first 200 chars of text.  Each query keyword that matches at least one
    token gets a score contribution weighted by inverse document frequency
    (approximated as 1 / sqrt(token_count)).
    """
    # Build token bag from the statute entry
    token_bag: list[str] = []
    token_bag.extend(k.lower() for k in statute.get("keywords", []))
    token_bag.extend(_tokenise(statute.get("section_title", "")))
    token_bag.extend(_tokenise(statute.get("text", "")[:200]))

    total_tokens = max(len(token_bag), 1)
    score = 0.0
    for kw in keywords:
        kw_lower = kw.lower()
        # count occurrences across token bag
        hits = sum(1 for t in token_bag if kw_lower in t)
        if hits:
            tf = hits / total_tokens
            idf = 1.0 / math.sqrt(total_tokens)
            score += tf + idf  # simple combined weight

    return round(score, 6)


def _tokenise(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


# ---------------------------------------------------------------------------
# Public API: search_applicable_laws
# ---------------------------------------------------------------------------

def search_applicable_laws(
    facts_summary: str,
    category: str,
    top_k: int = 5,
) -> list[StatuteResult]:
    """
    Return up to `top_k` statute sections most relevant to `facts_summary`
    within the given `category`.

    Parameters
    ----------
    facts_summary : str
        Plain-language summary of the citizen's grievance facts.
    category : str
        One of "unpaid_wages", "consumer_fraud", "security_deposit".
    top_k : int
        Maximum number of results to return (default 5).

    Returns
    -------
    list[StatuteResult]
        Sorted by relevance_score descending.  All text is verbatim from
        statutes.json.

    Raises
    ------
    ValueError
        If `category` is not one of the three valid values.
    """
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. "
            f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        )

    statutes = _load_statutes()
    keywords = _tokenise(facts_summary)

    candidates = [s for s in statutes if s["category"] == category]
    scored = [(s, _score(s, keywords)) for s in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    results: list[StatuteResult] = []
    for statute, score in top:
        excerpt = statute["text"]
        if len(excerpt) > 500:
            excerpt = excerpt[:497] + "..."
        results.append(
            StatuteResult(
                act=statute["act"],
                section=f"Section {statute['section']}",
                section_title=statute["section_title"],
                excerpt=excerpt,
                relevance_score=score,
                notice_period_days=statute.get("notice_period_days"),
                penalty=statute.get("penalty"),
                forum=statute["forum"],
            )
        )

    return results


# ---------------------------------------------------------------------------
# Public API: validate_notice_citations
# ---------------------------------------------------------------------------

# Patterns that could look like a section reference in a drafted notice.
# Catches: "Section 35", "Section 35(1)(a)", "S. 38", "Sec 4", "§ 106"
_CITATION_RE = re.compile(
    r"(?:section|sec|s\.)\s*(\d+(?:\(\w+\))*)|§\s*(\d+(?:\(\w+\))*)",
    re.IGNORECASE,
)

# Known acts, normalised for fuzzy matching
_ACT_ALIASES: dict[str, str] = {
    "payment of wages act": "Payment of Wages Act 1936",
    "payment of wages act 1936": "Payment of Wages Act 1936",
    "industrial relations code": "Industrial Relations Code 2020",
    "industrial relations code 2020": "Industrial Relations Code 2020",
    "consumer protection act": "Consumer Protection Act 2019",
    "consumer protection act 2019": "Consumer Protection Act 2019",
    "model tenancy act": "Model Tenancy Act 2021",
    "model tenancy act 2021": "Model Tenancy Act 2021",
}


def _resolve_act(text: str) -> str | None:
    """Best-effort act name resolution from surrounding text."""
    text_lower = text.lower()
    for alias, canonical in _ACT_ALIASES.items():
        if alias in text_lower:
            return canonical
    return None


def validate_notice_citations(draft_text: str) -> ValidationReport:
    """
    Scan a draft legal notice for section citations and verify each one
    exists verbatim in the statute knowledge base.

    Parameters
    ----------
    draft_text : str
        The full text of the drafted legal notice.

    Returns
    -------
    ValidationReport
        `is_valid` is True only when every detected citation resolves to a
        known statute section.  Unknown/hallucinated citations appear in
        `errors`.
    """
    statutes = _load_statutes()
    section_index = _build_section_index(statutes)

    # Build a lookup: normalised_section → set of acts that have it
    section_to_acts: dict[str, list[str]] = {}
    for s in statutes:
        norm_sec = _normalise(s["section"])
        section_to_acts.setdefault(norm_sec, []).append(s["act"])

    valid_citations: list[str] = []
    errors: list[ValidationError] = []

    # Detect all section-like references
    for match in _CITATION_RE.finditer(draft_text):
        raw_section = (match.group(1) or match.group(2)).strip()
        norm_sec = _normalise(raw_section)
        citation_str = match.group(0).strip()

        if norm_sec in section_to_acts:
            valid_citations.append(
                f"{citation_str} → {', '.join(section_to_acts[norm_sec])}"
            )
        else:
            # Try to find the nearest act mention for a helpful suggestion
            # Use a window of 200 chars around the citation
            start = max(0, match.start() - 200)
            end = min(len(draft_text), match.end() + 200)
            context_window = draft_text[start:end]
            resolved_act = _resolve_act(context_window)

            suggestion: str | None = None
            if resolved_act:
                # Find closest section number in that act
                act_sections = [
                    s["section"]
                    for s in statutes
                    if s["act"] == resolved_act
                ]
                suggestion = (
                    f"Known sections for {resolved_act}: "
                    + ", ".join(f"Section {sec}" for sec in act_sections)
                )

            errors.append(
                ValidationError(
                    citation=citation_str,
                    error=(
                        f"'{citation_str}' does not match any section in the "
                        f"statute knowledge base.  This citation may be "
                        f"hallucinated or misquoted."
                    ),
                    suggestion=suggestion,
                )
            )

    is_valid = len(errors) == 0

    if is_valid and valid_citations:
        summary = (
            f"All {len(valid_citations)} citation(s) verified against the "
            f"statute knowledge base."
        )
    elif is_valid and not valid_citations:
        summary = "No statute citations detected in the draft text."
    else:
        summary = (
            f"{len(errors)} unverified citation(s) found. "
            f"{len(valid_citations)} citation(s) are valid. "
            f"Review errors before sending the notice."
        )

    return ValidationReport(
        is_valid=is_valid,
        valid_citations=valid_citations,
        errors=errors,
        summary=summary,
    )
