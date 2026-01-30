from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.api.deps import require_student
from app.models.user import User
from app.models.exam import Exam
from app.models.exam_assignment import ExamAssignment
from app.models.exam_attempt import ExamAttempt
from app.models.question import Question
from app.models.attempt_answer import AttemptAnswer

router = APIRouter(prefix="/api/student", tags=["student"])


@router.post("/exams/{exam_id}/start")
async def start_exam(
    exam_id: int,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    # assignedmi?
    q = await db.execute(
        select(ExamAssignment).where(
            ExamAssignment.exam_id == exam_id,
            ExamAssignment.user_id == student.id,
        )
    )
    if not q.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Exam not assigned")

    # exam active-mi?
    q2 = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = q2.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if not getattr(exam, "is_active", False):
        raise HTTPException(status_code=400, detail="Exam is not active")

    # already active attempt bo‘lsa qaytaramiz
    q3 = await db.execute(
        select(ExamAttempt).where(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.user_id == student.id,
            ExamAttempt.is_active == True,  # noqa
        )
    )
    active = q3.scalar_one_or_none()
    if active:
        return {"ok": True, "attempt_id": active.id, "status": "existing"}

    attempt = ExamAttempt(
        exam_id=exam_id,
        user_id=student.id,
        started_at=datetime.utcnow(),
        is_active=True,
        score=0,
        total=0,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return {"ok": True, "attempt_id": attempt.id, "status": "created"}


@router.get("/attempts/{attempt_id}")
async def get_attempt(
    attempt_id: int,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(ExamAttempt).where(ExamAttempt.id == attempt_id, ExamAttempt.user_id == student.id))
    attempt = q.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    q2 = await db.execute(select(Exam).where(Exam.id == attempt.exam_id))
    exam = q2.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    q3 = await db.execute(select(Question).where(Question.exam_id == exam.id).order_by(Question.id.asc()))
    questions = q3.scalars().all()

    # old answers
    q4 = await db.execute(select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id))
    answers = q4.scalars().all()
    ans_map = {a.question_id: a.selected for a in answers}

    return {
        "ok": True,
        "attempt": {
            "id": attempt.id,
            "exam_id": attempt.exam_id,
            "is_active": attempt.is_active,
            "started_at": attempt.started_at,
            "finished_at": attempt.finished_at,
        },
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "starts_at": exam.starts_at,
            "ends_at": exam.ends_at,
        },
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "options": {
                    "A": q.option_a,
                    "B": q.option_b,
                    "C": q.option_c,
                    "D": q.option_d,
                },
                "selected": ans_map.get(q.id),
                "points": q.points,
            }
            for q in questions
        ],
    }


class AnswerIn(BaseModel):
    question_id: int
    selected: str = Field(pattern="^[ABCD]$")


@router.post("/attempts/{attempt_id}/answer")
async def submit_answer(
    attempt_id: int,
    payload: AnswerIn,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(ExamAttempt).where(ExamAttempt.id == attempt_id, ExamAttempt.user_id == student.id))
    attempt = q.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if not attempt.is_active:
        raise HTTPException(status_code=400, detail="Attempt is finished")

    # question belongs to this exam
    q2 = await db.execute(
        select(Question).where(
            Question.id == payload.question_id,
            Question.exam_id == attempt.exam_id,
        )
    )
    question = q2.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # upsert answer
    q3 = await db.execute(
        select(AttemptAnswer).where(
            AttemptAnswer.attempt_id == attempt.id,
            AttemptAnswer.question_id == question.id,
        )
    )
    ans = q3.scalar_one_or_none()
    if ans:
        ans.selected = payload.selected
    else:
        ans = AttemptAnswer(attempt_id=attempt.id, question_id=question.id, selected=payload.selected)
        db.add(ans)

    await db.commit()
    return {"ok": True}


@router.post("/attempts/{attempt_id}/finish")
async def finish_attempt(
    attempt_id: int,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(ExamAttempt).where(ExamAttempt.id == attempt_id, ExamAttempt.user_id == student.id))
    attempt = q.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if not attempt.is_active:
        return {"ok": True, "status": "already_finished"}

    # questions
    q2 = await db.execute(select(Question).where(Question.exam_id == attempt.exam_id))
    questions = q2.scalars().all()
    if not questions:
        raise HTTPException(status_code=400, detail="No questions in this exam")

    q3 = await db.execute(select(AttemptAnswer).where(AttemptAnswer.attempt_id == attempt.id))
    answers = q3.scalars().all()
    ans_map = {a.question_id: a.selected for a in answers}

    total = 0
    score = 0
    for qu in questions:
        total += int(qu.points or 0)
        if ans_map.get(qu.id) == qu.correct:
            score += int(qu.points or 0)

    attempt.total = total
    attempt.score = score
    attempt.is_active = False
    attempt.finished_at = datetime.utcnow()

    await db.commit()
    return {"ok": True, "score": score, "total": total, "status": "finished"}


@router.get("/attempts/{attempt_id}/result")
async def attempt_result(
    attempt_id: int,
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(ExamAttempt).where(ExamAttempt.id == attempt_id, ExamAttempt.user_id == student.id))
    attempt = q.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    return {
        "ok": True,
        "attempt": {
            "id": attempt.id,
            "exam_id": attempt.exam_id,
            "started_at": attempt.started_at,
            "finished_at": attempt.finished_at,
            "is_active": attempt.is_active,
            "score": attempt.score,
            "total": attempt.total,
        },
    }
