/** Hangul handwriting free practice. The drawing surface lives in
 * HangulCanvas (shared with write lesson blocks); this page adds the target
 * picker. The curriculum builds up the way Hangul does: basic vowels → basic
 * consonants → the syllables of the phrases the learner already says. */

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";

import { Button, Card, ErrorNote, ScoreRing, Spinner } from "../components/ui";
import { HangulCanvas } from "../components/HangulCanvas";
import { useActivityInvalidation } from "../hooks/queries";
import { apiPost } from "../lib/api";
import type { HandwritingAttempt } from "../lib/types";

interface TargetGroup {
  label: string;
  hint: string;
  targets: string[];
}

const TARGET_GROUPS: TargetGroup[] = [
  {
    label: "Vowels · 모음",
    hint: "The six basic vowels — vertical and horizontal lines with ticks.",
    targets: ["ㅏ", "ㅓ", "ㅗ", "ㅜ", "ㅡ", "ㅣ"],
  },
  {
    label: "Consonants · 자음",
    hint: "The most common consonants — each shape mimics your mouth making it.",
    targets: ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅎ"],
  },
  {
    label: "Syllables · 글자",
    hint: "Full syllable blocks from phrases you already speak.",
    targets: ["안", "녕", "하", "세", "요", "감", "사", "합", "니", "다"],
  },
];

const TARGETS = TARGET_GROUPS.flatMap((group) => group.targets);

export function WritingPage() {
  const [targetIndex, setTargetIndex] = useState(0);
  const invalidateActivity = useActivityInvalidation();

  const target = TARGETS[targetIndex] ?? TARGETS[0] ?? "안";

  const submit = useMutation({
    mutationFn: (imageBase64: string) =>
      apiPost<HandwritingAttempt>("/handwriting/attempts", {
        target_text: target,
        image_base64: imageBase64,
      }),
    onSuccess: () => invalidateActivity(),
  });

  function selectTarget(index: number) {
    setTargetIndex(index);
    submit.reset();
  }

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Write</h1>
        <p className="text-sm text-ink-soft">
          Trace the character, then get scored on proportion, strokes, and legibility.
        </p>
      </header>

      {/* Target picker — jamo first, then the syllables they build. */}
      <div className="space-y-3">
        {TARGET_GROUPS.map((group, groupIndex) => {
          const offset = TARGET_GROUPS.slice(0, groupIndex).reduce(
            (sum, g) => sum + g.targets.length,
            0,
          );
          const isActiveGroup =
            targetIndex >= offset && targetIndex < offset + group.targets.length;
          return (
            <div key={group.label}>
              <p className="mb-1 text-xs font-semibold text-ink-soft">
                {group.label}
                {isActiveGroup && (
                  <span className="ml-2 font-normal">{group.hint}</span>
                )}
              </p>
              <div className="flex flex-wrap gap-1.5" aria-label={group.label}>
                {group.targets.map((char, index) => {
                  const flatIndex = offset + index;
                  return (
                    <button
                      key={char}
                      type="button"
                      lang="ko"
                      onClick={() => selectTarget(flatIndex)}
                      aria-pressed={flatIndex === targetIndex}
                      className={`hangul-display size-10 rounded-lg border text-lg ${
                        flatIndex === targetIndex
                          ? "border-taegeuk-blue bg-taegeuk-blue/10 text-taegeuk-blue"
                          : "border-line bg-paper-raised text-ink-soft"
                      }`}
                    >
                      {char}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <Card>
        <HangulCanvas
          key={target}
          target={target}
          submitting={submit.isPending}
          onSubmit={(imageBase64) => submit.mutate(imageBase64)}
        />
      </Card>

      {submit.isPending && <Spinner label="Scoring your writing" />}
      {submit.isError && <ErrorNote error={submit.error} retry={() => submit.reset()} />}

      {submit.isSuccess && (
        <Card className="space-y-3">
          <div className="flex justify-center gap-3">
            <ScoreRing score={submit.data.scores.overall_score} label="Overall" />
            <ScoreRing score={submit.data.scores.proportion_score} label="Proportion" />
            <ScoreRing score={submit.data.scores.stroke_score} label="Strokes" />
            <ScoreRing score={submit.data.scores.legibility_score} label="Legibility" />
          </div>
          <p className="text-center text-sm text-ink-soft">{submit.data.scores.feedback}</p>
          {targetIndex < TARGETS.length - 1 && (
            <div className="text-center">
              <Button onClick={() => selectTarget(targetIndex + 1)}>
                Next character: {TARGETS[targetIndex + 1]}
              </Button>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
