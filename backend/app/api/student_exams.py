from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import require_student
from app.models.user import User
from app.models.exam import Exam
from app.models.exam_assignment import ExamAssignment

router = APIRouter(prefix="/api/student", tags=["student"])

@router.get("/exams")
async def my_exams(
    student: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(
        select(Exam)
        .join(ExamAssignment, ExamAssignment.exam_id == Exam.id)
        .where(ExamAssignment.user_id == student.id)
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
