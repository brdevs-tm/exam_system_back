from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_student
from app.core.database import get_db
from app.models.cheat_log import CheatLog
from app.models.user import User
from app.ws.hub import hub

router = APIRouter(prefix="/api/cheat", tags=["anti-cheat"])


class CheatIn(BaseModel):
    event: str
    attempt_id: int | None = None
    exam_id: int | None = None


@router.post("/log")
async def log_cheat(
    payload: CheatIn,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    log = CheatLog(user_id=student.id, event=payload.event)
    db.add(log)
    await db.commit()

    # 🔥 real-time broadcast (xatolik bo'lsa ham log saqlanib qoladi)
    try:
        await hub.broadcast(
            {
                "type": "CHEAT_EVENT",
                "student_id": student.id,
                "telegram_id": student.telegram_id,
                "event": payload.event,
                "attempt_id": payload.attempt_id,
                "exam_id": payload.exam_id,
            }
        )
    except Exception as e:
        print("WS broadcast error:", e)

    return {"ok": True}
