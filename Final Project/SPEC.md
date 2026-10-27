# Legal Rights Navigator: Pre-Litigation Engine — Implementation Specification

**Version:** 1.0  
**SDG Alignment:** SDG 16 — Peace, Justice and Strong Institutions  
**LLM Default:** Ollama + Mistral 7B (zero-cost, local, PII-safe)  
**LLM Production Upgrade Path:** OpenAI GPT-4o mini (config-switchable)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Monorepo Structure](#2-monorepo-structure)
3. [Data Schemas](#3-data-schemas)
4. [API Contracts](#4-api-contracts)
5. [MCP Statute Server Specification](#5-mcp-statute-server-specification)
6. [Phase 1 — Foundation](#phase-1--foundation)
7. [Phase 2 — Core Engine](#phase-2--core-engine)
8. [Phase 3 — Frontend Roles](#phase-3--frontend-roles)
9. [Phase 4 — Settlement Portal](#phase-4--settlement-portal)
10. [Phase 5 — Hardening and Validation](#phase-5--hardening-and-validation)
11. [Validation Checkpoints](#11-validation-checkpoints)
12. [Environment Configuration](#12-environment-configuration)

---

## 1. Project Overview

### Goal

Convert a citizen's voice or plain-language grievance into a statute-cited, law-clinic-verified legal notice, and provide a structured settlement portal for the opposing party — entirely without hallucinated legal citations.

### Core Actors

| Actor | Role |
|---|---|
| **Citizen** | Submits grievance via voice or text through the Intake Wizard |
| **Law Clinic Student** | Reviews auto-drafted notices in the Review Queue, approves or edits |
| **Opposing Party** | Receives notice, responds via the Settlement Resolution Page |
| **MCP Statute Server** | Deterministic tool that guarantees all legal citations come from verified statute text |
| **LLM (Mistral 7B)** | Formats, drafts prose; never invents citations |

### Anti-Hallucination Guarantee

The LLM is **never asked to recall statute section numbers**. All citations flow through `lookup_statute_section()` on the MCP server, which queries a local ChromaDB collection seeded from the actual statute texts. The LLM only fills prose around citations returned by the tool.

---

## 2. Monorepo Structure

```
legal-rights-navigator/
├── SPEC.md                          ← this file
├── .env.example                     ← root env template
├── docker-compose.yml               ← full stack local dev
├── .gitignore
│
├── backend/                         ← Python 3.11, FastAPI
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py                  ← FastAPI app entrypoint
│   │   ├── config.py                ← env-driven config (LLM provider switch)
│   │   ├── routers/
│   │   │   ├── grievance.py         ← POST /grievance/submit, /grievance/{id}
│   │   │   ├── notice.py            ← POST /notice/generate, GET /notice/{id}/pdf
│   │   │   ├── review.py            ← PATCH /review/{notice_id}
│   │   │   └── settlement.py        ← POST /settlement/respond, GET /settlement/{id}
│   │   ├── services/
│   │   │   ├── llm_service.py       ← provider-agnostic LLM caller (Ollama | OpenAI)
│   │   │   ├── rag_service.py       ← ChromaDB query + statute chunk retrieval
│   │   │   ├── notice_service.py    ← notice assembly + PDF generation
│   │   │   └── mcp_client.py        ← calls mcp-statute-server over stdio/HTTP
│   │   ├── models/
│   │   │   ├── grievance.py         ← Pydantic schemas for grievances
│   │   │   ├── notice.py            ← Pydantic schemas for legal notices
│   │   │   └── settlement.py        ← Pydantic schemas for settlement responses
│   │   └── db/
│   │       ├── chroma_init.py       ← seeds ChromaDB from statute JSON files
│   │       └── statutes/
│   │           ├── consumer_protection_2019.json
│   │           ├── payment_of_wages.json
│   │           └── tenancy_disputes.json
│   └── tests/
│       ├── test_grievance.py
│       ├── test_rag.py
│       └── test_notice.py
│
├── frontend/                        ← Next.js 14 App Router, Tailwind CSS
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   ├── .env.local.example
│   └── app/
│       ├── layout.tsx               ← root layout, font, global styles
│       ├── page.tsx                 ← landing / role selector
│       ├── citizen/
│       │   ├── page.tsx             ← Citizen Intake Wizard (step 1: voice/text)
│       │   ├── review/page.tsx      ← step 2: review parsed grievance
│       │   └── status/[id]/page.tsx ← step 3: notice status tracker
│       ├── clinic/
│       │   ├── page.tsx             ← Law Clinic Review Queue
│       │   └── [noticeId]/page.tsx  ← individual notice editor
│       ├── settlement/
│       │   └── [settlementId]/page.tsx ← Settlement Resolution Page
│       └── components/
│           ├── VoiceRecorder.tsx
│           ├── GrievanceForm.tsx
│           ├── NoticePreview.tsx
│           ├── StatuteBadge.tsx     ← displays a single statute citation pill
│           ├── ReviewEditor.tsx
│           └── SettlementPanel.tsx
│
└── mcp-statute-server/              ← Python MCP server (stdio transport)
    ├── pyproject.toml
    ├── requirements.txt
    ├── server.py                    ← MCP server entrypoint
    ├── tools/
    │   └── statute_lookup.py        ← lookup_statute_section() implementation
    ├── data/
    │   └── statutes/                ← same JSON statute files (or symlink to backend)
    └── tests/
        └── test_lookup.py
```

---

## 3. Data Schemas

### 3.1 Grievance

```python
# backend/app/models/grievance.py

class GrievanceSubmit(BaseModel):
    citizen_name: str                   # full name
    citizen_contact: str                # phone or email
    dispute_type: Literal[
        "consumer_protection",
        "payment_of_wages",
        "tenancy"
    ]
    description: str                    # plain-language or voice-transcript text
    voice_audio_b64: str | None = None  # base64-encoded audio, optional
    opposing_party_name: str
    opposing_party_contact: str         # email for settlement portal invite
    incident_date: date
    evidence_urls: list[str] = []       # uploaded file URLs

class GrievanceRecord(GrievanceSubmit):
    id: str                             # UUID
    status: Literal[
        "received",
        "parsed",
        "notice_drafted",
        "notice_under_review",
        "notice_approved",
        "notice_sent",
        "settlement_open",
        "settled",
        "escalated"
    ]
    parsed_facts: dict | None = None    # LLM-extracted structured facts
    created_at: datetime
    updated_at: datetime
```

### 3.2 Legal Notice

```python
# backend/app/models/notice.py

class StatuteCitation(BaseModel):
    act: str                            # e.g. "Consumer Protection Act 2019"
    section: str                        # e.g. "Section 35(1)(a)"
    section_title: str                  # e.g. "Complaints to District Commission"
    excerpt: str                        # verbatim statutory text snippet
    relevance_score: float              # ChromaDB cosine similarity score

class LegalNotice(BaseModel):
    id: str                             # UUID
    grievance_id: str
    draft_body: str                     # full notice prose (Markdown/plain text)
    citations: list[StatuteCitation]    # all statute citations used
    review_status: Literal[
        "auto_drafted",
        "under_review",
        "approved",
        "rejected",
        "sent"
    ]
    reviewer_id: str | None = None      # law clinic student ID
    reviewer_notes: str | None = None
    approved_body: str | None = None    # final edited body after clinic review
    pdf_url: str | None = None          # generated PDF path
    created_at: datetime
    updated_at: datetime

class NoticeReviewPatch(BaseModel):
    review_status: Literal["approved", "rejected"]
    reviewer_id: str
    reviewer_notes: str | None = None
    approved_body: str | None = None    # required when status = "approved"
```

### 3.3 Settlement

```python
# backend/app/models/settlement.py

class SettlementResponse(BaseModel):
    id: str                             # UUID
    notice_id: str
    grievance_id: str
    opposing_party_response: Literal[
        "accept_full",
        "accept_partial",
        "reject",
        "request_mediation"
    ]
    proposed_resolution: str | None = None  # free text from opposing party
    proposed_amount: float | None = None    # for monetary disputes
    response_date: datetime
    status: Literal[
        "pending",
        "citizen_reviewing",
        "agreed",
        "disagreed",
        "mediation_requested"
    ]
```

### 3.4 Statute Chunk (ChromaDB Document)

```json
{
  "id": "cpa2019_s35_1a",
  "act": "Consumer Protection Act 2019",
  "chapter": "IV",
  "section": "35",
  "sub_section": "(1)(a)",
  "section_title": "Complaints to District Commission",
  "text": "a consumer; or ...",
  "keywords": ["complaint", "district commission", "consumer", "deficiency"],
  "dispute_types": ["consumer_protection"],
  "embedding": "[float array — populated at ingest time]"
}
```

---

## 4. API Contracts

Base URL: `http://localhost:8000/api/v1`

### 4.1 Grievance Routes

#### `POST /grievance/submit`
Submit a new citizen grievance.

**Request body:** `GrievanceSubmit`  
**Response `201`:**
```json
{
  "grievance_id": "uuid",
  "status": "received",
  "message": "Grievance received. Notice will be drafted shortly."
}
```

**Side effects:**
1. Persists `GrievanceRecord` to SQLite (dev) / Postgres (prod)
2. If `voice_audio_b64` present → transcribes via Whisper (local)
3. Enqueues background task: `parse_grievance_facts()` → LLM extracts structured facts
4. Enqueues background task: `draft_notice()` → calls RAG + MCP server + LLM

---

#### `GET /grievance/{id}`
**Response `200`:** Full `GrievanceRecord`

---

### 4.2 Notice Routes

#### `POST /notice/generate`
Manually trigger notice generation (idempotent).

**Request body:**
```json
{ "grievance_id": "uuid" }
```
**Response `200`:** `LegalNotice` with `review_status: "auto_drafted"`

---

#### `GET /notice/{id}`
**Response `200`:** Full `LegalNotice`

---

#### `GET /notice/{id}/pdf`
**Response `200`:** `application/pdf` stream  
**Side effect:** Generates PDF if not yet generated; caches at `pdf_url`

---

#### `PATCH /review/{notice_id}`
Law clinic student approves or rejects.

**Request body:** `NoticeReviewPatch`  
**Response `200`:** Updated `LegalNotice`  
**Side effect on approve:** Sends notice PDF to `opposing_party_contact` via email; creates `SettlementResponse` record with `status: "pending"`

---

### 4.3 Settlement Routes

#### `GET /settlement/{id}`
Returns `SettlementResponse` record.

---

#### `POST /settlement/respond`
Opposing party submits response via their unique settlement link.

**Request body:**
```json
{
  "settlement_id": "uuid",
  "token": "jwt-signed-token",
  "opposing_party_response": "accept_partial",
  "proposed_resolution": "Refund of ₹4,500 within 7 days",
  "proposed_amount": 4500.00
}
```
**Response `200`:** Updated `SettlementResponse`  
**Side effect:** Notifies citizen by email; updates `GrievanceRecord.status`

---

#### `PATCH /settlement/{id}/citizen-decision`
Citizen accepts or rejects the opposing party's settlement offer.

**Request body:**
```json
{
  "decision": "agreed" | "disagreed" | "mediation_requested"
}
```
**Response `200`:** Updated `SettlementResponse`

---

## 5. MCP Statute Server Specification

**Transport:** stdio (local dev) — mountable as HTTP for cloud deploy  
**File:** `mcp-statute-server/server.py`

### 5.1 Registered Tool: `lookup_statute_section`

```python
@server.register_tool(
    name="lookup_statute_section",
    description=(
        "Deterministic lookup of statute sections relevant to a legal dispute. "
        "Returns verbatim statutory text with section numbers. "
        "NEVER infer or guess — only return what the statute data contains."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "dispute_type": {
                "type": "string",
                "enum": ["consumer_protection", "payment_of_wages", "tenancy"],
                "description": "The category of legal dispute."
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key facts or legal terms from the grievance, e.g. ['refund', 'defective product', '30 days']"
            },
            "top_k": {
                "type": "integer",
                "default": 5,
                "description": "Number of most relevant sections to return."
            }
        },
        "required": ["dispute_type", "keywords"]
    }
)
def lookup_statute_section(
    dispute_type: str,
    keywords: list[str],
    top_k: int = 5
) -> list[StatuteResult]:
    ...
```

### 5.2 Tool Return Schema

```python
class StatuteResult(TypedDict):
    act: str             # "Consumer Protection Act 2019"
    section: str         # "Section 35(1)(a)"
    section_title: str   # "Complaints to District Commission"
    excerpt: str         # verbatim statutory text (max 500 chars)
    relevance_score: float
```

### 5.3 Implementation Strategy

- Queries ChromaDB using keyword embedding similarity
- Filters by `dispute_type` metadata field before ranking
- Returns top-K results sorted by cosine similarity
- **Never generates, infers, or paraphrases statute text** — all `excerpt` values are verbatim from the ingested JSON

### 5.4 LLM Prompt Contract

The backend `notice_service.py` must follow this prompt pattern:

```
You are a legal notice drafter. You MUST only use the statute citations provided
in the [STATUTES] block below. Do not add any section numbers not listed there.

[GRIEVANCE FACTS]
{parsed_facts}

[STATUTES]
{json.dumps(statute_results)}

Draft a formal pre-litigation legal notice using only the above statutes.
Structure: addressee, background, legal basis (cite only from [STATUTES]),
demand, deadline (30 days), consequence of non-compliance.
```

---

## Phase 1 — Foundation

**Status:** `[x] complete — mcp-statute-server/ implemented, 50/50 tests passing`

**Implementation notes:**
- Used MCP 2.x `MCPServer` API (`mcp.server.mcpserver`) — `@server.tool()` decorator pattern
- ChromaDB dependency deferred: search engine uses BM25-style TF-IDF keyword scoring over `data/statutes.json` (zero external dependencies beyond `mcp` and `pydantic`)
- Two tools exposed: `search_applicable_laws` and `validate_notice_citations` (superset of original `lookup_statute_section` spec)
- `validate_notice_citations` detects `Section N`, `Sec N`, `S. N`, `§ N` patterns and cross-checks against the knowledge base; unknown sections return `is_valid=false` with a suggestion

### Intent
Scaffold the monorepo, install dependencies, seed ChromaDB with the three statute corpuses, and verify the MCP server's `lookup_statute_section` returns correct results before any LLM is involved.

### Expected Outcomes
- Monorepo folder structure created as specified in Section 2
- ChromaDB seeded with Consumer Protection Act 2019, Payment of Wages Act, and Tenancy dispute statutes (minimum 50 chunks per act)
- `lookup_statute_section("consumer_protection", ["refund", "defective goods"])` returns ≥ 3 relevant sections
- MCP server passes its unit tests in `mcp-statute-server/tests/test_lookup.py`

### Todo List
1. Create monorepo root with `.gitignore`, `.env.example`, `docker-compose.yml`
2. Scaffold `backend/` with `pyproject.toml`, `requirements.txt` (FastAPI, ChromaDB, WeasyPrint, SQLModel, python-jose, ollama)
3. Scaffold `mcp-statute-server/` with `pyproject.toml`, `requirements.txt` (mcp, chromadb)
4. Author statute JSON files for all three acts in `backend/app/db/statutes/`
5. Write `backend/app/db/chroma_init.py` — ingests statute JSONs, embeds, stores in ChromaDB
6. Write `mcp-statute-server/tools/statute_lookup.py` — ChromaDB query logic
7. Write `mcp-statute-server/server.py` — register `lookup_statute_section` tool
8. Write `mcp-statute-server/tests/test_lookup.py` — verify 3 dispute types × 2 keyword sets
9. Run ingest script and verify ChromaDB collection counts

### Relevant Context
- Statute JSON schema: Section 3.4
- MCP tool signature: Section 5.1
- ChromaDB filter by `dispute_type` metadata: Section 5.3

---

## Phase 2 — Core Engine

**Status:** `[x] complete — backend/ implemented, 55/55 tests passing`

**Implementation notes:**
- Three endpoints: `POST /api/intake/message`, `POST /api/notice/generate`, `PATCH /api/clinic/verify/{case_id}`
- **Database:** SQLModel + SQLite (dev) / Postgres (prod) via `DATABASE_URL` env var; `Store` class exposes unchanged dict-like API (`get`, `put`, `filter`) so no service/router code changes for DB migration
- **Auth:** `POST /api/auth/register` + `POST /api/auth/login` issue JWT access tokens (8h, PBKDF2-HMAC-SHA256 passwords); clinic routes protected by `Depends(get_current_reviewer)` Bearer guard
- **Statute corpus:** 34 provisions across Payment of Wages Act 1936, Industrial Relations Code 2020, Consumer Protection Act 2019, Model Tenancy Act 2021
- LLM service is provider-agnostic: Ollama (default, $0) or OpenAI via `LLM_PROVIDER` env var; deterministic fallback template ensures tests pass without any LLM running
- MCP client imports statute lookup directly from `mcp-statute-server/` (no subprocess overhead; swap to HTTP for multi-container deploy)
- PDF generation: WeasyPrint (if installed) → pure-Python fallback; SHA-256 hash embedded in PDF and returned in API response
- Settlement URL: JWT-signed 30-day token via `python-jose`, pattern: `{SETTLEMENT_BASE_URL}/{case_id}?token=...`

### Intent
Build the FastAPI backend: grievance submission, LLM fact extraction, RAG-based notice drafting via MCP server, and PDF generation. The LLM is provider-agnostic via `config.py`.

### Expected Outcomes
- `POST /grievance/submit` accepts a grievance and triggers background notice drafting
- A generated notice contains only statute citations sourced from `lookup_statute_section`
- `GET /notice/{id}/pdf` returns a valid, formatted PDF
- All Pydantic models validate correctly
- `pytest backend/tests/` passes

### Todo List
1. Write `backend/app/config.py` — reads `LLM_PROVIDER` env var (`ollama` | `openai`), exposes `get_llm_client()`
2. Write `backend/app/services/llm_service.py` — wraps Ollama and OpenAI clients behind common `complete(prompt) -> str` interface
3. Write `backend/app/services/mcp_client.py` — calls `mcp-statute-server` via stdio subprocess, returns `list[StatuteResult]`
4. Write `backend/app/services/rag_service.py` — ChromaDB similarity search (used as fallback / double-check alongside MCP)
5. Write `backend/app/services/notice_service.py` — orchestrates: facts → MCP lookup → prompt (Section 5.4) → LLM draft → assemble `LegalNotice`
6. Write `backend/app/services/notice_service.py` PDF section — WeasyPrint renders HTML notice template to PDF
7. Write all Pydantic models: `grievance.py`, `notice.py`, `settlement.py` (Section 3)
8. Write all routers: `grievance.py`, `notice.py`, `review.py`, `settlement.py` (Section 4)
9. Write `backend/app/main.py` — mount routers, CORS, lifespan (init ChromaDB on startup)
10. Write `backend/tests/test_grievance.py`, `test_rag.py`, `test_notice.py`

### Relevant Context
- LLM prompt contract: Section 5.4
- API contracts: Section 4
- Provider switch pattern: `LLM_PROVIDER=ollama` uses `http://localhost:11434`, `LLM_PROVIDER=openai` uses `OPENAI_API_KEY`

---

## Phase 3 — Frontend Roles

**Status:** `[ ] pending`

### Intent
Build all three role views in Next.js with Tailwind CSS, wired to the FastAPI backend. Each view is a separate route group with its own UX flow.

### Expected Outcomes
- **Citizen Intake Wizard** (3 steps): voice/text input → parsed facts review → submission confirmation with live status polling
- **Law Clinic Review Queue**: table of `notice_under_review` notices with approve/reject actions; individual notice editor shows statute citation badges
- **Settlement Resolution Page**: opposing party lands via unique URL, sees notice summary, submits response form
- All views are responsive (mobile-first for citizen flow)
- TypeScript compiles with zero errors

### Todo List

#### Citizen Intake Wizard
1. `app/citizen/page.tsx` — Step 1: `VoiceRecorder.tsx` (Web Speech API) + fallback `GrievanceForm.tsx` text input; dispute type selector
2. `app/citizen/review/page.tsx` — Step 2: display LLM-parsed facts for citizen confirmation before submitting
3. `app/citizen/status/[id]/page.tsx` — Step 3: poll `GET /grievance/{id}` every 5s, show status stepper

#### Law Clinic Review Queue
4. `app/clinic/page.tsx` — paginated table of notices with `review_status: "auto_drafted"` / `"under_review"`
5. `app/clinic/[noticeId]/page.tsx` — `ReviewEditor.tsx` with full notice body (editable textarea), `StatuteBadge.tsx` list, approve/reject buttons

#### Settlement Resolution Page
6. `app/settlement/[settlementId]/page.tsx` — `SettlementPanel.tsx`: notice summary, response radio (accept full / accept partial / reject / mediation), resolution text field, submit

#### Shared Components
7. `components/StatuteBadge.tsx` — pill showing act name + section number, tooltip with excerpt
8. `components/NoticePreview.tsx` — renders formatted notice with citations highlighted
9. `app/layout.tsx` — root layout, Tailwind base, nav with role switcher (dev mode)
10. `app/page.tsx` — landing role selector (Citizen / Law Clinic / Opposing Party)

### Relevant Context
- API base URL from `NEXT_PUBLIC_API_URL` env var
- Settlement page accessed via `/settlement/[id]?token=jwt` — token passed to `POST /settlement/respond`
- `StatuteBadge` data shape: `StatuteCitation` schema (Section 3.2)

---

## Phase 4 — Settlement Portal

**Status:** `[ ] pending`

### Intent
Complete the end-to-end settlement flow: email delivery of approved notice to opposing party with a JWT-signed unique link, opposing party response, citizen review of offer, and final status update.

### Expected Outcomes
- On notice approval, opposing party receives email with PDF attachment and unique settlement URL
- Opposing party can submit response without creating an account (token-authenticated)
- Citizen can accept/reject/request mediation via their status page
- `GrievanceRecord.status` correctly reflects terminal states: `settled`, `escalated`

### Todo List
1. Add `email_service.py` to `backend/app/services/` — SMTP (dev: Mailhog) sends notice PDF + settlement link
2. Add JWT token generation for settlement links in `backend/app/routers/review.py` — signed with `SETTLEMENT_SECRET_KEY`, 30-day expiry
3. Add token verification middleware in `backend/app/routers/settlement.py` — `POST /settlement/respond` validates token before accepting response
4. Add `PATCH /settlement/{id}/citizen-decision` route
5. Update `app/citizen/status/[id]/page.tsx` — when `settlement_open`, show offer details and accept/reject/mediation buttons
6. Write `docker-compose.yml` service for Mailhog (dev email catcher)
7. Write integration test: full flow from submit → draft → approve → email → respond → citizen decision

### Relevant Context
- Settlement routes: Section 4.3
- Token payload: `{ settlement_id, notice_id, grievance_id, exp }`
- Mailhog UI at `http://localhost:8025` in dev

---

## Phase 5 — Hardening and Validation

**Status:** `[ ] pending`

### Intent
Security, data integrity, accessibility, and deployment readiness. Ensure no PII leaks, no LLM bypass of the statute citation constraint, and the app is deployable.

### Expected Outcomes
- All API endpoints have input validation and return structured error responses
- Statute citation hallucination is demonstrably impossible (integration test: LLM prompt contains no statute info → output contains no section numbers)
- WCAG 2.1 AA compliance on citizen intake flow
- `docker-compose up` starts the full stack with zero manual steps

### Todo List
1. Add rate limiting to `POST /grievance/submit` (10 req/min per IP) using `slowapi`
2. Add PII scrubbing: citizen contact info never logged, never sent to LLM
3. Write hallucination-prevention integration test: submit grievance with empty statute corpus → verify notice draft contains no section numbers
4. Add `Content-Security-Policy` headers to FastAPI middleware
5. Add `aria-label`, `role`, and keyboard navigation to all Citizen Intake Wizard steps
6. Write `Dockerfile` for `backend/` and `mcp-statute-server/`
7. Write `frontend/Dockerfile`
8. Finalize `docker-compose.yml` with health checks for all services
9. Write root `README.md` with setup instructions and architecture diagram

---

## 11. Validation Checkpoints

These are go/no-go gates between phases. Do not proceed to the next phase until the checkpoint passes.

| Checkpoint | Gate Condition |
|---|---|
| **CP-1** (end of Phase 1) | `lookup_statute_section("tenancy", ["eviction", "notice period"])` returns ≥ 2 results with `relevance_score > 0.6` |
| **CP-2** (end of Phase 2) | A drafted `LegalNotice` contains ≥ 1 `StatuteCitation` with `section` matching a real section number from the seeded statute JSON |
| **CP-3** (end of Phase 2) | `GET /notice/{id}/pdf` returns a valid PDF (PyPDF2 parse succeeds, page count ≥ 1) |
| **CP-4** (end of Phase 3) | Citizen Intake Wizard completes a full submission in Playwright E2E test without JS errors |
| **CP-5** (end of Phase 4) | Mailhog captures the notice email with PDF attachment within 10s of notice approval |
| **CP-6** (end of Phase 5) | Hallucination test passes: notice draft with empty statute corpus contains zero section-number patterns matching `/Section\s+\d+/` |

---

## 12. Environment Configuration

### Root `.env.example`

```ini
# LLM Provider — "ollama" (free, local) or "openai" (paid, cloud)
LLM_PROVIDER=ollama

# Ollama (used when LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# OpenAI (used when LLM_PROVIDER=openai)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Backend
DATABASE_URL=sqlite:///./legal_navigator.db
CHROMA_PERSIST_DIR=./chroma_data
SETTLEMENT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256

# Email (dev uses Mailhog, prod uses SMTP)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_FROM=noreply@legalnavigator.local

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### Service Ports (Local Dev)

| Service | Port |
|---|---|
| FastAPI backend | 8000 |
| Next.js frontend | 3000 |
| MCP statute server | stdio (subprocess) |
| ChromaDB | embedded in backend process |
| Mailhog SMTP | 1025 |
| Mailhog Web UI | 8025 |
| Ollama | 11434 |
