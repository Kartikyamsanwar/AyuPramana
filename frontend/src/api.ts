/** Thin wrappers around the backend REST API. All paths are relative, so the dev proxy / nginx handle routing. */
import type { HealthInfo } from "./types";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${path} failed: ${response.status}`);
  return (await response.json()) as T;
}

export const fetchHealth = () => getJson<HealthInfo>("/api/health");
