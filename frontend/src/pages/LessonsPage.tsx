import { Link } from "react-router-dom";

import { Card, ErrorNote, MeterBar, Spinner } from "../components/ui";
import { useLessons, useProgress } from "../hooks/queries";

export function LessonsPage() {
  const lessons = useLessons();
  const progress = useProgress();
  const progressBySlug = new Map(
    (progress.data?.lessons ?? []).map((item) => [item.lesson_slug, item]),
  );

  return (
    <div className="space-y-4">
      <header>
        <h1 className="text-2xl font-bold">Lessons</h1>
        <p className="text-sm text-ink-soft">
          Small phrase chunks — pass each one by saying it out loud.
        </p>
      </header>

      {lessons.isPending && <Spinner label="Loading lessons" />}
      {lessons.isError && (
        <ErrorNote error={lessons.error} retry={() => void lessons.refetch()} />
      )}

      {lessons.isSuccess && (
        <ul className="space-y-3">
          {lessons.data.map((lesson) => {
            const state = progressBySlug.get(lesson.slug);
            return (
              <li key={lesson.id}>
                <Link to={`/lessons/${lesson.slug}`} className="block">
                  <Card className="space-y-2 transition-colors hover:border-taegeuk-blue">
                    <div className="flex items-center justify-between">
                      <h2 className="font-bold">{lesson.title}</h2>
                      {state?.status === "completed" && (
                        <span className="rounded-full bg-jade/10 px-2.5 py-0.5 text-[11px] font-semibold text-jade">
                          Completed
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-ink-soft">{lesson.description}</p>
                    <MeterBar
                      label="Phrases passed"
                      used={state?.phrases_completed ?? 0}
                      limit={lesson.phrase_count}
                    />
                  </Card>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
