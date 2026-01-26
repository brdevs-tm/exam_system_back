import asyncio
from app.core.database import engine
from app.models.user import Base
from app.models.exam import Exam  # noqa: F401
from app.models.cheat_log import CheatLog  # noqa: F401
from app.models.exam_assignment import ExamAssignment  # noqa: F401
from app.models.exam_attempt import ExamAttempt

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(main())
