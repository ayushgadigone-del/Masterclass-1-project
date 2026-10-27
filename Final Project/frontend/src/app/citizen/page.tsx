"use client";
import { useCallback, useState } from "react";
import { VoiceRecorder } from "@/components/VoiceRecorder";
import { SampleCaseButton, SAMPLE_CASES, SampleCase } from "@/components/SampleCaseButton";
import { api } from "@/lib/api";
import type { CaseStatus, DisputeCategory, IntakeResponse } from "@/lib/types";

type Lang = "en" | "hi";

const CATEGORY_LABELS: Record<DisputeCategory, string> = {
  unpaid_wages: "💼 Unpaid Wages",
  consumer_fraud: "🛒 Consumer Fraud",
  security_deposit: "🏠 Security Deposit",
};

const STATUS_STEPS: { key: CaseStatus; label: string }[] = [
  { key: "intake_in_progress", label: "Collecting Facts" },
  { key: "ready_for_notice", label: "Facts Complete" },
  { key: "pending_clinic_review", label: "Clinic Review" },
  { key: "clinic_approved", label: "Notice Approved" },
  { key: "notice_sent", label: "Notice Dispatched" },
  { key: "settlement_open", label: "Settlement Open" },
  { key: "settled", label: "Resolved" },
];

// ── Offline demo simulation ───────────────────────────────────────────────────
// When the backend is not reachable (GitHub Pages, offline), we walk the user
// through the sample case messages and then show a pre-built notice.

const DEMO_QUESTIONS: Record<string, string[]> = {
  unpaid_wages: [
    "What is the name of your employer / company?",
    "When did the unpaid period begin? (e.g. November 2023)",
    "Do you have salary slips, bank statements, or any written proof?",
  ],
  consumer_fraud: [
    "What product or service did you purchase, and from which seller?",
    "When did you make the purchase, and what is the invoice amount?",
    "What proof do you have — receipt, photos, WhatsApp messages?",
  ],
  security_deposit: [
    "What is your landlord's name and address?",
    "When did you vacate the property and how much deposit was paid?",
    "Do you have a rent agreement or any written communication?",
  ],
};

const DEMO_NOTICE: Record<string, string> = {
  unpaid_wages: `LEGAL NOTICE

To: ABC Garments Pvt Ltd, Industrial Area, Sector 12, Delhi – 110001
Date: ${new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}

Subject: Demand for Payment of Unpaid Wages — Section 5 & Section 15, Payment of Wages Act 1936

Dear Sir/Madam,

I, Ramesh Kumar, hereby serve this legal notice for unpaid wages totalling ₹45,000 for November 2023 to January 2024.

LEGAL BASIS:
• Section 5, Payment of Wages Act 1936 — wages must be paid within 2 working days of termination.
• Section 15, Payment of Wages Act 1936 — penalty of up to 10× delayed wages may be claimed.

DEMAND: Pay ₹45,000 within 30 days of this notice.

Yours faithfully,
Ramesh Kumar`,

  consumer_fraud: `LEGAL NOTICE

To: QuickMart Pvt Ltd
Date: ${new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}

Subject: Defective Product — Refund Demand — Section 2(47) & Section 35, Consumer Protection Act 2019

Dear Sir/Madam,

I, Priya Sharma, purchased a washing machine from your store on 15 March 2024 for ₹25,000. The product failed within 2 weeks and you have refused to refund.

LEGAL BASIS:
• Section 2(47), Consumer Protection Act 2019 — definition of unfair trade practice.
• Section 35, Consumer Protection Act 2019 — right to file complaint before District Commission.

DEMAND: Refund ₹25,000 within 30 days or face proceedings before the District Consumer Disputes Redressal Commission.

Yours faithfully,
Priya Sharma`,

  security_deposit: `LEGAL NOTICE

To: Suresh Properties
Date: ${new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}

Subject: Return of Security Deposit — Section 21, Model Tenancy Act 2021

Dear Sir/Madam,

I, Ananya Singh, vacated the premises on 10 February 2024. You continue to wrongfully withhold my security deposit of ₹60,000.

LEGAL BASIS:
• Section 21, Model Tenancy Act 2021 — landlord shall refund security deposit within one month of vacating.

DEMAND: Return ₹60,000 within 30 days or face proceedings before the Rent Authority.

Yours faithfully,
Ananya Singh`,
};

const DEMO_GUIDE: Record<string, string> = {
  unpaid_wages:
    "Your employer must pay your wages within 2 working days after your employment ends (Section 5, Payment of Wages Act 1936). If they don't, you can claim up to 10× the delayed amount as penalty (Section 15). Keep your salary slips and bank statements safe. If there is no response in 30 days, file a claim with the Authority under the Payment of Wages Act in your district.",
  consumer_fraud:
    "Under the Consumer Protection Act 2019, every consumer has the right to a refund or replacement for defective goods. You can file a complaint before the District Consumer Disputes Redressal Commission if the seller ignores this notice. Keep your purchase receipt, photos, and all chat messages as evidence.",
  security_deposit:
    "Under the Model Tenancy Act 2021, your landlord must return your security deposit within one month of you vacating. If they refuse, you can approach the Rent Authority in your city. Make sure you keep your rent agreement, vacating receipt, and any written messages from the landlord.",
};

// ── Progress bar ──────────────────────────────────────────────────────────────

function ProgressBar({ status }: { status: CaseStatus }) {
  const idx = STATUS_STEPS.findIndex((s) => s.key === status);
  return (
    <ol className="flex items-center w-full text-xs text-slate-400 mb-6 overflow-x-auto gap-0" aria-label="Case progress">
      {STATUS_STEPS.map((step, i) => {
        const done = i < idx;
        const active = i === idx;
        return (
          <li key={step.key} className="flex items-center shrink-0">
            <div className={`flex flex-col items-center ${i > 0 ? "ml-1" : ""}`}>
              <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border-2 transition-colors
                ${done ? "bg-green-500 border-green-500 text-white" : active ? "bg-blue-600 border-blue-600 text-white" : "bg-white border-slate-300 text-slate-400"}`}>
                {done ? "✓" : i + 1}
              </div>
              <span className={`mt-1 whitespace-nowrap ${active ? "text-blue-600 font-semibold" : done ? "text-green-600" : ""}`}>{step.label}</span>
            </div>
            {i < STATUS_STEPS.length - 1 && (
              <div className={`h-0.5 w-6 mx-1 mt-[-1rem] transition-colors ${done ? "bg-green-400" : "bg-slate-200"}`} />
            )}
          </li>
        );
      })}
    </ol>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function CitizenPage() {
  const [lang, setLang] = useState<Lang>("en");
  const [category, setCategory] = useState<DisputeCategory | "">("");
  const [text, setText] = useState("");
  const [caseId, setCaseId] = useState<string | null>(null);
  const [status, setStatus] = useState<CaseStatus>("intake_in_progress");
  const [followUp, setFollowUp] = useState<string | null>(null);
  const [missing, setMissing] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [noticeId, setNoticeId] = useState<string | null>(null);
  const [plainGuide, setPlainGuide] = useState<string | null>(null);
  const [messages, setMessages] = useState<{ role: "user" | "bot"; text: string }[]>([]);

  // Demo-mode state
  const [demoMode, setDemoMode] = useState(false);
  const [demoStep, setDemoStep] = useState(0);
  const [demoCategory, setDemoCategory] = useState<DisputeCategory | "">("");

  const handleTranscript = useCallback((t: string) => {
    setText((prev) => (prev ? prev + " " + t : t));
  }, []);

  // ── Load a sample case (works fully offline) ───────────────────────────────
  const handleSample = useCallback((sample: SampleCase) => {
    const cat = sample.category as DisputeCategory;
    setDemoMode(true);
    setDemoCategory(cat);
    setCategory(cat);
    setDemoStep(0);
    setMessages([]);
    setCaseId("demo-" + Math.random().toString(36).slice(2, 8));
    setStatus("intake_in_progress");
    setFollowUp(null);
    setMissing([]);
    setError(null);
    setNoticeId(null);
    setPlainGuide(null);
    setText(sample.messages[0]);

    // Greet with first follow-up question
    const questions = DEMO_QUESTIONS[cat] ?? [];
    setTimeout(() => {
      setMessages([
        { role: "bot", text: `👋 I'll help you draft a legal notice for your ${CATEGORY_LABELS[cat]} dispute. ${questions[0] ?? "Please describe what happened."}` },
      ]);
    }, 400);
  }, []);

  // ── Demo send (offline simulation) ────────────────────────────────────────
  const sendDemoMessage = useCallback(() => {
    if (!text.trim()) return;
    const userMsg = text.trim();
    setText("");

    setMessages((m) => [...m, { role: "user", text: userMsg }]);
    setLoading(true);

    const cat = demoCategory as DisputeCategory;
    const questions = DEMO_QUESTIONS[cat] ?? [];
    const nextStep = demoStep + 1;

    setTimeout(() => {
      setLoading(false);
      if (nextStep < questions.length) {
        setDemoStep(nextStep);
        setMessages((m) => [...m, { role: "bot", text: questions[nextStep] }]);
        setMissing(questions.slice(nextStep));
      } else {
        // All facts collected — show the notice
        setDemoStep(nextStep);
        setStatus("pending_clinic_review");
        setMissing([]);
        const fakeNoticeId = "demo-notice-" + Math.random().toString(36).slice(2, 8);
        setNoticeId(fakeNoticeId);
        setPlainGuide(DEMO_GUIDE[cat] ?? "");
        setMessages((m) => [
          ...m,
          { role: "bot", text: "✅ All facts collected! Generating your legal notice…" },
          { role: "bot", text: `📄 Legal notice drafted!\n\n${DEMO_NOTICE[cat] ?? ""}` },
          { role: "bot", text: `✅ Notice ID: ${fakeNoticeId.slice(0, 12)}… — queued for law clinic review.` },
        ]);
      }
    }, 900);
  }, [text, demoStep, demoCategory]);

  // ── Live send (real backend) ───────────────────────────────────────────────
  const sendLiveMessage = useCallback(async () => {
    if (!text.trim()) return;
    if (!caseId && !category) { setError("Please select a dispute type first."); return; }

    setLoading(true);
    setError(null);
    const userMsg = text.trim();
    setMessages((m) => [...m, { role: "user", text: userMsg }]);
    setText("");

    try {
      const res: IntakeResponse = await api.submitMessage({
        case_id: caseId ?? undefined,
        message: userMsg,
        dispute_category: !caseId ? (category as DisputeCategory) : undefined,
        language: lang,
      });

      setCaseId(res.case_id);
      setStatus(res.status);
      setMissing(res.missing_fields);

      if (res.follow_up_question) {
        setFollowUp(res.follow_up_question);
        setMessages((m) => [...m, { role: "bot", text: res.follow_up_question! }]);
      }

      if (res.status === "ready_for_notice") {
        setMessages((m) => [...m, { role: "bot", text: res.message }]);
        const notice = await api.generateNotice(res.case_id);
        setNoticeId(notice.notice_id);
        setPlainGuide(notice.plain_language_guide);
        setStatus("pending_clinic_review");
        setMessages((m) => [...m, {
          role: "bot",
          text: `✅ Legal notice drafted! Notice ID: ${notice.notice_id.slice(0, 8)}…`,
        }]);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }, [text, caseId, category, lang]);

  const sendMessage = demoMode ? sendDemoMessage : sendLiveMessage;

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Citizen Grievance Intake</h1>
        <p className="text-sm text-slate-500 mt-1">
          Describe your problem in plain language or speak it. We&apos;ll draft your legal notice automatically.
        </p>
        {demoMode && (
          <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-xs text-amber-700 font-medium">
            🔌 Demo mode — no backend required
          </div>
        )}
      </div>

      {/* Progress */}
      {caseId && <ProgressBar status={status} />}

      {/* Lang + Category row */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex rounded-lg overflow-hidden border border-slate-300 text-sm" role="group" aria-label="Language">
          {(["en", "hi"] as Lang[]).map((l) => (
            <button key={l} type="button" onClick={() => setLang(l)}
              className={`px-3 py-1.5 font-medium transition-colors ${lang === l ? "bg-blue-600 text-white" : "bg-white text-slate-600 hover:bg-slate-50"}`}
              aria-pressed={lang === l}>
              {l === "en" ? "🇮🇳 English" : "🇮🇳 हिन्दी"}
            </button>
          ))}
        </div>

        {!caseId && (
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as DisputeCategory)}
            className="flex-1 min-w-[180px] px-3 py-1.5 border border-slate-300 rounded-lg text-sm bg-white text-slate-700 focus:ring-2 focus:ring-blue-400"
            aria-label="Select dispute type"
          >
            <option value="">-- Select dispute type --</option>
            {(Object.keys(CATEGORY_LABELS) as DisputeCategory[]).map((k) => (
              <option key={k} value={k}>{CATEGORY_LABELS[k]}</option>
            ))}
          </select>
        )}
      </div>

      {/* Sample case buttons */}
      <div className="mb-3">
        <p className="text-xs text-slate-500 mb-2 font-medium">⚡ Try a sample case instantly (no backend needed):</p>
        <div className="flex flex-wrap gap-2" aria-label="Load sample cases">
          {(["wage_theft", "consumer_fraud", "security_deposit"] as const).map((k) => (
            <SampleCaseButton key={k} variant={k} onLoad={handleSample} />
          ))}
        </div>
      </div>

      {/* Chat messages */}
      {messages.length > 0 && (
        <div className="mb-4 rounded-xl bg-slate-50 border border-slate-200 max-h-72 overflow-y-auto p-3 space-y-2">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[88%] px-3 py-2 rounded-xl text-sm whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-blue-600 text-white rounded-br-none"
                  : "bg-white border border-slate-200 text-slate-700 rounded-bl-none"
              }`}>
                {m.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 px-3 py-2 rounded-xl rounded-bl-none">
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:300ms]" />
                </span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Voice recorder */}
      <div className="flex items-center gap-6 mb-4 p-4 bg-white border border-slate-200 rounded-xl">
        <VoiceRecorder onTranscript={handleTranscript} language={lang} />
        <div className="flex-1 text-xs text-slate-400">
          <p className="font-medium text-slate-600 mb-1">Or type your grievance below</p>
          <p>After speaking, edit if needed, then click Send.</p>
        </div>
      </div>

      {/* Text input */}
      <div className="flex gap-2 mb-4">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
          placeholder={followUp ?? (lang === "hi" ? "अपनी समस्या यहाँ लिखें…" : "Describe your grievance here…")}
          rows={3}
          className="flex-1 px-3 py-2 border border-slate-300 rounded-xl text-sm resize-none focus:ring-2 focus:ring-blue-400"
          aria-label="Grievance description"
          disabled={loading}
        />
        <button
          type="button"
          onClick={sendMessage}
          disabled={loading || !text.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors self-end"
          aria-label="Send message"
        >
          {loading ? "…" : "Send"}
        </button>
      </div>

      {error && (
        <div role="alert" className="mb-4 px-4 py-3 bg-red-50 border border-red-300 rounded-xl text-sm text-red-700">
          ⚠ {error}
        </div>
      )}

      {/* Missing fields hint */}
      {missing.length > 0 && !noticeId && (
        <div className="mb-4 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
          <p className="font-semibold mb-1">Still needed:</p>
          <ul className="list-disc list-inside space-y-0.5">
            {missing.map((f) => <li key={f}>{f.replace(/_/g, " ")}</li>)}
          </ul>
        </div>
      )}

      {/* Plain language guide */}
      {plainGuide && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-xl">
          <h2 className="text-sm font-bold text-green-800 mb-2">📋 Your Plain-Language Action Guide</h2>
          <p className="text-xs text-slate-600 whitespace-pre-wrap leading-relaxed">{plainGuide}</p>
        </div>
      )}

      {noticeId && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl text-sm">
          <p className="font-semibold text-blue-800">✅ Notice in Review Queue</p>
          <p className="text-blue-600 text-xs mt-1">
            A law clinic student will verify and dispatch your notice.{" "}
            Case ID: <code className="bg-white px-1 rounded">{caseId}</code>
          </p>
        </div>
      )}
    </div>
  );
}
