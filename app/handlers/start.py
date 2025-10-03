# -*- coding: utf-8 -*-
# app/handlers/start.py

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# Locales xavfsiz import (fallback bilan)
try:
    from ..locales import L as LOCALES
except Exception:
    LOCALES = {"uz": {"greet_prompt": "Iltimos, tilni tanlang:"}}

# 3 ta til bitta qatorda inline tugmalar
from ..keyboards.inline import LANG_KB

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    name = message.from_user.full_name or message.from_user.first_name or ""

    # 3 tilda salom
    greet_uz = f"Assalomu alaykum, {name}"
    greet_en = f"Hello {name}"
    greet_ru = f"Привет {name}"

    prompt = LOCALES.get("uz", {}).get("greet_prompt", "Iltimos, tilni tanlang:")

    text = f"{greet_uz}\n{greet_en}\n{greet_ru}\n\n{prompt}"
    await message.answer(text, reply_markup=LANG_KB)

# /lang komandasi bilan til tanlash oynasini qayta ochish
@router.message(Command("lang"))
async def choose_lang(message: Message):
    prompt = LOCALES.get("uz", {}).get("greet_prompt", "Iltimos, tilni tanlang:")
    await message.answer(prompt, reply_markup=LANG_KB)
