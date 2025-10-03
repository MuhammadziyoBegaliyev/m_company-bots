from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LANG_KB = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang:uz"),
    InlineKeyboardButton(text="🇷🇺 Русский",   callback_data="lang:ru"),
    InlineKeyboardButton(text="🇬🇧 English",   callback_data="lang:en"),
]])
