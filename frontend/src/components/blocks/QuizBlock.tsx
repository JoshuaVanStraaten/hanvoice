/** One-question check. Wrong answers can be retried freely; Continue only
 * unlocks (and marks the block passed) after the right choice. */

import { useState } from "react";

import { Button } from "../ui";
import { renderBold } from "./ExplainBlock";
import type { QuizPayload } from "../../lib/types";

export function QuizBlock({
  payload,
  completing,
  onCorrectContinue,
}: {
  payload: QuizPayload;
  completing: boolean;
  onCorrectContinue: () => void;
}) {
  const [selected, setSelected] = useState<number | null>(null);
  const isCorrect = selected === payload.answer;

  return (
    <div className="space-y-4">
      <p className="text-base font-semibold text-ink">{renderBold(payload.question)}</p>
      <ul className="space-y-2" role="listbox" aria-label="Answers">
        {payload.choices.map((choice, index) => {
          const isSelected = selected === index;
          const state = !isSelected
            ? "border-line bg-paper-raised text-ink hover:border-taegeuk-blue"
            : index === payload.answer
              ? "border-jade bg-jade/10 text-jade"
              : "border-taegeuk-red bg-taegeuk-red/5 text-taegeuk-red";
          return (
            <li key={index}>
              <button
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => setSelected(index)}
                disabled={isCorrect}
                className={`w-full rounded-lg border px-4 py-3 text-left text-sm font-medium transition-colors ${state}`}
              >
                {choice}
              </button>
            </li>
          );
        })}
      </ul>
      {selected !== null && !isCorrect && (
        <p className="text-center text-sm text-ink-soft" role="status">
          Not quite — try another answer.
        </p>
      )}
      {isCorrect && (
        <div className="space-y-3" role="status">
          <p className="text-center text-sm font-semibold text-jade">맞아요! Correct.</p>
          {payload.explanation && (
            <p className="text-center text-sm text-ink-soft">
              {renderBold(payload.explanation)}
            </p>
          )}
          <div className="text-center">
            <Button onClick={onCorrectContinue} disabled={completing}>
              {completing ? "Saving…" : "Continue"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
