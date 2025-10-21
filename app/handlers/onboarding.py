
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from loguru import logger

from ..locales import L
from ..config import settings
from ..storage.db import db
from ..storage.memory import get_lang
from .main_menu import show_main_menu

router = Router()

class Onb(StatesGroup):
    NAME = State()
    PHONE = State()

def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

def _share_phone_kb(lang: str) -> ReplyKeyboardMarkup:
    t = _t(lang)
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t.get("ob_share_phone_btn", t.get("share_phone_btn", "📲 Share phone")), request_contact=True)]],
        resize_keyboard=True
    )

def _clean_phone(raw: str) -> str:
    s = (raw or "").strip()
    plus = s.startswith("+")
    digits = "".join(ch for ch in s if ch.isdigit())
    return f"+{digits}" if plus else digits

async def start_onboarding(message: Message, state: FSMContext, lang: str | None = None):
    """Start.py yoki lang.py dan chaqiriladi."""
    if not lang:
        lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    await message.answer(t.get("ob_ask_name", t.get("onb_ask_name", "👋 Ismingizni yozing:")))
    await state.set_state(Onb.NAME)

@router.message(Onb.NAME)
async def take_name(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    name = (message.text or "").strip()
    if not name or len(name) < 2:
        await message.answer(t.get("ob_ask_name", "👋 Ismingizni yozing:"))
        return

    try:
        db.set_name(message.from_user.id, name)
    except Exception as e:
        logger.error(f"db.set_name failed: {e}")

    await state.update_data(name=name)
    await message.answer(
        t.get("ob_ask_phone", t.get("onb_ask_phone", "📞 Raqamingizni yuboring.")),
        reply_markup=_share_phone_kb(lang)
    )
    await state.set_state(Onb.PHONE)

@router.message(Onb.PHONE, F.contact)
async def take_phone_contact(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    phone = message.contact.phone_number if message.contact else None
    if not phone:
        await message.answer(t.get("ob_ask_phone", "📞 Raqamingizni yuboring."), reply_markup=_share_phone_kb(lang))
        return
    phone = _clean_phone(phone)

    try:
        db.set_phone(message.from_user.id, phone)
        db.set_onboarded(message.from_user.id, True)
    except Exception as e:
        logger.error(f"db.set_phone/onboarded failed: {e}")

    await state.clear()
    await message.answer(t.get("ob_saved_ok", t.get("onb_saved", "✅ Saqlandi.")))
    # reply keyboardni qayta ko'rsatamiz
    await show_main_menu(message, lang)

@router.message(Onb.PHONE)
async def take_phone_text(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    txt = (message.text or "").strip()
    if not txt:
        await message.answer(t.get("ob_ask_phone", "📞 Raqamingizni yuboring."), reply_markup=_share_phone_kb(lang))
        return

    phone = _clean_phone(txt)
    # eng sodda validatsiya: 8–15 raqam
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 8 or len(digits) > 15:
        await message.answer(t.get("ob_bad_phone", "❗️ Raqam formati noto‘g‘ri."), reply_markup=_share_phone_kb(lang))
        return

    try:
        db.set_phone(message.from_user.id, phone)
        db.set_onboarded(message.from_user.id, True)
    except Exception as e:
        logger.error(f"db.set_phone/onboarded failed: {e}")

    await state.clear()
    await message.answer(t.get("ob_saved_ok", t.get("onb_saved", "✅ Saqlandi.")))
    await show_main_menu(message, lang)
