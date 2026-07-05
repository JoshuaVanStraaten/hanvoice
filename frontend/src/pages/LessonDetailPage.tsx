/** The lesson player: one block at a time, in order. Explain and quiz blocks
 * self-attest via the complete endpoint; speak and write blocks pass on the
 * backend when a scored attempt clears the threshold. Resumes at the first
 * unpassed block. */

import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";

import { Dojang } from "../components/Dojang";
import { ExplainBlock } from "../components/blocks/ExplainBlock";
import { QuizBlock } from "../components/blocks/QuizBlock";
import { SpeakBlock } from "../components/blocks/SpeakBlock";
import { WriteBlock } from "../components/blocks/WriteBlock";
import { Button, Card, ErrorNote, MeterBar, SkeletonCards } from "../components/ui";
import { useCompleteBlock, useLesson } from "../hooks/queries";
import type { LessonBlock, LessonDetail } from "../lib/types";

function BlockBody({
  block,
  completing,
  onSelfComplete,
  onScoredPass,
  onAdvance,
}: {
  block: LessonBlock;
  completing: boolean;
  onSelfComplete: () => void;
  onScoredPass: () => void;
  onAdvance: () => void;
}) {
  switch (block.kind) {
    case "explain":
      return (
        <ExplainBlock
          blockId={block.id}
          payload={block.payload}
          completing={completing}
          onContinue={onSelfComplete}
        />
      );
    case "quiz":
      return (
        <QuizBlock
          payload={block.payload}
          completing={completing}
          onCorrectContinue={onSelfComplete}
        />
      );
    case "speak":
      return block.phrase ? (
        <SpeakBlock phrase={block.phrase} onPassed={onScoredPass} onContinue={onAdvance} />
      ) : null;
    case "write":
      return (
        <WriteBlock
          blockId={block.id}
          payload={block.payload}
          onPassed={onScoredPass}
          onContinue={onAdvance}
        />
      );
  }
}

/** Mounted only once the lesson is loaded, so the resume index can be
 * computed in the state initializer — refetches update pass flags without
 * yanking the learner off the block they're on. */
function LessonPlayer({ lesson }: { lesson: LessonDetail }) {
  const completeBlock = useCompleteBlock(lesson.slug);
  const queryClient = useQueryClient();
  const [index, setIndex] = useState(() => {
    const firstUnpassed = lesson.blocks.findIndex((b) => !b.passed);
    return firstUnpassed === -1 ? 0 : firstUnpassed;
  });

  const blocks = lesson.blocks;
  const block = blocks[index];
  const passedCount = blocks.filter((b) => b.passed).length;
  const finished = blocks.length > 0 && index >= blocks.length;

  function advance() {
    completeBlock.reset();
    setIndex((current) => current + 1);
  }

  /** Explain/quiz: tell the backend, then move on (skip the POST if the
   * block already passed on a previous run). */
  function selfComplete(current: LessonBlock) {
    if (current.passed) {
      advance();
      return;
    }
    completeBlock.mutate(current.id, { onSuccess: advance });
  }

  /** Speak/write passed server-side — refresh the passed flags. */
  function scoredPass() {
    void queryClient.invalidateQueries({ queryKey: ["lesson", lesson.slug] });
  }

  if (blocks.length === 0) {
    return (
      <Card>
        <p className="text-sm text-ink-soft">This lesson has no content yet.</p>
      </Card>
    );
  }

  if (finished) {
    return (
      <Card className="space-y-3 text-center">
        {passedCount === blocks.length ? (
          <>
            <Dojang label="Lesson complete" />
            <p className="text-lg font-bold text-jade">수고했어요! Lesson complete.</p>
            <p className="text-sm text-ink-soft">All {blocks.length} steps passed.</p>
          </>
        ) : (
          <>
            <p className="text-lg font-bold">End of the lesson run.</p>
            <p className="text-sm text-ink-soft">
              {passedCount} of {blocks.length} steps passed — skipped steps are waiting for
              you.
            </p>
          </>
        )}
        <div className="flex justify-center gap-3">
          <Button variant="quiet" onClick={() => setIndex(0)}>
            Go through it again
          </Button>
          <Link to="/lessons">
            <Button>Back to lessons</Button>
          </Link>
        </div>
      </Card>
    );
  }

  if (!block) return null;

  return (
    <>
      {completeBlock.isError && (
        <ErrorNote error={completeBlock.error} retry={() => completeBlock.reset()} />
      )}
      <MeterBar
        label={`Step ${index + 1} of ${blocks.length}`}
        used={passedCount}
        limit={blocks.length}
      />
      <Card>
        <div key={block.id} className="block-enter space-y-3">
          {block.passed && (
            <p className="text-right text-xs font-semibold text-jade" aria-label="Already passed">
              Passed ✓
            </p>
          )}
          <BlockBody
            block={block}
            completing={completeBlock.isPending}
            onSelfComplete={() => selfComplete(block)}
            onScoredPass={scoredPass}
            onAdvance={advance}
          />
        </div>
      </Card>
      <div className="flex justify-between">
        <Button variant="quiet" onClick={() => setIndex(index - 1)} disabled={index === 0}>
          ← Back
        </Button>
        {(block.kind === "speak" || block.kind === "write") && (
          <Button variant="quiet" onClick={advance}>
            {block.passed ? "Continue →" : "Skip for now"}
          </Button>
        )}
      </div>
    </>
  );
}

export function LessonDetailPage() {
  const { slug = "" } = useParams();
  const lesson = useLesson(slug);

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

      {lesson.isPending && <SkeletonCards count={1} label="Loading lesson" />}
      {lesson.isError && <ErrorNote error={lesson.error} retry={() => void lesson.refetch()} />}

      {lesson.isSuccess && <LessonPlayer key={slug} lesson={lesson.data} />}
    </div>
  );
}
