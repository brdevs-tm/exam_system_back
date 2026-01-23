import asyncio
import aiohttp
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from config import API_URL, WEBAPP_URL

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    payload = {
        "telegram_id": message.from_user.id,
        "full_name": (message.from_user.full_name or "").strip() or None
    }

    try:
        async with aiohttp.ClientSession() as session:
            await session.post(f"{API_URL}/api/bot/register", json=payload)

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

    if not WEBAPP_URL:
        await message.answer("❌ WEBAPP_URL sozlanmagan. .env ga WebApp link kiriting.")
        return

    token = data["token"]

    # ✅ Fallback: telegram_id ham berib yuboramiz
    webapp_link = f"{WEBAPP_URL}?token={token}&telegram_id={message.from_user.id}"

    is_localhost = WEBAPP_URL.startswith("http://localhost") or WEBAPP_URL.startswith("http://127.0.0.1")
    if is_localhost:
        await message.answer(
            "❌ Telegram WebApp localhost HTTP linklarni qabul qilmaydi.\n"
            "Iltimos, HTTPS tunnel (masalan, ngrok) orqali domen oling.\n"
            f"Joriy link: {webapp_link}"
        )
        return

    if not WEBAPP_URL.startswith("https://"):
        await message.answer(
            "❌ Telegram WebApp faqat HTTPS linklarni qabul qiladi.\n"
            "Iltimos, WEBAPP_URL uchun HTTPS domen (masalan, ngrok) sozlang.\n"
            f"Joriy link: {webapp_link}"
        )
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="📝 Imtihon Paneliga Kirish",
            web_app=WebAppInfo(url=webapp_link)
        )
    ]])

    await message.answer("Panelga kirish uchun tugmani bosing:", reply_markup=keyboard)
