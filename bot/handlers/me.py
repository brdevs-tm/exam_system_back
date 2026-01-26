from aiogram import Router, types
from aiogram.filters import Command

router = Router()

@router.message(Command("me"))
async def me_cmd(message: types.Message):
    await message.answer(
        "👤 Your info:\n"
        f"Telegram ID: {message.from_user.id}\n"
        f"Name: {message.from_user.full_name}"
    )
