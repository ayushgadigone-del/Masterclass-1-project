"use client";

export interface SampleCase {
  label: string;
  category: "unpaid_wages" | "consumer_fraud" | "security_deposit";
  messages: string[];
  facts: {
    claimant_name: string;
    respondent_name: string;
    incident_date: string;
    claim_amount_inr: number;
    evidence_summary: string;
  };
}

export const SAMPLE_CASES: Record<string, SampleCase> = {
  wage_theft: {
    label: "⚡ Load Sample Wage Theft Case",
    category: "unpaid_wages",
    messages: [
      "My name is Ramesh Kumar. I worked at ABC Garments Pvt Ltd as a machine operator.",
      "My employer did not pay my salary for the last 3 months after I resigned on 15 January 2024.",
      "The total unpaid amount is Rs. 45,000. I have salary slips and bank statement as evidence.",
    ],
    facts: {
      claimant_name: "Ramesh Kumar",
      respondent_name: "ABC Garments Pvt Ltd",
      incident_date: "2024-01-15",
      claim_amount_inr: 45000,
      evidence_summary: "Salary slips for Nov 2023–Jan 2024, bank statements showing non-payment, resignation letter",
    },
  },
  consumer_fraud: {
    label: "🛒 Load Sample Consumer Fraud Case",
    category: "consumer_fraud",
    messages: [
      "My name is Priya Sharma. I bought a washing machine from QuickMart Pvt Ltd on 15 March 2024.",
      "The machine stopped working after 2 weeks. They are refusing to refund or replace it.",
      "I paid Rs. 25,000. I have the purchase receipt, photos of defect, and WhatsApp screenshots.",
    ],
    facts: {
      claimant_name: "Priya Sharma",
      respondent_name: "QuickMart Pvt Ltd",
      incident_date: "2024-03-15",
      claim_amount_inr: 25000,
      evidence_summary: "Purchase receipt No. 4521, defect photos, WhatsApp screenshots with seller",
    },
  },
  security_deposit: {
    label: "🏠 Load Sample Security Deposit Case",
    category: "security_deposit",
    messages: [
      "My name is Ananya Singh. I vacated my flat from Suresh Properties on 10 February 2024.",
      "My landlord is refusing to return my security deposit of Rs. 60,000 deposited 2 years ago.",
      "I have the rent agreement, vacating receipts, and messages where the landlord admits holding the deposit.",
    ],
    facts: {
      claimant_name: "Ananya Singh",
      respondent_name: "Suresh Properties",
      incident_date: "2024-02-10",
      claim_amount_inr: 60000,
      evidence_summary: "Rent agreement, vacating receipt, WhatsApp messages with landlord, bank transfer proof",
    },
  },
};

interface Props {
  variant?: keyof typeof SAMPLE_CASES;
  onLoad: (sample: SampleCase) => void;
}

export function SampleCaseButton({ variant = "wage_theft", onLoad }: Props) {
  const sample = SAMPLE_CASES[variant];
  return (
    <button
      type="button"
      onClick={() => onLoad(sample)}
      className="
        flex items-center gap-2 px-4 py-2 rounded-lg border
        border-blue-200 bg-blue-50 text-blue-700 text-sm font-medium
        hover:bg-blue-100 transition-colors
        focus-visible:ring-2 focus-visible:ring-blue-400
      "
      aria-label={`${sample.label} — pre-fills the intake form for fast testing`}
    >
      {sample.label}
    </button>
  );
}
