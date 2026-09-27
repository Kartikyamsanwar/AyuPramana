/** Thin wrappers around the backend REST API. All paths are relative, so the dev proxy / nginx handle routing. */
import type { ChatRequest, ChatResponse, HealthInfo, SourceDocument } from "./types";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} failed: ${response.status}`);
  return (await response.json()) as T;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`${path} failed: ${response.status}`);
  return (await response.json()) as T;
}

export const fetchHealth = () => getJson<HealthInfo>("/api/health");
export const fetchSources = () => getJson<{ documents: SourceDocument[]; manifest_error: string | null }>("/api/sources");
export const sendChat = (request: ChatRequest) => postJson<ChatResponse>("/api/chat", request);

/** Anonymous id for this browser tab — never tied to a person. */
export function getSessionId(): string {
  const make = () =>
    (globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`).replace(/[^A-Za-z0-9_-]/g, "");
  try {
    const existing = sessionStorage.getItem("ayupramana-session");
    if (existing) return existing;
    const created = make();
    sessionStorage.setItem("ayupramana-session", created);
    return created;
  } catch {
    return make();
  }
}
