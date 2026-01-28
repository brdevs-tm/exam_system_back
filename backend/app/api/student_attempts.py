from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_student
from app.core.database import get_db
from app.models.exam_assignment import ExamAssignment
from app.models.exam_attempt import ExamAttempt
from app.models.user import User
from app.ws.hub import hub

router = APIRouter(prefix="/api/student", tags=["student-attempts"])


@router.post("/exams/{exam_id}/start")
async def start_exam(
    exam_id: int,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    # assignment check
    q = await db.execute(
        select(ExamAssignment).where(
            ExamAssignment.exam_id == exam_id,
            ExamAssignment.user_id == student.id,
        )
    )
    if not q.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Exam not assigned")

    # active attempt bor-mi?
    q2 = await db.execute(
        select(ExamAttempt).where(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.user_id == student.id,
            ExamAttempt.is_active == True,
        )
    )
    existing = q2.scalar_one_or_none()
    if existing:
        # Frontend kutayotgan formatga yaqin qilib qaytaramiz
        return {
            "ok": True,
            "status": "already_started",
            "attempt_id": existing.id,
            "exam_id": exam_id,
            "student": {
                "telegram_id": student.telegram_id,
                "full_name": student.full_name,
            },
            "started_at": (
                existing.started_at.isoformat()
                if getattr(existing, "started_at", None)
                else None
            ),
        }

    now = datetime.now(timezone.utc)

    # Eslatma: sening model field'laringga moslab berildi:
    # oldin (exam_id, user_id) ishlatilgan, shuni saqlab qoldik.
    attempt = ExamAttempt(
        exam_id=exam_id,
        user_id=student.id,
        started_at=now,
        is_active=True,
    )

    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    # 🔥 real-time broadcast (yiqilsa ham start ishlasin)
    try:
        await hub.broadcast(
            {
                "type": "ATTEMPT_STARTED",
                "student_id": student.id,
                "telegram_id": student.telegram_id,
                "exam_id": exam_id,
                "attempt_id": attempt.id,
            }
        )
    except Exception as e:
        print("WS broadcast error:", e)

    # 🔥 MUHIM: Frontend kutayotgan format
    return {
        "ok": True,
        "attempt_id": attempt.id,
        "exam_id": exam_id,
        "student": {
            "telegram_id": student.telegram_id,
            "full_name": student.full_name,
        },
        "started_at": attempt.started_at.isoformat()
        if getattr(attempt, "started_at", None)
        else now.isoformat(),
    }


@router.post("/attempts/{attempt_id}/finish")
async def finish_exam(
    attempt_id: int,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(ExamAttempt).where(
            ExamAttempt.id == attempt_id,
            ExamAttempt.user_id == student.id,
            ExamAttempt.is_active == True,
        )
    )
    attempt = q.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    attempt.is_active = False
    attempt.finished_at = datetime.utcnow()
    await db.commit()

    # 🔥 real-time broadcast (yiqilsa ham finish ishlasin)
    try:
        await hub.broadcast(
            {
                "type": "ATTEMPT_FINISHED",
                "student_id": student.id,
                "telegram_id": student.telegram_id,
                "attempt_id": attempt_id,
            }
        )
    except Exception as e:
        print("WS broadcast error:", e)

    return {"ok": True}
