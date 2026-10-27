"use client";
import { useEffect, useState } from "react";

interface Props {
  /** ISO date string or Date — deadline for the countdown */
  deadline: Date | string;
  /** Label shown beneath the timer */
  label?: string;
  /** Called when the timer reaches zero */
  onExpired?: () => void;
}

function pad(n: number) {
  return String(n).padStart(2, "0");
}

export function CountdownTimer({ deadline, label = "to respond before escalation", onExpired }: Props) {
  const target = typeof deadline === "string" ? new Date(deadline) : deadline;

  const [remaining, setRemaining] = useState(() => Math.max(0, target.getTime() - Date.now()));

  useEffect(() => {
    if (remaining <= 0) {
      onExpired?.();
      return;
    }
    const id = setInterval(() => {
      const r = Math.max(0, target.getTime() - Date.now());
      setRemaining(r);
      if (r === 0) {
        clearInterval(id);
        onExpired?.();
      }
    }, 1000);
    return () => clearInterval(id);
  }, [target, onExpired]);

  const totalSecs = Math.floor(remaining / 1000);
  const days = Math.floor(totalSecs / 86400);
  const hrs  = Math.floor((totalSecs % 86400) / 3600);
  const mins = Math.floor((totalSecs % 3600) / 60);
  const secs = totalSecs % 60;

  const isUrgent = days < 2;
  const isExpired = remaining === 0;

  if (isExpired) {
    return (
      <div className="flex flex-col items-center gap-1 p-4 bg-red-50 border border-red-300 rounded-xl">
        <span className="text-2xl font-bold text-red-600">EXPIRED</span>
        <span className="text-xs text-red-500 font-medium">Escalated to e-Daakhil / Samadhan</span>
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-center gap-2 p-4 rounded-xl border ${
      isUrgent ? "bg-red-50 border-red-300" : "bg-amber-50 border-amber-300"
    }`}>
      <div className="flex items-end gap-2 font-mono">
        <Block value={days} unit="days" urgent={isUrgent} />
        <Colon urgent={isUrgent} />
        <Block value={hrs} unit="hrs" urgent={isUrgent} />
        <Colon urgent={isUrgent} />
        <Block value={mins} unit="min" urgent={isUrgent} />
        <Colon urgent={isUrgent} />
        <Block value={secs} unit="sec" urgent={isUrgent} />
      </div>
      <p className={`text-xs font-semibold ${isUrgent ? "text-red-600" : "text-amber-700"}`}>
        {label}
      </p>
      {isUrgent && (
        <p className="text-[10px] text-red-500 text-center">
          ⚠ Failure to respond will escalate to e-Daakhil / Samadhan portal
        </p>
      )}
    </div>
  );
}

function Block({ value, unit, urgent }: { value: number; unit: string; urgent: boolean }) {
  return (
    <div className="flex flex-col items-center">
      <span className={`text-3xl font-bold tabular-nums leading-none ${urgent ? "text-red-600" : "text-amber-700"}`}>
        {String(value).padStart(2, "0")}
      </span>
      <span className={`text-[10px] uppercase tracking-wider ${urgent ? "text-red-400" : "text-amber-500"}`}>
        {unit}
      </span>
    </div>
  );
}

function Colon({ urgent }: { urgent: boolean }) {
  return (
    <span className={`text-2xl font-bold pb-3 ${urgent ? "text-red-400" : "text-amber-400"}`}>:</span>
  );
}
