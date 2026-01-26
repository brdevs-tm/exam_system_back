from sqlalchemy import ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.user import Base

class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
