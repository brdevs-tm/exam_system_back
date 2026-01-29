from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    selected_option = Column(String(1), nullable=False)  # A | B | C | D
