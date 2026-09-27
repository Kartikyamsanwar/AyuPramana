import { useEffect, useState } from "react";
import { fetchHealth } from "./api";
import { Header } from "./components/Header";
import { I18nProvider } from "./i18n";
import { ChatPage } from "./pages/ChatPage";
import type { HealthInfo, Jurisdiction, Language } from "./types";

export default function App() {
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>("india");
  const [language, setLanguage] = useState<Language>("en");
  // undefined = still checking, null = unreachable
  const [health, setHealth] = useState<HealthInfo | null | undefined>(undefined);

  useEffect(() => {
    fetchHealth().then(setHealth, () => setHealth(null));
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
        />
        <main className="flex-1 overflow-y-auto">
          <ChatPage jurisdiction={jurisdiction} language={language} health={health} />
        </main>
      </div>
    </I18nProvider>
  );
}
