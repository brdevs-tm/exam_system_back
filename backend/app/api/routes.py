import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth import create_webapp_token

router = APIRouter(prefix="/api", tags=["bot"])

# old: ADMIN_SECRET = "teachme123"
def get_teacher_secret() -> str:
    # .env dan o‘qiydi, bo‘lmasa fallback
    return os.getenv("TEACHER_SECRET", "teachme123")


class BotRegisterIn(BaseModel):
    telegram_id: int
    full_name: str | None = None


@router.post("/bot/register")
async def bot_register(payload: BotRegisterIn, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.telegram_id == payload.telegram_id))
    user = q.scalar_one_or_none()

    if user:
        if payload.full_name and user.full_name != payload.full_name:
            user.full_name = payload.full_name
        await db.commit()
        return {"ok": True, "status": "updated", "user_id": user.id}

    user = User(
        telegram_id=payload.telegram_id,
        full_name=payload.full_name or "Unknown",
        role="student",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"ok": True, "status": "created", "user_id": user.id}


class WebAppTokenIn(BaseModel):
    telegram_id: int


@router.post("/bot/webapp-token")
async def bot_webapp_token(payload: WebAppTokenIn, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.telegram_id == payload.telegram_id))
    user = q.scalar_one_or_none()

    if not user:
        return {"ok": False, "error": "User not registered"}

    token = create_webapp_token(user.id)

    return {
        "ok": True,
        "token": token,
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "full_name": user.full_name,
            "role": user.role,
        },
    }


class BecomeTeacherIn(BaseModel):
    telegram_id: int
    secret: str
    full_name: str | None = None  # qo‘shdik (ixtiyoriy)


@router.post("/bot/become-teacher")
async def become_teacher(payload: BecomeTeacherIn, db: AsyncSession = Depends(get_db)):
    if payload.secret != get_teacher_secret():
        raise HTTPException(status_code=403, detail="Wrong secret")

    q = await db.execute(select(User).where(User.telegram_id == payload.telegram_id))
    user = q.scalar_one_or_none()

    # ✅ user yo‘q bo‘lsa ham yaratib yuboramiz
    if not user:
        user = User(
            telegram_id=payload.telegram_id,
            full_name=payload.full_name or "Unknown",
            role="teacher",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return {"ok": True, "status": "created_as_teacher", "user_id": user.id}

    # ✅ bor bo‘lsa teacherga o‘tkazamiz
    user.role = "teacher"
    if payload.full_name and user.full_name != payload.full_name:
        user.full_name = payload.full_name

    await db.commit()
    return {"ok": True, "status": "updated_to_teacher", "user_id": user.id}
