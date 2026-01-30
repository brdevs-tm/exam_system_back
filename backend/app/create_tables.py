import asyncio

from app.core.database import engine
from app.models.user import Base

from app.models.user import User
from app.models.exam import Exam
from app.models.exam_assignment import ExamAssignment
from app.models.exam_attempt import ExamAttempt
from app.models.cheat_log import CheatLog

from app.models.question import Question
from app.models.attempt_answer import AttemptAnswer


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(main())
