# -*- coding: utf-8 -*-
# app/handlers/start.py

import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from ..locales import L
from ..storage.memory import get_lang
from . import main_menu as main_menu_handlers  # <-- asosiy menyuni ko‘rsatish uchun

router = Router()

WELCOME_PHOTO = "app/assets/welcome.jpg"  # mavjud bo'lmasa matn bilan yuboriladi


def _welcome_kb(lang: str) -> InlineKeyboardMarkup:
    t = L.get(lang, L["uz"])
    rows = [
        [InlineKeyboardButton(text=t["welcome_btn_about"],   callback_data="nav:about")],
        [InlineKeyboardButton(text=t["welcome_btn_projects"], callback_data="nav:projects")],
        [InlineKeyboardButton(text=t["welcome_btn_contact"],  callback_data="nav:contact")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(F.text == "/start")
async def start(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])

    kb = _welcome_kb(lang)
    caption = t["welcome_caption"]

    if os.path.isfile(WELCOME_PHOTO):
        try:
            await message.answer_photo(
                photo=FSInputFile(WELCOME_PHOTO),
                caption=caption,
                reply_markup=kb,
            )
        except Exception:
            # rasm bo'lmasa yoki o'qilmasa — faqat matn
            await message.answer(caption, reply_markup=kb)
    else:
        await message.answer(caption, reply_markup=kb)

    # ❗️ MUHIM: welcome’dan keyin darhol asosiy menyu (reply keyboard) ni ko‘rsatamiz
    await main_menu_handlers.show_main_menu(message, lang)


# Quyidagi nav callback’lar welcome inline tugmalaridan foydalanadi
@router.callback_query(F.data == "nav:about")
async def nav_about(cb: CallbackQuery):
    # Reply tugmasidagi "Biz haqimizda" bilan bir xil bo'limga olib boring
    from . import about as about_handlers
    await cb.answer()
    # Reply bo'lim handlerini chaqiradigan alohida funksiya bo'lmasa, shunchaki komandaga yo'naltiring:
    await cb.message.answer(L.get(get_lang(cb.from_user.id, "uz"), L["uz"])["btn_about"])

@router.callback_query(F.data == "nav:projects")
async def nav_projects(cb: CallbackQuery):
    from . import projects as projects_handlers  # ro‘yxatni shu fayl o‘zi ochadi
    await cb.answer()
    # projects.py ichidagi `@router.callback_query(F.data == "nav:projects")` allaqachon bor bo'lsa, shu yetarli;
    # Yo‘q bo‘lsa, reply bo‘lim trigger matnini yuboramiz:
    await cb.message.answer(L.get(get_lang(cb.from_user.id, "uz"), L["uz"])["btn_projects"])

@router.callback_query(F.data == "nav:contact")
async def nav_contact(cb: CallbackQuery):
    from . import contact as contact_handlers
    await cb.answer()
    await cb.message.answer(L.get(get_lang(cb.from_user.id, "uz"), L["uz"])["btn_contact"])
