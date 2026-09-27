import type { ChatResponse, Citation, QuickReply, SingleJurisdiction } from "../types";
import { AnswerCard } from "./AnswerCard";
import { Markdown } from "./Markdown";

const ORDER: SingleJurisdiction[] = ["india", "international"];
const SCOPE_REASONS = new Set(["out_of_scope_medical", "off_topic"]);

/**
 * An assistant reply: optional notice, per-jurisdiction answer cards (India and International
 * side by side, never merged), and an optional follow-up question with quick-reply buttons.
 */
export function AssistantTurn({
  response,
  onCite,
  onQuickReply,
  active,
}: {
  response: ChatResponse;
  onCite: (citation: Citation) => void;
  onQuickReply: (reply: QuickReply) => void;
  active: boolean;
}) {
  let blocks = ORDER.map((key) => response.answers[key]).filter((b) => b !== undefined);
  // An out-of-scope refusal is the same for every jurisdiction: show it once
  if (blocks.length > 1 && blocks.every((b) => b.abstained && SCOPE_REASONS.has(b.abstain_reason ?? ""))) {
    blocks = blocks.slice(0, 1);
  }
  const replies = response.quick_replies ?? [];

  return (
    <div className="space-y-3">
      {response.notice && (
        <p role="note" className="rounded-lg border border-turmeric-400/60 bg-turmeric-100 px-4 py-2 text-sm text-stone-800">
          {response.notice}
        </p>
      )}

      {blocks.length > 0 && (
        <div className={`grid gap-3 ${blocks.length > 1 ? "md:grid-cols-2" : ""}`}>
          {blocks.map((block) => (
            <AnswerCard
              key={block.jurisdiction}
              block={block}
              disclaimer={response.disclaimer}
              queryId={response.query_id}
              language={response.language}
              onCite={onCite}
            />
          ))}
        </div>
      )}

      {response.follow_up_question && (
        <div className="max-w-[90%] rounded-2xl rounded-bl-sm border border-stone-200 bg-white px-4 py-2 shadow-sm">
          <Markdown text={response.follow_up_question} citations={[]} onCite={onCite} />
          {replies.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2 pb-1" role="group">
              {replies.map((reply) => (
                <button
                  key={reply.id}
                  type="button"
                  disabled={!active}
                  onClick={() => onQuickReply(reply)}
                  className={`rounded-full border px-3 py-1.5 text-sm transition disabled:cursor-default disabled:opacity-50 ${
                    reply.id === "flow:cancel"
                      ? "border-stone-300 text-stone-600 hover:bg-stone-100"
                      : "border-leaf-600 text-leaf-700 hover:bg-leaf-600 hover:text-white"
                  }`}
                >
                  {reply.label}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
