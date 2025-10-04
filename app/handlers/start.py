# -*- coding: utf-8 -*-
# app/handlers/start.py
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

# Locales (fallback bilan)
try:
    from ..locales import L as LOCALES
except Exception:
    LOCALES = {"uz": {"greet_prompt": "Iltimos, tilni tanlang:"}}

# 3 ta til tugmalari (inline)
from ..keyboards.inline import LANG_KB

# DB (yangi userni saqlash uchun)
try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    # 📝 foydalanuvchini DBga kiritib qo'yamiz
    if db:
        db.init()  # xavfsizlik uchun
        db.upsert_user(
            user_id=message.from_user.id,
            username=message.from_user.username or None,
            name=message.from_user.full_name or None,
        )

    name = message.from_user.full_name or message.from_user.first_name or ""

    greet_uz = f"Assalomu alaykum, {name}"
    greet_en = f"Hello {name}"
    greet_ru = f"Привет {name}"

    prompt = LOCALES.get("uz", {}).get("greet_prompt", "Iltimos, tilni tanlang:")

    text = f"{greet_uz}\n{greet_en}\n{greet_ru}\n\n{prompt}"
    await message.answer(text, reply_markup=LANG_KB)
