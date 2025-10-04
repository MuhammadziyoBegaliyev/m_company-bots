# -*- coding: utf-8 -*-
# app/handlers/admin.py

from __future__ import annotations

import asyncio
from typing import List, Optional

from loguru import logger
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from ..config import settings
from ..locales import L
from ..storage.memory import get_lang

# ixtiyoriy DB yordamchilari (sizda bor)
try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()

# ==========================
# Foydali util-lar
# ==========================

def _t(lang: str) -> dict:
    """Til lug‘ati + xavfsiz fallback."""
    return L.get(lang, L["uz"])

def _g(t: dict, key: str, default: str) -> str:
    """Get with fallback (lug‘atda bo‘lmasa ham matn chiqsin)."""
    return t.get(key, default)

def _ikb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _row(*btns: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    return [*btns]

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)

def _is_admin(user_id: int) -> bool:
    return user_id in (settings.admin_ids or [])


# ==========================
# Admin kirish (/admin)
# ==========================

@router.message(Command("admin"), ~F.from_user.id.in_(settings.admin_ids))
async def admin_denied(message: Message):
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    await message.answer(_g(t, "adm_not_admin", "❌ Siz admin emassiz."))

@router.message(Command("admin"), F.from_user.id.in_(settings.admin_ids))
async def admin_menu(message: Message):
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    logger.info(f"Admin menu -> {message.from_user.id}")

    kb = _ikb([
        _row(_btn("📣 " + _g(t, "adm_send_msg", "Xabar yuborish"), "adm:send")),
        _row(_btn("👥 " + _g(t, "adm_users_list", "Foydalanuvchilar ro‘yxati"), "adm:users:0")),
    ])
    await message.answer("🛠 <b>Admin panel</b>", reply_markup=kb, parse_mode="HTML")


# ==========================
# Yordamchi: foydalanuvchi kartasi
# ==========================

def _user_card(u: dict) -> str:
    id_       = u.get("user_id") or u.get("id")
    username  = u.get("username") or "-"
    name      = u.get("name") or u.get("full_name") or "-"
    phone     = u.get("phone") or "-"
    lang      = u.get("lang") or "-"
    onboarded = "✅" if u.get("onboarded") else "—"
    feature   = u.get("last_feature") or "-"
    last_seen = u.get("last_seen") or u.get("created_at") or "-"

    return (
        f"🆔 <code>{id_}</code>\n"
        f"👤 {name}\n"
        f"@ {username}\n"
        f"☎️ {phone}\n"
        f"🌍 {lang} | 🎯 {feature}\n"
        f"🟢 Onboarded: {onboarded}\n"
        f"⏱ Oxirgi faollik: {last_seen}\n"
        + "—" * 12
    )


# ==========================
# 1) 📣 Xabar yuborish oqimi
# ==========================

class SendFSM(StatesGroup):
    TARGET   = State()    # one | all
    ONE_USER = State()    # id/username/forward
    MEDIA    = State()    # (optional) photo/video
    TEXT     = State()    # message text
    PREVIEW  = State()

def _send_menu_kb(t: dict) -> InlineKeyboardMarkup:
    return _ikb([
        _row(
            _btn("🧍‍♂️ " + _g(t, "adm_send_one", "Bitta foydalanuvchi"), "adm:send:one"),
            _btn("🌍 "   + _g(t, "adm_send_all", "Hammaga"),              "adm:send:all"),
        ),
        _row(_btn(_g(t, "back_btn", "◀️ Orqaga"), "adm:back")),
    ])

@router.callback_query(F.data == "adm:send")
async def adm_send_root(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer()
    await state.clear()
    await cb.message.answer(_g(t, "adm_send_choose", "Qaysi turdagi xabar?"), reply_markup=_send_menu_kb(t))

@router.callback_query(F.data.in_({"adm:send:one", "adm:send:all"}))
async def adm_send_target(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer()

    target = "one" if cb.data.endswith(":one") else "all"
    await state.update_data(target=target, media=None, text=None)

    if target == "one":
        await cb.message.answer(_g(t, "adm_ask_user", "ID yoki @username yuboring (yoki xabarini forward qiling):"))
        await state.set_state(SendFSM.ONE_USER)
    else:
        await cb.message.answer(_g(t, "adm_send_media", "Rasm/video yuboring (ixtiyoriy)."))
        await cb.message.answer(
            _g(t, "adm_skip_or_send", "Yoki o‘tkazib yuborish uchun tugmani bosing."),
            reply_markup=_ikb([_row(_btn("⏭ " + _g(t, "skip_btn", "O‘tkazib yuborish"), "adm:skip_media"))]),
        )
        await state.set_state(SendFSM.MEDIA)

@router.message(SendFSM.ONE_USER)
async def adm_one_user(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)

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
        await message.answer(_g(t, "adm_user_not_found", "Foydalanuvchi topilmadi."))
        return

    await state.update_data(to_user=user_id)
    await message.answer(_g(t, "adm_send_media", "Rasm/video yuboring (ixtiyoriy)."))
    await message.answer(
        _g(t, "adm_skip_or_send", "Yoki o‘tkazib yuborish uchun tugmani bosing."),
        reply_markup=_ikb([_row(_btn("⏭ " + _g(t, "skip_btn", "O‘tkazib yuborish"), "adm:skip_media"))]),
    )
    await state.set_state(SendFSM.MEDIA)

@router.callback_query(SendFSM.MEDIA, F.data == "adm:skip_media")
async def adm_skip_media(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer("⏭")
    await cb.message.answer(_g(t, "adm_ask_text", "Matn yuboring:"))
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.MEDIA, F.photo)
async def adm_take_photo(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    file_id = message.photo[-1].file_id
    await state.update_data(media={"type": "photo", "file_id": file_id})
    t = _t(get_lang(message.from_user.id, settings.DEFAULT_LANG))
    await message.answer(_g(t, "adm_ask_text", "Matn yuboring:"))
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.MEDIA, F.video)
async def adm_take_video(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    file_id = message.video.file_id
    await state.update_data(media={"type": "video", "file_id": file_id})
    t = _t(get_lang(message.from_user.id, settings.DEFAULT_LANG))
    await message.answer(_g(t, "adm_ask_text", "Matn yuboring:"))
    await state.set_state(SendFSM.TEXT)

@router.message(SendFSM.TEXT)
async def adm_take_text(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
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
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer()
    await cb.message.answer(_g(t, "adm_ask_text", "Matn yuboring:"))
    await state.set_state(SendFSM.TEXT)

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:cancel")
async def adm_cancel(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer("❌")
    await state.clear()
    await cb.message.answer(_g(t, "adm_broadcast_canceled", "Yuborish bekor qilindi."))

@router.callback_query(SendFSM.PREVIEW, F.data == "adm:submit")
async def adm_submit(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer("🚀")

    data   = await state.get_data()
    target = data.get("target")
    media  = data.get("media")
    text   = data.get("text") or ""

    sent_ok = 0
    sent_fail = 0

    try:
        if target == "one":
            uid = int(data["to_user"])
            await _send_one(cb, uid, media, text)
            sent_ok = 1
        else:
            # broadcast — barcha foydalanuvchilar (sizda: db.get_all_users)
            users = db.get_all_users(0, 100_000) if db else []
            for u in users:
                uid = int(u.get("user_id") or u.get("id"))
                try:
                    await _send_one(cb, uid, media, text)
                    sent_ok += 1
                    await asyncio.sleep(0.04)  # yumshoq rate-limit
                except (TelegramForbiddenError, TelegramBadRequest):
                    sent_fail += 1
                except Exception:
                    sent_fail += 1
    finally:
        await state.clear()

    done = _g(t, "adm_broadcast_done", "Tayyor: {ok} ta yuborildi, {fail} ta xato.")
    await cb.message.answer(f"✅ {done.format(ok=sent_ok, fail=sent_fail)}")

async def _send_one(cb: CallbackQuery, uid: int, media: Optional[dict], text: str):
    if media:
        if media["type"] == "photo":
            await cb.message.bot.send_photo(uid, media["file_id"], caption=text or None)
        else:
            await cb.message.bot.send_video(uid, media["file_id"], caption=text or None)
    else:
        await cb.message.bot.send_message(uid, text or " ")


# ==========================
# 2) 👥 Foydalanuvchilar ro‘yxati
# ==========================

PAGE_SIZE = 10

def _users_nav_kb(page: int, has_prev: bool, has_next: bool, t: dict) -> InlineKeyboardMarkup:
    nav = []
    if has_prev:
        nav.append(_btn("⬅️", f"adm:users:{page-1}"))
    nav.append(_btn(f"{page+1}", f"adm:users:{page}"))  # “current page”
    if has_next:
        nav.append(_btn("➡️", f"adm:users:{page+1}"))

    rows: List[List[InlineKeyboardButton]] = []
    if nav:
        rows.append(nav)
    rows.append([_btn("🔍 " + _g(t, "adm_user_show_btn", "Foydalanuvchini ko‘rish"), "adm:find")])
    rows.append([_btn(_g(t, "back_btn", "◀️ Orqaga"), "adm:back")])
    return _ikb(rows)

@router.callback_query(F.data.startswith("adm:users:"))
async def adm_users(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer()

    page = int(cb.data.split(":")[-1])
    users = db.get_all_users(page * PAGE_SIZE, PAGE_SIZE + 1) if db else []  # +1 to check next
    items = users[:PAGE_SIZE]
    has_next = len(users) > PAGE_SIZE
    has_prev = page > 0

    if not items:
        await cb.message.answer("— Ro‘yxat bo‘sh —")
        return

    blocks = [_user_card(u) for u in items]
    txt = "👥 <b>Foydalanuvchilar</b>\n\n" + "\n".join(blocks)
    await cb.message.answer(txt, parse_mode="HTML",
                            reply_markup=_users_nav_kb(page, has_prev, has_next, t))

@router.callback_query(F.data == "adm:find")
async def adm_find_prompt(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer()
    await state.set_state(SendFSM.ONE_USER)  # shu holatni qayta ishlatamiz
    await cb.message.answer(_g(t, "adm_find_prompt", "ID yoki @username yuboring (yoki xabarini forward qiling):"))

# ONE_USER holatini yuqorida yuborish oqimi ham ishlatadi.
# Agar bu 'find' bo‘lsa, state ichida 'target' yo‘q bo‘ladi — demak bu yerda “karta ko‘rsatish”ni bajaramiz.
@router.message(SendFSM.ONE_USER)
async def adm_find_user_show(message: Message, state: FSMContext):
    if not _is_admin(message.from_user.id):
        return
    t = _t(get_lang(message.from_user.id, settings.DEFAULT_LANG))

    data = await state.get_data()
    # Agar target bo‘lsa — bu send oqimi, yuqoridagi handler allaqachon ushlaydi.
    if data.get("target") in ("one", "all"):
        return

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
        await message.answer(_g(t, "adm_user_not_found", "Foydalanuvchi topilmadi."))
        await state.clear()
        return

    u = db.get_user(uid)
    if not u:
        await message.answer(_g(t, "adm_user_not_found", "Foydalanuvchi topilmadi."))
        await state.clear()
        return

    # Tez xabar yuborish tugmasi bilan karta
    kb = _ikb([
        [_btn("✉️ " + _g(t, "adm_msg_this_user", "Shu foydalanuvchiga yozish"), f"adm:sendto:{uid}")],
        [_btn(_g(t, "back_btn", "◀️ Orqaga"), "adm:back")],
    ])

    await message.answer(_user_card(u), parse_mode="HTML", reply_markup=kb)
    await state.clear()

@router.callback_query(F.data.startswith("adm:sendto:"))
async def adm_send_to_user_fast(cb: CallbackQuery, state: FSMContext):
    """Karta ichidagi “Shu foydalanuvchiga yozish” tugmasi."""
    if not _is_admin(cb.from_user.id):
        return
    t = _t(get_lang(cb.from_user.id, settings.DEFAULT_LANG))
    await cb.answer()

    uid = int(cb.data.split(":")[-1])
    await state.clear()
    await state.update_data(target="one", to_user=uid, media=None, text=None)

    await cb.message.answer(_g(t, "adm_send_media", "Rasm/video yuboring (ixtiyoriy)."))
    await cb.message.answer(
        _g(t, "adm_skip_or_send", "Yoki o‘tkazib yuborish uchun tugmani bosing."),
        reply_markup=_ikb([_row(_btn("⏭ " + _g(t, "skip_btn", "O‘tkazib yuborish"), "adm:skip_media"))]),
    )
    await state.set_state(SendFSM.MEDIA)


# ==========================
# Orqaga
# ==========================

@router.callback_query(F.data == "adm:back")
async def adm_back(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    await cb.answer("◀️")
    await admin_menu(cb.message)


# ==========================
# Qo‘shimcha: diagnostika
# ==========================

@router.message(Command("whoami"))
async def whoami(message: Message):
    await message.answer(f"🆔 <code>{message.from_user.id}</code>")
