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
from .start import _show_welcome  # ✅ YANGI: welcome rasmni ko'rsatish uchun

router = Router()


def _lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 Oʻz", callback_data="lang:uz"),
        InlineKeyboardButton(text="🇷🇺 Ру", callback_data="lang:ru"),
        InlineKeyboardButton(text="🇬🇧 Eng", callback_data="lang:en"),
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
    
    # Tilni DB ga saqlash
    try:
        db.set_lang(uid, lang)
        logger.info(f"✅ Language set to '{lang}' for user {uid}")
    except Exception as e:
        logger.error(f"❌ db.set_lang failed: {e}")
    
    # Memory cache yangilash
    if memory_set_lang:
        try:
            memory_set_lang(uid, lang)
        except Exception:
            pass
    
    t = L.get(lang, L["uz"])
    await cb.answer(t.get("lang_ok", "Saqlandi ✅"))
    
    # Til tanlash xabarini o'chirish
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    
    # ✅ YANGI: Welcome rasm + caption ko'rsatish
    logger.info(f"📸 Showing welcome screen for user {uid}")
    await _show_welcome(cb.message, lang)
    
    # User onboarding holati tekshirish
    u = db.get_user(uid)
    if not u or not bool(u.get("onboarded", 0)):
        # Ism va telefonni so'raymiz
        logger.info(f"🎯 Starting onboarding for user {uid}")
        await start_onboarding(cb.message, lang)
    else:
        # Allaqachon onboarding o'tgan
        logger.info(f"✅ User {uid} already onboarded")
        # show_main_menu allaqachon _show_welcome ichida chaqiriladi
        pass