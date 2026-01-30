from __future__ import annotations

from sqlalchemy import String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ✅ asyncpg bilan muammo bo‘lmasligi uchun timezone=True
    starts_at: Mapped[object] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[object] = mapped_column(DateTime(timezone=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")

    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan",)

