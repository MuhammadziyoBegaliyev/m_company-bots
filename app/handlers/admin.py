# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from typing import Dict, Any, List, Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from ..config import settings
from ..locales import L
from ..storage.memory import get_lang
from .audit import BOOKINGS  # bronlar holati uchun

# ixtiyoriy: DB mavjud bo'lmasa ham ishlasin
try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()

# ---------------------- HELPERS ----------------------

def _is_admin(user_id: int) -> bool:
    return user_id in (settings.admin_ids or [])

def _t(lang: str) -> dict:
    # Fallbacklar bilan
    base = L.get(lang, L.get("uz", {})).copy()
    base.setdefault("adm_send_msg", "Xabar yuborish")
    base.setdefault("adm_users_list", "Foydalanuvchilar ro‘yxati")
    base.setdefault("adm_send_choose", "Qaysi turdagi yuborishni tanlang:")
    base.setdefault("adm_send_one", "1 foydalanuvchiga")
    base.setdefault("adm_send_all", "Hammaga")
    base.setdefault("adm_ask_user", "Foydalanuvchini kiriting: ID / @username / forward qiling")
    base.setdefault("adm_send_media", "Rasm yoki video yuboring (ixtiyoriy).")
    base.setdefault("adm_skip_or_send", "Yoki ⏭️ O‘tkazib yuborish tugmasini bosing.")
    base.setdefault("skip_btn", "O‘tkazib yuborish")
    base.setdefault("adm_ask_text", "Endi matnni yuboring:")
    base.setdefault("send_btn", "Yuborish")
    base.setdefault("edit_btn", "O‘zgartirish")
    base.setdefault("cancel_btn", "Bekor qilish")
    base.setdefault("adm_broadcast_canceled", "Bekor qilindi.")
    base.setdefault("adm_broadcast_done", "Yuborildi: {ok} ta ✅ | Xato: {fail} ta ❗️")
    base.setdefault("adm_user_not_found", "Foydalanuvchi topilmadi.")
    base.setdefault("adm_find_prompt", "ID yoki @username yuboring (yoki forward qiling).")
    base.setdefault("adm_user_show_btn", "Foydalanuvchini ko‘rish")
    base.setdefault("back_btn", "◀️ Orqaga")
    return base

def _ikb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _row(*btns: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    return [*btns]

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)

def _lang(obj: Message | CallbackQuery) -> str:
    uid = obj.from_user.id
    return get_lang(uid, "uz")

def _user_has_approved_booking(user_id: int) -> bool:
    for b in BOOKINGS.values():
        prof = b.get("profile") or {}
        uid = prof.get("user_id") or b.get("user_id")
        if uid == user_id and b.get("status") == "approved":
            return True
    return False

def _user_card(u: dict) -> str:
    id_ = u.get("user_id") or u.get("id")
    username = u.get("username") or "-"
    name = u.get("name") or u.get("full_name") or "-"
    phone = u.get("phone") or "-"
    lang = u.get("lang") or "-"
    onboard = "✅" if u.get("onboarded") else "—"
    feature = u.get("last_feature") or "-"
    booked = "✅" if _user_has_approved_booking(int(id_ or 0)) else "—"

    return (
        f"🆔 <code>{id_}</code>\n"
        f"👤 {name}\n"
        f"@ {username}\n"
        f"☎️ {phone}\n"
        f"🌍 {lang} | 🎯 {feature}\n"
        f"🟢 Onboarded: {onboard} | 📅 Booking: {booked}\n"
        "—" * 12
    )

# ---------------------- DIAGNOSTIKA ----------------------

@router.message(Command("id"))
async def show_my_id(message: Message):
    await message.answer(
        f"🆔 Sizning ID: <code>{message.from_user.id}</code>\n"
        f"👮 ADMIN_IDS: <code>{settings.admin_ids}</code>"
    )

# ---------------------- ADMIN MENU ----------------------

@router.message(Command("admin"))
async def admin_entry(message: Message):
    if not _is_admin(message.from_user.id):
        # jim turish — ili quyidagini ochsangiz ham bo'ladi:
        # await message.answer("⛔️ Siz admin emassiz.")
        return
    t = _t(_lang(message))
    kb = _ikb([
        _row(_btn("📣 " + t["adm_send_msg"], "adm:send")),
        _row(_btn("👥 " + t["adm_users_list"], "adm:users:0")),  # 0-sahifa
    ])
    await message.answer("🛠 <b>Admin panel</b>", reply_markup=kb, parse_mode="HTML")

# ---------------------- SEND FLOW ----------------------

class SendFSM(StatesGroup):
    TARGET = State()      # "one" | "all"
    ONE_USER = State()    # id/username/forward (faqat SEND oqimi uchun)
    MEDIA = State()       # photo/video optional
    TEXT = State()        # caption or message text
    PREVIEW = State()

def _send_menu_kb(t: dict) -> InlineKeyboardMarkup:
    return _ikb([
        _row(_btn("🧍‍♂️ " + t["adm_send_one"], "adm:send:one"),
             _btn("🌍 "   + t["adm_send_all"], "adm:send:all")),
        _row(_btn(t["back_btn"], "adm:back"))
    ])

@router.callback_query(F.data == "adm:send")
async def adm_send(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(_lang(cb))
    await cb.answer()
    await state.clear()
    await cb.message.answer(t["adm_send_choose"], reply_markup=_send_menu_kb(t))

@router.callback_query(F.data.in_({"adm:send:one", "adm:send:all"}))
async def adm_send_target(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(_lang(cb)); await cb.answer()
    target = "one" if cb.data.endswith(":one") else "all"
    await state.update_data(target=target, media=None, text=None)

    if target == "one":
        await cb.message.answer(t["adm_ask_user"])
        await state.set_state(SendFSM.ONE_USER)
    else:
        await cb.message.answer(t["adm_send_media"])
        await cb.message.answer(
            t["adm_skip_or_send"],
            reply_markup=_ikb([_row(_btn("⏭ " + t["skip_btn"], "adm:skip_media"))])
        )
        await state.set_state(SendFSM.MEDIA)

@router.message(SendFSM.ONE_USER)
async def adm_pick_one_user(message: Message, state: FSMContext):
    # faqat SEND oqimi uchun
    if not _is_admin(message.from_user.id):
        return
    t = _t(_lang(message))

    user_id: Optional[int] = None
    txt = (message.text or "").strip()

    if message.forward_from:
        user_id = message.forward_from.id
    elif txt.isdigit():
        user_id = int(txt)
    elif txt.startswith("@") and db:
        u = db.find_user_by_username(txt[1:])
        if u:
            user_id = int(u.get("user_id") or u.get("id"))

    if not user_id:
        await message.answer(t["adm_user_not_found"])
        return

    await state.update_data(to_user=user_id)
    await message.answer(t["adm_send_media"])
    await message.answer(
        t["adm_skip_or_send"],
        reply_markup=_ikb([_row(_btn("⏭ " + t["skip_btn"], "adm:skip_media"))])
    )
    await state.set_state(SendFSM.MEDIA)

@router.callback_query(SendFSM.MEDIA, F.data == "adm:skip_media")
async def adm_skip_media(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(_lang(cb)); await cb.answer("⏭")
    await cb.message.answer(t["adm_ask_text"])
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.MEDIA, F.photo)
async def adm_take_photo(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    file_id = message.photo[-1].file_id
    await state.update_data(media={"type": "photo", "file_id": file_id})
    t = _t(_lang(message))
    await message.answer(t["adm_ask_text"])
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.MEDIA, F.video)
async def adm_take_video(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    file_id = message.video.file_id
    await state.update_data(media={"type": "video", "file_id": file_id})
    t = _t(_lang(message))
    await message.answer(t["adm_ask_text"])
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.TEXT)
async def adm_take_text(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    txt = (message.text or "").strip()
    await state.update_data(text=txt)

    data = await state.get_data()
    t = _t(_lang(message))

    kb = _ikb([
        _row(_btn("✅ " + t["send_btn"], "adm:submit"),
             _btn("✏️ " + t["edit_btn"],  "adm:edit"),
             _btn("❌ " + t["cancel_btn"], "adm:cancel"))
    ])
    await message.answer("🧪 <b>Preview</b>", parse_mode="HTML")
    media = data.get("media")
    if media:
        if media["type"] == "photo":
            await message.answer_photo(media["file_id"], caption=txt or None, reply_markup=kb)
        else:
            await message.answer_video(media["file_id"], caption=txt or None, reply_markup=kb)
    else:
        await message.answer(txt or "—", reply_markup=kb)
    await state.set_state(SendFSM.PREVIEW)

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:edit")
async def adm_edit(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(_lang(cb)); await cb.answer()
    await cb.message.answer(t["adm_ask_text"])
    await state.set_state(SendFSM.TEXT)

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:cancel")
async def adm_cancel(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(_lang(cb)); await cb.answer("❌")
    await state.clear()
    await cb.message.answer(t["adm_broadcast_canceled"])

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:submit")
async def adm_submit(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(_lang(cb)); await cb.answer("🚀")

    data = await state.get_data()
    target = data.get("target")
    media = data.get("media")
    text  = data.get("text") or ""

    sent_ok = 0
    sent_fail = 0

    try:
        if target == "one":
            uid = int(data["to_user"])
            await _send_one(cb, uid, media, text)
            sent_ok = 1
        else:
            users = db.get_all_users(0, 10000) if db else []
            for u in users:
                uid = int(u.get("user_id") or u.get("id"))
                try:
                    await _send_one(cb, uid, media, text)
                    sent_ok += 1
                    await asyncio.sleep(0.05)  # yumshoq rate-limit
                except (TelegramForbiddenError, TelegramBadRequest):
                    sent_fail += 1
                except Exception:
                    sent_fail += 1
    finally:
        await state.clear()

    await cb.message.answer(f"✅ {t['adm_broadcast_done'].format(ok=sent_ok, fail=sent_fail)}")

async def _send_one(cb: CallbackQuery, uid: int, media: Optional[dict], text: str):
    if media:
        if media["type"] == "photo":
            await cb.message.bot.send_photo(uid, media["file_id"], caption=text or None)
        else:
            await cb.message.bot.send_video(uid, media["file_id"], caption=text or None)
    else:
        await cb.message.bot.send_message(uid, text or " ")

# ---------------------- USERS LIST ----------------------

PAGE_SIZE = 10

def _users_page_kb(page: int, has_prev: bool, has_next: bool, t: dict) -> InlineKeyboardMarkup:
    rows = []
    nav = []
    if has_prev:
        nav.append(_btn("⬅️", f"adm:users:{page-1}"))
    # mark current page (readonly)
    nav.append(_btn(f"{page+1}", f"adm:users:{page}"))
    if has_next:
        nav.append(_btn("➡️", f"adm:users:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([_btn("🔍 " + t["adm_user_show_btn"], "adm:find")])
    rows.append([_btn(t["back_btn"], "adm:back")])
    return _ikb(rows)

@router.callback_query(F.data.startswith("adm:users:"))
async def adm_users(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(_lang(cb)); await cb.answer()

    page = int(cb.data.split(":")[-1])
    got = db.get_all_users(page * PAGE_SIZE, PAGE_SIZE + 1) if db else []
    items = got[:PAGE_SIZE]
    has_next = len(got) > PAGE_SIZE
    has_prev = page > 0

    if not items:
        await cb.message.answer("— Ro‘yxat bo‘sh —")
        return

    blocks = [_user_card(u) for u in items]
    txt = "👥 <b>Foydalanuvchilar</b>\n\n" + "\n".join(blocks)
    await cb.message.answer(
        txt, parse_mode="HTML",
        reply_markup=_users_page_kb(page, has_prev, has_next, t)
    )

# ---- Alohida FIND FSM (SEND oqimi bilan to'qnashmasin) ----

class FindFSM(StatesGroup):
    QUERY = State()

@router.callback_query(F.data == "adm:find")
async def adm_find_prompt(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(_lang(cb)); await cb.answer()
    await state.set_state(FindFSM.QUERY)
    await cb.message.answer(t["adm_find_prompt"])

@router.message(FindFSM.QUERY)
async def adm_find_user_show(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    lang = _lang(message); t = _t(lang)

    uid: Optional[int] = None
    txt = (message.text or "").strip()

    if message.forward_from:
        uid = message.forward_from.id
    elif txt.isdigit():
        uid = int(txt)
    elif txt.startswith("@") and db:
        u = db.find_user_by_username(txt[1:])
        if u:
            uid = int(u.get("user_id") or u.get("id"))

    if not uid or not db:
        await message.answer(t["adm_user_not_found"]); await state.clear(); return

    u = db.get_user(uid)
    if not u:
        await message.answer(t["adm_user_not_found"]); await state.clear(); return

    await message.answer(_user_card(u), parse_mode="HTML")
    await state.clear()

# ---------------------- BACK ----------------------

@router.callback_query(F.data == "adm:back")
async def adm_back(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    await cb.answer("◀️")
    await admin_entry(cb.message)
