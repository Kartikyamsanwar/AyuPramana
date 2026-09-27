import { useEffect, useRef } from "react";
import { useT } from "../i18n";
import type { Citation } from "../types";

/** Side panel (bottom sheet on phones) showing the exact source text behind a citation. */
export function CitationPanel({ citation, onClose }: { citation: Citation | null; onClose: () => void }) {
  const t = useT();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!citation) return;
    closeRef.current?.focus();
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [citation, onClose]);

  if (!citation) return null;
  const jurisdictionKey = citation.jurisdiction === "india" ? "india" : "international";

  return (
    <div className="fixed inset-0 z-40 flex justify-end" role="dialog" aria-modal="true" aria-label={t("sourceDetails")}>
      <button type="button" aria-label={t("close")} onClick={onClose} className="absolute inset-0 bg-black/30" />
      <aside className="relative mt-auto flex max-h-[85vh] w-full flex-col rounded-t-2xl bg-white shadow-xl sm:mt-0 sm:h-full sm:max-h-none sm:max-w-md sm:rounded-none">
        <div className="flex items-start justify-between gap-3 border-b border-stone-200 p-4">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-turmeric-600">
              [{citation.marker}] {t(jurisdictionKey)}
            </p>
            <h2 className="mt-1 font-semibold text-leaf-900">{citation.section_ref}</h2>
            <p className="text-sm text-stone-600">{citation.doc_title}</p>
          </div>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-sm text-stone-600 hover:bg-stone-100"
          >
            {t("close")} ✕
          </button>
        </div>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-2 border-b border-stone-200 p-4 text-sm">
          <dt className="text-stone-500">{t("versionDate")}</dt>
          <dd>{citation.version_date}</dd>
          <dt className="text-stone-500">{t("fileVersion")}</dt>
          <dd className="font-mono text-xs">{citation.version}</dd>
          {citation.page != null && (
            <>
              <dt className="text-stone-500">{t("page")}</dt>
              <dd>{citation.page}</dd>
            </>
          )}
          <dt className="text-stone-500">{t("document")}</dt>
          <dd className="truncate font-mono text-xs" title={citation.file}>
            {citation.file}
          </dd>
        </dl>
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">{t("sourceText")}</h3>
          <p className="whitespace-pre-wrap rounded-lg bg-stone-50 p-3 font-serif text-sm leading-relaxed text-stone-800">
            {citation.snippet}
          </p>
        </div>
        <div className="border-t border-stone-200 p-4">
          {citation.source_url ? (
            <a
              href={citation.source_url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex rounded-lg bg-leaf-700 px-4 py-2 text-sm font-medium text-white hover:bg-leaf-800"
            >
              {t("openOfficialSource")} ↗
            </a>
          ) : (
            <p className="text-sm text-stone-500">{t("noSourceUrl")}</p>
          )}
        </div>
      </aside>
    </div>
  );
}
