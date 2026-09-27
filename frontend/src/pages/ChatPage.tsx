import { useState } from "react";
import { useT } from "../i18n";

/** Chat screen. Phase 1: empty state with starter prompts; sending is enabled in Phase 2. */
export function ChatPage() {
  const t = useT();
  const [draft, setDraft] = useState("");

  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col px-4">
      <section className="flex flex-1 flex-col items-center justify-center py-10 text-center">
        <h2 className="text-2xl font-semibold text-leaf-800">{t("emptyTitle")}</h2>
        <p className="mt-3 max-w-xl text-stone-600">{t("emptyBody")}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {(["starter1", "starter2"] as const).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setDraft(t(key))}
              className="rounded-full border border-leaf-100 bg-white px-4 py-2 text-sm text-leaf-700 shadow-sm hover:bg-leaf-50"
            >
              {t(key)}
            </button>
          ))}
        </div>
      </section>

      <form className="sticky bottom-0 bg-stone-50 pb-4" onSubmit={(event) => event.preventDefault()}>
        <div className="flex gap-2 rounded-xl border border-stone-200 bg-white p-2 shadow-sm">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={t("inputPlaceholder")}
            aria-label={t("inputPlaceholder")}
            className="min-w-0 flex-1 bg-transparent px-2 outline-none"
          />
          <button type="submit" disabled className="rounded-lg bg-leaf-700 px-4 py-2 text-white disabled:opacity-50">
            {t("send")}
          </button>
        </div>
        <p className="mt-2 text-center text-xs text-stone-500">{t("chatComingSoon")}</p>
      </form>
    </div>
  );
}
