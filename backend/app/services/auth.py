import jwt
from app.core.config import settings
from datetime import datetime, timedelta
from app.core.config import settings

def create_webapp_token(user_id: int):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "type": "webapp"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_webapp_token(token: str) -> int | None:
    decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    if decoded.get("type") != "webapp":
        return None
    return int(decoded["sub"])