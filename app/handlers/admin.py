# -*- coding: utf-8 -*-
# app/handlers/admin.py

from __future__ import annotations
import asyncio
from typing import List, Optional

from loguru import logger
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatType
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from ..config import settings
from ..locales import L

# ixtiyoriy DB (foydalanuvchilar ro'yxati uchun)
try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()

# ---------------------- HELPERS ----------------------
def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

def _g(t: dict, key: str, default: str) -> str:
    return t.get(key, default)

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)

def _ikb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _row(*btns: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    return [*btns]

def _admin_main_kb(t: dict) -> InlineKeyboardMarkup:
    return _ikb([
        _row(_btn("📣 " + _g(t, "adm_send_msg", "Xabar yuborish"), "adm:send")),
        _row(_btn("👥 " + _g(t, "adm_users_list", "Foydalanuvchilar ro'yxati"), "adm:users:0")),
    ])

# kartochka ko‘rinishi
def _user_card(u: dict) -> str:
    id_ = u.get("user_id") or u.get("id")
    username = u.get("username") or "-"
    name = u.get("name") or u.get("full_name") or "-"
    phone = u.get("phone") or "-"
    lang = u.get("lang") or "-"
    onboard = "✅" if u.get("onboarded") else "—"
    feature = u.get("last_feature") or "-"
    return (
        f"🆔 <code>{id_}</code>\n"
        f"👤 {name}\n"
        f"@ {username}\n"
        f"☎️ {phone}\n"
        f"🌍 {lang} | 🎯 {feature}\n"
        f"🟢 Onboarded: {onboard}\n"
        "—" * 12
    )

# ---------------------- ADMIN ENTRY ----------------------
# ✅ faqat PM va faqat adminlar
@router.message(
    Command("admin"),
    F.chat.type == ChatType.PRIVATE,
    F.from_user.id.in_(settings.admin_ids),
)
async def admin_entry_ok(message: Message):
    lang = "uz"
    try:
        # agar sizda get_lang bo'lsa shu yerga qo'ying
        from ..storage.memory import get_lang
        lang = get_lang(message.from_user.id, "uz")
    except Exception:
        pass
    t = _t(lang)
    logger.info(f"/admin from {message.from_user.id} (ADMIN)")
    await message.answer("🛠 <b>Admin panel</b>", parse_mode="HTML", reply_markup=_admin_main_kb(t))

# ❌ boshqalar uchun
@router.message(Command("admin"))
async def admin_entry_denied(message: Message):
    await message.answer("❌ Siz admin emassiz yoki bu buyruqni shaxsiy chatda yuboring.")

# Diagnostika
@router.message(Command("whoami"))
async def whoami(message: Message):
    await message.answer(f"🆔 <code>{message.from_user.id}</code>", parse_mode="HTML")

@router.message(Command("chatid"))
async def chatid(message: Message):
    await message.answer(f"💬 Chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")

# ---------------------- SEND FLOW ----------------------
class SendFSM(StatesGroup):
    MEDIA = State()
    TEXT = State()
    PREVIEW = State()
    TARGET = State()     # "one" / "all"
    ONE_USER = State()   # only for "one"

def _send_menu_kb(t: dict) -> InlineKeyboardMarkup:
    return _ikb([
        _row(_btn("🧍‍♂️ " + _g(t, "adm_send_one", "1 foydalanuvchi"), "adm:send:one"),
             _btn("🌍 "   + _g(t, "adm_send_all", "Hammaga"),          "adm:send:all")),
        _row(_btn(_g(t, "back_btn", "◀️ Orqaga"), "adm:back")),
    ])

@router.callback_query(F.data == "adm:back")
async def adm_back(cb: CallbackQuery):
    if cb.from_user.id not in settings.admin_ids:
        return
    await cb.answer("◀️")
    lang = "uz"
    try:
        from ..storage.memory import get_lang
        lang = get_lang(cb.from_user.id, "uz")
    except Exception:
        pass
    t = _t(lang)
    await cb.message.edit_text("🛠 <b>Admin panel</b>", parse_mode="HTML", reply_markup=_admin_main_kb(t))

@router.callback_query(F.data == "adm:send")
async def adm_send(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    await cb.answer()
    await state.clear()
    lang = "uz"
    try:
        from ..storage.memory import get_lang
        lang = get_lang(cb.from_user.id, "uz")
    except Exception:
        pass
    t = _t(lang)
    await cb.message.edit_text(_g(t, "adm_send_choose", "Qaysi turdagi tarqatma?"), reply_markup=_send_menu_kb(t))

@router.callback_query(F.data.in_({"adm:send:one", "adm:send:all"}))
async def adm_send_target(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    await cb.answer()
    lang = "uz"
    try:
        from ..storage.memory import get_lang
        lang = get_lang(cb.from_user.id, "uz")
    except Exception:
        pass
    t = _t(lang)

    target = "one" if cb.data.endswith(":one") else "all"
    await state.update_data(target=target, media=None, text=None)

    if target == "one":
        await cb.message.edit_text(_g(t, "adm_ask_user", "Forward / @username / user_id yuboring:"))
        await state.set_state(SendFSM.ONE_USER)
    else:
        await cb.message.edit_text(_g(t, "adm_send_media", "Rasm/video yuboring (ixtiyoriy)."))
        await cb.message.answer(
            _g(t, "adm_skip_or_send", "Yoki ⏭ tugmasi orqali o‘tkazing."),
            reply_markup=_ikb([_row(_btn("⏭ " + _g(t, "skip_btn", "O‘tkazish"), "adm:skip_media"))])
        )
        await state.set_state(SendFSM.MEDIA)

@router.message(SendFSM.ONE_USER)
async def adm_pick_one_user(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_ids:
        return
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
        await message.answer("❗️ Foydalanuvchi topilmadi.")
        return

    await state.update_data(to_user=user_id)
    await message.answer("Rasm/video yuboring (ixtiyoriy).")
    await message.answer(
        "Yoki ⏭ tugmasi orqali o‘tkazing.",
        reply_markup=_ikb([_row(_btn("⏭ O‘tkazish", "adm:skip_media"))])
    )
    await state.set_state(SendFSM.MEDIA)

@router.callback_query(SendFSM.MEDIA, F.data == "adm:skip_media")
async def adm_skip_media(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    await cb.answer("⏭")
    await cb.message.answer("Matn/caption yuboring:")
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.MEDIA, F.photo)
async def adm_take_photo(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_ids:
        return
    file_id = message.photo[-1].file_id
    await state.update_data(media={"type": "photo", "file_id": file_id})
    await message.answer("Matn/caption yuboring:")
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.MEDIA, F.video)
async def adm_take_video(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_ids:
        return
    file_id = message.video.file_id
    await state.update_data(media={"type": "video", "file_id": file_id})
    await message.answer("Matn/caption yuboring:")
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.TEXT)
async def adm_take_text(message: Message, state: FSMContext):
    if message.from_user.id not in settings.admin_ids:
        return
    txt = (message.text or "").strip()
    await state.update_data(text=txt)

    data = await state.get_data()
    kb = _ikb([_row(_btn("✅ Yuborish", "adm:submit"),
                    _btn("✏️ O‘zgartirish", "adm:edit"),
                    _btn("❌ Bekor qilish", "adm:cancel"))])

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
    if cb.from_user.id not in settings.admin_ids:
        return
    await cb.answer()
    await cb.message.answer("Matn/caption qayta yuboring:")
    await state.set_state(SendFSM.TEXT)

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:cancel")
async def adm_cancel(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    await cb.answer("❌")
    await state.clear()
    await cb.message.answer("Tarqatma bekor qilindi.", reply_markup=None)

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:submit")
async def adm_submit(cb: CallbackQuery, state: FSMContext):
    if cb.from_user.id not in settings.admin_ids:
        return
    await cb.answer("🚀")

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
            if not db:
                await cb.message.answer("DB ulanmagan — hammaga yuborish mumkin emas.")
                await state.clear()
                return
            all_users = db.get_all_users(0, 10_000)
            for u in all_users:
                uid = int(u.get("user_id") or u.get("id"))
                try:
                    await _send_one(cb, uid, media, text)
                    sent_ok += 1
                    await asyncio.sleep(0.05)
                except (TelegramForbiddenError, TelegramBadRequest):
                    sent_fail += 1
                except Exception:
                    sent_fail += 1
    finally:
        await state.clear()

    await cb.message.answer(f"✅ Yuborildi: {sent_ok} | ❌ Xato: {sent_fail}")

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

def _users_page_kb(page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    nav: List[InlineKeyboardButton] = []
    if has_prev:
        nav.append(_btn("⬅️", f"adm:users:{page-1}"))
    nav.append(_btn(f"{page+1}", f"adm:users:{page}"))
    if has_next:
        nav.append(_btn("➡️", f"adm:users:{page+1}"))
    rows = []
    if nav:
        rows.append(nav)
    rows.append([_btn("◀️ Orqaga", "adm:back")])
    return _ikb(rows)

@router.callback_query(F.data.startswith("adm:users:"))
async def adm_users(cb: CallbackQuery):
    if cb.from_user.id not in settings.admin_ids:
        return
    await cb.answer()
    if not db:
        await cb.message.answer("DB ulanmagan — ro‘yxat yo‘q.")
        return

    page = int(cb.data.split(":")[-1])
    # +1 ta qo‘shimcha yozuv — nav bor-yo‘qligini bilish uchun
    all_users = db.get_all_users(page * PAGE_SIZE, PAGE_SIZE + 1)
    items = all_users[:PAGE_SIZE]
    has_next = len(all_users) > PAGE_SIZE
    has_prev = page > 0

    if not items:
        await cb.message.edit_text("— Ro‘yxat bo‘sh —", reply_markup=_users_page_kb(page, has_prev, has_next))
        return

    blocks = [_user_card(u) for u in items]
    txt = "👥 <b>Foydalanuvchilar</b>\n\n" + "\n".join(blocks)
    await cb.message.edit_text(txt, parse_mode="HTML", reply_markup=_users_page_kb(page, has_prev, has_next))
