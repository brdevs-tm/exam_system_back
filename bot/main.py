import asyncio

from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.me import router as me_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Routers
    dp.include_router(start_router)
    dp.include_router(me_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
