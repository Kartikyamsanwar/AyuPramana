import type { ChatResponse, Citation, SingleJurisdiction } from "../types";
import { AnswerCard } from "./AnswerCard";

const ORDER: SingleJurisdiction[] = ["india", "international"];

/** An assistant reply. With "Both", India and International answers sit side by side, never merged. */
export function AssistantTurn({ response, onCite }: { response: ChatResponse; onCite: (citation: Citation) => void }) {
  const blocks = ORDER.map((key) => response.answers[key]).filter((b) => b !== undefined);
  return (
    <div className={`grid gap-3 ${blocks.length > 1 ? "md:grid-cols-2" : ""}`}>
      {blocks.map((block) => (
        <AnswerCard
          key={block.jurisdiction}
          block={block}
          disclaimer={response.disclaimer}
          queryId={response.query_id}
          language={response.language}
          onCite={onCite}
        />
      ))}
    </div>
  );
}
