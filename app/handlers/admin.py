# -*- coding: utf-8 -*-
# app/handlers/admin.py

from __future__ import annotations
import asyncio
from typing import List, Optional

from loguru import logger
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

# --- Optional: Audit booking holati (bo'lmasa ham ishlaydi)
try:
    from .audit import BOOKINGS  # type: ignore
except Exception:
    BOOKINGS = {}  # type: ignore

# --- DB (bo'lmasa ham ishlaydi)
try:
    from ..storage.db import db  # type: ignore
except Exception:
    db = None  # type: ignore

router = Router()

# ===================== UTILITIES =====================

def _ikb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _row(*btns: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    return [*btns]

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)

def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

def _g(t: dict, key: str, default: str) -> str:
    return t.get(key, default)

async def _safe_cb_answer(cb: CallbackQuery, text: Optional[str] = None):
    try:
        await cb.answer(text)
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "query is too old" in s or "query id is invalid" in s:
            return
        raise

def _split_text_blocks(text: str, max_len: int = 3800) -> list[str]:
    """Telegram 4096 limitidan oshmaslik uchun bo‘lib yuborish."""
    text = (text or "").strip()
    if len(text) <= max_len:
        return [text]
    parts: list[str] = []
    cur = text
    while len(cur) > max_len:
        cut = cur.rfind("\n", 0, max_len)
        if cut == -1:
            cut = max_len
        parts.append(cur[:cut].strip())
        cur = cur[cut:].strip()
    if cur:
        parts.append(cur)
    return parts

def _user_has_approved_booking(user_id: int) -> bool:
    try:
        for b in BOOKINGS.values():
            prof = b.get("profile") or {}
            uid = prof.get("user_id") or b.get("user_id")
            if uid == user_id and b.get("status") == "approved":
                return True
    except Exception:
        pass
    return False

def _user_card(u: dict) -> str:
    uid = u.get("user_id") or u.get("id")
    username = u.get("username") or "-"
    name = u.get("name") or u.get("full_name") or "-"
    phone = u.get("phone") or "-"
    lang = u.get("lang") or "-"
    onboard = "✅" if u.get("onboarded") else "—"
    feature = u.get("last_feature") or "-"
    booked = "✅" if _user_has_approved_booking(int(uid or 0)) else "—"
    return (
        f"🆔 <code>{uid}</code>\n"
        f"👤 {name}\n"
        f"@ {username}\n"
        f"☎️ {phone}\n"
        f"🌍 {lang} | 🎯 {feature}\n"
        f"🟢 Onboarded: {onboard} | 📅 Booking: {booked}\n"
        + "—" * 12
    )

# ===================== ROOT / MENU =====================

def _admin_menu_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    return _ikb([
        _row(_btn("📣 " + _g(t, "adm_send_msg", "Xabar yuborish"), "adm:send")),
        _row(_btn("👥 " + _g(t, "adm_users_list", "Foydalanuvchilar ro‘yxati"), "adm:users:0")),
        _row(_btn("📚 " + _g(t, "adm_materials_btn", "Materiallar"), "adm:mats")),  # admin_materials.py bilan ulanadi
    ])

@router.message(Command("admin"), F.from_user.id.in_(settings.admin_ids))
async def admin_entry_ok(message: Message):
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    logger.info(f"/admin from {message.from_user.id} (ADMIN)")
    await message.answer("🛠 <b>Admin panel</b>", reply_markup=_admin_menu_kb(lang), parse_mode="HTML")

@router.message(Command("admin"))
async def admin_entry_denied(message: Message):
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    logger.info(f"/admin from {message.from_user.id} (DENIED)")
    await message.answer(_g(t, "adm_not_admin", "❌ Siz admin emassiz."))

@router.message(Command("whoami"))
async def whoami(message: Message):
    await message.answer(f"🆔 <code>{message.from_user.id}</code>")

@router.callback_query(F.data == "adm:back")
async def adm_back(cb: CallbackQuery):
    await _safe_cb_answer(cb, "◀️")
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await cb.message.answer("🛠 <b>Admin panel</b>", reply_markup=_admin_menu_kb(lang), parse_mode="HTML")

# ===================== SEND / BROADCAST =====================

class SendFSM(StatesGroup):
    TARGET = State()      # "one" | "all"
    ONE_USER = State()    # id/username/forward
    MEDIA = State()       # photo/video optional
    TEXT = State()        # caption/text
    PREVIEW = State()

def _send_menu_kb(t: dict) -> InlineKeyboardMarkup:
    return _ikb([
        _row(
            _btn("🧍‍♂️ " + _g(t, "adm_send_one", "Bitta foydalanuvchi"), "adm:send:one"),
            _btn("🌍 "   + _g(t, "adm_send_all", "Hammaga"),              "adm:send:all"),
        ),
        _row(_btn(_g(t, "back_btn", "◀️ Orqaga"), "adm:back"))
    ])

@router.callback_query(F.data == "adm:send")
async def adm_send(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await _safe_cb_answer(cb)
    await state.clear()
    await cb.message.answer(_g(t, "adm_send_choose", "Qaysi turdagi tarqatma?"), reply_markup=_send_menu_kb(t))

@router.callback_query(F.data.in_({"adm:send:one", "adm:send:all"}))
async def adm_send_target(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await _safe_cb_answer(cb)

    target = "one" if cb.data.endswith(":one") else "all"
    await state.update_data(target=target, media=None, text=None)

    if target == "one":
        await cb.message.answer(_g(t, "adm_ask_user", "Foydalanuvchini yuboring:\n- forward qiling yoki\n- @username yoki user_id kiriting"))
        await state.set_state(SendFSM.ONE_USER)
    else:
        await cb.message.answer(_g(t, "adm_send_media", "Rasm yoki video jo‘nating (ixtiyoriy)."))
        await cb.message.answer(
            _g(t, "adm_skip_or_send", "Yoki ⏭ O‘tkazib yuborish tugmasini bosing:"),
            reply_markup=_ikb([_row(_btn("⏭ " + _g(t, "skip_btn", "O‘tkazib yuborish"), "adm:skip_media"))])
        )
        await state.set_state(SendFSM.MEDIA)

@router.message(SendFSM.ONE_USER)
async def adm_pick_one_user(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_ids:
        return
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG); t = _t(lang)

    user_id: Optional[int] = None
    txt = (message.text or "").strip()

    if message.forward_from:
        user_id = message.forward_from.id
    elif txt.isdigit():
        user_id = int(txt)
    elif txt.startswith("@") and db:
        try:
            u = db.find_user_by_username(txt[1:])
            if u:
                user_id = int(u.get("user_id") or u.get("id"))
        except Exception:
            user_id = None

    if not user_id:
        await message.answer(_g(t, "adm_user_not_found", "Foydalanuvchi topilmadi."))
        return

    await state.update_data(to_user=user_id)
    await message.answer(_g(t, "adm_send_media", "Rasm yoki video jo‘nating (ixtiyoriy)."))
    await message.answer(
        _g(t, "adm_skip_or_send", "Yoki ⏭ O‘tkazib yuborish tugmasini bosing:"),
        reply_markup=_ikb([_row(_btn("⏭ " + _g(t, "skip_btn", "O‘tkazib yuborish"), "adm:skip_media"))])
    )
    await state.set_state(SendFSM.MEDIA)

@router.callback_query(SendFSM.MEDIA, F.data == "adm:skip_media")
async def adm_skip_media(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await _safe_cb_answer(cb, "⏭")
    await cb.message.answer(_g(t, "adm_ask_text", "Matn/caption kiriting (ixtiyoriy)."))
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.MEDIA, F.photo)
async def adm_take_photo(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_ids:
        return
    file_id = message.photo[-1].file_id
    await state.update_data(media={"type": "photo", "file_id": file_id})
    t = _t(get_lang(message.from_user.id, settings.DEFAULT_LANG))
    await message.answer(_g(t, "adm_ask_text", "Matn/caption kiriting (ixtiyoriy)."))
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.MEDIA, F.video)
async def adm_take_video(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_ids:
        return
    file_id = message.video.file_id
    await state.update_data(media={"type": "video", "file_id": file_id})
    t = _t(get_lang(message.from_user.id, settings.DEFAULT_LANG))
    await message.answer(_g(t, "adm_ask_text", "Matn/caption kiriting (ixtiyoriy)."))
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.TEXT)
async def adm_take_text(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_ids:
        return
    txt = (message.text or "").strip()
    await state.update_data(text=txt)

    t = _t(get_lang(message.from_user.id, settings.DEFAULT_LANG))
    kb = _ikb([
        _row(
            _btn("✅ " + _g(t, "send_btn", "Yuborish"), "adm:submit"),
            _btn("✏️ " + _g(t, "edit_btn", "O‘zgartirish"), "adm:edit"),
            _btn("❌ " + _g(t, "cancel_btn", "Bekor qilish"), "adm:cancel"),
        )
    ])

    await message.answer("🧪 <b>Preview</b>", parse_mode="HTML")
    data = await state.get_data()
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
    if cb.from_user.id not in settings.admin_ids:
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await _safe_cb_answer(cb)
    await cb.message.answer(_g(t, "adm_ask_text", "Matn/caption kiriting (ixtiyoriy)."))
    await state.set_state(SendFSM.TEXT)

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:cancel")
async def adm_cancel(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await _safe_cb_answer(cb, "❌")
    await state.clear()
    await cb.message.answer(_g(t, "adm_broadcast_canceled", "Tarqatma bekor qilindi."))

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:submit")
async def adm_submit(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await _safe_cb_answer(cb, "🚀")

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
            all_users = db.get_all_users(0, 10_000) if db else []
            for u in all_users:
                uid = int(u.get("user_id") or u.get("id"))
                try:
                    await _send_one(cb, uid, media, text)
                    sent_ok += 1
                    await asyncio.sleep(0.05)  # floodlimit xavfsizligi
                except (TelegramForbiddenError, TelegramBadRequest):
                    sent_fail += 1
                except Exception:
                    sent_fail += 1
    finally:
        await state.clear()

    done_txt = _g(t, "adm_broadcast_done", "Tarqatma yakunlandi. ✅: {ok}, ❌: {fail}")
    await cb.message.answer(done_txt.format(ok=sent_ok, fail=sent_fail))

async def _send_one(cb: CallbackQuery, uid: int, media: Optional[dict], text: str):
    if media:
        if media["type"] == "photo":
            await cb.message.bot.send_photo(uid, media["file_id"], caption=text or None)
        else:
            await cb.message.bot.send_video(uid, media["file_id"], caption=text or None)
    else:
        await cb.message.bot.send_message(uid, text or " ")

# ===================== USERS LIST =====================

PAGE_SIZE = 8  # xavfsizroq

def _users_page_kb(page: int, has_prev: bool, has_next: bool, t: dict) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    nav: list[InlineKeyboardButton] = []
    if has_prev:
        nav.append(_btn("⬅️", f"adm:users:{page-1}"))
    nav.append(_btn(f"{page+1}", f"noop:{page}"))  # sahifa raqami (noop)
    if has_next:
        nav.append(_btn("➡️", f"adm:users:{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([_btn("🔍 " + _g(t, "adm_user_show_btn", "Foydalanuvchini ko‘rish"), "adm:find")])
    rows.append([_btn(_g(t, "back_btn", "◀️ Orqaga"), "adm:back")])
    return _ikb(rows)

@router.callback_query(F.data.startswith("adm:users:"))
async def adm_users(cb: CallbackQuery):
    if cb.from_user.id not in settings.admin_ids:
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await _safe_cb_answer(cb)

    page = int(cb.data.split(":")[-1])
    all_users = db.get_all_users(page * PAGE_SIZE, PAGE_SIZE + 1) if db else []
    items = all_users[:PAGE_SIZE]
    has_next = len(all_users) > PAGE_SIZE
    has_prev = page > 0

    if not items:
        await cb.message.answer("— Ro‘yxat bo‘sh —", reply_markup=_users_page_kb(page, has_prev, has_next, t))
        return

    header = "👥 <b>Foydalanuvchilar</b>\n"
    body = "\n".join(_user_card(u) for u in items)
    txt = header + body

    chunks = _split_text_blocks(txt, 3800)
    for i, chunk in enumerate(chunks):
        kb = _users_page_kb(page, has_prev, has_next, t) if i == len(chunks) - 1 else None
        await cb.message.answer(chunk, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "adm:find")
async def adm_find_prompt(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await _safe_cb_answer(cb)
    # ONE_USER holatini qayta ishlatamiz (ID/@/forward qabul qiladi)
    await state.set_state(SendFSM.ONE_USER)
    await cb.message.answer(_g(t, "adm_find_prompt", "Forward / @username / user_id yuboring:"))

# No-op tugma (sahifa raqami)
@router.callback_query(F.data.startswith("noop:"))
async def adm_noop(cb: CallbackQuery):
    await _safe_cb_answer(cb)
