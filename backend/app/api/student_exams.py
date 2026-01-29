from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_student
from app.core.database import get_db
from app.models.exam import Exam
from app.models.exam_assignment import ExamAssignment
from app.models.user import User

router = APIRouter(prefix="/api/student", tags=["student"])


@router.get("/exams")
async def my_exams(
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(Exam)
        .join(ExamAssignment, ExamAssignment.exam_id == Exam.id)
        .where(ExamAssignment.user_id == student.id)  # ✅ inactive bo‘lsa ham chiqadi
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
