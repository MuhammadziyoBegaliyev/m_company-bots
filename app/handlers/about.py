# app/handlers/about.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from ..locales import L
from ..storage.memory import get_lang

router = Router()

# Reply tugma (3 tilda)
ABOUT_BTNS = {L["uz"]["btn_about"], L["en"]["btn_about"], L["ru"]["btn_about"]}

def _about_menu_kb(lang: str) -> InlineKeyboardMarkup:
    t = L[lang]
    rows = [
        [
            InlineKeyboardButton(text=f"ℹ️ {t['about_btn_what']}", callback_data="about:what")],
            [InlineKeyboardButton(text=f"🧭 {t['about_btn_why']}",  callback_data="about:why")],
        
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _back_kb(lang: str) -> InlineKeyboardMarkup:
    t = L[lang]
    rows = [[InlineKeyboardButton(text=t["back_btn"], callback_data="about:back")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.message(F.text.in_(ABOUT_BTNS))
async def about_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = L[lang]
    await message.answer(f"🚀 {t['about_title']}", reply_markup=_about_menu_kb(lang))

@router.callback_query(F.data == "about:what")
async def about_what(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = L[lang]
    await cb.answer()
    await cb.message.answer(t["about_what_text"], reply_markup=_back_kb(lang))

@router.callback_query(F.data == "about:why")
async def about_why(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = L[lang]
    await cb.answer()
    await cb.message.answer(t["about_why_text"], reply_markup=_back_kb(lang))

@router.callback_query(F.data == "about:back")
async def about_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = L[lang]
    await cb.answer()
    await cb.message.answer(f"🚀 {t['about_title']}", reply_markup=_about_menu_kb(lang))
