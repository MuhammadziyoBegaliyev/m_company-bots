from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from ..locales import L




def make_main_menu(lang: str) -> ReplyKeyboardMarkup:
    t = L[lang]
    return ReplyKeyboardMarkup(
    keyboard=[
    [KeyboardButton(text=t["btn_services"]),KeyboardButton(text=t["btn_projects"])],
    [KeyboardButton(text=t["btn_faq"])],
    [KeyboardButton(text=t["btn_contact"]), KeyboardButton(text=t["btn_about"])],
    ],
    resize_keyboard=True,
    input_field_placeholder=t["menu_title"],
    )