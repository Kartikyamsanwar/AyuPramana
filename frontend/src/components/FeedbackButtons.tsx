import { useState } from "react";
import { getSessionId, sendFeedback } from "../api";
import { useT } from "../i18n";
import type { SingleJurisdiction } from "../types";

/** 👍 / 👎 on an answer. A thumbs-down offers an optional comment (PII is scrubbed server-side). */
export function FeedbackButtons({ queryId, jurisdiction }: { queryId: number | null; jurisdiction: SingleJurisdiction }) {
  const t = useT();
  const [state, setState] = useState<"idle" | "comment" | "sent">("idle");
  const [comment, setComment] = useState("");

  async function send(rating: "up" | "down", text = "") {
    try {
      await sendFeedback({ session_id: getSessionId(), query_id: queryId, jurisdiction, rating, comment: text });
    } finally {
      setState("sent");
    }
  }

  if (state === "sent") return <span className="text-xs text-leaf-700">{t("feedbackThanks")}</span>;

  if (state === "comment") {
    return (
      <form
        className="flex w-full gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void send("down", comment);
        }}
      >
        <input
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          maxLength={1000}
          placeholder={t("feedbackCommentPlaceholder")}
          aria-label={t("feedbackCommentPlaceholder")}
          className="min-w-0 flex-1 rounded-md border border-stone-300 px-2 py-1 text-sm"
        />
        <button type="submit" className="rounded-md bg-leaf-700 px-3 py-1 text-sm text-white">
          {t("submit")}
        </button>
      </form>
    );
  }

  return (
    <div className="flex gap-1">
      <button
        type="button"
        onClick={() => void send("up")}
        aria-label={t("helpful")}
        title={t("helpful")}
        className="rounded-md px-2 py-1 text-sm hover:bg-stone-100"
      >
        👍
      </button>
      <button
        type="button"
        onClick={() => setState("comment")}
        aria-label={t("notHelpful")}
        title={t("notHelpful")}
        className="rounded-md px-2 py-1 text-sm hover:bg-stone-100"
      >
        👎
      </button>
    </div>
  );
}
