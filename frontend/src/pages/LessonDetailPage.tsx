/** The pronunciation loop: read a phrase, hold the speak ring, get scored.
 * One recorder for the page; whichever card is recording owns the red ring. */

import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { RecordButton } from "../components/RecordButton";
import { Card, ErrorNote, ScoreRing, Spinner } from "../components/ui";
import { useActivityInvalidation, useLesson } from "../hooks/queries";
import { useRecorder } from "../hooks/useRecorder";
import { apiGet, apiPostForm } from "../lib/api";
import { extensionFor } from "../lib/audio";
import type { LessonPhrase, PronunciationAttempt } from "../lib/types";

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
      {attempt.scores.overall >= 60 ? (
        <p className="text-center text-sm font-semibold text-jade">
          통과! That one counts as passed.
        </p>
      ) : (
        <p className="text-center text-sm text-ink-soft">Almost — try again.</p>
      )}
    </div>
  );
}

/** Plays the reference pronunciation (Azure TTS), fetched once then cached. */
function ListenButton({ phraseId, hangul }: { phraseId: number; hangul: string }) {
  const [audio, setAudio] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function play() {
    if (pending) return;
    let base64 = audio;
    if (!base64) {
      setPending(true);
      try {
        const response = await apiGet<{ audio_base64: string }>(
          `/pronunciation/phrases/${phraseId}/audio`,
        );
        base64 = response.audio_base64;
        setAudio(base64);
      } catch {
        return; // listening is optional — fail quietly, the phrase text remains
      } finally {
        setPending(false);
      }
    }
    void new Audio(`data:audio/mpeg;base64,${base64}`).play().catch(() => undefined);
  }

  return (
    <button
      type="button"
      onClick={() => void play()}
      disabled={pending}
      aria-label={`Hear ${hangul} pronounced`}
      className="flex size-9 items-center justify-center rounded-full bg-taegeuk-blue/10 text-taegeuk-blue transition-colors hover:bg-taegeuk-blue/20 disabled:opacity-50"
    >
      {pending ? (
        <span className="size-2 animate-pulse rounded-full bg-taegeuk-blue" aria-hidden />
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
          <path d="M8 5.5v13l11-6.5z" />
        </svg>
      )}
    </button>
  );
}

function PhraseCard({
  phrase,
  isActive,
  isRecording,
  isScoring,
  attempt,
  onPress,
  level,
}: {
  phrase: LessonPhrase;
  isActive: boolean;
  isRecording: boolean;
  isScoring: boolean;
  attempt: PronunciationAttempt | undefined;
  onPress: () => void;
  level: number;
}) {
  return (
    <Card className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="hangul-display text-2xl" lang="ko">
            {phrase.hangul}
          </p>
          <p className="mt-1 text-sm text-ink-soft">
            {phrase.romanized} · {phrase.english}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <ListenButton phraseId={phrase.id} hangul={phrase.hangul} />
          <RecordButton
            isRecording={isActive && isRecording}
            onPress={onPress}
            disabled={isScoring || (isRecording && !isActive)}
            level={level}
          />
        </div>
      </div>
      {isActive && isScoring && <Spinner label="Scoring your pronunciation" />}
      {attempt && <AttemptResult attempt={attempt} />}
    </Card>
  );
}

export function LessonDetailPage() {
  const { slug = "" } = useParams();
  const lesson = useLesson(slug);
  const recorder = useRecorder();
  const invalidateActivity = useActivityInvalidation();

  const [activePhraseId, setActivePhraseId] = useState<number | null>(null);
  const [attempts, setAttempts] = useState<Record<number, PronunciationAttempt>>({});

  const scoreAttempt = useMutation({
    mutationFn: async ({ phraseId, audio }: { phraseId: number; audio: Blob }) => {
      const form = new FormData();
      form.append("audio", audio, `recording.${extensionFor(audio)}`);
      form.append("phrase_id", String(phraseId));
      return apiPostForm<PronunciationAttempt>("/pronunciation/attempts", form);
    },
    onSuccess: (attempt, { phraseId }) => {
      setAttempts((current) => ({ ...current, [phraseId]: attempt }));
      invalidateActivity();
    },
    onSettled: () => setActivePhraseId(null),
  });

  async function handlePress(phraseId: number) {
    if (recorder.isRecording && activePhraseId === phraseId) {
      const audio = await recorder.stop();
      if (audio) {
        scoreAttempt.mutate({ phraseId, audio });
      } else {
        setActivePhraseId(null);
      }
      return;
    }
    scoreAttempt.reset();
    setActivePhraseId(phraseId);
    await recorder.start();
  }

  return (
    <div className="space-y-4">
      <header className="space-y-1">
        <Link to="/lessons" className="text-sm font-semibold text-taegeuk-blue">
          ← Lessons
        </Link>
        {lesson.isSuccess && (
          <>
            <h1 className="text-2xl font-bold">{lesson.data.title}</h1>
            <p className="text-sm text-ink-soft">{lesson.data.description}</p>
          </>
        )}
      </header>

      {recorder.error && (
        <p role="alert" className="text-sm text-taegeuk-red">
          {recorder.error}
        </p>
      )}
      {scoreAttempt.isError && (
        <ErrorNote error={scoreAttempt.error} retry={() => scoreAttempt.reset()} />
      )}

      {lesson.isPending && <Spinner label="Loading lesson" />}
      {lesson.isError && <ErrorNote error={lesson.error} retry={() => void lesson.refetch()} />}

      {lesson.isSuccess && (
        <ul className="space-y-3">
          {lesson.data.phrases.map((phrase) => (
            <li key={phrase.id}>
              <PhraseCard
                phrase={phrase}
                isActive={activePhraseId === phrase.id}
                isRecording={recorder.isRecording}
                level={recorder.level}
                isScoring={scoreAttempt.isPending && activePhraseId === phrase.id}
                attempt={attempts[phrase.id]}
                onPress={() => void handlePress(phrase.id)}
              />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
