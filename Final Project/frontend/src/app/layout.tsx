import type { Metadata } from "next";
import "./globals.css";
import { RoleSwitcher } from "@/components/RoleSwitcher";

export const metadata: Metadata = {
  title: "Legal Rights Navigator",
  description: "SDG 16 Pre-Litigation Engine — Citizen Legal Aid",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <RoleSwitcher />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-slate-200 py-3 text-center text-xs text-slate-400">
          Legal Rights Navigator &mdash; SDG 16 LegalTech MVP &mdash; Pre-litigation only, not legal advice
        </footer>
      </body>
    </html>
  );
}
