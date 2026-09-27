import { useEffect, useState } from "react";
import { fetchSources } from "../api";
import { useT, type StringKey } from "../i18n";
import type { SourceDocument } from "../types";

const STATUS_STYLE: Record<SourceDocument["status"], string> = {
  ingested: "bg-emerald-100 text-emerald-800",
  pending: "bg-amber-100 text-amber-800",
  missing_file: "bg-red-100 text-red-800",
  removed_from_manifest: "bg-stone-200 text-stone-700",
};

/** Corpus documents with jurisdiction, version date and chunk count. */
export function SourcesPage() {
  const t = useT();
  const [data, setData] = useState<{ documents: SourceDocument[]; manifest_error: string | null } | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetchSources().then(setData, () => setFailed(true));
  }, []);

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6">
      <h2 className="text-xl font-semibold text-leaf-800">{t("sourcesTitle")}</h2>
      <p className="mt-1 text-sm text-stone-600">{t("sourcesIntro")}</p>

      {failed && <p className="mt-6 text-red-700">{t("loadFailed")}</p>}
      {!data && !failed && <p className="mt-6 text-stone-500">{t("loading")}</p>}
      {data?.manifest_error && (
        <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800">
          {t("manifestError")}: {data.manifest_error}
        </p>
      )}
      {data && data.documents.length === 0 && <p className="mt-6 text-stone-600">{t("noSources")}</p>}

      {data && data.documents.length > 0 && (
        <div className="mt-4 overflow-x-auto rounded-xl border border-stone-200 bg-white">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
              <tr>
                <th className="px-3 py-2">{t("colDocument")}</th>
                <th className="px-3 py-2">{t("colJurisdiction")}</th>
                <th className="px-3 py-2">{t("colDomain")}</th>
                <th className="px-3 py-2">{t("colType")}</th>
                <th className="px-3 py-2">{t("colVersionDate")}</th>
                <th className="px-3 py-2 text-right">{t("colChunks")}</th>
                <th className="px-3 py-2">{t("colStatus")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {data.documents.map((doc) => (
                <tr key={doc.id}>
                  <td className="px-3 py-2">
                    {doc.source_url ? (
                      <a href={doc.source_url} target="_blank" rel="noreferrer" className="font-medium text-leaf-700 underline">
                        {doc.title}
                      </a>
                    ) : (
                      <span className="font-medium">{doc.title}</span>
                    )}
                    <div className="font-mono text-xs text-stone-400">
                      {doc.id}
                      {doc.active_version && ` · ${doc.active_version.version}`}
                    </div>
                  </td>
                  <td className="px-3 py-2">{t(doc.jurisdiction)}</td>
                  <td className="px-3 py-2">{doc.domain}</td>
                  <td className="px-3 py-2">{doc.doc_type}</td>
                  <td className="px-3 py-2">{doc.active_version?.version_date ?? "—"}</td>
                  <td className="px-3 py-2 text-right">{doc.active_version?.chunk_count ?? "—"}</td>
                  <td className="px-3 py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs ${STATUS_STYLE[doc.status]}`}>
                      {t(`status_${doc.status}` as StringKey)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
