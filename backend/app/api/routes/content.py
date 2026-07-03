from fastapi import APIRouter

from app.api.deps import CurrentUser, Db
from app.db.repositories import content
from app.schemas.content import LessonDetail, LessonPhrase, LessonSummary, ScenarioSummary

router = APIRouter(tags=["content"])


@router.get("/lessons", response_model=list[LessonSummary])
async def list_lessons(user: CurrentUser, db: Db) -> list[LessonSummary]:
    lessons = await content.list_published_lessons(db)
    summaries = []
    for row in lessons:
        phrases = await content.list_lesson_phrases(db, int(row["id"]))
        summaries.append(LessonSummary(**row, phrase_count=len(phrases)))
    return summaries


@router.get("/lessons/{slug}", response_model=LessonDetail)
async def get_lesson(slug: str, user: CurrentUser, db: Db) -> LessonDetail:
    lesson = await content.get_published_lesson(db, slug)
    phrases = await content.list_lesson_phrases(db, int(lesson["id"]))
    return LessonDetail(
        **lesson, phrases=[LessonPhrase.model_validate(p) for p in phrases]
    )


@router.get("/scenarios", response_model=list[ScenarioSummary])
async def list_scenarios(user: CurrentUser, db: Db) -> list[ScenarioSummary]:
    rows = await content.list_published_scenarios(db)
    return [ScenarioSummary.model_validate(row) for row in rows]
