/** Shapes shared between the UI and the backend API. */

export type Jurisdiction = "india" | "international" | "both";
export type SingleJurisdiction = "india" | "international";
export type Language = "en" | "hi" | "mr";

export interface HealthInfo {
  status: string;
  app: string;
  version: string;
  llm: { provider: string; model: string; configured: boolean };
  embedding_model: string;
  corpus: { raw_files: number; manifest_entries: number; documents: number; chunks: number };
  features: { admin_mode: boolean; reranker: boolean; citation_verification: boolean; translator: string | null };
}

export interface Citation {
  marker: number;
  chunk_id: string;
  doc_id: string;
  doc_title: string;
  section_ref: string;
  jurisdiction: SingleJurisdiction;
  version_date: string;
  version: string;
  source_url: string;
  file: string;
  page: number | null;
  snippet: string;
}

export interface AnswerBlock {
  jurisdiction: SingleJurisdiction;
  markdown: string;
  citations: Citation[];
  confidence: number;
  confidence_label: "high" | "medium" | "low";
  abstained: boolean;
  abstain_reason: string | null;
  mode: "generated" | "extractive" | "abstained";
  escalation_suggested: boolean;
  signals: Record<string, number>;
}

export interface QuickReply {
  id: string;
  label: string;
}

export interface ChatResponse {
  query_id: number | null;
  answers: Partial<Record<SingleJurisdiction, AnswerBlock>>;
  follow_up_question?: string | null;
  quick_replies?: QuickReply[];
  notice?: string | null;
  intents?: string[];
  disclaimer: string;
  language: Language;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  language: Language;
  jurisdiction: Jurisdiction;
  quick_reply_id?: string;
}

export type ProgressStage = "routing" | "retrieving" | "writing" | "verifying" | "translating";

export type ChatTurn =
  | { id: string; role: "user"; text: string }
  | { id: string; role: "assistant"; response: ChatResponse }
  | { id: string; role: "error"; text: string };

export interface SourceVersion {
  version: string;
  version_date: string;
  ingested_at: string;
  chunk_count: number;
  active: boolean;
}

export interface SourceDocument {
  id: string;
  title: string;
  jurisdiction: SingleJurisdiction;
  domain: string;
  doc_type: string;
  source_url: string;
  file: string;
  status: "ingested" | "pending" | "missing_file" | "removed_from_manifest";
  active_version: SourceVersion | null;
  versions: SourceVersion[];
}

export interface AdminOverview {
  stats: {
    queries: number;
    abstention_rate: number | null;
    avg_confidence: number | null;
    feedback_up: number;
    feedback_down: number;
    escalations: number;
    by_language: Record<string, number>;
  };
  queries: {
    id: number;
    created_at: string;
    language: string;
    jurisdiction: string;
    query_text: string;
    intents: string[];
    blocks: Record<string, { confidence: number; abstained: boolean; reason: string | null; mode: string; citations: string[] }>;
    min_confidence: number | null;
    abstained: boolean;
    latency_ms: number;
    llm_provider: string;
    source: string;
  }[];
  feedback: { id: number; query_id: number | null; jurisdiction: string | null; rating: string; comment: string; created_at: string }[];
  escalations: {
    id: number;
    reference: string;
    query_id: number | null;
    jurisdiction: string | null;
    language: string;
    note: string;
    status: string;
    created_at: string;
  }[];
}
