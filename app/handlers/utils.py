# app/handlers/utils.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
router = Router()

@router.message(Command("whoami"))
async def whoami(message: Message):
    await message.answer(f"🆔 Sizning ID: <code>{message.from_user.id}</code>")
