import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Citation } from "../types";

/**
 * Renders answer Markdown. Citation markers like [S2] become clickable chips.
 * Raw HTML in the answer is not rendered (react-markdown escapes it), which blocks injected markup.
 */
export function Markdown({
  text,
  citations,
  onCite,
}: {
  text: string;
  citations: Citation[];
  onCite: (citation: Citation) => void;
}) {
  const withLinks = text.replace(/\[S(\d+)\]/g, (_, n) => `[S${n}](#cite-${n})`);
  return (
    <div className="prose-answer text-[15px] leading-relaxed text-stone-800">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => {
            const match = href?.match(/^#cite-(\d+)$/);
            if (match) {
              const citation = citations.find((c) => c.marker === Number(match[1]));
              if (!citation) return null;
              return (
                <button
                  type="button"
                  onClick={() => onCite(citation)}
                  title={`${citation.doc_title} — ${citation.section_ref}`}
                  className="mx-0.5 inline-flex -translate-y-0.5 items-center rounded bg-leaf-100 px-1.5 text-[11px] font-semibold text-leaf-800 hover:bg-leaf-600 hover:text-white"
                >
                  {citation.marker}
                </button>
              );
            }
            return (
              <a href={href} target="_blank" rel="noreferrer" className="text-leaf-700 underline">
                {children}
              </a>
            );
          },
          ul: ({ children }) => <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>,
          ol: ({ children }) => <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>,
          p: ({ children }) => <p className="my-2">{children}</p>,
          h3: ({ children }) => <h3 className="mt-3 mb-1 font-semibold text-leaf-800">{children}</h3>,
          h4: ({ children }) => <h4 className="mt-3 mb-1 font-semibold text-leaf-800">{children}</h4>,
        }}
      >
        {withLinks}
      </ReactMarkdown>
    </div>
  );
}
