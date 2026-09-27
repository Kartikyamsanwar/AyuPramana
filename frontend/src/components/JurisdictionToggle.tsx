import { useT, type StringKey } from "../i18n";
import type { Jurisdiction } from "../types";

const OPTIONS: { value: Jurisdiction; key: StringKey }[] = [
  { value: "india", key: "india" },
  { value: "international", key: "international" },
  { value: "both", key: "both" },
];

/** Segmented control (radio group) choosing which legal regime answers come from. */
export function JurisdictionToggle({
  value,
  onChange,
}: {
  value: Jurisdiction;
  onChange: (value: Jurisdiction) => void;
}) {
  const t = useT();
  return (
    <div role="radiogroup" aria-label={t("jurisdiction")} className="inline-flex rounded-full bg-leaf-900/40 p-1">
      {OPTIONS.map((option) => {
        const selected = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(option.value)}
            className={`rounded-full px-3 py-1.5 text-sm font-medium transition sm:px-4 ${
              selected ? "bg-turmeric-400 text-leaf-900 shadow" : "text-leaf-50 hover:bg-white/10"
            }`}
          >
            {t(option.key)}
          </button>
        );
      })}
    </div>
  );
}
