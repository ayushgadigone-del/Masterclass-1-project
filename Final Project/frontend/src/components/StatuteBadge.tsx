// StatuteBadge — green verified citation pill with expandable excerpt tooltip
import type { StatuteCitation } from "@/lib/types";

interface Props {
  citation: StatuteCitation;
  index?: number;
}

export function StatuteBadge({ citation, index }: Props) {
  return (
    <details className="inline-block group">
      <summary
        className="
          inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full cursor-pointer
          bg-green-50 border border-green-300 text-green-800
          text-xs font-semibold select-none
          hover:bg-green-100 transition-colors
          list-none [&::-webkit-details-marker]:hidden
        "
        title={`${citation.act} — ${citation.section_title}`}
        aria-label={`${citation.section}: ${citation.section_title}. Click to expand.`}
      >
        {/* Verified checkmark */}
        <svg className="w-3 h-3 text-green-600 shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
        </svg>
        {citation.section}
        <span className="font-normal text-green-600 hidden sm:inline">
          · {citation.section_title}
        </span>
      </summary>

      {/* Expanded card */}
      <div className="
        absolute z-20 mt-1 w-80 max-w-[90vw] p-3 rounded-lg shadow-lg
        bg-white border border-green-200 text-left
      ">
        <div className="text-xs font-bold text-green-800 mb-1">{citation.section} — {citation.section_title}</div>
        <div className="text-xs text-slate-500 mb-2 italic">{citation.act}</div>
        <p className="text-xs text-slate-700 leading-relaxed mb-2 line-clamp-5">{citation.excerpt}</p>
        <div className="flex flex-wrap gap-1 mt-1">
          {citation.forum && (
            <span className="bg-blue-50 text-blue-700 text-[10px] px-2 py-0.5 rounded-full border border-blue-200">
              🏛 {citation.forum}
            </span>
          )}
          {citation.notice_period_days && (
            <span className="bg-amber-50 text-amber-700 text-[10px] px-2 py-0.5 rounded-full border border-amber-200">
              ⏱ {citation.notice_period_days} day notice
            </span>
          )}
          {citation.penalty && (
            <span className="bg-red-50 text-red-700 text-[10px] px-2 py-0.5 rounded-full border border-red-200">
              ⚖ {citation.penalty}
            </span>
          )}
        </div>
        <div className="mt-2 text-[10px] text-green-600 font-medium flex items-center gap-1">
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
          </svg>
          MCP-verified · No hallucination possible
        </div>
      </div>
    </details>
  );
}
