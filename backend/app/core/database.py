from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from sqlalchemy.orm import DeclarativeBase

# ==========================
# SQLALCHEMY BASE (MODELS)
# ==========================
Base = declarative_base()

class Base(DeclarativeBase):
    pass

# ==========================
# DATABASE CONFIG
# ==========================
DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:"
    f"{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:"
    f"{settings.DB_PORT}/"
    f"{settings.DB_NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ==========================
# FASTAPI DEPENDENCY
# ==========================
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ==========================
# DEBUG
# ==========================
print("✅ database.py LOADED OK")
print("✅ Base exists:", "Base" in globals())
