"""
pii_masker.py — Per-request PII masking for LLM prompt safety.

Sensitive identifiers are replaced with opaque tokens before any text
is sent to an external (or local) LLM.  The original values are stored
only in memory (a plain dict) and are re-hydrated by the caller — the
PDF renderer — immediately before writing the final document.

Masked PII types
----------------
  - Phone numbers       (Indian mobile / landline patterns)
  - Aadhaar numbers     (12-digit, with / without spaces)
  - PAN numbers         (AAAAA9999A format)
  - Bank account numbers(9–18 digit sequences not already matched)
  - UPI IDs             (anything@upihandle)
  - Email addresses     (RFC 5321 simplified)

Token format
------------
  Each detected value is replaced with  <<PII_TYPE_N>>  where N is a
  monotonically increasing counter within the request, e.g.
  <<PHONE_1>>, <<AADHAAR_1>>, <<EMAIL_2>>.

Usage
-----
    store: dict[str, str] = {}
    masked_text = mask_pii(original_text, store)
    # ... send masked_text to LLM ...
    final_text = unmask_pii(llm_output, store)
"""
from __future__ import annotations

import re
from typing import NamedTuple


# ── Regex patterns ────────────────────────────────────────────────────────────
# Order matters: more-specific patterns must appear before catch-all ones.

class _Pattern(NamedTuple):
    label: str   # token prefix, e.g. "PHONE"
    regex: str


_PATTERNS: list[_Pattern] = [
    # Aadhaar: 12 digits optionally grouped in 4-4-4 with spaces/hyphens
    _Pattern("AADHAAR", r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    # PAN: AAAAA9999A (5 letters, 4 digits, 1 letter)
    _Pattern("PAN", r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"),
    # UPI: something@bankhandle  (must come before email to avoid partial match)
    _Pattern("UPI", r"\b[\w.\-]+@(?:upi|oksbi|okaxis|okhdfcbank|okicici|ybl|ibl|axl|apl|paytm|"
                    r"freecharge|juspay|sbi|barodampay|unionbank|cnrb|mahb|rbl|"
                    r"hsbc|citi|dcb|indus|federal|kvb|dbs|nsdl|pnb|icici|hdfc|"
                    r"kotak|axis|yes|idbi|bob|boi|allbank|andb|vijb|uco)\b"),
    # Email addresses (generic)
    _Pattern("EMAIL", r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    # Indian mobile numbers: 10 digits optionally preceded by +91 / 0
    _Pattern("PHONE", r"(?<!\d)(?:\+91[\s\-]?|0)?[6-9]\d{9}(?!\d)"),
    # Indian landline: STD code (2–4 digits) + 6–8 digit number, hyphen-separated
    _Pattern("PHONE", r"\b0\d{2,4}[\s\-]\d{6,8}\b"),
    # Bank account: 9–18 consecutive digits (not already masked as Aadhaar/PAN)
    _Pattern("BANK_ACCOUNT", r"\b\d{9,18}\b"),
]

_COMPILED: list[tuple[str, re.Pattern[str]]] = [
    (p.label, re.compile(p.regex)) for p in _PATTERNS
]


# ── Public API ────────────────────────────────────────────────────────────────

def mask_pii(text: str, store: dict[str, str]) -> str:
    """
    Replace all PII in *text* with opaque tokens, recording the mapping
    in *store* (token → original value).

    The function is idempotent: calling it twice on already-masked text
    will not double-mask because masked tokens don't look like PII.

    Parameters
    ----------
    text  : str             The raw text that may contain PII.
    store : dict[str, str]  Mutable mapping owned by the caller; tokens are
                            added here.  Pass an empty dict per request.

    Returns
    -------
    str  The text with all detected PII replaced by tokens.
    """
    # Track per-label counters for readable token names
    counters: dict[str, int] = {}

    def _replace(label: str, pattern: re.Pattern[str], s: str) -> str:
        def _sub(match: re.Match[str]) -> str:
            original = match.group(0)
            # Check if this value is already stored (dedup)
            existing = _find_token(original, store)
            if existing:
                return existing
            counters[label] = counters.get(label, 0) + 1
            token = f"<<{label}_{counters[label]}>>"
            store[token] = original
            return token
        return pattern.sub(_sub, s)

    result = text
    for label, pattern in _COMPILED:
        result = _replace(label, pattern, result)
    return result


def unmask_pii(text: str, store: dict[str, str]) -> str:
    """
    Reverse all token substitutions recorded in *store*.

    Parameters
    ----------
    text  : str             Text that may contain <<TOKEN_N>> placeholders.
    store : dict[str, str]  The same mapping produced by :func:`mask_pii`.

    Returns
    -------
    str  Text with all tokens replaced by their original PII values.
    """
    result = text
    for token, original in store.items():
        result = result.replace(token, original)
    return result


def mask_dict(data: dict, store: dict[str, str]) -> dict:
    """
    Return a shallow copy of *data* with all string values masked.
    Non-string values (int, float, None, …) are passed through unchanged.
    Nested dicts and lists are recursively processed.

    Parameters
    ----------
    data  : dict            The dict to mask (e.g. ``facts.model_dump()``).
    store : dict[str, str]  Shared token store for this request.

    Returns
    -------
    dict  A new dict with the same structure but masked string values.
    """
    out: dict = {}
    for key, value in data.items():
        if isinstance(value, str):
            out[key] = mask_pii(value, store)
        elif isinstance(value, dict):
            out[key] = mask_dict(value, store)
        elif isinstance(value, list):
            out[key] = [
                mask_pii(item, store) if isinstance(item, str)
                else mask_dict(item, store) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            out[key] = value
    return out


# ── Internal helpers ──────────────────────────────────────────────────────────

def _find_token(original: str, store: dict[str, str]) -> str | None:
    """Return the existing token for *original* if already in *store*."""
    for token, value in store.items():
        if value == original:
            return token
    return None
