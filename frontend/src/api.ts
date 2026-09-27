/** Thin wrappers around the backend REST API. All paths are relative, so the dev proxy / nginx handle routing. */
import type { ChatRequest, ChatResponse, HealthInfo, Language, SingleJurisdiction, SourceDocument } from "./types";

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

/**
 * POST /api/chat/stream and parse server-sent events. `onStatus` receives progress stages;
 * resolves with the final response. Throws if streaming isn't available (callers fall back to sendChat).
 */
export async function streamChat(request: ChatRequest, onStatus: (stage: string) => void): Promise<ChatResponse> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok || !response.body) throw new Error(`stream failed: ${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) >= 0) {
      const raw = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const event = /^event: (.*)$/m.exec(raw)?.[1];
      const data = /^data: (.*)$/m.exec(raw)?.[1];
      if (!event || data === undefined) continue;
      const parsed = JSON.parse(data);
      if (event === "done") return parsed as ChatResponse;
      if (event === "error") throw new Error(parsed.message ?? "stream error");
      if (event === "status" && parsed.stage) onStatus(parsed.stage);
    }
  }
  throw new Error("stream ended without a response");
}

export const escalate = (body: {
  session_id: string;
  query_id: number | null;
  jurisdiction: SingleJurisdiction;
  language: Language;
  note: string;
}) => postJson<{ status: string; reference: string; message: string }>("/api/escalate", body);

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
