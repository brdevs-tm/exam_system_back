from __future__ import annotations

from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base  # <-- SHU

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), index=True
    )

    text: Mapped[str] = mapped_column(Text)

    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)

    correct: Mapped[str] = mapped_column(String(1))  # "A"|"B"|"C"|"D"
    points: Mapped[int] = mapped_column(Integer, default=1)

    exam = relationship("Exam", back_populates="questions")
