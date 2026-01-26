from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.user import Base

class ExamAssignment(Base):
    __tablename__ = "exam_assignments"
    __table_args__ = (
        UniqueConstraint("exam_id", "user_id", name="uq_exam_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
