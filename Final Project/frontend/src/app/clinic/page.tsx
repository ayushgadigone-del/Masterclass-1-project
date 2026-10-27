"use client";
import { useCallback, useRef, useState } from "react";
import { StatuteBadge } from "@/components/StatuteBadge";
import { api } from "@/lib/api";
import type { ClinicVerifyResponse, NoticeGenerateResponse, StatuteCitation } from "@/lib/types";

// ── Demo data (pre-loaded when no live backend is available) ──────────────────
const DEMO_NOTICE: NoticeGenerateResponse = {
  case_id: "demo-case-001",
  notice_id: "demo-notice-001",
  review_status: "pending_clinic_review",
  plain_language_guide:
    "Your employer was required to pay your wages within 7 days of the wage period end (Section 5, Payment of Wages Act 1936). Since they failed to do so, you are entitled to claim up to 10× the delayed amount as penalty under Section 15. File your claim with the Authority under the Payment of Wages Act for your district.",
  draft_body: `LEGAL NOTICE

To: ABC Garments Pvt Ltd, Industrial Area, Sector 12, Delhi – 110001
Date: ${new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}

Subject: Demand for Payment of Unpaid Wages — Section 5 & Section 15, Payment of Wages Act 1936

Dear Sir/Madam,

I, Ramesh Kumar, a permanent employee having served in your establishment as Machine Operator, hereby issue this pre-litigation notice on the following grounds:

BACKGROUND: I was employed with your establishment from 01 April 2021. I submitted my resignation on 15 January 2024. Despite my lawful resignation, wages totalling ₹45,000 for the period November 2023 to January 2024 remain unpaid.

LEGAL BASIS: Under Section 5 of the Payment of Wages Act 1936, wages of any person whose employment is terminated shall be paid within the second working day of such termination. Under Section 15, your failure to pay entitles me to a penalty of up to ten times the unpaid amount.

DEMAND: You are hereby called upon to pay ₹45,000 (Rupees Forty-Five Thousand Only) together with applicable interest and penalty within 30 (thirty) days of receipt of this notice.

CONSEQUENCE OF NON-COMPLIANCE: Failure to comply will leave me with no option but to file a claim before the Authority appointed under Section 15 of the Payment of Wages Act 1936, at your cost and risk.

Yours faithfully,
Ramesh Kumar`,
  citations: [
    {
      act: "Payment of Wages Act 1936",
      section: "Section 5",
      section_title: "Time of payment of wages",
      excerpt: "Where the employment of any person is terminated by or on behalf of the employer, the wages earned by him shall be paid before the expiry of the second working day after the day on which his employment is so terminated.",
      relevance_score: 0.91,
      notice_period_days: 7,
      penalty: null,
      forum: "Authority under Payment of Wages Act",
    },
    {
      act: "Payment of Wages Act 1936",
      section: "Section 15",
      section_title: "Claims arising out of deductions or delay in payment",
      excerpt: "The authority may direct payment of the delayed wages together with a penalty not exceeding ten times the amount of deduction or delayed wages.",
      relevance_score: 0.88,
      notice_period_days: null,
      penalty: "Up to 10× the delayed wages",
      forum: "Authority appointed under Section 15",
    },
    {
      act: "Industrial Relations Code 2020",
      section: "Section 45",
      section_title: "Payment of wages on termination",
      excerpt: "The wages payable to such worker shall be paid within two working days of such termination. Any employer who fails to pay wages within the period prescribed shall be punishable with fine which may extend to fifty thousand rupees.",
      relevance_score: 0.84,
      notice_period_days: 2,
      penalty: "Fine up to ₹50,000",
      forum: "Industrial Tribunal / Labour Court",
    },
  ],
  message: "All 3 citations verified by MCP statute server.",
};

// ── Highlight citations in notice text ───────────────────────────────────────
function renderNoticeWithHighlights(body: string, citations: StatuteCitation[]) {
  const lines = body.split("\n");
  return lines.map((line, i) => {
    // Check if line contains a citation reference
    const matchedCitation = citations.find(
      (c) => line.includes(c.section) || line.includes(c.section_title)
    );
    return (
      <div key={i} className={`${matchedCitation ? "bg-green-50 border-l-2 border-green-400 pl-2 -ml-2 rounded-r" : ""}`}>
        <span className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">{line || "\u00A0"}</span>
        {matchedCitation && (
          <span className="ml-2 relative inline-block" style={{ verticalAlign: "middle" }}>
            <StatuteBadge citation={matchedCitation} />
          </span>
        )}
      </div>
    );
  });
}

// ── Login panel ───────────────────────────────────────────────────────────────
function LoginPanel({ onLogin }: { onLogin: (token: string, id: string) => void }) {
  const [username, setUsername] = useState("clinic_student_01");
  const [password, setPassword] = useState("password123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(username, password);
      onLogin(res.access_token, res.reviewer_id);
    } catch (e: unknown) {
      // Demo mode — proceed without real auth
      onLogin("demo-token", "demo-reviewer-001");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-8 p-6 bg-white border border-slate-200 rounded-2xl shadow-sm">
      <h2 className="text-base font-bold text-slate-700 mb-4">Law Clinic Reviewer Login</h2>
      <div className="space-y-3">
        <input value={username} onChange={(e) => setUsername(e.target.value)}
          placeholder="Username" className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
          placeholder="Password" className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
        {error && <p className="text-xs text-red-600">{error}</p>}
        <button onClick={handleLogin} disabled={loading}
          className="w-full py-2 bg-green-600 text-white rounded-lg text-sm font-semibold hover:bg-green-700 disabled:opacity-50">
          {loading ? "Logging in…" : "Login / Demo Mode"}
        </button>
        <p className="text-[10px] text-slate-400 text-center">
          Demo mode: any credentials load the sample wage-theft case.
        </p>
      </div>
    </div>
  );
}

// ── Main clinic page ──────────────────────────────────────────────────────────
export default function ClinicPage() {
  const [token, setToken] = useState<string | null>(null);
  const [reviewerId, setReviewerId] = useState<string>("demo-reviewer");
  const [notice, setNotice] = useState<NoticeGenerateResponse | null>(null);
  const [editedBody, setEditedBody] = useState("");
  const [notes, setNotes] = useState("");
  const [result, setResult] = useState<ClinicVerifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleLogin = useCallback((t: string, id: string) => {
    setToken(t);
    setReviewerId(id);
    setNotice(DEMO_NOTICE);
    setEditedBody(DEMO_NOTICE.draft_body);
  }, []);

  const handleAction = async (action: "approve" | "reject") => {
    if (!notice || !token) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.verifyNotice(notice.case_id, {
        reviewer_id: reviewerId,
        action,
        edited_body: action === "approve" ? editedBody : undefined,
        reviewer_notes: notes || undefined,
      }, token);
      setResult(res);
    } catch (e: unknown) {
      // Demo mode — simulate approval
      if (action === "approve") {
        const mockHash = Array.from({ length: 64 }, () => Math.floor(Math.random() * 16).toString(16)).join("");
        setResult({
          case_id: notice.case_id,
          notice_id: notice.notice_id,
          review_status: "approved",
          pdf_path: `/data/pdfs/${notice.case_id}_${notice.notice_id}.pdf`,
          pdf_hash: mockHash,
          settlement_url: `http://localhost:3000/settlement/${notice.case_id}?token=demo-jwt-token`,
          message: `[DEMO] Notice approved. SHA-256: ${mockHash.slice(0, 16)}… Settlement URL generated.`,
        });
      } else {
        setResult({ case_id: notice.case_id, notice_id: notice.notice_id, review_status: "rejected", pdf_path: null, pdf_hash: null, settlement_url: null, message: "[DEMO] Notice rejected and returned to citizen." });
      }
    } finally {
      setLoading(false);
    }
  };

  if (!token) return <LoginPanel onLogin={handleLogin} />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Law Clinic Review</h1>
          <p className="text-sm text-slate-500">Verify citations, edit if needed, then approve or reject.</p>
        </div>
        <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded-full border border-green-300">
          Reviewer: {reviewerId.slice(0, 12)}
        </span>
      </div>

      {/* Success result */}
      {result && (
        <div className={`mb-5 p-4 rounded-xl border ${result.review_status === "approved" ? "bg-green-50 border-green-300" : "bg-amber-50 border-amber-300"}`}>
          <p className="text-sm font-semibold text-slate-800">{result.message}</p>
          {result.pdf_hash && (
            <p className="text-xs text-slate-500 mt-1 font-mono break-all">SHA-256: {result.pdf_hash}</p>
          )}
          {result.settlement_url && (
            <div className="mt-2">
              <p className="text-xs text-slate-600 font-medium mb-1">Settlement URL (copy & send to respondent):</p>
              <code className="block text-xs bg-white border border-slate-200 rounded px-2 py-1 break-all text-blue-700">
                {result.settlement_url}
              </code>
            </div>
          )}
        </div>
      )}

      {notice && !result && (
        <>
          {/* Citation badges row */}
          <div className="mb-4">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              MCP-Verified Statute Citations ({notice.citations.length})
            </p>
            <div className="flex flex-wrap gap-2 relative">
              {notice.citations.map((c, i) => (
                <StatuteBadge key={i} citation={c} index={i} />
              ))}
            </div>
          </div>

          {/* Split screen */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-5">
            {/* Left — highlighted preview */}
            <div className="flex flex-col">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Auto-Draft Preview (citations highlighted)
              </div>
              <div className="flex-1 p-4 bg-white border border-slate-200 rounded-xl overflow-y-auto max-h-[500px] font-mono text-sm leading-relaxed">
                {renderNoticeWithHighlights(notice.draft_body, notice.citations)}
              </div>
            </div>

            {/* Right — editable textarea */}
            <div className="flex flex-col">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Edit Notice (your approved version)
              </div>
              <textarea
                ref={textareaRef}
                value={editedBody}
                onChange={(e) => setEditedBody(e.target.value)}
                className="flex-1 p-4 border border-slate-300 rounded-xl font-mono text-sm resize-none min-h-[500px] focus:ring-2 focus:ring-green-400"
                aria-label="Edit notice body"
                spellCheck={false}
              />
            </div>
          </div>

          {/* Notes */}
          <div className="mb-4">
            <label className="text-xs font-semibold text-slate-500 block mb-1.5" htmlFor="reviewer-notes">
              Reviewer Notes (optional)
            </label>
            <input id="reviewer-notes" value={notes} onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. 'Added claimant address. Citations verified.'"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-green-400" />
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => handleAction("approve")}
              disabled={loading || !editedBody.trim()}
              className="px-6 py-2.5 bg-green-600 text-white rounded-xl text-sm font-bold hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center gap-2"
              aria-label="Approve and dispatch legal notice"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
              </svg>
              {loading ? "Processing…" : "Approve & Dispatch Notice"}
            </button>
            <button
              onClick={() => handleAction("reject")}
              disabled={loading}
              className="px-6 py-2.5 bg-white border border-red-300 text-red-600 rounded-xl text-sm font-semibold hover:bg-red-50 disabled:opacity-50 transition-colors"
              aria-label="Reject and return to citizen"
            >
              Reject & Return to Citizen
            </button>
          </div>
        </>
      )}
    </div>
  );
}
