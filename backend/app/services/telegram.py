import aiohttp
from app.core.config import settings

async def tg_send_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            return await resp.json()
