"use client";
import { useState } from "react";
import { CountdownTimer } from "@/components/CountdownTimer";

// ── Demo notice data ───────────────────────────────────────────────────────────
const DEMO_NOTICE_TEXT = `LEGAL NOTICE

To: ABC Garments Pvt Ltd
    Industrial Area, Sector 12, Delhi – 110001

Date: ${new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}

Subject: Demand for Payment of Unpaid Wages — Section 5 & Section 15, Payment of Wages Act 1936

Dear Sir/Madam,

I, Ramesh Kumar, hereby serve this legal notice upon you for unpaid wages totalling ₹45,000 for the period November 2023 to January 2024.

LEGAL BASIS:
• Section 5, Payment of Wages Act 1936: Wages must be paid within 2 working days of termination.
• Section 15, Payment of Wages Act 1936: Penalty of up to 10× the delayed wages may be claimed.
• Section 45, Industrial Relations Code 2020: Fine up to ₹50,000 for non-payment.

DEMAND: Pay ₹45,000 (Rupees Forty-Five Thousand Only) within 30 days of this notice.

CONSEQUENCE OF NON-COMPLIANCE: Failure to comply will result in a claim before the Authority appointed under Section 15, Payment of Wages Act, and/or the Industrial Tribunal.

Yours faithfully,
Ramesh Kumar
(Complainant)

Verified by: Law Clinic Review — National Law University, Delhi
Notice Verification Hash (SHA-256): 3a7f9c2e1b4d6f8a0e2c4b6d8f0a2c4e6b8d0f2a4c6e8b0d2f4a6c8e0b2d4f6a`;

const DEMO_CITATIONS = [
  { section: "Section 5", act: "Payment of Wages Act 1936", penalty: null, notice_period_days: 7 },
  { section: "Section 15", act: "Payment of Wages Act 1936", penalty: "Up to 10× delayed wages", notice_period_days: null },
  { section: "Section 45", act: "Industrial Relations Code 2020", penalty: "Fine up to ₹50,000", notice_period_days: 2 },
];

// Deadline = 7 days from "now" for demo purposes
const DEMO_DEADLINE = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

type ResponseType = "accept_full" | "accept_partial" | "reject" | "request_mediation";

const RESPONSE_OPTIONS: { value: ResponseType; label: string; description: string; color: string }[] = [
  {
    value: "accept_full",
    label: "✅ Accept Full Claim",
    description: "I agree to pay the full claimed amount of ₹45,000 within the agreed period.",
    color: "green",
  },
  {
    value: "accept_partial",
    label: "🤝 Propose Partial Settlement",
    description: "I agree to pay a partial amount and propose revised terms.",
    color: "blue",
  },
  {
    value: "request_mediation",
    label: "⚖ Request Mediation",
    description: "I request a neutral mediator through the Samadhan portal.",
    color: "violet",
  },
  {
    value: "reject",
    label: "✗ Contest the Claim",
    description: "I dispute the claim and will respond through proper legal channels.",
    color: "red",
  },
];

const COLOR_STYLES: Record<string, string> = {
  green:  "border-green-300 bg-green-50 text-green-800 hover:bg-green-100",
  blue:   "border-blue-300 bg-blue-50 text-blue-800 hover:bg-blue-100",
  violet: "border-violet-300 bg-violet-50 text-violet-800 hover:bg-violet-100",
  red:    "border-red-300 bg-red-50 text-red-800 hover:bg-red-50",
};

const SELECTED_COLOR: Record<string, string> = {
  green:  "border-green-500 bg-green-100 ring-2 ring-green-400",
  blue:   "border-blue-500 bg-blue-100 ring-2 ring-blue-400",
  violet: "border-violet-500 bg-violet-100 ring-2 ring-violet-400",
  red:    "border-red-500 bg-red-100 ring-2 ring-red-400",
};

export default function SettlementDemoPage() {
  const [selected, setSelected] = useState<ResponseType | null>(null);
  const [amount, setAmount] = useState("45000");
  const [message, setMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [expired, setExpired] = useState(false);

  const handleSubmit = () => {
    if (!selected) return;
    setSubmitted(true);
  };

  if (submitted) {
    const resp = RESPONSE_OPTIONS.find((r) => r.value === selected)!;
    const escalateMsg =
      selected === "reject"
        ? "Your contestation has been recorded. The claimant may escalate to the e-Daakhil portal or Labour Court."
        : selected === "request_mediation"
        ? "A mediation request has been sent to the Samadhan portal. A mediator will contact both parties within 3 working days."
        : "Your settlement proposal has been forwarded to the claimant for acceptance. The case will be marked 'Settled' upon agreement.";

    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center">
        <div className="text-5xl mb-4">{selected === "reject" ? "⚖️" : selected === "request_mediation" ? "🤝" : "✅"}</div>
        <h2 className="text-xl font-bold text-slate-800 mb-2">Response Submitted</h2>
        <p className="text-sm text-slate-600 mb-4">{escalateMsg}</p>
        <button onClick={() => setSubmitted(false)}
          className="text-xs text-blue-600 underline">← Back to notice</button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <span className="text-xs font-semibold uppercase tracking-wide text-red-600 bg-red-50 border border-red-200 px-2 py-1 rounded-full">
          ⚠ Legal Notice Received
        </span>
        <h1 className="text-2xl font-bold text-slate-800 mt-3">Respond to Pre-Litigation Notice</h1>
        <p className="text-sm text-slate-500 mt-1">
          This notice has been verified by a law clinic student. Your response is required within <strong>7 days</strong>.
        </p>
      </div>

      {/* Countdown */}
      <div className="mb-6">
        <CountdownTimer
          deadline={DEMO_DEADLINE}
          label="to respond before escalation to e-Daakhil / Samadhan"
          onExpired={() => setExpired(true)}
        />
        {expired && (
          <div className="mt-3 p-3 bg-red-50 border border-red-300 rounded-xl text-sm text-red-700 font-medium text-center">
            ⚠ Deadline expired. This case has been escalated to the e-Daakhil portal.
          </div>
        )}
      </div>

      {/* Citation summary */}
      <div className="mb-5 p-3 bg-amber-50 border border-amber-200 rounded-xl">
        <p className="text-xs font-semibold text-amber-800 mb-2">Applicable Statute Sections</p>
        <div className="flex flex-wrap gap-2">
          {DEMO_CITATIONS.map((c, i) => (
            <span key={i} className="px-2 py-0.5 bg-white border border-amber-300 text-amber-800 text-xs rounded-full font-medium">
              {c.section} · {c.act}
              {c.penalty && <span className="ml-1 text-red-600">· {c.penalty}</span>}
            </span>
          ))}
        </div>
      </div>

      {/* Formal notice */}
      <details className="mb-6">
        <summary className="cursor-pointer text-sm font-semibold text-slate-700 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl hover:bg-slate-100 list-none flex items-center justify-between [&::-webkit-details-marker]:hidden">
          <span>📄 View Full Legal Notice</span>
          <span className="text-slate-400 text-xs">click to expand</span>
        </summary>
        <div className="mt-2 p-5 bg-white border border-slate-200 rounded-xl font-mono text-xs leading-relaxed whitespace-pre-wrap text-slate-700 max-h-80 overflow-y-auto">
          {DEMO_NOTICE_TEXT}
        </div>
      </details>

      {/* Response card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <h2 className="text-base font-bold text-slate-800 mb-4">Propose Settlement / Pay Dues</h2>

        <div className="space-y-2 mb-5" role="radiogroup" aria-label="Select your response">
          {RESPONSE_OPTIONS.map((opt) => {
            const isSelected = selected === opt.value;
            return (
              <button
                key={opt.value}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => setSelected(opt.value)}
                className={`w-full text-left px-4 py-3 rounded-xl border transition-all ${
                  isSelected ? SELECTED_COLOR[opt.color] : COLOR_STYLES[opt.color]
                }`}
              >
                <span className="font-semibold text-sm">{opt.label}</span>
                <span className="block text-xs mt-0.5 opacity-80">{opt.description}</span>
              </button>
            );
          })}
        </div>

        {/* Partial amount input */}
        {selected === "accept_partial" && (
          <div className="mb-4">
            <label className="text-xs font-semibold text-slate-600 block mb-1.5">
              Proposed settlement amount (₹)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-400"
              min={1}
              aria-label="Proposed settlement amount in rupees"
            />
          </div>
        )}

        {/* Message */}
        {selected && (
          <div className="mb-5">
            <label className="text-xs font-semibold text-slate-600 block mb-1.5">
              Message to claimant (optional)
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
              placeholder="Explain your response or propose specific terms…"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-400"
              aria-label="Message to claimant"
            />
          </div>
        )}

        <button
          type="button"
          onClick={handleSubmit}
          disabled={!selected || expired}
          className="w-full py-3 bg-blue-600 text-white rounded-xl text-sm font-bold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          aria-label="Submit your settlement response"
        >
          {expired ? "Deadline Expired" : selected ? "Submit Response" : "Select a response above"}
        </button>

        <p className="text-[10px] text-slate-400 text-center mt-3">
          No response within 7 days triggers automatic escalation to e-Daakhil / Samadhan portal.
        </p>
      </div>
    </div>
  );
}
