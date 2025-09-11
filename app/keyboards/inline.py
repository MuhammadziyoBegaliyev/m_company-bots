from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


LANG_KB = InlineKeyboardMarkup(inline_keyboard=[
[
InlineKeyboardButton(text="UZ 🇺🇿", callback_data="lang:uz"),
InlineKeyboardButton(text="РУ 🇷🇺",callback_data="lang:ru" ),#
InlineKeyboardButton(text="ENG 🇷🇺",callback_data="lang:en" ),
]
])
