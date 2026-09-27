import { useEffect, useState } from "react";
import { fetchHealth } from "./api";
import { Header, type Page } from "./components/Header";
import { I18nProvider } from "./i18n";
import { AdminPage } from "./pages/AdminPage";
import { ChatPage } from "./pages/ChatPage";
import { SourcesPage } from "./pages/SourcesPage";
import type { HealthInfo, Jurisdiction, Language } from "./types";

function pageFromHash(): Page {
  const hash = window.location.hash;
  if (hash.startsWith("#/sources")) return "sources";
  if (hash.startsWith("#/admin")) return "admin";
  return "chat";
}

export default function App() {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>("india");
  const [language, setLanguage] = useState<Language>("en");
  const [page, setPage] = useState<Page>(pageFromHash);
  // undefined = still checking, null = unreachable
  const [health, setHealth] = useState<HealthInfo | null | undefined>(undefined);

  useEffect(() => {
    fetchHealth().then(setHealth, () => setHealth(null));
    const onHash = () => setPage(pageFromHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  return (
    <I18nProvider language={language}>
      <div className="flex h-full flex-col">
        <Header
          jurisdiction={jurisdiction}
          onJurisdictionChange={setJurisdiction}
          language={language}
          onLanguageChange={setLanguage}
          health={health}
          page={page}
        />
        <main className="flex-1 overflow-y-auto">
          {/* The chat stays mounted (hidden) so the conversation survives visits to other pages */}
          <div className={page === "chat" ? "h-full" : "hidden"}>
            <ChatPage jurisdiction={jurisdiction} language={language} health={health} />
          </div>
          {page === "sources" && <SourcesPage />}
          {page === "admin" && <AdminPage />}
        </main>
      </div>
    </I18nProvider>
  );
}
