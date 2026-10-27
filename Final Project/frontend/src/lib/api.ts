// API client — thin wrappers over fetch, base URL from env
import type {
  IntakeMessage,
  IntakeResponse,
  NoticeGenerateResponse,
  ClinicVerifyRequest,
  ClinicVerifyResponse,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function post<T>(path: string, body: unknown, token?: string): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { method: "POST", headers, body: JSON.stringify(body) });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail?.detail ?? res.statusText);
  }
  return res.json();
}

async function patch<T>(path: string, body: unknown, token?: string): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { method: "PATCH", headers, body: JSON.stringify(body) });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail?.detail ?? res.statusText);
  }
  return res.json();
}

export const api = {
  submitMessage: (body: IntakeMessage) =>
    post<IntakeResponse>("/api/intake/message", body),

  generateNotice: (case_id: string) =>
    post<NoticeGenerateResponse>("/api/notice/generate", { case_id }),

  login: (username: string, password: string) =>
    post<{ access_token: string; reviewer_id: string; role: string }>(
      "/api/auth/login", { username, password }
    ),

  verifyNotice: (case_id: string, body: ClinicVerifyRequest, token: string) =>
    patch<ClinicVerifyResponse>(`/api/clinic/verify/${case_id}`, body, token),
};
