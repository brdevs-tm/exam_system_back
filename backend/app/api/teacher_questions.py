from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_teacher
from app.core.database import get_db
from app.models.exam import Exam
from app.models.question import Question
from app.models.user import User

router = APIRouter(prefix="/api/teacher", tags=["teacher"])

VALID = {"A", "B", "C", "D"}

class QuestionCreateIn(BaseModel):
    text: str = Field(min_length=1)
    option_a: str = Field(min_length=1)
    option_b: str = Field(min_length=1)
    option_c: str = Field(min_length=1)
    option_d: str = Field(min_length=1)
    correct: str = Field(min_length=1, max_length=1)
    points: int = 1

@router.post("/exams/{exam_id}/questions")
async def add_question(
    exam_id: int,
    payload: QuestionCreateIn,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    corr = (payload.correct or "").upper().strip()
    if corr not in VALID:
        raise HTTPException(status_code=400, detail="correct must be A/B/C/D")
    if payload.points < 1:
        raise HTTPException(status_code=400, detail="points must be >= 1")

    q = await db.execute(select(Exam).where(Exam.id == exam_id, Exam.created_by == teacher.id))
    exam = q.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    item = Question(
        exam_id=exam_id,
        text=payload.text.strip(),
        option_a=payload.option_a.strip(),
        option_b=payload.option_b.strip(),
        option_c=payload.option_c.strip(),
        option_d=payload.option_d.strip(),
        correct=corr,
        points=payload.points,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"ok": True, "id": item.id}

@router.get("/exams/{exam_id}/questions")
async def list_questions(
    exam_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(Exam).where(Exam.id == exam_id, Exam.created_by == teacher.id))
    exam = q.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    q2 = await db.execute(
        select(Question).where(Question.exam_id == exam_id).order_by(Question.id.asc())
    )
    items = q2.scalars().all()

    return {
        "ok": True,
        "items": [
            {
                "id": x.id,
                "text": x.text,
                "option_a": x.option_a,
                "option_b": x.option_b,
                "option_c": x.option_c,
                "option_d": x.option_d,
                "correct": x.correct,
                "points": x.points,
            }
            for x in items
        ],
    }

@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: int,
    teacher: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db),
):
    # faqat o‘zining examidagi savolni o‘chira olsin
    q = await db.execute(
        select(Question, Exam)
        .join(Exam, Exam.id == Question.exam_id)
        .where(Question.id == question_id, Exam.created_by == teacher.id)
    )
    row = q.first()
    if not row:
        raise HTTPException(status_code=404, detail="Question not found")

    await db.execute(delete(Question).where(Question.id == question_id))
    await db.commit()
    return {"ok": True}
