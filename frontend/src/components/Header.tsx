import { useT } from "../i18n";
import type { HealthInfo, Jurisdiction, Language } from "../types";
import { JurisdictionToggle } from "./JurisdictionToggle";
import { LanguageSelector } from "./LanguageSelector";

export type Page = "chat" | "sources" | "admin";

interface HeaderProps {
  jurisdiction: Jurisdiction;
  onJurisdictionChange: (value: Jurisdiction) => void;
  language: Language;
  onLanguageChange: (value: Language) => void;
  health: HealthInfo | null | undefined;
  page: Page;
}

/** Top bar: brand, page tabs, jurisdiction toggle, language selector and backend status. */
export function Header({ jurisdiction, onJurisdictionChange, language, onLanguageChange, health, page }: HeaderProps) {
  const t = useT();
  const online = Boolean(health);
  const tabs: { page: Page; href: string; label: string }[] = [
    { page: "chat", href: "#/", label: t("navChat") },
    { page: "sources", href: "#/sources", label: t("navSources") },
  ];
  if (health?.features?.admin_mode) tabs.push({ page: "admin", href: "#/admin", label: t("navAdmin") });
  return (
    <header className="bg-leaf-800 text-white shadow">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
        <div className="mr-auto min-w-0">
          <h1 className="text-xl font-bold tracking-tight">
            Ayu<span className="text-turmeric-400">Pramana</span>
          </h1>
          <p className="truncate text-xs text-leaf-100">{t("psLabel")}</p>
        </div>
        <nav aria-label="Main" className="flex gap-1">
          {tabs.map((tab) => (
            <a
              key={tab.page}
              href={tab.href}
              aria-current={page === tab.page ? "page" : undefined}
              className={`rounded-md px-3 py-1.5 text-sm ${
                page === tab.page ? "bg-white/15 font-semibold text-white" : "text-leaf-100 hover:bg-white/10"
              }`}
            >
              {tab.label}
            </a>
          ))}
        </nav>
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
