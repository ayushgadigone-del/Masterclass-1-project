# Legal Rights Navigator: Pre-Litigation Engine

> **SDG 16 LegalTech MVP** — Converting a citizen's plain-language grievance into a statute-cited, law-clinic-verified legal notice, with a settlement portal for the opposing party.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-blue?logo=github)](https://ayushgadigone-del.github.io/legal-rights-navigator/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](https://nextjs.org)
[![Deploy](https://img.shields.io/github/actions/workflow/status/ayushgadigone-del/legal-rights-navigator/deploy-frontend.yml?label=Deploy&logo=github-actions)](https://github.com/ayushgadigone-del/legal-rights-navigator/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-108%20passing-brightgreen)](#running-tests)

---

## 🌐 Try It Now — No Installation Required

**The frontend is live on GitHub Pages:**

| Role | Link |
|---|---|
| 🏠 Landing page | **[ayushgadigone-del.github.io/legal-rights-navigator/](https://ayushgadigone-del.github.io/legal-rights-navigator/)** |
| 🎙️ Citizen Intake Wizard | [/citizen](https://ayushgadigone-del.github.io/legal-rights-navigator/citizen) |
| ⚖️ Law Clinic Review Queue | [/clinic](https://ayushgadigone-del.github.io/legal-rights-navigator/clinic) |
| 🤝 Settlement Portal | [/settlement/demo](https://ayushgadigone-del.github.io/legal-rights-navigator/settlement/demo) |
| 📊 SDG Metrics Dashboard | [/dashboard](https://ayushgadigone-del.github.io/legal-rights-navigator/dashboard) |

> **Click any of the three sample case buttons** on the Citizen page to see a full end-to-end demo — statute-cited legal notice generated entirely in the browser with no backend.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
  - [Open in Browser (No Install)](#open-in-browser-no-install)
  - [Run Locally (One Click)](#run-locally-one-click)
  - [Backend](#backend)
  - [MCP Statute Server](#mcp-statute-server)
  - [Full Stack Dev](#full-stack-dev)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Security & Privacy](#security--privacy)
- [SDG 16 Alignment](#sdg-16-alignment)
- [Specification](#specification)

---

## Overview

**Legal Rights Navigator** lowers the barrier to justice for citizens who cannot afford legal representation. A citizen describes their grievance in plain language (or by voice) — the system:

1. Extracts structured legal facts through a conversational intake wizard
2. Looks up relevant statute sections via a deterministic **MCP Statute Server** (no LLM hallucination of citations)
3. Drafts a formal pre-litigation legal notice using a local LLM (Mistral 7B via Ollama)
4. Routes the draft to a **law clinic student** for review and approval
5. Generates a tamper-evident PDF with a SHA-256 hash
6. Provides the opposing party with a JWT-signed **Settlement Portal** URL

The frontend works **fully offline in demo mode** — no backend or API key needed to explore the full citizen journey.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               Next.js Frontend (GitHub Pages)               │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Citizen      │  │ Law Clinic       │  │ Settlement   │  │
│  │ Intake Wizard│  │ Review Queue     │  │ Portal       │  │
│  └──────┬───────┘  └────────┬─────────┘  └──────┬───────┘  │
└─────────│───────────────────│────────────────────│──────────┘
          │  HTTP (REST)  [optional — demo mode    │
          │  when backend not running works offline]│
┌─────────▼───────────────────▼────────────────────▼──────────┐
│                    FastAPI Backend                           │
│  POST /api/intake/message    PATCH /api/clinic/verify/{id}  │
│  POST /api/notice/generate   GET  /api/clinic/notice/{id}/pdf│
│  POST /api/auth/register     POST /api/auth/login           │
│             │                          │                     │
│    ┌────────▼──────────┐    ┌──────────▼─────────┐          │
│    │  LLM Service      │    │  PDF Service        │          │
│    │  Ollama/OpenAI    │    │  WeasyPrint+SHA256  │          │
│    └────────┬──────────┘    └────────────────────-┘          │
│             │ calls directly (no subprocess)                 │
│    ┌────────▼──────────┐                                     │
│    │ MCP Statute Server│  ← anti-hallucination layer        │
│    │  search_laws()    │                                     │
│    │  validate_cites() │                                     │
│    └────────┬──────────┘                                     │
│             │                                                │
│    ┌────────▼──────────┐                                     │
│    │  statutes.json    │  34 provisions across 4 acts       │
│    └───────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

**Anti-hallucination guarantee:** The LLM is never asked to recall statute section numbers. Every citation in the draft notice is sourced verbatim from `statutes.json` via the MCP server tools.

---

## Repository Structure

```
legal-rights-navigator/
├── SPEC.md                          ← Full implementation specification
├── README.md                        ← This file
├── Start Frontend.bat               ← Double-click launcher (Windows, no terminal)
├── .github/
│   └── workflows/
│       └── deploy-frontend.yml      ← Auto-deploy to GitHub Pages on push
│
├── backend/                         ← Python FastAPI service
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                  ← FastAPI app + lifespan
│   │   ├── config.py                ← Pydantic settings (reads .env)
│   │   ├── models/
│   │   │   ├── case.py              ← CaseRecord, LegalFacts, MANDATORY_FIELDS
│   │   │   ├── notice.py            ← LegalNotice, StatuteCitation, DTOs
│   │   │   └── reviewer.py          ← ReviewerRecord, TokenResponse
│   │   ├── db/
│   │   │   ├── database.py          ← SQLModel engine, create_db_and_tables()
│   │   │   ├── sql_models.py        ← CaseTable, NoticeTable, ReviewerTable
│   │   │   └── store.py             ← Generic Store[M] — get/put/filter/delete
│   │   ├── services/
│   │   │   ├── pii_masker.py        ← PII masking before LLM calls (GDPR-safe)
│   │   │   ├── auth_service.py      ← PBKDF2 passwords + JWT tokens
│   │   │   ├── mcp_client.py        ← Calls MCP statute tools (direct import)
│   │   │   ├── llm_service.py       ← Ollama / OpenAI / fallback
│   │   │   ├── intake_service.py    ← Regex fact extraction, follow-up questions
│   │   │   ├── notice_service.py    ← MCP → mask → LLM → unmask → validate
│   │   │   └── pdf_service.py       ← HTML→PDF, SHA-256 hash, settlement JWT
│   │   └── routers/
│   │       ├── auth.py              ← /api/auth/* + get_current_reviewer dep
│   │       ├── intake.py            ← POST /api/intake/message
│   │       ├── notice.py            ← POST /api/notice/generate
│   │       └── clinic.py            ← PATCH /api/clinic/verify/{id} [auth]
│   └── tests/
│       ├── conftest.py              ← Isolated per-test SQLite DB + auth fixtures
│       ├── test_intake.py
│       ├── test_notice.py
│       ├── test_clinic.py
│       └── test_pii_security.py     ← 53 PII masking + RBAC tests
│
├── mcp-statute-server/              ← MCP 2.x deterministic statute lookup
│   ├── server.py                    ← MCPServer with 2 registered tools
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── data/
│   │   └── statutes.json            ← 34 provisions across 4 Acts
│   ├── tools/
│   │   └── statute_lookup.py        ← BM25-style search engine
│   └── tests/
│       ├── test_lookup.py           ← 30 lookup tests
│       └── test_server_tools.py     ← 20 MCP tool interface tests
│
└── frontend/                        ← Next.js 14 App Router + Tailwind CSS
    ├── next.config.js               ← Static export config for GitHub Pages
    ├── src/app/
    │   ├── page.tsx                 ← Landing: 4 role cards
    │   ├── citizen/page.tsx         ← Voice intake + offline demo mode
    │   ├── clinic/page.tsx          ← Split-screen editor + statute badges
    │   ├── settlement/demo/page.tsx ← 7-day countdown + 4-option resolution
    │   └── dashboard/page.tsx       ← SDG metrics + unit economics
    └── src/components/
        ├── StatuteBadge.tsx
        ├── CountdownTimer.tsx
        ├── VoiceRecorder.tsx
        └── SampleCaseButton.tsx
```

---

## Key Features

| Feature | Detail |
|---|---|
| **🌐 Live on GitHub Pages** | No installation — open the URL and explore immediately |
| **🔌 Offline Demo Mode** | Citizen intake runs fully in-browser with pre-built statute-cited notices |
| **🎙️ Voice + Text Intake** | Web Speech API with Hindi/English toggle; 3 sample case templates |
| **🧠 Anti-Hallucination Citations** | MCP server returns verbatim statute text; LLM fills prose only |
| **📚 Statute Coverage** | Consumer Protection Act 2019 · Payment of Wages Act 1936 · Industrial Relations Code 2020 · Model Tenancy Act 2021 |
| **🔒 PII Masking** | Phone · Aadhaar · PAN · Bank account · UPI · Email masked before LLM transit |
| **⚖️ Law Clinic Review** | JWT-authenticated PATCH endpoint; split-screen editor in UI |
| **📄 Tamper-Evident PDF** | SHA-256 hash embedded in document footer |
| **🤝 Settlement Portal** | JWT-signed URL (30-day expiry) for opposing party response |
| **🔑 RBAC** | PBKDF2-HMAC-SHA256 passwords + 8-hour JWT access tokens |
| **🤖 Zero-Cost Local LLM** | Ollama + Mistral 7B by default; OpenAI GPT-4o mini via `LLM_PROVIDER=openai` |
| **🚀 Auto-Deploy** | GitHub Actions deploys frontend to Pages on every push to `main` |

---

## Quick Start

### Open in Browser (No Install)

Just click: **[https://ayushgadigone-del.github.io/legal-rights-navigator/](https://ayushgadigone-del.github.io/legal-rights-navigator/)**

On the Citizen page, click any sample case button — the full intake → notice → review flow runs offline in your browser with no backend needed.

---

### Run Locally (One Click)

**Windows:** Double-click **`Start Frontend.bat`** in the project folder.

It will:
1. Check Node.js is installed
2. Auto-install `node_modules` on first run (takes ~30 seconds)
3. Start the Next.js dev server
4. Open **http://localhost:3000** in your browser automatically

No terminal, no commands.

---

### Backend

```bash
cd backend
pip install -r requirements.txt

# Copy and edit environment variables
copy .env.example .env

# Run the API server
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

**Minimum `.env` for local dev:**
```env
DATABASE_URL=sqlite:///./dev.db
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
SECRET_KEY=change-me-in-production
SETTLEMENT_SECRET_KEY=change-me-in-production
```

---

### MCP Statute Server

The MCP server is consumed **directly by the backend as a Python import** (no subprocess). To run it standalone for inspection:

```bash
cd mcp-statute-server
pip install -r requirements.txt
python server.py
```

The server exposes two MCP tools:

| Tool | Signature | Purpose |
|---|---|---|
| `search_applicable_laws` | `(query, dispute_type, top_k)` | BM25-style search across 34 statute provisions |
| `validate_notice_citations` | `(notice_text)` | Verifies every citation in a draft notice exists in the corpus |

---

### Full Stack Dev

With both backend and frontend running, the citizen intake connects to the real FastAPI backend for live LLM-powered notice generation:

```bash
# Terminal 1 — backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend (or just double-click Start Frontend.bat)
cd frontend && npm run dev
```

The frontend auto-detects whether the backend is reachable. If it isn't, it falls back to offline demo mode automatically.

---

## API Reference

### Public Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/intake/message` | Submit or continue a grievance intake conversation |
| `POST` | `/api/notice/generate` | Generate a statute-cited legal notice for a case |
| `POST` | `/api/auth/register` | Register a law clinic reviewer account |
| `POST` | `/api/auth/login` | Authenticate and receive a JWT access token |

### Authenticated Endpoints (Bearer JWT required)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/auth/me` | Return current reviewer profile |
| `PATCH` | `/api/clinic/verify/{case_id}` | Approve or reject a notice draft |
| `GET` | `/api/clinic/notice/{notice_id}/pdf` | Download the approved PDF |

### Example: Start an Intake

```bash
curl -X POST http://localhost:8000/api/intake/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "QuickMart sold me a broken mixer for Rs 4500. They refused to refund.",
    "dispute_category": "consumer_fraud",
    "language": "en"
  }'
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./dev.db` | SQLAlchemy URL; use Postgres in production |
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base |
| `OLLAMA_MODEL` | `mistral` | Model name served by Ollama |
| `OPENAI_API_KEY` | _(empty)_ | Required when `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `SECRET_KEY` | _(required)_ | JWT signing key for reviewer auth |
| `SETTLEMENT_SECRET_KEY` | _(required)_ | JWT signing key for settlement URLs |
| `PDF_DIR` | `./pdfs` | Directory where approved PDFs are written |
| `SETTLEMENT_BASE_URL` | `http://localhost:3000/settlement` | Base URL for settlement portal links |
| `BASE_PATH` | _(empty)_ | Set to `/legal-rights-navigator` for GitHub Pages builds |

---

## Running Tests

### Backend (108 tests)

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

**Test coverage breakdown:**

| File | Tests | Covers |
|---|---|---|
| `test_intake.py` | 12 | Fact extraction, follow-up questions, status transitions |
| `test_notice.py` | 14 | MCP → LLM → validate pipeline, citation fields |
| `test_clinic.py` | 29 | Approve/reject, PDF generation, RBAC auth |
| `test_pii_security.py` | 53 | PII masking correctness + RBAC enforcement |

### MCP Statute Server (50 tests)

```bash
cd mcp-statute-server
pip install -r requirements.txt
pytest tests/ -v
```

---

## Security & Privacy

### PII Masking Pipeline

Sensitive identifiers are **never sent to any external LLM** in plain text. The `pii_masker` service runs before every LLM call:

```
Raw facts (Aadhaar, phone, email, PAN, bank account, UPI)
    │
    ▼  mask_dict(facts, pii_store)          # per-request, in-memory only
Tokenised facts  ──►  LLM prompt  ──►  LLM draft (contains <<PHONE_1>> tokens)
    │
    ▼  unmask_pii(draft, pii_store)         # before clinic storage / PDF render
Final notice (real names restored)
```

The `pii_store` dict lives only on the call stack — it is never written to the database, logs, or the settlement JWT.

### Auth Model

- Passwords: PBKDF2-HMAC-SHA256 with random salt
- Access tokens: HS256 JWT, 8-hour expiry
- Settlement tokens: HS256 JWT, 30-day expiry, separate signing key
- Clinic routes: `Depends(get_current_reviewer)` FastAPI dependency

---

## SDG 16 Alignment

> *SDG 16.3 — Promote the rule of law at the national and international levels and ensure equal access to justice for all.*

| Metric | Target |
|---|---|
| Cost per notice | < ₹50 (LLM compute + hosting) |
| Time to draft | < 3 minutes end-to-end |
| Statute accuracy | 100% — zero hallucinated citations by design |
| Languages | English + Hindi (intake wizard) |
| Accessibility | Voice input via Web Speech API |
| Deployment | Zero-install — live on GitHub Pages |

---

## Specification

The full phased implementation specification — data schemas, API contracts, and validation checkpoints — is in [`SPEC.md`](SPEC.md).

---

## License

MIT © 2024 Legal Rights Navigator Contributors
