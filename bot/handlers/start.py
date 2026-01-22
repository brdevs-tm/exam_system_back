import asyncio
import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import API_URL  # ✅ bot.config emas

WEBAPP_URL = "http://localhost:3000"

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    payload = {
        "telegram_id": message.from_user.id,
        "full_name": (message.from_user.full_name or "").strip() or None
    }

    try:
        async with aiohttp.ClientSession() as session:
            # register (response shart emas)
            await session.post(f"{API_URL}/api/bot/register", json=payload)

            # webapp token
            async with session.post(
                f"{API_URL}/api/bot/webapp-token",
                json={"telegram_id": message.from_user.id},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()

    except aiohttp.ClientError:
        await message.answer("❌ Backendga ulanib bo‘lmadi (network/URL).")
        return
    except asyncio.TimeoutError:
        await message.answer("❌ Backend javobi kechikdi (timeout).")
        return

    if not data.get("ok"):
        await message.answer("❌ WebApp token olishda xatolik")
        return

    token = data["token"]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📝 Imtihon Paneliga Kirish",
            web_app=WebAppInfo(url=f"{WEBAPP_URL}?token={token}")
        )
    ]])

    await message.answer("Panelga kirish uchun tugmani bosing:", reply_markup=keyboard)
