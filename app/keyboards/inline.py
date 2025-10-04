from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..locales import L


LANG_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="🇺🇿 uz", callback_data="lang:uz"),
    InlineKeyboardButton(text="🇷🇺 ru",   callback_data="lang:ru"),
    InlineKeyboardButton(text="🇬🇧 eng",   callback_data="lang:en"),
]])





def WELCOME_KB(lang: str) -> InlineKeyboardMarkup:
    """
    Welcome ekrani uchun 3 ta tugmali inline klaviatura:
    - Biz haqimizda
    - Bizning loyihalar
    - Biz bilan aloqa
    """
    t = L.get(lang, L["uz"])
    rows = [
        [InlineKeyboardButton(
            text=t.get("welcome_btn_about", "ℹ️ Biz haqimizda"),
            callback_data="welcome:about"
        )],
        [InlineKeyboardButton(
            text=t.get("welcome_btn_projects", "🧩 Bizning loyihalar"),
            callback_data="welcome:projects"
        )],
        [InlineKeyboardButton(
            text=t.get("welcome_btn_contact", "☎️ Biz bilan aloqa"),
            callback_data="welcome:contact"
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

__all__ = ["WELCOME_KB"]