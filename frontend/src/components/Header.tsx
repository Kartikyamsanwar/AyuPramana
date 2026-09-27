import { useT } from "../i18n";
import type { HealthInfo, Jurisdiction, Language } from "../types";
import { JurisdictionToggle } from "./JurisdictionToggle";
import { LanguageSelector } from "./LanguageSelector";

interface HeaderProps {
  jurisdiction: Jurisdiction;
  onJurisdictionChange: (value: Jurisdiction) => void;
  language: Language;
  onLanguageChange: (value: Language) => void;
  health: HealthInfo | null | undefined;
}

/** Top bar: brand, backend status, jurisdiction toggle and language selector. */
export function Header({ jurisdiction, onJurisdictionChange, language, onLanguageChange, health }: HeaderProps) {
  const t = useT();
  const online = Boolean(health);
  return (
    <header className="bg-leaf-800 text-white shadow">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <div className="mr-auto min-w-0">
          <h1 className="text-xl font-bold tracking-tight">
            Ayu<span className="text-turmeric-400">Pramana</span>
          </h1>
          <p className="truncate text-xs text-leaf-100">{t("psLabel")}</p>
        </div>
        <JurisdictionToggle value={jurisdiction} onChange={onJurisdictionChange} />
        <LanguageSelector value={language} onChange={onLanguageChange} />
        <span className="flex items-center gap-1.5 text-xs text-leaf-100" aria-live="polite">
          <span
            aria-hidden
            className={`h-2 w-2 rounded-full ${online ? "bg-emerald-300" : health === null ? "bg-red-400" : "bg-stone-400"}`}
          />
          {online ? t("backendOnline") : t("backendOffline")}
          {health && !health.llm.configured && <span className="text-turmeric-400">· {t("llmNotConfigured")}</span>}
        </span>
      </div>
    </header>
  );
}
