from fastapi import FastAPI
from app.core.config import settings
from app.api.routes import router as api_router

from pydantic import BaseModel

app = FastAPI()

class RegisterPayload(BaseModel):
    telegram_id: int
    full_name: str | None = None

@app.post("/api/bot/register")
async def bot_register(payload: RegisterPayload):
    print("✅ REGISTER HIT:", payload.model_dump())
    return {"ok": True}

app = FastAPI(title=settings.APP_NAME)
app.include_router(api_router)

@app.get("/")
async def root():
    return {"status": "Backend Running", "app": settings.APP_NAME}
