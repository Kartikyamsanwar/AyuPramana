import { useT } from "../i18n";
import type { AnswerBlock, Citation } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { Markdown } from "./Markdown";

/** One jurisdiction's answer: text with citation chips, source list, confidence and disclaimer. */
export function AnswerCard({
  block,
  disclaimer,
  onCite,
}: {
  block: AnswerBlock;
  disclaimer: string;
  onCite: (citation: Citation) => void;
}) {
  const t = useT();
  const accent = block.jurisdiction === "india" ? "border-t-turmeric-400" : "border-t-sky-500";
  return (
    <article
      aria-label={t(block.jurisdiction)}
      className={`flex flex-col rounded-xl border border-t-4 border-stone-200 bg-white shadow-sm ${accent}`}
    >
      <header className="flex flex-wrap items-center justify-between gap-2 px-4 pt-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-stone-600">{t(block.jurisdiction)}</h3>
        <div className="flex items-center gap-2">
          {block.mode === "extractive" && (
            <span className="rounded-full bg-stone-100 px-2.5 py-0.5 text-xs text-stone-600">{t("quotedSources")}</span>
          )}
          <ConfidenceBadge block={block} />
        </div>
      </header>

      <div className="px-4">
        <Markdown text={block.markdown} citations={block.citations} onCite={onCite} />
      </div>

      {block.citations.length > 0 && (
        <div className="px-4 pb-2">
          <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-stone-500">{t("sources")}</h4>
          <ul className="flex flex-wrap gap-1.5">
            {block.citations.map((citation) => (
              <li key={citation.marker}>
                <button
                  type="button"
                  onClick={() => onCite(citation)}
                  className="flex max-w-[18rem] items-center gap-1.5 rounded-full border border-leaf-100 bg-leaf-50 px-2.5 py-1 text-left text-xs text-leaf-800 hover:border-leaf-600"
                >
                  <span className="font-semibold">{citation.marker}</span>
                  <span className="truncate">
                    {citation.section_ref} · {citation.doc_title}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <footer className="mt-auto border-t border-stone-100 px-4 py-2 text-xs text-stone-500">{disclaimer}</footer>
    </article>
  );
}
