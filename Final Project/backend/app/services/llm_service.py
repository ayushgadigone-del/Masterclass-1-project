"""
llm_service.py — provider-agnostic LLM completion.

Switches between:
  - Ollama (local, free, PII-safe)  when LLM_PROVIDER=ollama
  - OpenAI GPT-4o mini (paid)       when LLM_PROVIDER=openai

The interface is a single synchronous function:
    complete(prompt: str, system: str | None) -> str

If neither provider is reachable, falls back to a deterministic
template renderer so the backend stays functional for tests.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from app.config import settings


def complete(prompt: str, system: str | None = None) -> str:
    """
    Send a completion request to the configured LLM provider.

    Parameters
    ----------
    prompt : str
        The user prompt (may contain the full notice-drafting instruction).
    system : str | None
        Optional system message.

    Returns
    -------
    str
        The LLM's completion text.
    """
    if settings.llm_provider == "openai":
        return _openai_complete(prompt, system)
    return _ollama_complete(prompt, system)


# ── Ollama ────────────────────────────────────────────────────────────────────

def _ollama_complete(prompt: str, system: str | None) -> str:
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps(
        {
            "model": settings.ollama_model,
            "messages": messages,
            "stream": False,
        }
    ).encode()

    req = urllib.request.Request(
        f"{settings.ollama_base_url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data: dict[str, Any] = json.loads(resp.read().decode())
            return data["message"]["content"]
    except Exception as exc:
        # Fall back to template on connection failure (dev without Ollama)
        return _fallback_draft(prompt, error=str(exc))


# ── OpenAI ────────────────────────────────────────────────────────────────────

def _openai_complete(prompt: str, system: str | None) -> str:
    if not settings.openai_api_key:
        return _fallback_draft(prompt, error="OPENAI_API_KEY not set")

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps(
        {
            "model": settings.openai_model,
            "messages": messages,
            "temperature": 0.3,
        }
    ).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.openai_api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data: dict[str, Any] = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"]
    except Exception as exc:
        return _fallback_draft(prompt, error=str(exc))


# ── Deterministic fallback (no LLM available) ─────────────────────────────────

def _fallback_draft(prompt: str, error: str = "") -> str:
    """
    Used when no LLM is reachable (offline dev / CI).
    Extracts the [STATUTES] block and returns a minimal template notice.
    The template still only contains verbatim statute text — no hallucination.
    """
    note = f"[LLM unavailable: {error}]\n\n" if error else ""
    # Extract facts and statutes from the structured prompt
    facts_section = ""
    statutes_section = ""
    if "[GRIEVANCE FACTS]" in prompt and "[STATUTES]" in prompt:
        parts = prompt.split("[STATUTES]")
        facts_part = parts[0].split("[GRIEVANCE FACTS]")[-1].strip()
        statutes_part = parts[1].strip()
        facts_section = facts_part
        statutes_section = statutes_part

    return (
        f"{note}"
        "LEGAL NOTICE\n"
        "============\n\n"
        f"Facts:\n{facts_section}\n\n"
        "Legal Basis (verbatim from statute knowledge base):\n"
        f"{statutes_section}\n\n"
        "You are hereby called upon to address the above grievance within "
        "30 (thirty) days of receipt of this notice.  Failure to respond "
        "will result in initiation of appropriate legal proceedings before "
        "the competent forum as cited above.\n"
    )
