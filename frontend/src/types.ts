/** Shapes shared between the UI and the backend API. */

export type Jurisdiction = "india" | "international" | "both";
export type Language = "en" | "hi" | "mr";

export interface HealthInfo {
  status: string;
  app: string;
  version: string;
  llm: { provider: string; model: string; configured: boolean };
  embedding_model: string;
  corpus: { raw_files: number };
}
