from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jwt

from app.core.config import settings  # JWT_SECRET shu yerda bo'lsin

router = APIRouter(prefix="/api/auth", tags=["auth"])

class VerifyIn(BaseModel):
    token: str

@router.post("/verify")
def verify_token(payload: VerifyIn):
    try:
        data = jwt.decode(payload.token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # data ichida sen qanday qo'yganingga qarab o'zgaradi:
    # masalan: {"sub": user_id, "type":"webapp", "exp": ...}
    return {"ok": True, "payload": data}
