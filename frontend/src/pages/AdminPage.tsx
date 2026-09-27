import { useEffect, useState } from "react";
import { fetchAdminOverview } from "../api";
import { useT } from "../i18n";
import type { AdminOverview } from "../types";

const percent = (value: number | null) => (value == null ? "—" : `${Math.round(value * 100)}%`);
const time = (iso: string) => new Date(iso).toLocaleString();

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-stone-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-leaf-800">{value}</p>
    </div>
  );
}

/** Audit view: recent PII-scrubbed questions, confidence, abstentions, feedback and escalations. */
export function AdminPage() {
  const t = useT();
  const [data, setData] = useState<AdminOverview | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetchAdminOverview().then(setData, () => setFailed(true));
  }, []);

  if (failed) return <p className="mx-auto max-w-6xl px-4 py-6 text-stone-600">{t("adminDisabled")}</p>;
  if (!data) return <p className="mx-auto max-w-6xl px-4 py-6 text-stone-500">{t("loading")}</p>;
  const { stats } = data;

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-4 py-6">
      <div>
        <h2 className="text-xl font-semibold text-leaf-800">{t("adminTitle")}</h2>
        <p className="mt-1 text-sm text-stone-600">{t("adminIntro")}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <Stat label={t("statQueries")} value={String(stats.queries)} />
        <Stat label={t("statAbstentionRate")} value={percent(stats.abstention_rate)} />
        <Stat label={t("statAvgConfidence")} value={stats.avg_confidence == null ? "—" : stats.avg_confidence.toFixed(2)} />
        <Stat label={t("statFeedback")} value={`${stats.feedback_up} / ${stats.feedback_down}`} />
        <Stat label={t("statEscalations")} value={String(stats.escalations)} />
      </div>

      <section>
        <h3 className="mb-2 font-semibold text-stone-700">{t("recentQueries")}</h3>
        <div className="overflow-x-auto rounded-xl border border-stone-200 bg-white">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
              <tr>
                <th className="px-3 py-2">{t("colTime")}</th>
                <th className="px-3 py-2">{t("colQuestion")}</th>
                <th className="px-3 py-2">{t("colLanguage")}</th>
                <th className="px-3 py-2">{t("colResult")}</th>
                <th className="px-3 py-2 text-right">{t("colLatency")}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {data.queries.map((q) => (
                <tr key={q.id} className="align-top">
                  <td className="whitespace-nowrap px-3 py-2 text-xs text-stone-500">
                    #{q.id} · {time(q.created_at)}
                  </td>
                  <td className="px-3 py-2">
                    {q.query_text}
                    {q.intents.length > 0 && <div className="text-xs text-stone-400">{q.intents.join(", ")}</div>}
                  </td>
                  <td className="px-3 py-2">{q.language}</td>
                  <td className="px-3 py-2">
                    {Object.entries(q.blocks).map(([jurisdiction, block]) => (
                      <div key={jurisdiction} className="text-xs">
                        <span className="font-medium">{t(jurisdiction === "india" ? "india" : "international")}:</span>{" "}
                        {block.abstained ? (
                          <span className="text-red-700">
                            {t("abstained")} ({block.reason})
                          </span>
                        ) : (
                          <span className="text-emerald-700">
                            {t("answered")} · {block.confidence.toFixed(2)}
                          </span>
                        )}
                      </div>
                    ))}
                  </td>
                  <td className="px-3 py-2 text-right text-xs">{q.latency_ms} ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <section>
          <h3 className="mb-2 font-semibold text-stone-700">{t("recentFeedback")}</h3>
          <ul className="divide-y divide-stone-100 rounded-xl border border-stone-200 bg-white text-sm">
            {data.feedback.map((f) => (
              <li key={f.id} className="px-3 py-2">
                {f.rating === "up" ? "👍" : "👎"} {f.query_id != null && <span className="text-stone-400">#{f.query_id} </span>}
                {f.comment}
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h3 className="mb-2 font-semibold text-stone-700">{t("recentEscalations")}</h3>
          <ul className="divide-y divide-stone-100 rounded-xl border border-stone-200 bg-white text-sm">
            {data.escalations.map((e) => (
              <li key={e.id} className="px-3 py-2">
                <span className="font-mono text-xs">{e.reference}</span>{" "}
                {e.query_id != null && <span className="text-stone-400">#{e.query_id} </span>}
                {e.note}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
