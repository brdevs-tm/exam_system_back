from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_teacher
from app.core.database import get_db
from app.models.exam import Exam
from app.models.exam_assignment import ExamAssignment
from app.models.user import User
from app.services.telegram import tg_send_message

router = APIRouter(prefix="/api/teacher", tags=["teacher"])


def ensure_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class ExamCreateIn(BaseModel):
    title: str
    description: str | None = None
    starts_at: datetime
    ends_at: datetime


@router.post("/exams")
async def create_exam(
    payload: ExamCreateIn,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    starts_at = ensure_aware_utc(payload.starts_at)
    ends_at = ensure_aware_utc(payload.ends_at)

    if ends_at <= starts_at:
        raise HTTPException(status_code=400, detail="ends_at must be after starts_at")

    exam = Exam(
        title=payload.title.strip(),
        description=payload.description,
        starts_at=starts_at,
        ends_at=ends_at,
        is_active=False,
        created_by=teacher.id,
    )
    db.add(exam)
    await db.commit()
    await db.refresh(exam)

    if getattr(teacher, "telegram_id", None):
        try:
            await tg_send_message(
                chat_id=teacher.telegram_id,
                text=(
                    f"✅ Exam yaratildi: {exam.title}\n"
                    f"Start: {exam.starts_at.isoformat()}\n"
                    f"End: {exam.ends_at.isoformat()}"
                ),
            )
        except Exception as e:
            print("Telegram notify error:", e)

    return {"ok": True, "exam_id": exam.id}


@router.get("/exams")
async def list_my_exams(
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(Exam)
        .where(Exam.created_by == teacher.id)
        .order_by(Exam.id.desc())
    )
    exams = q.scalars().all()

    return {
        "ok": True,
        "items": [
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "starts_at": e.starts_at.isoformat() if e.starts_at else None,
                "ends_at": e.ends_at.isoformat() if e.ends_at else None,
                "is_active": bool(e.is_active),
            }
            for e in exams
        ],
    }


class ExamActiveIn(BaseModel):
    is_active: bool


@router.patch("/exams/{exam_id}/active")
async def set_exam_active(
    exam_id: int,
    payload: ExamActiveIn,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.created_by == teacher.id)
    )
    exam = q.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    exam.is_active = bool(payload.is_active)
    await db.commit()
    await db.refresh(exam)

    return {"ok": True, "exam_id": exam.id, "is_active": bool(exam.is_active)}


@router.patch("/exams/{exam_id}/toggle")
async def toggle_exam_active(
    exam_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.created_by == teacher.id)
    )
    exam = q.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    exam.is_active = not bool(exam.is_active)
    await db.commit()
    await db.refresh(exam)

    return {"ok": True, "exam_id": exam.id, "is_active": bool(exam.is_active)}


class AssignIn(BaseModel):
    student_telegram_id: int


@router.post("/exams/{exam_id}/assign")
async def assign_exam(
    exam_id: int,
    payload: AssignIn,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.created_by == teacher.id)
    )
    exam = q.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    q2 = await db.execute(select(User).where(User.telegram_id == payload.student_telegram_id))
    student = q2.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.role != "student":
        raise HTTPException(status_code=400, detail="Target user is not a student")

    assign = ExamAssignment(exam_id=exam.id, user_id=student.id)
    db.add(assign)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        return {"ok": True, "status": "already_assigned"}

    if getattr(student, "telegram_id", None):
        try:
            await tg_send_message(
                chat_id=student.telegram_id,
                text=(
                    f"📝 Sizga yangi imtihon biriktirildi: {exam.title}\n"
                    f"Boshlanish: {exam.starts_at.isoformat()}"
                ),
            )
        except Exception as e:
            print("Telegram notify error:", e)

    return {"ok": True, "status": "assigned"}
