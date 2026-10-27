import Link from "next/link";

const ROLES = [
  {
    href: "/citizen",
    emoji: "🙋",
    title: "Citizen View",
    subtitle: "Submit a grievance",
    desc: "Speak or type your problem in Hindi or English. Get a law-clinic-verified legal notice drafted for free.",
    color: "blue",
    cta: "Start Intake →",
  },
  {
    href: "/clinic",
    emoji: "⚖️",
    title: "Law Clinic Reviewer",
    subtitle: "Review & approve notices",
    desc: "Review auto-drafted notices with MCP-verified green statute badges. Approve to dispatch or reject with notes.",
    color: "green",
    cta: "Open Review Queue →",
  },
  {
    href: "/settlement/demo",
    emoji: "🤝",
    title: "Opposing Party",
    subtitle: "Respond to a notice",
    desc: "View the formal notice, see the 7-day countdown timer, and propose a settlement or pay dues.",
    color: "amber",
    cta: "View Settlement Portal →",
  },
  {
    href: "/dashboard",
    emoji: "📊",
    title: "Impact Dashboard",
    subtitle: "SDG 16 metrics & unit economics",
    desc: "₹0 per notice (Ollama), 97% cost reduction vs. traditional legal fees, end-to-end pipeline view.",
    color: "violet",
    cta: "See Impact →",
  },
] as const;

const CARD_COLOR: Record<string, string> = {
  blue:   "border-blue-200 hover:border-blue-400 hover:bg-blue-50",
  green:  "border-green-200 hover:border-green-400 hover:bg-green-50",
  amber:  "border-amber-200 hover:border-amber-400 hover:bg-amber-50",
  violet: "border-violet-200 hover:border-violet-400 hover:bg-violet-50",
};

const CTA_COLOR: Record<string, string> = {
  blue:   "text-blue-600",
  green:  "text-green-600",
  amber:  "text-amber-600",
  violet: "text-violet-600",
};

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-12">
      {/* Hero */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-full text-xs font-semibold text-blue-700 mb-4">
          ⚖️ SDG 16 · Legal Rights Navigator · Pre-Litigation Engine
        </div>
        <h1 className="text-4xl font-bold text-slate-900 mb-3 leading-tight">
          Your Legal Rights.<br />
          <span className="text-blue-600">Plain Language. Free.</span>
        </h1>
        <p className="text-slate-500 text-base max-w-xl mx-auto">
          Convert your grievance into a statute-cited, law-clinic-verified legal notice — in Hindi or English,
          by voice or text, at zero cost.
        </p>
      </div>

      {/* Role cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-12">
        {ROLES.map((r) => (
          <Link
            key={r.href}
            href={r.href}
            className={`group p-6 rounded-2xl bg-white border-2 transition-all ${CARD_COLOR[r.color]}`}
          >
            <div className="text-3xl mb-3">{r.emoji}</div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-0.5">{r.subtitle}</div>
            <h2 className="text-lg font-bold text-slate-800 mb-2">{r.title}</h2>
            <p className="text-sm text-slate-500 mb-4 leading-relaxed">{r.desc}</p>
            <span className={`text-sm font-semibold ${CTA_COLOR[r.color]} group-hover:underline`}>{r.cta}</span>
          </Link>
        ))}
      </div>

      {/* Feature pills */}
      <div className="flex flex-wrap justify-center gap-2 text-xs text-slate-500">
        {[
          "🎙 Voice input (Hindi/English)",
          "🔒 Zero hallucination (MCP-verified)",
          "📄 SHA-256 verified PDF",
          "⏱ 7-day settlement countdown",
          "📚 34 statute provisions",
          "💰 ₹0 running cost (Ollama)",
          "⚖️ e-Daakhil / Samadhan escalation",
          "🛡 JWT-authenticated clinic review",
        ].map((f, i) => (
          <span key={i} className="px-3 py-1 bg-slate-100 rounded-full border border-slate-200">{f}</span>
        ))}
      </div>
    </div>
  );
}
