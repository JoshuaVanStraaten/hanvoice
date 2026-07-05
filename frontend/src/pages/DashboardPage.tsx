/** Home dashboard: today's quota meters, the next thing to practice, and a
 * glance at overall progress. Red belongs to the speaking card, blue to
 * lessons — same split as everywhere else. */

import { Link } from "react-router-dom";

import { Button, Card, ErrorNote, MeterBar, SkeletonCards } from "../components/ui";
import {
  useLessons,
  useMe,
  useProgress,
  useScenarios,
  useUsageToday,
} from "../hooks/queries";
import type { LessonProgressItem, LessonSummary } from "../lib/types";

/** First lesson in progress, else the first one not yet completed. */
function nextLesson(
  lessons: LessonSummary[],
  progress: LessonProgressItem[],
): { lesson: LessonSummary; started: LessonProgressItem | null } | null {
  const bySlug = new Map(progress.map((item) => [item.lesson_slug, item]));
  const inProgress = lessons.find((l) => bySlug.get(l.slug)?.status === "in_progress");
  if (inProgress) return { lesson: inProgress, started: bySlug.get(inProgress.slug) ?? null };
  const unstarted = lessons.find((l) => bySlug.get(l.slug)?.status !== "completed");
  if (unstarted) return { lesson: unstarted, started: null };
  return null;
}

export function DashboardPage() {
  const me = useMe();
  const usage = useUsageToday();
  const lessons = useLessons();
  const scenarios = useScenarios();
  const progress = useProgress();

  const displayName = me.data?.profile.display_name;
  const continueTarget =
    lessons.data && progress.data ? nextLesson(lessons.data, progress.data.lessons) : null;
  const scenario = scenarios.data?.[0];
  const completedLessons =
    progress.data?.lessons.filter((l) => l.status === "completed").length ?? 0;

  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-2xl font-bold">
          {displayName ? `안녕하세요, ${displayName}!` : "안녕하세요!"}
        </h1>
        <p className="text-sm text-ink-soft">Ready to say something out loud?</p>
      </section>

      {/* Today's usage */}
      <section aria-labelledby="usage-heading">
        <h2 id="usage-heading" className="mb-2 text-sm font-semibold text-ink-soft">
          Today&apos;s practice
        </h2>
        {usage.isPending && <SkeletonCards count={1} label="Loading usage" />}
        {usage.isError && <ErrorNote error={usage.error} retry={() => void usage.refetch()} />}
        {usage.isSuccess && (
          <Card className="space-y-3">
            <MeterBar
              label="Pronunciation checks"
              used={usage.data.usage.pronunciation_attempts}
              limit={usage.data.plan.daily_pronunciation_limit}
            />
            <MeterBar
              label="Conversation turns"
              used={usage.data.usage.conversation_turns}
              limit={usage.data.plan.daily_conversation_turn_limit}
            />
            <MeterBar
              label="Handwriting checks"
              used={usage.data.usage.handwriting_checks}
              limit={usage.data.plan.daily_handwriting_limit}
            />
            {me.data && me.data.plan.id === "free" && (
              <Link
                to="/subscription"
                className="block text-sm font-semibold text-taegeuk-blue"
              >
                Need more? See plans
              </Link>
            )}
          </Card>
        )}
      </section>

      {/* Continue learning */}
      <section aria-labelledby="continue-heading" className="space-y-3">
        <h2 id="continue-heading" className="text-sm font-semibold text-ink-soft">
          Keep going
        </h2>
        {(lessons.isPending || progress.isPending) && (
          <SkeletonCards count={2} label="Loading lessons" />
        )}
        {lessons.isError && (
          <ErrorNote error={lessons.error} retry={() => void lessons.refetch()} />
        )}
        {continueTarget && (
          <Card className="space-y-2">
            <p className="text-xs font-semibold tracking-wide text-taegeuk-blue uppercase">
              {continueTarget.started ? "Continue lesson" : "Next lesson"}
            </p>
            <h3 className="text-lg font-bold">{continueTarget.lesson.title}</h3>
            <p className="text-sm text-ink-soft">{continueTarget.lesson.description}</p>
            {continueTarget.started && (
              <MeterBar
                label="Steps passed"
                used={continueTarget.started.blocks_completed}
                limit={continueTarget.started.block_count}
              />
            )}
            <Link to={`/lessons/${continueTarget.lesson.slug}`}>
              <Button>{continueTarget.started ? "Continue" : "Start lesson"}</Button>
            </Link>
          </Card>
        )}
        {lessons.isSuccess && progress.isSuccess && !continueTarget && (
          <Card>
            <p className="text-sm">
              All lessons completed — 대단해요! Keep your streak alive in the café.
            </p>
          </Card>
        )}

        {scenario && (
          <Card className="space-y-2 border-taegeuk-red/30">
            <p className="text-xs font-semibold tracking-wide text-taegeuk-red uppercase">
              Speaking scenario
            </p>
            <h3 className="text-lg font-bold">{scenario.title}</h3>
            <p className="text-sm text-ink-soft">{scenario.description}</p>
            <Link to="/talk">
              <Button variant="speak">Talk to Minji</Button>
            </Link>
          </Card>
        )}
      </section>

      {/* Progress glance */}
      <section aria-labelledby="progress-heading">
        <h2 id="progress-heading" className="mb-2 text-sm font-semibold text-ink-soft">
          Progress
        </h2>
        {progress.isSuccess && lessons.isSuccess && (
          <Card className="space-y-2">
            <MeterBar
              label="Lessons completed"
              used={completedLessons}
              limit={lessons.data.length}
            />
            <Link to="/progress" className="block text-sm font-semibold text-taegeuk-blue">
              See full progress
            </Link>
          </Card>
        )}
      </section>
    </div>
  );
}
