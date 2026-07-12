/** The handwriting step: trace the target on the shared canvas. Submitting
 * with block_id lets the backend verify the target and mark the pass
 * (overall >= 60) — the client only decides when to show Continue. */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { AudioButton, blockAudioProps } from "../AudioButton";
import { Dojang } from "../Dojang";
import { HangulCanvas } from "../HangulCanvas";
import { Button, ErrorNote, ScoreRing, Spinner } from "../ui";
import { useActivityInvalidation } from "../../hooks/queries";
import { track } from "../../lib/analytics";
import { apiPost } from "../../lib/api";
import { audioTextFor } from "../../lib/hangulAudio";
import type { HandwritingAttempt, WritePayload } from "../../lib/types";

const PASS_THRESHOLD = 60;

export function WriteBlock({
  blockId,
  payload,
  onPassed,
  onContinue,
}: {
  blockId: number;
  payload: WritePayload;
  onPassed: () => void;
  onContinue: () => void;
}) {
  const invalidateActivity = useActivityInvalidation();
  const [attempt, setAttempt] = useState<HandwritingAttempt | null>(null);

  const submit = useMutation({
    mutationFn: (imageBase64: string) =>
      apiPost<HandwritingAttempt>("/handwriting/attempts", {
        target_text: payload.target,
        image_base64: imageBase64,
        block_id: blockId,
      }),
    onSuccess: (result) => {
      setAttempt(result);
      invalidateActivity();
      track("attempt_scored", { kind: "handwriting", score: result.scores.overall_score });
      if (result.scores.overall_score >= PASS_THRESHOLD) onPassed();
    },
  });

  const passed = attempt !== null && attempt.scores.overall_score >= PASS_THRESHOLD;

  return (
    <div className="space-y-3">
      <div className="text-center">
        <p className="flex items-center justify-center gap-2 text-sm text-ink-soft">
          <span>
            Write{" "}
            <span lang="ko" className="hangul-display text-lg text-ink">
              {payload.target}
            </span>
            {payload.hint ? ` — ${payload.hint}` : ""}
          </span>
          <AudioButton
            size="sm"
            {...blockAudioProps(
              blockId,
              payload.target,
              audioTextFor(payload.target, payload.audio),
            )}
          />
        </p>
      </div>

      <HangulCanvas
        target={payload.target}
        submitting={submit.isPending}
        onSubmit={(imageBase64) => submit.mutate(imageBase64)}
      />

      {submit.isPending && <Spinner label="Scoring your writing" />}
      {submit.isError && <ErrorNote error={submit.error} retry={() => submit.reset()} />}

      {attempt && (
        <div className="space-y-3 border-t border-line pt-3">
          <div className="flex justify-center gap-3">
            <ScoreRing score={attempt.scores.overall_score} label="Overall" />
            <ScoreRing score={attempt.scores.proportion_score} label="Proportion" />
            <ScoreRing score={attempt.scores.stroke_score} label="Strokes" />
            <ScoreRing score={attempt.scores.legibility_score} label="Legibility" />
          </div>
          <p className="text-center text-sm text-ink-soft">{attempt.scores.feedback}</p>
          {passed ? (
            <div className="space-y-2 text-center">
              <Dojang />
              <p className="text-sm font-semibold text-jade">That one counts as passed.</p>
              <Button onClick={onContinue}>Continue</Button>
            </div>
          ) : (
            <p className="text-center text-sm text-ink-soft">Almost — try again.</p>
          )}
        </div>
      )}
    </div>
  );
}
