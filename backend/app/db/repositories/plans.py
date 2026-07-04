from app.core.errors import NotFoundError
from app.db.client import Database
from app.schemas.plans import Plan


async def get_plan(db: Database, plan_id: str) -> Plan:
    row = await db.select_one("plans", filters={"id": f"eq.{plan_id}"})
    if row is None:
        raise NotFoundError(f"Plan '{plan_id}' does not exist.")
    return Plan.model_validate(row)
