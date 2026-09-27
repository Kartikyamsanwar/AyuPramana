import { useState } from "react";
import { escalate, getSessionId } from "../api";
import { useT } from "../i18n";
import type { Language, SingleJurisdiction } from "../types";

/** "Talk to an IP facilitator": logs a request (with an optional, PII-scrubbed note) and shows a reference. */
export function EscalateButton({
  queryId,
  jurisdiction,
  language,
  emphasised,
}: {
  queryId: number | null;
  jurisdiction: SingleJurisdiction;
  language: Language;
  emphasised: boolean;
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    try {
      const result = await escalate({ session_id: getSessionId(), query_id: queryId, jurisdiction, language, note });
      setStatus({ ok: true, text: result.message });
      setOpen(false);
    } catch {
      setStatus({ ok: false, text: t("requestFailed") });
    } finally {
      setBusy(false);
    }
  }

  if (status?.ok) {
    return (
      <p role="status" className="rounded-lg bg-leaf-50 px-3 py-2 text-sm text-leaf-800">
        {status.text}
      </p>
    );
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
          emphasised
            ? "bg-turmeric-400 text-leaf-900 hover:bg-turmeric-600 hover:text-white"
            : "border border-stone-300 text-stone-700 hover:bg-stone-100"
        }`}
      >
        {t("talkToFacilitator")}
      </button>
    );
  }

  return (
    <div className="w-full space-y-2 rounded-lg border border-stone-200 bg-stone-50 p-3">
      <label className="block text-sm font-medium text-stone-700">
        {t("escalateNoteLabel")}
        <textarea
          value={note}
          onChange={(event) => setNote(event.target.value)}
          maxLength={1000}
          rows={2}
          className="mt-1 w-full rounded-md border border-stone-300 bg-white p-2 text-sm font-normal"
        />
      </label>
      <p className="text-xs text-stone-500">{t("escalateNoPii")}</p>
      {status && !status.ok && <p className="text-xs text-red-700">{status.text}</p>}
      <div className="flex gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => void submit()}
          className="rounded-lg bg-leaf-700 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
        >
          {t("sendRequest")}
        </button>
        <button type="button" onClick={() => setOpen(false)} className="rounded-lg px-3 py-1.5 text-sm text-stone-600">
          {t("cancel")}
        </button>
      </div>
    </div>
  );
}
