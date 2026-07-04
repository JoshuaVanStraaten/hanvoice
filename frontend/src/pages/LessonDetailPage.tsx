/** The pronunciation loop: read a phrase, hold the speak ring, get scored.
 * One recorder for the page; whichever card is recording owns the red ring. */

import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";

import { RecordButton } from "../components/RecordButton";
import { Card, ErrorNote, ScoreRing, Spinner } from "../components/ui";
import { useActivityInvalidation, useLesson } from "../hooks/queries";
import { useRecorder } from "../hooks/useRecorder";
import { apiPostForm } from "../lib/api";
import { extensionFor } from "../lib/audio";
import type { LessonPhrase, PronunciationAttempt } from "../lib/types";

interface WordScore {
  word: string;
  accuracy: number | null;
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
    return [{ word, accuracy }];
  });
}

function wordChipClass(accuracy: number | null): string {
  if (accuracy === null) return "bg-line text-ink-soft";
  if (accuracy >= 80) return "bg-jade/10 text-jade";
  if (accuracy >= 60) return "bg-taegeuk-blue/10 text-taegeuk-blue";
  return "bg-taegeuk-red/10 text-taegeuk-red";
}

function AttemptResult({ attempt }: { attempt: PronunciationAttempt }) {
  const words = parseWords(attempt.scores.words);
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
      {attempt.scores.overall >= 60 ? (
        <p className="text-center text-sm font-semibold text-jade">
          통과! That one counts as passed.
        </p>
      ) : (
        <p className="text-center text-sm text-ink-soft">
          Almost — listen to the low-scoring words and try again.
        </p>
      )}
    </div>
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
        <div>
          <p className="hangul-display text-2xl" lang="ko">
            {phrase.hangul}
          </p>
          <p className="mt-1 text-sm text-ink-soft">
            {phrase.romanized} · {phrase.english}
          </p>
        </div>
        <RecordButton
          isRecording={isActive && isRecording}
          onPress={onPress}
          disabled={isScoring || (isRecording && !isActive)}
          level={level}
        />
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
