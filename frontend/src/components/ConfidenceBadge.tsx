import { useT, type StringKey } from "../i18n";
import type { AnswerBlock } from "../types";

const STYLES: Record<AnswerBlock["confidence_label"], string> = {
  high: "bg-emerald-100 text-emerald-800 ring-emerald-300",
  medium: "bg-amber-100 text-amber-800 ring-amber-300",
  low: "bg-red-100 text-red-800 ring-red-300",
};

const KEYS: Record<AnswerBlock["confidence_label"], StringKey> = {
  high: "confidenceHigh",
  medium: "confidenceMedium",
  low: "confidenceLow",
};

/** High / Medium / Low badge; the exact score is in the tooltip. */
export function ConfidenceBadge({ block }: { block: AnswerBlock }) {
  const t = useT();
  const label = block.abstained ? t("abstained") : t(KEYS[block.confidence_label]);
  return (
    <span
      title={`${t("confidence")}: ${Math.round(block.confidence * 100)}%`}
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${STYLES[block.abstained ? "low" : block.confidence_label]}`}
    >
      {label}
    </span>
  );
}
