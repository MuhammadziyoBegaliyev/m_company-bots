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

# ---- Sozlamalar ----
ABOUT_PHOTO = "app/assets/about.png"      # Rasm fayli (mavjud bo'lsa yuboriladi)
ABOUT_WEBSITE = "https://mcompany.uz"     # Rasmiy sayt

# Reply tugma (har uch tilda)
ABOUT_BTNS = {
    L.get("uz", {}).get("btn_about", "Biz haqimizda"),
    L.get("en", {}).get("btn_about", "About us"),
    L.get("ru", {}).get("btn_about", "О нас"),
}


def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])


def _about_kb(lang: str) -> InlineKeyboardMarkup:
    """
    Tugmalar:
      [🌐 Website] [◀️ Asosiy menyu]
    """
    t = _t(lang)
    site_text = (
        t.get("open_website_btn")
        or (lang == "uz" and "🌐 Websayt")
        or (lang == "ru" and "🌐 Сайт")
        or "🌐 Website"
    )
    back_text = t.get("welcome_back_to_main") or t.get("back_btn") or "⬅️ Asosiy menyu"

    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=site_text, url=ABOUT_WEBSITE),
        InlineKeyboardButton(text=back_text, callback_data="about:back"),
    ]])


async def _send_about_root(message: Message, lang: str):
    """
    Bo‘limning kirish xabarini (rasm + matn yoki faqat matn) yuboradi.
    """
    t = _t(lang)
    title = t.get("about_title", L["uz"].get("about_title", "Biz haqimizda"))
    desc = t.get("about_what_text", L["uz"].get("about_what_text", ""))
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
            # Rasm bo'yicha muammo bo‘lsa ham bo‘lim ishlayversin
            pass

    await message.answer(caption, reply_markup=_about_kb(lang), parse_mode="HTML")


# ——— Entry: Reply tugmadan
@router.message(F.text.in_(ABOUT_BTNS))
async def about_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    await _send_about_root(message, lang)


# ——— Entry: Welcome inline tugmadan
@router.callback_query(F.data == "nav:about")
async def nav_about(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    await cb.answer()
    await _send_about_root(cb.message, lang)


# ——— Orqaga: Asosiy menyuga qaytish
@router.callback_query(F.data == "about:back")
async def about_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    await cb.answer()
    await main_menu_handlers.show_main_menu(cb.message, lang)
