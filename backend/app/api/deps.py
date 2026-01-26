from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.services.auth import decode_webapp_token


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.replace("Bearer ", "").strip()
    try:
        user_id = decode_webapp_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token type")

    q = await db.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="Teacher only")
    return user


def require_student(user: User = Depends(get_current_user)) -> User:
    if user.role != "student":
        raise HTTPException(status_code=403, detail="Student only")
    return user
