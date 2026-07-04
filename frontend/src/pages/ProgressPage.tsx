import { Link } from "react-router-dom";

import { Card, ErrorNote, MeterBar, Spinner } from "../components/ui";
import { useProgress } from "../hooks/queries";

export function ProgressPage() {
  const progress = useProgress();

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold">Progress</h1>
        <p className="text-sm text-ink-soft">Every phrase you pass stays passed.</p>
      </header>

      {progress.isPending && <Spinner label="Loading progress" />}
      {progress.isError && (
        <ErrorNote error={progress.error} retry={() => void progress.refetch()} />
      )}

      {progress.isSuccess && (
        <>
          <section aria-labelledby="lesson-progress-heading" className="space-y-3">
            <h2 id="lesson-progress-heading" className="text-sm font-semibold text-ink-soft">
              Lessons
            </h2>
            {progress.data.lessons.length === 0 && (
              <Card>
                <p className="text-sm">
                  Nothing yet — pass your first phrase in{" "}
                  <Link to="/lessons" className="font-semibold text-taegeuk-blue">
                    Lessons
                  </Link>
                  .
                </p>
              </Card>
            )}
            {progress.data.lessons.map((lesson) => (
              <Card key={lesson.lesson_id} className="space-y-2">
                <div className="flex items-center justify-between">
                  <Link
                    to={`/lessons/${lesson.lesson_slug}`}
                    className="font-bold hover:text-taegeuk-blue"
                  >
                    {lesson.lesson_title}
                  </Link>
                  {lesson.best_pronunciation_score !== null && (
                    <span className="text-xs text-ink-soft">
                      Best score {Math.round(lesson.best_pronunciation_score)}
                    </span>
                  )}
                </div>
                <MeterBar
                  label={lesson.status === "completed" ? "Completed" : "Phrases passed"}
                  used={lesson.phrases_completed}
                  limit={lesson.phrase_count}
                />
              </Card>
            ))}
          </section>

          <section aria-labelledby="scenario-progress-heading" className="space-y-3">
            <h2 id="scenario-progress-heading" className="text-sm font-semibold text-ink-soft">
              Conversations
            </h2>
            {progress.data.scenarios.length === 0 && (
              <Card>
                <p className="text-sm">
                  No conversations yet —{" "}
                  <Link to="/talk" className="font-semibold text-taegeuk-red">
                    talk to Minji
                  </Link>
                  .
                </p>
              </Card>
            )}
            {progress.data.scenarios.map((scenario) => (
              <Card key={scenario.scenario_id} className="flex items-center justify-between">
                <p className="font-bold">{scenario.scenario_title}</p>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                    scenario.times_completed > 0
                      ? "bg-jade/10 text-jade"
                      : "bg-line text-ink-soft"
                  }`}
                >
                  {scenario.times_completed > 0
                    ? `Completed ×${scenario.times_completed}`
                    : "In progress"}
                </span>
              </Card>
            ))}
          </section>
        </>
      )}
    </div>
  );
}
