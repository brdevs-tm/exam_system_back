from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)

    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    started_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User", back_populates="attempts")
