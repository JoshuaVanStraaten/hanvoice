from fastapi import APIRouter

from app.api.deps import CurrentUser, Db
from app.db.repositories import content
from app.db.repositories import progress as progress_repo
from app.schemas.progress import LessonProgressItem, ProgressResponse, ScenarioProgressItem

router = APIRouter(tags=["progress"])


@router.get("/progress", response_model=ProgressResponse)
async def get_progress(user: CurrentUser, db: Db) -> ProgressResponse:
    lessons = {int(row["id"]): row for row in await content.list_published_lessons(db)}
    scenarios = {int(row["id"]): row for row in await content.list_published_scenarios(db)}
    lesson_rows = await progress_repo.list_lesson_progress(db, user.id)
    scenario_rows = await progress_repo.list_scenario_progress(db, user.id)

    lesson_items = []
    for row in lesson_rows:
        lesson = lessons.get(int(row["lesson_id"]))
        if lesson is None:
            continue  # progress on an unpublished/removed lesson stays hidden
        phrases = await content.list_lesson_phrases(db, int(lesson["id"]))
        lesson_items.append(
            LessonProgressItem(
                lesson_id=int(lesson["id"]),
                lesson_slug=str(lesson["slug"]),
                lesson_title=str(lesson["title"]),
                status=row["status"],
                phrases_completed=int(row["phrases_completed"]),
                phrase_count=len(phrases),
                best_pronunciation_score=row.get("best_pronunciation_score"),
            )
        )

    scenario_items = []
    for row in scenario_rows:
        scenario = scenarios.get(int(row["scenario_id"]))
        if scenario is None:
            continue
        scenario_items.append(
            ScenarioProgressItem(
                scenario_id=int(scenario["id"]),
                scenario_slug=str(scenario["slug"]),
                scenario_title=str(scenario["title"]),
                status=row["status"],
                times_completed=int(row["times_completed"]),
                last_session_id=row.get("last_session_id"),
            )
        )

    return ProgressResponse(lessons=lesson_items, scenarios=scenario_items)
