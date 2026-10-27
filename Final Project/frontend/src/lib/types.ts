// Shared TypeScript types mirroring backend Pydantic models

export type DisputeCategory = "unpaid_wages" | "consumer_fraud" | "security_deposit";

export type CaseStatus =
  | "intake_in_progress"
  | "ready_for_notice"
  | "notice_drafted"
  | "pending_clinic_review"
  | "clinic_approved"
  | "clinic_rejected"
  | "notice_sent"
  | "settlement_open"
  | "settled"
  | "escalated";

export interface IntakeMessage {
  case_id?: string;
  message: string;
  dispute_category?: DisputeCategory;
  language?: string;
}

export interface IntakeResponse {
  case_id: string;
  status: CaseStatus;
  follow_up_question: string | null;
  missing_fields: string[];
  collected_facts: Record<string, unknown>;
  message: string;
}

export interface StatuteCitation {
  act: string;
  section: string;
  section_title: string;
  excerpt: string;
  relevance_score: number;
  notice_period_days: number | null;
  penalty: string | null;
  forum: string;
}

export interface NoticeGenerateResponse {
  case_id: string;
  notice_id: string;
  review_status: string;
  plain_language_guide: string;
  draft_body: string;
  citations: StatuteCitation[];
  message: string;
}

export interface ClinicVerifyRequest {
  reviewer_id: string;
  action: "approve" | "reject";
  edited_body?: string;
  reviewer_notes?: string;
}

export interface ClinicVerifyResponse {
  case_id: string;
  notice_id: string;
  review_status: string;
  pdf_path: string | null;
  pdf_hash: string | null;
  settlement_url: string | null;
  message: string;
}
