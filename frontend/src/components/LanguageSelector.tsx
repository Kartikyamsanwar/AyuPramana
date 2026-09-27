import { LANGUAGE_NAMES, useT } from "../i18n";
import type { Language } from "../types";

/** Chooses the language for both UI strings and answers. */
export function LanguageSelector({ value, onChange }: { value: Language; onChange: (value: Language) => void }) {
  const t = useT();
  return (
    <label className="flex items-center gap-2 text-sm text-leaf-50">
      <span className="sr-only sm:not-sr-only">{t("language")}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value as Language)}
        className="rounded-md border border-white/20 bg-leaf-900/40 px-2 py-1.5 text-leaf-50"
      >
        {(Object.keys(LANGUAGE_NAMES) as Language[]).map((code) => (
          <option key={code} value={code} className="text-stone-900">
            {LANGUAGE_NAMES[code]}
          </option>
        ))}
      </select>
    </label>
  );
}
