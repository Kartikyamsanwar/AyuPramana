/**
 * UI strings and a tiny translation context.
 * Add a key to `en` first; other languages fall back to English for missing keys.
 */
import { createContext, useContext, type ReactNode } from "react";
import type { Language } from "./types";

const en = {
  appTagline: "Source-cited IP & regulatory guidance for Ayurveda",
  psLabel: "IP-SAKTI Sahayak · SIH26045",
  jurisdiction: "Jurisdiction",
  india: "India",
  international: "International",
  both: "Both",
  language: "Language",
  backendOnline: "Backend online",
  backendOffline: "Backend offline",
  llmNotConfigured: "LLM not configured",
  emptyTitle: "Ask about protecting or approving an Ayurvedic product",
  emptyBody:
    "Every answer cites the exact provision it comes from. If the sources don't answer your question, the assistant says so.",
  starter1: "Can I patent a classical Ayurvedic formulation?",
  starter2: "What approvals do I need to use a medicinal plant commercially?",
  inputPlaceholder: "Type your question…",
  send: "Send",
  chatComingSoon: "Chat becomes available once the document corpus is ingested.",
};

export type StringKey = keyof typeof en;
type Strings = Record<StringKey, string>;

const dictionaries: Record<Language, Partial<Strings>> = {
  en,
  hi: {},
  mr: {},
};

export const LANGUAGE_NAMES: Record<Language, string> = {
  en: "English",
  hi: "हिंदी",
  mr: "मराठी",
};

const I18nContext = createContext<Language>("en");

export function I18nProvider({ language, children }: { language: Language; children: ReactNode }) {
  return <I18nContext.Provider value={language}>{children}</I18nContext.Provider>;
}

/** Returns a `t(key)` function for the current UI language. */
export function useT() {
  const language = useContext(I18nContext);
  return (key: StringKey): string => dictionaries[language][key] ?? en[key];
}
