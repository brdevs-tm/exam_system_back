from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(primary_key=True)

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("exam_attempts.id", ondelete="CASCADE"),
        index=True,
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
    )

    # masalan tanlangan javob / text:
    answer: Mapped[str | None] = mapped_column(nullable=True)

    # ✅ back_populates nomi ExamAttempt dagi "answers" ga mos bo‘lsin
    attempt = relationship("ExamAttempt", back_populates="answers")

    # ixtiyoriy:
    question = relationship("Question")
