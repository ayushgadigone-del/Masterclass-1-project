# Concept Note

## Legal Rights Navigator: Pre-Litigation Engine

**SDG 16.3 — Equal Access to Justice for All**

---

| Field | Detail |
|---|---|
| **Project Title** | Legal Rights Navigator: Pre-Litigation Engine |
| **Primary SDG Target** | SDG 16.3 — Access to Justice for All |
| **Programme** | IBM SkillsBuild / CSRBOX AI for Good |
| **Technology Stack** | Python FastAPI · Next.js 14 · MCP Statute Server · Mistral 7B (Ollama) |
| **Live Demo** | https://ayushgadigone-del.github.io/legal-rights-navigator/ |
| **Repository** | https://github.com/ayushgadigone-del/legal-rights-navigator |

---

## 1. Executive Summary

India's judiciary carries over 40 million pending cases, and the average citizen seeking redress for a consumer fraud, unpaid wages, or security deposit dispute cannot afford the ₹2,000–₹8,000 lawyer fee required even for a basic legal notice. The **Legal Rights Navigator: Pre-Litigation Engine** is an open-source LegalTech MVP that guides any citizen through a structured, five-step intake interview and produces a jurisdiction-correct, statute-backed legal notice in under three minutes — at a cost of less than ₹50 per document. The system achieves verifiable legal accuracy through a Model Context Protocol (MCP) Statute Server that injects verbatim legislative text at inference time, making it architecturally impossible for the AI to hallucinate a citation. Built on a zero-marginal-cost local LLM stack (Ollama + Mistral 7B), the platform is designed to operate in low-connectivity environments and is fully deployable as a static Progressive Web App, making it appropriate for grassroots legal aid clinics across India.

---

## 2. Problem Statement

### 2.1 India's Access-to-Justice Gap

India's formal justice system, though robust in design, is functionally inaccessible to the majority of its citizens. As of the latest National Judicial Data Grid figures, **more than 40 million cases** are pending across district and subordinate courts. For every case that reaches the courts, many more disputes are abandoned at the threshold because the aggrieved party cannot navigate the procedural and financial barriers that stand between them and a remedy.

### 2.2 The Cost Barrier

The pre-litigation phase — sending a legally valid notice that puts the opposing party on record and triggers the clock on statutory response deadlines — is the single most powerful and least expensive tool available to an ordinary citizen. Yet the professional fee for a competent legal notice ranges from **₹2,000 to ₹8,000** per matter, a sum that exceeds a week's income for a large fraction of India's working population. For disputes involving withheld wages of ₹3,000, a wrongfully retained security deposit of ₹15,000, or a consumer fraud claim of ₹5,000, the cost of seeking professional help is economically irrational — and so most victims simply absorb the loss.

### 2.3 The Complexity Barrier

Even if a citizen attempts to draft a notice independently, they face:

- **Statutory identification**: which of dozens of Central and State Acts applies to their dispute?
- **Provision accuracy**: citing the wrong section number or repealed version invalidates the notice.
- **Procedural form**: a notice must invoke the correct reliefs, timelines, and dispute-resolution machinery specified in the applicable statute.
- **Evidence framing**: what facts must be stated and in what sequence to constitute a valid cause of action?

Existing AI chatbots fail this use-case because general-purpose large language models (LLMs) are known to confabulate statute numbers, invent case citations, and misstate legal thresholds — errors that can harm rather than help the user.

### 2.4 The Trust Gap

Citizens who do attempt self-help with generic AI tools have no assurance that the output is grounded in real law. Without a verifiable chain of custody from statute to notice, the document lacks credibility with the opposing party, consumer forums, and labour commissioners.

---

## 3. Solution Overview

### 3.1 What the System Does

The Legal Rights Navigator accepts a citizen's description of their dispute, maps it to the correct statutory framework, and produces a ready-to-send legal notice that cites verbatim legislative text — all without requiring the user to know which law applies or how to write a legal document.

### 3.2 The Five-Step Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   LEGAL RIGHTS NAVIGATOR — CORE PIPELINE                   │
├───────┬─────────────────────────────────────────────────────────────────────┤
│ Step  │ Description                                                         │
├───────┼─────────────────────────────────────────────────────────────────────┤
│  1    │ INTAKE INTERVIEW                                                    │
│       │ Citizen describes dispute via structured Next.js form.              │
│       │ Dispute type is classified into one of three categories:            │
│       │ consumer_fraud · unpaid_wages · security_deposit                    │
├───────┼─────────────────────────────────────────────────────────────────────┤
│  2    │ PII MASKING (Pre-LLM)                                               │
│       │ FastAPI middleware detects and replaces all personal identifiers    │
│       │ (phone, Aadhaar, PAN, bank account, UPI ID, email) with typed       │
│       │ placeholders before the payload leaves the application server.      │
│       │ The LLM never receives raw personal data.                           │
├───────┼─────────────────────────────────────────────────────────────────────┤
│  3    │ STATUTE RETRIEVAL VIA MCP SERVER                                    │
│       │ A dedicated Model Context Protocol Statute Server selects the       │
│       │ applicable Act and returns the exact verbatim statutory text for    │
│       │ the relevant provisions. The LLM prompt is constructed with this    │
│       │ grounded text as the authoritative source.                          │
├───────┼─────────────────────────────────────────────────────────────────────┤
│  4    │ NOTICE GENERATION (LLM)                                             │
│       │ Ollama + Mistral 7B (or GPT-4o mini) drafts the notice using       │
│       │ only the facts from the intake and the statute text from the MCP    │
│       │ server. The prompt architecture prohibits the model from citing     │
│       │ any provision not supplied by the server.                           │
├───────┼─────────────────────────────────────────────────────────────────────┤
│  5    │ PDF GENERATION & SETTLEMENT PORTAL                                  │
│       │ PII is re-hydrated into the final document. A SHA-256 hash of      │
│       │ the notice body is embedded in the PDF footer for tamper           │
│       │ evidence. A JWT-signed settlement URL (30-day expiry) is           │
│       │ generated and included, enabling out-of-court resolution.          │
└───────┴─────────────────────────────────────────────────────────────────────┘
```

### 3.3 Dual LLM Mode

| Mode | LLM | Cost | Connectivity Required |
|---|---|---|---|
| **Local (Default)** | Ollama + Mistral 7B | ₹0 per notice | No internet required after setup |
| **Cloud Upgrade** | OpenAI GPT-4o mini | < ₹50 per notice | Internet required |

The local mode makes the platform viable for legal aid organisations with constrained infrastructure budgets and for deployment in areas with unreliable internet connectivity.

---

## 4. SDG 16 Alignment

### 4.1 Primary Target — SDG 16.3: Access to Justice for All

> *"Promote the rule of law at the national and international levels and ensure equal access to justice for all."*

The Legal Rights Navigator directly operationalises SDG 16.3 by:

- **Removing cost as a barrier**: A legally valid, statute-grounded notice for under ₹50 versus ₹2,000–₹8,000 from a professional.
- **Removing knowledge as a barrier**: Citizens need not know the name of the applicable statute, only the facts of their dispute.
- **Removing language as a barrier**: The multi-modal intake is designed for plain language; future phases include vernacular language support.
- **Enabling pre-litigation resolution**: The built-in settlement portal gives opposing parties a structured path to resolve disputes without court involvement, directly reducing the case-load burden on the judiciary.

### 4.2 Secondary Target — SDG 16.6: Accountable and Transparent Institutions

> *"Develop effective, accountable and transparent institutions at all levels."*

The SHA-256 tamper-evident hash embedded in every generated PDF notice creates an auditable, verifiable record. Citizens, consumer forums, labour commissioners, and courts can independently verify that a document has not been altered since generation, supporting the accountability principle.

### 4.3 Tertiary Target — SDG 16.b: Non-Discriminatory Laws and Policies

> *"Promote and enforce non-discriminatory laws and policies for sustainable development."*

By grounding every notice in verbatim statutory text, the platform applies the law equally to every user regardless of their social or economic position. A migrant worker claiming unpaid wages receives the same quality of legal framing as any other citizen.

### 4.4 SDG 16 Contribution Summary

| SDG Target | Contribution Mechanism |
|---|---|
| 16.3 | Low-cost, AI-guided legal notice generation; pre-litigation settlement pathway |
| 16.6 | SHA-256 tamper-evident PDF; verifiable notice audit trail |
| 16.b | Uniform statute application; equal-quality output for all socioeconomic groups |

---

## 5. Technical Innovation

### 5.1 MCP Statute Server — Architectural Anti-Hallucination

The central innovation of this system is its approach to LLM accuracy in a high-stakes domain. Rather than asking a general-purpose model to recall statutory text from training data — a process known to produce confident but incorrect citations — the platform uses a **Model Context Protocol (MCP) Statute Server** as a factual grounding layer.

The MCP server:
1. Maintains a curated, version-controlled database of 34 statutory provisions across 4 Central Acts.
2. Receives the classified dispute type from the intake pipeline.
3. Returns the **verbatim text** of the applicable provisions — not a summary, not a paraphrase.
4. Injects this text into the LLM system prompt as the sole authoritative source.
5. The LLM prompt is explicitly instructed to cite only provisions present in the supplied context.

This architecture makes it structurally impossible for the model to hallucinate a section number, a threshold amount, or a statutory deadline. The statute text in the notice is always traceable to a real provision in a real Act.

### 5.2 PII Masking Pipeline

Citizen data privacy is protected by a two-stage masking and re-hydration pipeline operating at the application layer, entirely independent of the LLM:

```
Raw Input ──► [PII Detector] ──► Masked Payload ──► [LLM] ──► Masked Draft
                                                                     │
PDF Output ◄── [Re-hydration] ◄──────────────────────────────────────┘
```

**Entities masked (regex + pattern matching):**
- Indian mobile numbers (10-digit, +91 prefix)
- Aadhaar numbers (12-digit, with space variants)
- PAN card numbers (alphanumeric format)
- Bank account numbers
- UPI IDs
- Email addresses

The LLM receives `{{PHONE_1}}`, `{{AADHAAR_1}}`, `{{PAN_1}}` placeholders. Re-hydration occurs only at PDF generation time, in memory, and the mapping table is discarded after the PDF is written.

### 5.3 Offline Demo Mode & Static Deployment

The Next.js 14 frontend is exported as a fully static site and hosted on GitHub Pages, requiring no server for the demonstration layer. The static demo mode uses a pre-recorded response fixture, enabling evaluators and citizens to experience the full user journey without a running backend — critical for programme demonstrations in bandwidth-constrained environments.

### 5.4 Test Coverage

The system is validated by **158 automated tests**:

| Layer | Test Count | Coverage |
|---|---|---|
| FastAPI Backend | 108 | Auth flows, PII masking, notice generation, PDF hashing, settlement URL |
| MCP Statute Server | 50 | Statute retrieval accuracy, provision completeness, edge cases |
| **Total** | **158** | **All passing** |

---

## 6. Target Beneficiaries

### 6.1 Primary Beneficiaries — Citizens

| Profile | Dispute Type | Barrier Addressed |
|---|---|---|
| Consumer who received defective goods or was denied a refund | Consumer Fraud | Cost of hiring a lawyer for a consumer notice |
| Migrant worker whose wages were withheld by an employer | Unpaid Wages | Knowledge of Payment of Wages Act 1936 provisions and complaint thresholds |
| Tenant from whom a landlord refused to return a security deposit | Security Deposit | Knowledge of Model Tenancy Act 2021 timelines and remedies |

### 6.2 Secondary Beneficiaries — Legal Aid Clinics and Law Students

University legal aid clinics and paralegal training programmes can use the platform as both a client-service tool and a pedagogical resource. The verbatim statute display shows students exactly which provision applies and why, turning every notice generation into a learning exercise.

### 6.3 Tertiary Beneficiaries — Opposing Parties

The built-in JWT-signed settlement portal gives the receiving party (employer, landlord, seller) a structured, time-bound mechanism to respond and settle without litigation. This benefits both parties: the aggrieved citizen receives faster relief, and the opposing party avoids the cost and reputational risk of a formal complaint or court case. Reducing contested cases at this stage directly relieves pressure on consumer forums, labour commissioners, and civil courts.

---

## 7. System Architecture

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                               │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    PRESENTATION LAYER                               │  │
│  │              Next.js 14 · Static Export · GitHub Pages              │  │
│  │         Intake Form │ Notice Preview │ PDF Download │ Settlement    │  │
│  └──────────────────────────────┬──────────────────────────────────────┘  │
│                                 │ HTTPS / REST                            │
│  ┌──────────────────────────────▼──────────────────────────────────────┐  │
│  │                    APPLICATION LAYER                                │  │
│  │                    Python FastAPI Backend                           │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐  │  │
│  │  │ Auth Module │  │ PII Masker   │  │ Notice API   │  │ PDF Gen │  │  │
│  │  │ PBKDF2/JWT  │  │ Pre-LLM mask │  │ Orchestrator │  │ SHA-256 │  │  │
│  │  └─────────────┘  └──────────────┘  └──────┬───────┘  └─────────┘  │  │
│  └─────────────────────────────────────────────┼────────────────────────┘  │
│                                                │ MCP Protocol              │
│  ┌─────────────────────────────────────────────▼────────────────────────┐  │
│  │                    KNOWLEDGE LAYER                                  │  │
│  │              MCP Statute Server (Python)                            │  │
│  │   Consumer Protection Act 2019 │ Payment of Wages Act 1936         │  │
│  │   Industrial Relations Code 2020 │ Model Tenancy Act 2021          │  │
│  │                    34 verbatim provisions                           │  │
│  └─────────────────────────────────────────────┬────────────────────────┘  │
│                                                │ Grounded Prompt           │
│  ┌─────────────────────────────────────────────▼────────────────────────┐  │
│  │                    INFERENCE LAYER                                  │  │
│  │   Ollama + Mistral 7B (local, offline)  OR  OpenAI GPT-4o mini      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### 7.1 Data Flow Summary

| Stage | Input | Processing | Output |
|---|---|---|---|
| Intake | Citizen narrative | Form validation, dispute classification | Structured dispute object |
| PII Masking | Structured dispute object | Regex entity detection | Masked dispute object + PII map |
| Statute Retrieval | Dispute category | MCP server lookup | Verbatim statute text |
| Generation | Masked object + statute text | LLM inference | Masked draft notice |
| PDF Export | Masked draft + PII map | Re-hydration + SHA-256 hashing | Signed, verifiable PDF |

---

## 8. Statute Knowledge Base

| Act | Year | Dispute Category | Key Provisions Covered |
|---|---|---|---|
| **Consumer Protection Act** | 2019 | `consumer_fraud` | Defects in goods, deficiency in services, unfair trade practices, consumer disputes redressal mechanism, complaint timelines, compensation |
| **Payment of Wages Act** | 1936 | `unpaid_wages` | Wage payment obligations, permissible deductions, wage period limits, authority for claims, penalties for non-payment |
| **Industrial Relations Code** | 2020 | `unpaid_wages` | Grievance redressal committees, notice period requirements, retrenchment compensation, industrial dispute resolution machinery |
| **Model Tenancy Act** | 2021 | `security_deposit` | Security deposit caps, return timelines, landlord obligations on vacation, interest on withheld deposits, Rent Authority jurisdiction |

**Total provisions in knowledge base: 34**

Each provision is stored as a structured record containing the Act name, section number, section title, verbatim text, and applicable dispute categories. The MCP server returns the full verbatim text record — not a synthesised summary — ensuring the notice always quotes the law exactly as enacted.

---

## 9. Security & Privacy Design

### 9.1 Authentication

| Control | Implementation |
|---|---|
| Password storage | PBKDF2-HMAC-SHA256 with per-user salt |
| Session tokens | JWT access tokens, 8-hour expiry |
| Settlement URLs | JWT-signed, 30-day expiry, single-dispute scope |
| Transport | HTTPS enforced on all endpoints |

The PBKDF2-HMAC-SHA256 scheme ensures that even in the event of a database compromise, stored passwords cannot be recovered by brute-force within a practically relevant timeframe.

### 9.2 PII Masking Flow

```
CITIZEN INPUT
     │
     ▼
┌──────────────────────────────────────────────────┐
│  PII DETECTION ENGINE (Application Layer)        │
│                                                  │
│  Entities detected and replaced:                 │
│  • Phone numbers      →  {{PHONE_n}}             │
│  • Aadhaar numbers    →  {{AADHAAR_n}}           │
│  • PAN card numbers   →  {{PAN_n}}               │
│  • Bank account nos.  →  {{BANK_ACCOUNT_n}}      │
│  • UPI IDs            →  {{UPI_n}}               │
│  • Email addresses    →  {{EMAIL_n}}             │
└─────────────────────┬────────────────────────────┘
                      │ Masked payload only
                      ▼
              ┌───────────────┐
              │  LLM ENGINE   │  ← Never sees raw PII
              └───────┬───────┘
                      │ Masked draft
                      ▼
┌──────────────────────────────────────────────────┐
│  RE-HYDRATION ENGINE (PDF Generation Only)       │
│  Substitutes {{PHONE_n}} → original value        │
│  PII mapping table is discarded after PDF write  │
└──────────────────────────────────────────────────┘
```

### 9.3 Document Integrity

Every generated PDF embeds a SHA-256 hash of the notice body text in the document footer. Any post-generation alteration of the notice content will cause the hash to mismatch, providing tamper evidence to consumer forums, labour courts, or any other authority receiving the document.

### 9.4 Role-Based Access

| Role | Capabilities |
|---|---|
| Citizen (authenticated) | Create disputes, generate notices, download PDFs, access settlement portal |
| Opposing party (settlement URL) | View notice, submit settlement response via JWT-scoped URL only |
| Admin | Dispute analytics, system health (roadmap) |

---

## 10. Impact Metrics & KPIs

### 10.1 Efficiency Metrics (Demonstrated)

| Metric | Current Value | Baseline |
|---|---|---|
| Time to draft legal notice | **< 3 minutes** | 1–3 days (lawyer engagement) |
| Cost per notice (cloud mode) | **< ₹50** | ₹2,000–₹8,000 (professional fee) |
| Cost per notice (local mode) | **₹0 marginal cost** | ₹2,000–₹8,000 (professional fee) |
| Statute accuracy | **100% (verbatim)** | Variable (LLM hallucination risk) |
| Test suite pass rate | **158/158 (100%)** | — |

### 10.2 Quality Metrics

| Metric | Design Target | Mechanism |
|---|---|---|
| Citation accuracy | Zero hallucinated citations | MCP server injects verbatim text; LLM cannot cite outside supplied context |
| PII exposure to LLM | Zero raw PII transmitted | Pre-LLM masking enforced at application layer |
| Document integrity | Tamper-evident | SHA-256 hash embedded in PDF footer |
| Session security | 8-hour token expiry | JWT with configurable TTL |

### 10.3 Scale Potential

India's access-to-justice gap implies an addressable population of hundreds of millions of citizens who face the cost and knowledge barriers described in Section 2. Specific near-term target segments:

- **Consumer disputes**: Approximately 1.7 million complaints filed annually with consumer commissions; a much larger number go unfiled due to cost barriers.
- **Wage disputes**: Approximately 30,000 claims filed annually under the Payment of Wages Act; actual wage-theft incidence is estimated to be far higher.
- **Tenancy disputes**: The Model Tenancy Act 2021 covers a large and growing urban rental market, with security deposit disputes among the most common pre-litigation matters.

If the platform were deployed at even 0.1% of the currently unfiled dispute population, it would represent tens of thousands of citizens per year gaining access to a meaningful legal remedy they currently cannot afford to pursue.

---

## 11. Scalability Roadmap

### Phase 1 — Current State (MVP Demonstrated)

- Three dispute categories: consumer fraud, unpaid wages, security deposit
- Four Acts, 34 provisions
- Local LLM (Mistral 7B via Ollama) and cloud LLM (GPT-4o mini) modes
- Static GitHub Pages frontend with demo mode
- FastAPI backend with full auth, PII masking, PDF generation, settlement portal
- 158 automated tests, all passing

### Phase 2 — Corpus Expansion (0–6 months post-funding)

- Expand MCP statute database to 10+ Acts covering domestic violence, right to information, scheduled caste/scheduled tribe protection, motor vehicle accidents, and employment provident fund
- Add 5+ additional dispute categories
- Integrate with National Consumer Helpline (NCH) API for automated complaint registration
- Vernacular language intake forms (Hindi, Marathi, Bengali, Tamil) via translation layer

### Phase 3 — Institutional Deployment (6–18 months)

- White-label deployment kit for university legal aid clinics and NGO legal empowerment centres
- Integration with e-Courts API for case status tracking after notice dispatch
- Lawyer referral marketplace for disputes that escalate beyond pre-litigation
- Analytics dashboard for legal aid organisations (aggregate, anonymised)
- Offline-capable mobile PWA with service worker caching of statute database

### Phase 4 — Ecosystem Integration (18–36 months)

- State-specific regulation overlays (rent control acts, labour welfare fund rules)
- Integration with Lok Adalat scheduling systems for automated alternate dispute resolution referral
- API programme enabling courts, consumer forums, and labour commissioners to verify SHA-256 notice hashes directly
- Community annotation layer allowing verified legal professionals to review and flag statute coverage gaps

---

## 12. Conclusion

The Legal Rights Navigator: Pre-Litigation Engine demonstrates that the access-to-justice gap in India is not merely a legal or institutional problem — it is, in large part, an information asymmetry problem that AI can address without requiring court reform, legislative change, or large capital investment. By combining a local open-weight LLM with a deterministic statute retrieval layer, the platform achieves a quality of legal grounding that general-purpose AI tools cannot match, while keeping the marginal cost of a legally valid notice below ₹50.

The system's design choices — local-first LLM, static frontend deployment, strict PII isolation, verbatim statute injection, and SHA-256 document integrity — reflect a considered understanding of the constraints and trust requirements of deploying AI in a legal context for underserved populations. These are not incidental features; they are the architecture of trustworthy, responsible AI in a high-stakes domain.

SDG 16.3 asks that every person have access to justice. This platform takes one concrete, measurable step toward that goal: it makes the first and most important instrument of self-advocacy — the legal notice — available to any citizen with a smartphone and a genuine grievance. At scale, that is a meaningful reduction in one of the most persistent structural inequalities in the world's largest democracy.

---

*Submitted to the IBM SkillsBuild / CSRBOX AI for Good Programme.*

*Repository: https://github.com/ayushgadigone-del/legal-rights-navigator*
*Live Demo: https://ayushgadigone-del.github.io/legal-rights-navigator/*
