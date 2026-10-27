"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const ROLES = [
  { label: "1. Citizen View", href: "/citizen", color: "blue" },
  { label: "2. Law Clinic Reviewer", href: "/clinic", color: "green" },
  { label: "3. Opposing Party Settlement", href: "/settlement/demo", color: "amber" },
  { label: "4. Impact & Unit Economics", href: "/dashboard", color: "violet" },
] as const;

const COLOR_MAP: Record<string, { active: string; hover: string }> = {
  blue:   { active: "bg-blue-600 text-white shadow-sm",   hover: "hover:bg-blue-50 text-blue-700" },
  green:  { active: "bg-green-600 text-white shadow-sm",  hover: "hover:bg-green-50 text-green-700" },
  amber:  { active: "bg-amber-600 text-white shadow-sm",  hover: "hover:bg-amber-50 text-amber-700" },
  violet: { active: "bg-violet-600 text-white shadow-sm", hover: "hover:bg-violet-50 text-violet-700" },
};

export function RoleSwitcher() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 py-2 flex flex-wrap items-center gap-1.5">
        <span className="text-xs font-semibold text-slate-500 mr-2 shrink-0">DEMO ROLE:</span>
        {ROLES.map((r) => {
          const isActive = pathname.startsWith(r.href.replace("/demo", ""));
          const c = COLOR_MAP[r.color];
          return (
            <Link
              key={r.href}
              href={r.href}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors whitespace-nowrap
                ${isActive ? c.active : `bg-slate-100 ${c.hover}`}`}
              aria-current={isActive ? "page" : undefined}
            >
              {r.label}
            </Link>
          );
        })}
        <span className="ml-auto text-xs text-slate-400 hidden sm:inline">⚖️ SDG 16 · Legal Rights Navigator</span>
      </div>
    </header>
  );
}
