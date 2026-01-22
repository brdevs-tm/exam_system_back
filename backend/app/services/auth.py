import jwt
from datetime import datetime, timedelta
from app.core.config import settings

def create_webapp_token(user_id: int):
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=5),
        "type": "webapp"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
