import { useEffect, useRef, useState, type FormEvent } from "react";
import { getSessionId, sendChat, streamChat } from "../api";
import { AssistantTurn } from "../components/AssistantTurn";
import { CitationPanel } from "../components/CitationPanel";
import { VoiceButton } from "../components/VoiceButton";
import { useT, type StringKey } from "../i18n";
import type { ChatRequest, ChatTurn, Citation, HealthInfo, Jurisdiction, Language, QuickReply } from "../types";

let turnCounter = 0;
const nextId = () => `turn-${++turnCounter}`;

export function ChatPage({
  jurisdiction,
  language,
  health,
}: {
  jurisdiction: Jurisdiction;
  language: Language;
  health: HealthInfo | null | undefined;
}) {
  const t = useT();
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [stage, setStage] = useState<string>("routing");
  const [citation, setCitation] = useState<Citation | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const sessionId = useRef(getSessionId());

  useEffect(() => {
    bottomRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [turns, pending]);

  async function ask(message: string, quickReplyId?: string) {
    const text = message.trim();
    if (!text || pending) return;
    setDraft("");
    setTurns((previous) => [...previous, { id: nextId(), role: "user", text }]);
    setPending(true);
    setStage("routing");
    const request: ChatRequest = { session_id: sessionId.current, message: text, language, jurisdiction };
    if (quickReplyId && !quickReplyId.startsWith("starter:")) request.quick_reply_id = quickReplyId;
    try {
      let response;
      try {
        response = await streamChat(request, setStage);
      } catch {
        response = await sendChat(request); // streaming unavailable (e.g. a proxy buffers it)
      }
      setTurns((previous) => [...previous, { id: nextId(), role: "assistant", response }]);
    } catch {
      setTurns((previous) => [
        ...previous,
        { id: nextId(), role: "error", text: t("errorGeneric"), retry: { message: text, quickReplyId } },
      ]);
    } finally {
      setPending(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void ask(draft);
  }

  const noCorpus = health && health.corpus.chunks === 0;
  const lastAssistantId = [...turns].reverse().find((turn) => turn.role === "assistant")?.id;

  return (
    <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col px-4">
      {turns.length === 0 ? (
        <section className="flex flex-1 flex-col items-center justify-center py-10 text-center">
          <h2 className="text-2xl font-semibold text-leaf-800">{t("emptyTitle")}</h2>
          <p className="mt-3 max-w-xl text-stone-600">{t("emptyBody")}</p>
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {(["starter1", "starter2", "starter3"] as const).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => void ask(t(key))}
                className="rounded-full border border-leaf-100 bg-white px-4 py-2 text-sm text-leaf-700 shadow-sm hover:bg-leaf-50"
              >
                {t(key)}
              </button>
            ))}
          </div>
          {noCorpus && <p className="mt-6 text-sm text-turmeric-600">{t("noCorpusHint")}</p>}
          {health === null && <p className="mt-6 text-sm text-red-700">{t("backendOfflineHint")}</p>}
        </section>
      ) : (
        <section className="flex-1 space-y-4 py-6" aria-live="polite">
          {turns.map((turn) =>
            turn.role === "user" ? (
              <div key={turn.id} className="flex justify-end">
                <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-leaf-700 px-4 py-2 text-white">{turn.text}</p>
              </div>
            ) : turn.role === "assistant" ? (
              <AssistantTurn
                key={turn.id}
                response={turn.response}
                onCite={setCitation}
                onQuickReply={(reply: QuickReply) => void ask(reply.label, reply.id)}
                active={!pending && turn.id === lastAssistantId}
              />
            ) : (
              <div key={turn.id} role="alert" className="flex items-center gap-3 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700">
                <span className="flex-1">{turn.text}</span>
                {turn.retry && (
                  <button
                    type="button"
                    disabled={pending}
                    onClick={() => void ask(turn.retry!.message, turn.retry!.quickReplyId)}
                    className="rounded-md border border-red-300 px-2 py-1 text-xs font-medium hover:bg-red-100"
                  >
                    {t("retry")}
                  </button>
                )}
              </div>
            ),
          )}
          {pending && (
            <p className="flex items-center gap-2 text-sm text-stone-500">
              <span className="h-2 w-2 animate-pulse rounded-full bg-leaf-600" />
              {t(`stage_${stage}` as StringKey) ?? t("thinking")}
            </p>
          )}
          <div ref={bottomRef} />
        </section>
      )}

      <form className="sticky bottom-0 bg-stone-50 pb-4 pt-2" onSubmit={onSubmit}>
        <div className="flex gap-2 rounded-xl border border-stone-200 bg-white p-2 shadow-sm focus-within:border-leaf-600">
          <input
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder={t("inputPlaceholder")}
            aria-label={t("inputPlaceholder")}
            maxLength={2000}
            className="min-w-0 flex-1 bg-transparent px-2 outline-none"
          />
          <VoiceButton language={language} onText={(text) => setDraft(text)} />
          <button
            type="submit"
            disabled={pending || !draft.trim()}
            className="rounded-lg bg-leaf-700 px-4 py-2 font-medium text-white hover:bg-leaf-800 disabled:opacity-50"
          >
            {t("send")}
          </button>
        </div>
      </form>

      <CitationPanel citation={citation} onClose={() => setCitation(null)} />
    </div>
  );
}
