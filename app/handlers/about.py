# -*- coding: utf-8 -*-
# app/handlers/about.py

import os
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
)

from ..locales import L
from ..storage.memory import get_lang
from . import main_menu as main_menu_handlers

router = Router()

# ---- Sozlamalar (kerak bo‘lsa o‘zgartiring) ----
ABOUT_PHOTO = "app/assets/about.png"          # Rasm
ABOUT_WEBSITE = "https://mcompany.uz"         #Sayt m company.uz


# Reply tugma (har uch tilda ishlaydi)
ABOUT_BTNS = {
    L.get("uz", {}).get("btn_about", "Biz haqimizda"),
    L.get("en", {}).get("btn_about", "About Us"),
    L.get("ru", {}).get("btn_about", "О нас"),
}

def _about_kb(lang: str) -> InlineKeyboardMarkup:
    t = L.get(lang, L["uz"])
    # Tugmalar: [Websayt] [Asosiy menyu]
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=t.get("open_website_btn") or
                 (lang == "uz" and "🌐 Websayt") or
                 (lang == "ru" and "🌐 Сайт") or
                 "🌐 Website",
            url=ABOUT_WEBSITE
        ),
        InlineKeyboardButton(
            text=t.get("welcome_back_to_main") or t.get("back_btn") or "⬅️ Asosiy menyu",
            callback_data="about:back"
        )
    ]])

@router.message(F.text.in_(ABOUT_BTNS))
async def about_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])

    title = t.get("about_title", L["uz"].get("about_title", "Biz haqimizda"))
    desc  = t.get("about_what_text", L["uz"].get("about_what_text", ""))

    caption = f"<b>{title}</b>\n\n{desc}"

    if os.path.isfile(ABOUT_PHOTO):
        try:
            await message.answer_photo(
                photo=FSInputFile(ABOUT_PHOTO),
                caption=caption,
                reply_markup=_about_kb(lang),
                parse_mode="HTML",
            )
            return
        except Exception:
            pass  # rasm muammosida matnga qaytamiz

    # Fallback: faqat matn
    await message.answer(caption, reply_markup=_about_kb(lang), parse_mode="HTML")

@router.callback_query(F.data == "about:back")
async def about_back(cb: CallbackQuery):
    # Orqaga -> Asosiy menyu
    lang = get_lang(cb.from_user.id, "uz")
    await cb.answer()
    await main_menu_handlers.show_main_menu(cb.message, lang)
