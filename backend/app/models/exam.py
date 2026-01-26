from sqlalchemy import String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.models.user import Base

class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
