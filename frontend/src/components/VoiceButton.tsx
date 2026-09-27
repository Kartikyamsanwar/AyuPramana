import { useEffect, useRef, useState } from "react";
import { useT } from "../i18n";
import type { Language } from "../types";

/* Minimal typing for the Web Speech API (not in TypeScript's DOM library everywhere). */
interface RecognitionResultEvent {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
}
interface Recognition {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: RecognitionResultEvent) => void) | null;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  start: () => void;
  stop: () => void;
}
type RecognitionConstructor = new () => Recognition;

const SPEECH_LANG: Record<Language, string> = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };

function recognitionClass(): RecognitionConstructor | undefined {
  const w = window as unknown as { SpeechRecognition?: RecognitionConstructor; webkitSpeechRecognition?: RecognitionConstructor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
}

/** Voice input (stretch goal). Shown only when VITE_VOICE_INPUT=true and the browser supports speech recognition. */
export function VoiceButton({ language, onText }: { language: Language; onText: (text: string) => void }) {
  const t = useT();
  const [listening, setListening] = useState(false);
  const recognition = useRef<Recognition | null>(null);
  const Recognition = recognitionClass();

  useEffect(() => () => recognition.current?.stop(), []);

  if (import.meta.env.VITE_VOICE_INPUT !== "true" || !Recognition) return null;

  function toggle() {
    if (listening) {
      recognition.current?.stop();
      return;
    }
    const instance = new Recognition!();
    instance.lang = SPEECH_LANG[language];
    instance.interimResults = false;
    instance.maxAlternatives = 1;
    instance.onresult = (event) => onText(event.results[0][0].transcript);
    instance.onend = () => setListening(false);
    instance.onerror = () => setListening(false);
    recognition.current = instance;
    setListening(true);
    instance.start();
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={listening}
      aria-label={listening ? t("voiceStop") : t("voiceStart")}
      title={listening ? t("voiceStop") : t("voiceStart")}
      className={`rounded-lg px-3 py-2 ${listening ? "animate-pulse bg-red-100 text-red-700" : "text-stone-600 hover:bg-stone-100"}`}
    >
      🎤
    </button>
  );
}
