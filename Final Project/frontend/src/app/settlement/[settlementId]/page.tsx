// Server component — exports generateStaticParams for static export compatibility.
// "use client" must NOT appear here.
import SettlementDemoPage from "../demo/page";
import { Suspense } from "react";

// Required for `output: "export"` — at least one path must be pre-rendered.
export function generateStaticParams() {
  return [{ settlementId: "demo" }];
}

export default function SettlementDynamicPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-400">Loading settlement…</div>}>
      <SettlementDemoPage />
    </Suspense>
  );
}
