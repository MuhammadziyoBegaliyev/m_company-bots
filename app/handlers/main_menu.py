# app/handlers/main_menu.py
# -*- coding: utf-8 -*-
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from ..locales import L
from ..storage.memory import get_lang

router = Router()

def build_main_kb(lang: str) -> ReplyKeyboardMarkup:
    """Asosiy reply menyu (tilga mos)."""
    t = L.get(lang, L["uz"])
    rows = [
        [KeyboardButton(text=t["btn_services"]),  KeyboardButton(text=t["btn_projects"])],
        [KeyboardButton(text=t["btn_faq"]),       KeyboardButton(text=t["btn_contact"])],
        [KeyboardButton(text=t["btn_about"]),     KeyboardButton(text=t["btn_audit"])],
        [KeyboardButton(text=t["btn_materials"])],  # yangi tugma
    ]
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

async def show_main_menu(message: Message, lang: str | None = None):
    """Asosiy menyuni ko‘rsatish uchun yagona funksiya."""
    lang = lang or get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    await message.answer(t.get("menu_hint", "🟡 Asosiy menyu:"), reply_markup=build_main_kb(lang))
