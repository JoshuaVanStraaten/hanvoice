import { Link } from "react-router-dom";

import { Card, ErrorNote, MeterBar, SkeletonCards } from "../components/ui";
import { useLessons, useProgress } from "../hooks/queries";
import type { LessonSummary } from "../lib/types";

/** Lessons arrive sorted; group consecutive runs by section label so the
 * list reads as a course ("Read & write Hangul" → "Speak"). */
function groupBySection(lessons: LessonSummary[]): Array<{ section: string; lessons: LessonSummary[] }> {
  const groups: Array<{ section: string; lessons: LessonSummary[] }> = [];
  for (const lesson of lessons) {
    const last = groups[groups.length - 1];
    if (last && last.section === lesson.section) {
      last.lessons.push(lesson);
    } else {
      groups.push({ section: lesson.section, lessons: [lesson] });
    }
  }
  return groups;
}

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
          Learn to read, write, and say Korean — from zero, one small step at a time.
        </p>
      </header>

      {lessons.isPending && <SkeletonCards count={4} label="Loading lessons" />}
      {lessons.isError && (
        <ErrorNote error={lessons.error} retry={() => void lessons.refetch()} />
      )}

      {lessons.isSuccess &&
        groupBySection(lessons.data).map((group) => (
          <section key={group.section || "lessons"} className="space-y-3">
            {group.section && (
              <h2 className="text-sm font-semibold tracking-wide text-ink-soft uppercase">
                {group.section}
              </h2>
            )}
            <ul className="space-y-3">
              {group.lessons.map((lesson, index) => {
                const state = progressBySlug.get(lesson.slug);
                return (
                  <li
                    key={lesson.id}
                    className="rise-in"
                    style={{ animationDelay: `${Math.min(index * 45, 270)}ms` }}
                  >
                    <Link to={`/lessons/${lesson.slug}`} className="block">
                      <Card className="space-y-2 transition-colors hover:border-taegeuk-blue">
                        <div className="flex items-center justify-between">
                          <h3 className="font-bold">{lesson.title}</h3>
                          {state?.status === "completed" && (
                            <span className="rounded-full bg-jade/10 px-2.5 py-0.5 text-[11px] font-semibold text-jade">
                              Completed
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-ink-soft">{lesson.description}</p>
                        <MeterBar
                          label="Steps passed"
                          used={state?.blocks_completed ?? 0}
                          limit={lesson.block_count}
                        />
                      </Card>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </section>
        ))}
    </div>
  );
}
