from datetime import datetime

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
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=400, detail="ends_at must be after starts_at")

    exam = Exam(
        title=payload.title.strip(),
        description=payload.description,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        is_active=False,
        created_by=teacher.id,
    )
    db.add(exam)
    await db.commit()
    await db.refresh(exam)

    # Teacher'ga bot orqali xabar (demo) — exam create'ni yiqitmaydi
    if teacher.telegram_id:
        try:
            await tg_send_message(
                chat_id=teacher.telegram_id,
                text=(
                    f"✅ Exam yaratildi: {exam.title}\n"
                    f"Start: {exam.starts_at}\n"
                    f"End: {exam.ends_at}"
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
                "starts_at": e.starts_at,
                "ends_at": e.ends_at,
                "is_active": e.is_active,
            }
            for e in exams
        ],
    }


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

    if student.telegram_id:
        try:
            await tg_send_message(
                chat_id=student.telegram_id,
                text=(
                    f"📝 Sizga yangi imtihon biriktirildi: {exam.title}\n"
                    f"Boshlanish: {exam.starts_at}"
                ),
            )
        except Exception as e:
            print("Telegram notify error:", e)

    return {"ok": True, "status": "assigned"}
