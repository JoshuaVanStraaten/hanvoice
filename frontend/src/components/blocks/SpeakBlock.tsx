/** The pronunciation step: hear the phrase, hold the speak ring, get scored.
 * The backend marks the block passed when the attempt scores >= 60 — the
 * client only decides when to show Continue. */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { AudioButton } from "../AudioButton";
import { RecordButton } from "../RecordButton";
import { Button, ErrorNote, ScoreRing, Spinner } from "../ui";
import { useActivityInvalidation } from "../../hooks/queries";
import { useRecorder } from "../../hooks/useRecorder";
import { apiPostForm } from "../../lib/api";
import { extensionFor } from "../../lib/audio";
import type { LessonPhrase, PronunciationAttempt } from "../../lib/types";

const PASS_THRESHOLD = 60;

/** Hard cap for one take, scaled to the phrase: a syllable needs ~4 s, a
 * long phrase up to 12 s. The silence gate usually fires well before this. */
export function recordingCapMs(hangul: string): number {
  const syllables = (hangul.match(/[가-힣]/g) ?? []).length || 1;
  return Math.min(4000 + 1600 * (syllables - 1), 12_000);
}

const PHASE_CAPTION = {
  armed: "Listening — speak now",
  hearing: "Got it — pause when you're done, or tap to stop",
  finishing: "Finishing…",
} as const;

interface WordScore {
  word: string;
  accuracy: number | null;
  errorType: string | null;
}

/** Azure's per-word payload comes through raw; pull out what we render. */
function parseWords(words: Array<Record<string, unknown>>): WordScore[] {
  return words.flatMap((entry) => {
    const word = typeof entry["Word"] === "string" ? entry["Word"] : null;
    if (!word) return [];
    const assessment = entry["PronunciationAssessment"] as
      | Record<string, unknown>
      | undefined;
    const accuracy =
      typeof assessment?.["AccuracyScore"] === "number"
        ? assessment["AccuracyScore"]
        : null;
    const errorType =
      typeof assessment?.["ErrorType"] === "string" ? assessment["ErrorType"] : null;
    return [{ word, accuracy, errorType }];
  });
}

/** One concrete, actionable line about what to fix — not just numbers. */
function feedbackLine(attempt: PronunciationAttempt, words: WordScore[]): string | null {
  const omitted = words.filter((w) => w.errorType === "Omission");
  if (omitted.length > 0) {
    return `We didn't hear ${omitted.map((w) => w.word).join(", ")} — say the whole phrase.`;
  }
  const scored = words.filter((w) => w.accuracy !== null);
  const weakest = scored.reduce<WordScore | null>(
    (lowest, w) =>
      lowest === null || (w.accuracy ?? 100) < (lowest.accuracy ?? 100) ? w : lowest,
    null,
  );
  if (weakest && (weakest.accuracy ?? 100) < 80) {
    return `Focus on “${weakest.word}” (${Math.round(weakest.accuracy ?? 0)}) — tap ▶ to hear it, then try again.`;
  }
  if (attempt.scores.fluency < 70) {
    return "Good sounds — now say it in one smooth breath, without pausing between words.";
  }
  return null;
}

function wordChipClass(accuracy: number | null): string {
  if (accuracy === null) return "bg-line text-ink-soft";
  if (accuracy >= 80) return "bg-jade/10 text-jade";
  if (accuracy >= 60) return "bg-taegeuk-blue/10 text-taegeuk-blue";
  return "bg-taegeuk-red/10 text-taegeuk-red";
}

function AttemptResult({ attempt }: { attempt: PronunciationAttempt }) {
  const words = parseWords(attempt.scores.words);
  const feedback = feedbackLine(attempt, words);
  return (
    <div className="space-y-3 border-t border-line pt-3">
      <div className="flex justify-center gap-3">
        <ScoreRing score={attempt.scores.overall} label="Overall" />
        <ScoreRing score={attempt.scores.accuracy} label="Accuracy" />
        <ScoreRing score={attempt.scores.fluency} label="Fluency" />
        <ScoreRing score={attempt.scores.completeness} label="Complete" />
      </div>
      {words.length > 0 && (
        <div className="flex flex-wrap justify-center gap-1.5" aria-label="Per-word scores">
          {words.map((item, index) => (
            <span
              key={`${item.word}-${index}`}
              lang="ko"
              className={`rounded-full px-2.5 py-1 text-sm font-semibold ${wordChipClass(item.accuracy)}`}
            >
              {item.word}
              {item.accuracy !== null && (
                <span className="ml-1 text-xs font-normal">{Math.round(item.accuracy)}</span>
              )}
            </span>
          ))}
        </div>
      )}
      {attempt.scores.recognized_text &&
        attempt.scores.recognized_text.replace(/[.?!\s]/g, "") !==
          attempt.target_text.replace(/[.?!\s]/g, "") && (
          <p className="text-center text-sm text-ink-soft">
            We heard:{" "}
            <span lang="ko" className="font-semibold text-ink">
              {attempt.scores.recognized_text}
            </span>
          </p>
        )}
      {feedback && <p className="text-center text-sm text-ink-soft">{feedback}</p>}
    </div>
  );
}

export function SpeakBlock({
  phrase,
  onPassed,
  onContinue,
}: {
  phrase: LessonPhrase;
  onPassed: () => void;
  onContinue: () => void;
}) {
  const recorder = useRecorder();
  const invalidateActivity = useActivityInvalidation();
  const [attempt, setAttempt] = useState<PronunciationAttempt | null>(null);
  const [heardNothing, setHeardNothing] = useState(false);

  const scoreAttempt = useMutation({
    mutationFn: async (audio: Blob) => {
      const form = new FormData();
      form.append("audio", audio, `recording.${extensionFor(audio)}`);
      form.append("phrase_id", String(phrase.id));
      return apiPostForm<PronunciationAttempt>("/pronunciation/attempts", form);
    },
    onSuccess: (result) => {
      setAttempt(result);
      invalidateActivity();
      if (result.scores.overall >= PASS_THRESHOLD) onPassed();
    },
  });

  async function handlePress() {
    if (recorder.isRecording) {
      const audio = await recorder.stop();
      if (audio) scoreAttempt.mutate(audio);
      return;
    }
    scoreAttempt.reset();
    setHeardNothing(false);
    await recorder.start({
      maxDurationMs: recordingCapMs(phrase.hangul),
      onAutoStop: (audio) => scoreAttempt.mutate(audio),
      onSilentDiscard: () => setHeardNothing(true),
    });
  }

  const passed = attempt !== null && attempt.scores.overall >= PASS_THRESHOLD;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="hangul-display text-3xl" lang="ko">
            {phrase.hangul}
          </p>
          <p className="mt-1 text-sm text-ink-soft">
            {phrase.romanized} · {phrase.english}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <AudioButton
            path={`/pronunciation/phrases/${phrase.id}/audio`}
            label={`Hear ${phrase.hangul} pronounced`}
          />
          <RecordButton
            isRecording={recorder.isRecording}
            onPress={() => void handlePress()}
            disabled={scoreAttempt.isPending}
            level={recorder.level}
            silenceProgress={recorder.silenceProgress}
          />
        </div>
      </div>

      {recorder.isRecording && recorder.phase !== "idle" && (
        <p className="text-center text-sm text-ink-soft" role="status">
          {PHASE_CAPTION[recorder.phase]}
        </p>
      )}
      {heardNothing && !recorder.isRecording && (
        <p className="text-center text-sm text-ink-soft" role="status">
          We didn't hear anything — check your mic and try again.
        </p>
      )}
      {recorder.error && (
        <p role="alert" className="text-sm text-taegeuk-red">
          {recorder.error}
        </p>
      )}
      {scoreAttempt.isPending && <Spinner label="Scoring your pronunciation" />}
      {scoreAttempt.isError && (
        <ErrorNote error={scoreAttempt.error} retry={() => scoreAttempt.reset()} />
      )}

      {attempt && <AttemptResult attempt={attempt} />}
      {attempt && !passed && (
        <p className="text-center text-sm text-ink-soft">Almost — try again.</p>
      )}
      {passed && (
        <div className="space-y-2 text-center">
          <p className="text-sm font-semibold text-jade">통과! That one counts as passed.</p>
          <Button onClick={onContinue}>Continue</Button>
        </div>
      )}
    </div>
  );
}
