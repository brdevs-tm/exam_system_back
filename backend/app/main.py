from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings

from app.api.routes import router as api_router
from app.api.teacher_exams import router as teacher_router
from app.api.student_exams import router as student_router
from app.api.student_attempts import router as student_attempt_router
from app.api.cheat import router as cheat_router
from app.api.auth import router as auth_router
from app.ws.routes import router as ws_router


app = FastAPI(title=settings.APP_NAME)

# Middleware (avval qo‘yiladi)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router)
app.include_router(auth_router)
app.include_router(teacher_router)
app.include_router(student_router)
app.include_router(student_attempt_router)
app.include_router(cheat_router)
app.include_router(ws_router)


# Models (dev/test uchun)
class RegisterPayload(BaseModel):
    telegram_id: int
    full_name: str | None = None


# Endpoints (health + debug)
@app.post("/api/bot/register")
async def bot_register(payload: RegisterPayload):
    print("✅ REGISTER HIT:", payload.model_dump())
    return {"ok": True}


@app.get("/")
async def root():
    return {"status": "Backend Running", "app": settings.APP_NAME}
