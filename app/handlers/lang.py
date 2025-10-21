
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from loguru import logger

from ..locales import L
from ..config import settings
from ..storage.db import db
from ..storage.memory import get_lang
# optional memory setter (agar mavjud bo'lsa)
try:
    from ..storage.memory import set_lang as memory_set_lang  # type: ignore
except Exception:
    memory_set_lang = None  # type: ignore

from .onboarding import start_onboarding
from .main_menu import show_main_menu, get_main_menu_kb

router = Router()

def _lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 Oʻz", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇷🇺 Ру",   callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 Eng",   callback_data="lang:en"),
    ]])

@router.message(Command("lang"))
async def cmd_lang(message: Message):
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = L.get(lang, L["uz"])
    await message.answer(t.get("choose_lang", "Tilni tanlang:"), reply_markup=_lang_kb())

@router.callback_query(F.data.startswith("lang:"))
async def set_language(cb: CallbackQuery):
    lang = cb.data.split(":", 1)[1].strip().lower()
    if lang not in {"uz", "ru", "en"}:
        lang = "uz"

    uid = cb.from_user.id
    try:
        db.set_lang(uid, lang)
    except Exception as e:
        logger.error(f"db.set_lang failed: {e}")

    if memory_set_lang:
        try:
            memory_set_lang(uid, lang)  # in-memory cache bo'lsa yangilasin
        except Exception:
            pass

    t = L.get(lang, L["uz"])
    await cb.answer(t.get("lang_ok", "Saved"))
    await cb.message.edit_reply_markup(reply_markup=None)

    # xush kelibsiz + inline menyu
    inline_kb = await get_main_menu_kb(lang, inline=True)
    await cb.message.answer(t.get("welcome_caption", "Welcome!"), reply_markup=inline_kb, parse_mode="HTML")

    # user onboarding holati
    u = db.get_user(uid)
    if not u or not bool(u.get("onboarded", 0)):
        # ism va telefonni so'raymiz
        await start_onboarding(cb.message, lang)
    else:
        await show_main_menu(cb.message, lang)
