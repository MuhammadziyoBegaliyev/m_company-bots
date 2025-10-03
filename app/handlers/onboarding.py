# -*- coding: utf-8 -*-
# app/handlers/onboarding.py

import os
import asyncio
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, ContentType
)
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from ..locales import L
from ..storage.memory import (
    get_lang,
    get_profile, set_profile,
    is_onboarded, set_onboarded,
)
from . import main_menu as main_menu_handlers
from . import projects as projects_handlers  # loyihalar menyusiga ulash uchun

router = Router()

WELCOME_PHOTO = "app/assets/welcome.png"   # ≤10MB rasm joylashiga ishonch hosil qiling


# --- FSM holatlar ---
class Onboard(StatesGroup):
    NAME = State()
    PHONE = State()


# --- Telefon so'rash klaviaturasi (reply) ---
def phone_req_kb(lang: str) -> ReplyKeyboardMarkup:
    t = L.get(lang, L["uz"])
    label = t.get("share_phone_btn") or t.get("onb_btn_share_phone") or "📲 Raqamni ulashish"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# --- Welcome sahifasi inline klaviaturasi ---
def welcome_kb(lang: str) -> InlineKeyboardMarkup:
    t = L.get(lang, L["uz"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["welcome_btn_about"],    callback_data="w:about")],
        [InlineKeyboardButton(text=t["welcome_btn_projects"], callback_data="w:projects")],
        [InlineKeyboardButton(text=t["welcome_btn_contact"],  callback_data="w:contact")],
        [InlineKeyboardButton(text=t["welcome_back_to_main"], callback_data="w:menu")],
    ])


# --- Eski/invalid callbackni yutib yuborish uchun yordamchi ---
async def _safe_cb_answer(cb: CallbackQuery, *args, **kwargs):
    try:
        await cb.answer(*args, **kwargs)
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "query is too old" in s or "query id is invalid" in s:
            return
        raise


# --- Welcome ni yuborish ---
async def send_welcome(message: Message, lang: str) -> None:
    t = L.get(lang, L["uz"])
    caption = t["welcome_caption"]
    kb = welcome_kb(lang)

    if os.path.isfile(WELCOME_PHOTO):
        try:
            await message.answer_photo(
                photo=FSInputFile(WELCOME_PHOTO),
                caption=caption,
                reply_markup=kb,
                parse_mode="HTML",
            )
            return
        except TelegramBadRequest:
            pass  # agar rasmda muammo bo'lsa, matnga tushamiz

    # Fallback: faqat matn
    await message.answer(caption, reply_markup=kb, parse_mode="HTML")


# --- Til tanlangandan keyin onboardingni boshlash (ism so'rash) ---
async def start_after_lang(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    await message.answer(t["ob_ask_name"])
    await state.set_state(Onboard.NAME)


# --- Ismni qabul qilish ---
@router.message(Onboard.NAME, F.text.len() > 0)
async def ob_take_name(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id, "uz")
    set_profile(message.from_user.id, name=message.text.strip())
    t = L.get(lang, L["uz"])
    await message.answer(t["ob_ask_phone"], reply_markup=phone_req_kb(lang))
    await state.set_state(Onboard.PHONE)


# --- Telefonni normalizatsiya ---
def _normalize_phone(raw: str) -> str | None:
    if not raw:
        return None
    s = raw.strip()
    plus = s.startswith("+")
    digits = "".join(ch for ch in s if ch.isdigit())
    # 7–15 raqam: E.164 minimal tekshiruv
    if not (7 <= len(digits) <= 15):
        return None
    return f"+{digits}"


# --- Telefon: CONTACT orqali ---
@router.message(Onboard.PHONE, F.content_type == ContentType.CONTACT)
async def ob_take_contact(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])

    c = message.contact
    # Boshqa odamning kontaktini yuborsa yoki bo'sh bo'lsa — rad etamiz
    if not c or (c.user_id and c.user_id != message.from_user.id):
        await message.answer(t["ob_bad_phone"], reply_markup=phone_req_kb(lang))
        return

    phone = _normalize_phone(c.phone_number)
    if not phone:
        await message.answer(t["ob_bad_phone"], reply_markup=phone_req_kb(lang))
        return

    set_profile(
        message.from_user.id,
        phone=phone,
        username=message.from_user.username or None
    )
    set_onboarded(message.from_user.id, True)
    await state.clear()

    saved_msg = await message.answer(t["ob_saved_ok"], parse_mode="HTML")
    await send_welcome(message, lang)

    # Chatni toza tutish: "saqlandi" xabarini muloyim o‘chirib yuboramiz
    try:
        await asyncio.sleep(1.5)
        await saved_msg.delete()
    except Exception:
        pass


# --- Telefon: TEXT orqali (qo'lda kiritilganda) ---
@router.message(Onboard.PHONE, F.text)
async def ob_take_phone_text(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])

    phone = _normalize_phone(message.text)
    if not phone:
        await message.answer(t["ob_bad_phone"], reply_markup=phone_req_kb(lang))
        return

    set_profile(
        message.from_user.id,
        phone=phone,
        username=message.from_user.username or None
    )
    set_onboarded(message.from_user.id, True)
    await state.clear()

    saved_msg = await message.answer(t["ob_saved_ok"], parse_mode="HTML")
    await send_welcome(message, lang)

    try:
        await asyncio.sleep(1.5)
        await saved_msg.delete()
    except Exception:
        pass


# --- Welcome callbacklari ---
@router.callback_query(F.data == "w:menu")  # Welcome'dan asosiy menyuga
async def w_menu(cb: CallbackQuery):
    await _safe_cb_answer(cb)
    lang = get_lang(cb.from_user.id, "uz")
    await main_menu_handlers.show_main_menu(cb.message, lang)

# Orqaga moslik uchun (agar oldin w:back ishlatilgan bo'lsa)
@router.callback_query(F.data == "w:back")
async def w_back(cb: CallbackQuery):
    await _safe_cb_answer(cb)
    lang = get_lang(cb.from_user.id, "uz")
    await main_menu_handlers.show_main_menu(cb.message, lang)

@router.callback_query(F.data == "w:about")
@router.callback_query(F.data == "w:about")
async def w_about(cb: CallbackQuery):
    await _safe_cb_answer(cb)
    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    title = t.get("about_title", L["uz"].get("about_title", "Biz haqimizda"))
    text = f"{title}\n\n{t.get('about_what_text', L['uz'].get('about_what_text', ''))}"
    back = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t.get("welcome_back_to_main", "⬅️ Asosiy menyu"),
                              callback_data="w:menu")]
    ])
    await cb.message.answer(text, reply_markup=back, parse_mode="HTML")

@router.callback_query(F.data == "w:projects")
async def w_projects(cb: CallbackQuery):
    await _safe_cb_answer(cb, "📂")
    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    # Loyihalar menyusini ochamiz
    await cb.message.answer(t["projects_title"], reply_markup=projects_handlers._kb_projects(lang))

@router.callback_query(F.data == "w:contact")
async def w_contact(cb: CallbackQuery):
    await _safe_cb_answer(cb, "📞")
    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])

    # Telefon va email matnda ko‘rsatiladi (Telegram o‘zi avtolink qiladi).
    text = (
        f"{t.get('contact_title', 'Biz bilan bog‘lanish:')}\n\n"
        f"{t.get('contact_email_text', 'info@mcompany.uz')}\n"
        f"{t.get('contact_phone_text', '+998 (90) 808-6383')}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t.get("welcome_back_to_main", "⬅️ Asosiy menyu"),
                              callback_data="w:menu")]
    ])
    await cb.message.answer(text, reply_markup=kb)
