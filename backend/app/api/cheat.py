from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_student
from app.core.database import get_db
from app.models.cheat_log import CheatLog
from app.models.user import User
from app.ws.manager import manager
from app.ws.monitor_store import monitor_store

router = APIRouter(prefix="/api/cheat", tags=["anti-cheat"])


class CheatIn(BaseModel):
    event: str
    attempt_id: int | None = None
    exam_id: int | None = None
    detail: str | None = None
    ts: str | None = None  # client yuborsa, saqlab qo'yamiz


@router.post("/log")
async def log_cheat(
    payload: CheatIn,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    # 1) DB log
    db_log = CheatLog(user_id=student.id, event=payload.event)
    db.add(db_log)
    await db.commit()

    # 2) history + live event object
    ts = payload.ts or datetime.now(timezone.utc).isoformat()
    event_obj = {
        "id": f"{payload.attempt_id}-{int(datetime.now().timestamp() * 1000)}",
        "ts": ts,
        "event": payload.event,
        "attempt_id": payload.attempt_id,
        "exam_id": payload.exam_id,
        "telegram_id": student.telegram_id,
        "full_name": student.full_name,
        "role": student.role,
        "detail": payload.detail,
    }

    # history
    if payload.attempt_id is not None:
        monitor_store.add(payload.attempt_id, event_obj)

    # live broadcast (yiqilsa ham API yiqilmaydi)
    try:
        await manager.broadcast_json({"type": "event", "event": event_obj})
    except Exception as e:
        print("WS broadcast error:", e)

    return {"ok": True}
