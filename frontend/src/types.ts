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
}

export interface ChatResponse {
  query_id: number | null;
  answers: Partial<Record<SingleJurisdiction, AnswerBlock>>;
  disclaimer: string;
  language: Language;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  language: Language;
  jurisdiction: Jurisdiction;
}

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
