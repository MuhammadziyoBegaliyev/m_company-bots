# app/keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..locales import L

def WELCOME_KB(lang: str) -> InlineKeyboardMarkup:
    t = L.get(lang, L["uz"])
    rows = [
        [InlineKeyboardButton(text=t["btn_about"],   callback_data="nav:about")],
        [InlineKeyboardButton(text=t["btn_projects"],callback_data="nav:projects")],
        [InlineKeyboardButton(text=t["btn_contact"], callback_data="nav:contact")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

# til tanlash (o'zingizda bor bo'lsa, shu ko'rinishga keltiring)
LANG_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="UZ 🇺🇿", callback_data="lang:uz"),
    InlineKeyboardButton(text="RU 🇷🇺", callback_data="lang:ru"),
    InlineKeyboardButton(text="EN 🇬🇧", callback_data="lang:en"),
]])
