# -*- coding: utf-8 -*-
# app/handlers/audit.py

import calendar
import datetime as dt
import itertools
import re
from typing import Dict, Any, List, Tuple

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from ..locales import L
from ..storage.memory import get_lang, get_profile
from ..config import settings

router = Router()

# --- In-memory (demo) ---
BOOKINGS: Dict[int, Dict[str, Any]] = {}
BOOKING_SEQ = itertools.count(1001)
PENDING_RETIME: Dict[int, int] = {}  # user_id -> booking_id

# --- Time parser ---
_TIME_RE = re.compile(
    r"^\s*(?P<h>[01]?\d|2[0-3])(?::|\.|\s)?(?P<m>[0-5]\d)?\s*(?P<ampm>[ap]m)?\s*$",
    re.IGNORECASE,
)

def _parse_time(text: str) -> str | None:
    if not text:
        return None
    m = _TIME_RE.match(text.strip())
    if not m:
        return None
    h = int(m.group("h"))
    mnt = m.group("m")
    ampm = (m.group("ampm") or "").lower()
    if ampm:
        if h == 12:
            h = 0
        if ampm == "pm":
            h += 12
    minute = int(mnt) if mnt is not None else 0
    if not (0 <= h <= 23 and 0 <= minute <= 59):
        return None
    return f"{h:02d}:{minute:02d}"

# --- FSM ---
class AuditFSM(StatesGroup):
    BIZ_NAME = State()
    BIZ_DESC = State()
    REVENUE = State()
    MONTH = State()
    DAY = State()
    TIME = State()
    TIME_MANUAL = State()
    REVIEW = State()

# --- Helpers ---
def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

def _row(*btns: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    return [*btns]

def _ikb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _months(lang: str) -> List[Tuple[str, int]]:
    if lang == "ru":
        names = ["Янв","Фев","Мар","Апр","Май","Июн","Июл","Авг","Сен","Окт","Ноя","Дек"]
    elif lang == "en":
        names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    else:
        names = ["Yan","Fev","Mar","Apr","May","Iyun","Iyul","Avg","Sen","Okt","Noy","Dek"]
    return list(zip(names, range(1, 13)))

def _days_in_month(y: int, m: int) -> int:
    return calendar.monthrange(y, m)[1]

def _time_slots() -> List[str]:
    return [f"{h:02d}:00" for h in range(8, 20)]  # 08:00..19:00

def _booked_slots_for_date(year: int, month: int, day: int) -> set[str]:
    """Faqat admin tasdiqlagan bronlar band hisoblanadi."""
    taken: set[str] = set()
    for b in BOOKINGS.values():
        if b.get("status") == "approved" and b.get("year") == year and b.get("month") == month and b.get("day") == day:
            t = b.get("time")
            if t:
                taken.add(str(t))
    return taken

def _is_taken(year: int, month: int, day: int, time_s: str) -> bool:
    return time_s in _booked_slots_for_date(year, month, day)

def _admin_booking_text(t: dict, b: dict) -> str:
    prof = b.get("profile", {})
    parts = [
        f"<b>{t['aud_admin_title']}</b>",
        f"🌍 Lang: <code>{b.get('lang')}</code>",
        f"👤 Name: {prof.get('name') or '-'}",
        f"@ Username: @{prof.get('username') or '-'}",
        f"☎️ Contact: {prof.get('phone') or '-'}",
        "—" * 10,
        f"🏢 Biznes: {b.get('biz_name')}",
        f"📝 Tafsilot: {b.get('biz_desc')}",
        f"💰 Daromad: {b.get('revenue')}",
        f"📅 Sana: {b.get('year')}-{b.get('month'):02d}-{b.get('day'):02d}",
        f"⏰ Vaqt: {b.get('time')}",
        f"👤 UserID: <code>{b.get('user_id')}</code>",
    ]
    return "\n".join(parts)

def _user_review_text(t: dict, b: dict) -> str:
    return (
        f"✨ <b>{t['aud_review_title']}</b>\n\n"
        f"🏢 <b>Biznes:</b> {b.get('biz_name')}\n"
        f"📝 <b>Tafsilot:</b> {b.get('biz_desc')}\n"
        f"💰 <b>Daromad:</b> {b.get('revenue')}\n"
        f"📅 <b>Sana:</b> {b.get('year')}-{b.get('month'):02d}-{b.get('day'):02d}\n"
        f"⏰ <b>Vaqt:</b> {b.get('time')}\n"
    )

# --- Entry ---
@router.message(F.text.func(lambda s: s in {L["uz"]["btn_audit"], L["en"]["btn_audit"], L["ru"]["btn_audit"]}))
async def audit_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = _t(lang)
    kb = _ikb([_row(
        InlineKeyboardButton(text=t["audit_web"], callback_data="audit:web"),
        InlineKeyboardButton(text=t["audit_book"], callback_data="audit:book"),
    )])
    await message.answer(f"<b>{t['audit_title']}</b>\n\n{t['audit_choose']}", reply_markup=kb)

# --- Website ---
@router.callback_query(F.data == "audit:web")
async def audit_web(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    url = getattr(settings, "AUDIT_WEBSITE_URL", "https://example.com/audit")
    kb = _ikb([
        _row(InlineKeyboardButton(text=t["more_btn"], url=url)),
        _row(InlineKeyboardButton(text=t["back_btn"], callback_data="audit:back")),
    ])
    await cb.answer()
    await cb.message.answer(t["audit_web_desc"], reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "audit:back")
async def audit_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    kb = _ikb([_row(
        InlineKeyboardButton(text=t["audit_web"], callback_data="audit:web"),
        InlineKeyboardButton(text=t["audit_book"], callback_data="audit:book"),
    )])
    await cb.answer()
    await cb.message.answer(f"<b>{t['audit_title']}</b>\n\n{t['audit_choose']}", reply_markup=kb)

# --- Booking flow ---
@router.callback_query(F.data == "audit:book")
async def audit_book(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    await cb.answer()
    await state.clear()
    await state.update_data(lang=lang, user_id=cb.from_user.id, chat_id=cb.message.chat.id, status="pending")
    await cb.message.answer(t["aud_ask_biz_name"])
    await state.set_state(AuditFSM.BIZ_NAME)

@router.message(AuditFSM.BIZ_NAME)
async def aud_take_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    lang = get_lang(message.from_user.id, "uz"); t = _t(lang)
    if not name:
        await message.answer(t["aud_ask_biz_name"]); return
    await state.update_data(biz_name=name)
    await message.answer(t["aud_ask_biz_desc"])
    await state.set_state(AuditFSM.BIZ_DESC)

@router.message(AuditFSM.BIZ_DESC)
async def aud_take_desc(message: Message, state: FSMContext):
    desc = (message.text or "").strip()
    lang = get_lang(message.from_user.id, "uz"); t = _t(lang)
    if not desc:
        await message.answer(t["aud_ask_biz_desc"]); return
    await state.update_data(biz_desc=desc)
    kb = _ikb([_row(
        InlineKeyboardButton(text=t["aud_rev_low"],  callback_data="aud:rev:low"),
        InlineKeyboardButton(text=t["aud_rev_mid"],  callback_data="aud:rev:mid"),
        InlineKeyboardButton(text=t["aud_rev_high"], callback_data="aud:rev:high"),
    )])
    await message.answer(t["aud_ask_revenue"], reply_markup=kb)
    await state.set_state(AuditFSM.REVENUE)

@router.callback_query(AuditFSM.REVENUE, F.data.startswith("aud:rev:"))
async def aud_take_revenue(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    key = cb.data.split(":")[-1]
    rev_map = {"low": t["aud_rev_low"], "mid": t["aud_rev_mid"], "high": t["aud_rev_high"]}
    await state.update_data(revenue=rev_map.get(key, key))
    await cb.answer()

    months = _months(lang)
    rows, row = [], []
    for label, m in months:
        row.append(InlineKeyboardButton(text=label, callback_data=f"aud:mo:{m}"))
        if len(row) == 4:
            rows.append(_row(*row)); row = []
    if row: rows.append(_row(*row))
    await cb.message.answer(t["aud_pick_month"], reply_markup=_ikb(rows))
    await state.set_state(AuditFSM.MONTH)

@router.callback_query(AuditFSM.MONTH, F.data.startswith("aud:mo:"))
async def aud_take_month(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    month = int(cb.data.split(":")[-1])
    year = dt.date.today().year
    await state.update_data(month=month, year=year)
    await cb.answer()

    ndays = _days_in_month(year, month)
    rows, row = [], []
    for d in range(1, ndays + 1):
        row.append(InlineKeyboardButton(text=str(d), callback_data=f"aud:day:{d}"))
        if len(row) == 7:
            rows.append(_row(*row)); row = []
    if row: rows.append(_row(*row))
    await cb.message.answer(t["aud_pick_day"], reply_markup=_ikb(rows))
    await state.set_state(AuditFSM.DAY)

@router.callback_query(AuditFSM.DAY, F.data.startswith("aud:day:"))
async def aud_take_day(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    day = int(cb.data.split(":")[-1])
    await state.update_data(day=day)
    await cb.answer()

    data = await state.get_data()
    taken = _booked_slots_for_date(data["year"], data["month"], day)

    # time grid with locked slots
    rows, row = [], []
    for s in _time_slots():
        if s in taken:
            row.append(InlineKeyboardButton(text=f"🔒 {s}", callback_data="aud:noop"))
        else:
            row.append(InlineKeyboardButton(text=s, callback_data=f"aud:time:{s}"))
        if len(row) == 4:
            rows.append(_row(*row)); row = []
    if row: rows.append(_row(*row))
    rows.append(_row(InlineKeyboardButton(text=t["aud_time_manual"], callback_data="aud:time:manual")))
    await cb.message.answer(t["aud_pick_time"], reply_markup=_ikb(rows))
    await state.set_state(AuditFSM.TIME)

@router.callback_query(F.data == "aud:noop")
async def aud_noop(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    await cb.answer(_t(lang).get("aud_slot_taken", "Bu vaqt band."), show_alert=False)

@router.callback_query(AuditFSM.TIME, F.data.startswith("aud:time:"))
async def aud_take_time(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    # ⚠️ to'g'ri ajratish: 'aud:time:08:00' -> '08:00'
    _, _, val = cb.data.partition("aud:time:")
    await cb.answer()

    if val == "manual":
        await cb.message.answer(t["aud_enter_time_prompt"], parse_mode="HTML")
        await state.set_state(AuditFSM.TIME_MANUAL)
        return

    data = await state.get_data()
    if _is_taken(data["year"], data["month"], data["day"], val):
        await cb.message.answer(t.get("aud_slot_taken", "Bu vaqt band. Iltimos, boshqa vaqt tanlang."))
        return

    await state.update_data(time=val)
    await _show_review(cb.message, state, lang)

@router.message(AuditFSM.TIME_MANUAL)
async def aud_take_time_manual(message: Message, state: FSMContext):
    lang = get_lang(message.from_user.id, "uz"); t = _t(lang)
    ts = _parse_time(message.text or "")
    if not ts:
        await message.answer(t["aud_time_invalid"], parse_mode="HTML"); return
    hh, mm = map(int, ts.split(":"))
    minutes = hh * 60 + mm
    if not (8 * 60 <= minutes <= 19 * 60):
        await message.answer(t["aud_time_invalid"], parse_mode="HTML"); return

    data = await state.get_data()
    if _is_taken(data["year"], data["month"], data["day"], ts):
        await message.answer(t.get("aud_slot_taken", "Bu vaqt band. Iltimos, boshqa vaqt tanlang."))
        return

    await state.update_data(time=ts)
    await _show_review(message, state, lang)

async def _show_review(msg: Message, state: FSMContext, lang: str):
    t = _t(lang)
    data = await state.get_data()
    prof = get_profile(data.get("user_id") or msg.chat.id) or {}
    prof.setdefault("user_id", data.get("user_id") or msg.chat.id)
    data.update(profile=prof, lang=lang)
    await state.update_data(**data)

    text = _user_review_text(t, data)
    kb = _ikb([_row(
        InlineKeyboardButton(text=t["aud_review_confirm"], callback_data="aud:confirm"),
        InlineKeyboardButton(text=t["aud_review_edit"],    callback_data="aud:edit"),
        InlineKeyboardButton(text=t["aud_review_cancel"],  callback_data="aud:cancel"),
    )])
    await msg.answer(text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(AuditFSM.REVIEW)

# --- Review actions ---
@router.callback_query(AuditFSM.REVIEW, F.data == "aud:cancel")
async def aud_cancel(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    await cb.answer("❌")
    await state.clear()
    await cb.message.answer(t["aud_canceled"])

@router.callback_query(AuditFSM.REVIEW, F.data == "aud:edit")
async def aud_edit(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    kb = _ikb([
        _row(
            InlineKeyboardButton(text=t["aud_edit_biz_name"], callback_data="aud:edit:name"),
            InlineKeyboardButton(text=t["aud_edit_biz_desc"], callback_data="aud:edit:desc"),
        ),
        _row(
            InlineKeyboardButton(text=t["aud_edit_revenue"],  callback_data="aud:edit:rev"),
            InlineKeyboardButton(text=t["aud_edit_datetime"], callback_data="aud:edit:dt"),
        ),
    ])
    await cb.answer()
    await cb.message.answer(t["aud_edit_which"], reply_markup=kb)

@router.callback_query(AuditFSM.REVIEW, F.data.startswith("aud:edit:"))
async def aud_edit_switch(cb: CallbackQuery, state: FSMContext):
    part = cb.data.split(":")[-1]
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    await cb.answer()
    if part == "name":
        await cb.message.answer(t["aud_ask_biz_name"]); await state.set_state(AuditFSM.BIZ_NAME)
    elif part == "desc":
        await cb.message.answer(t["aud_ask_biz_desc"]); await state.set_state(AuditFSM.BIZ_DESC)
    elif part == "rev":
        kb = _ikb([_row(
            InlineKeyboardButton(text=t["aud_rev_low"],  callback_data="aud:rev:low"),
            InlineKeyboardButton(text=t["aud_rev_mid"],  callback_data="aud:rev:mid"),
            InlineKeyboardButton(text=t["aud_rev_high"], callback_data="aud:rev:high"),
        )])
        await cb.message.answer(t["aud_ask_revenue"], reply_markup=kb); await state.set_state(AuditFSM.REVENUE)
    elif part == "dt":
        months = _months(lang)
        rows, row = [], []
        for label, m in months:
            row.append(InlineKeyboardButton(text=label, callback_data=f"aud:mo:{m}"))
            if len(row) == 4:
                rows.append(_row(*row)); row = []
        if row: rows.append(_row(*row))
        await cb.message.answer(t["aud_pick_month"], reply_markup=_ikb(rows))
        await state.set_state(AuditFSM.MONTH)

@router.callback_query(AuditFSM.REVIEW, F.data == "aud:confirm")
async def aud_confirm(cb: CallbackQuery, state: FSMContext):
    lang = get_lang(cb.from_user.id, "uz"); t = _t(lang)
    data = await state.get_data()
    await cb.answer("✅")

    bid = next(BOOKING_SEQ)
    data.update({
        "booking_id": bid,
        "user_id": data.get("user_id") or cb.from_user.id,
        "chat_id": data.get("chat_id") or cb.message.chat.id,
        "profile": get_profile(cb.from_user.id) or {},
        "lang": lang,
        "status": "pending",
    })
    data["profile"].setdefault("user_id", data["user_id"])
    BOOKINGS[bid] = data

    await cb.message.answer(t["aud_sent_to_admins"])
    await state.clear()

    text = _admin_booking_text(t, data)
    kb = _ikb([_row(
        InlineKeyboardButton(text=t["aud_admin_approve"], callback_data=f"audadmin:ok:{bid}"),
        InlineKeyboardButton(text=t["aud_admin_retime"],  callback_data=f"audadmin:rt:{bid}"),
        InlineKeyboardButton(text=t["aud_admin_cancel"],  callback_data=f"audadmin:cn:{bid}"),
    )])
    await cb.message.bot.send_message(
        chat_id=getattr(settings, "ADMIN_GROUP_ID", getattr(settings, "faq_group_id", -1001234567890)),
        text=text, reply_markup=kb, parse_mode="HTML"
    )

# --- Admin actions ---
@router.callback_query(F.data.startswith("audadmin:"))
async def admin_actions(cb: CallbackQuery):
    parts = cb.data.split(":")
    action, bid = parts[1], int(parts[2])
    booking = BOOKINGS.get(bid)
    if not booking:
        await cb.answer("Not found", show_alert=True); return

    user_id = booking.get("user_id")
    lang = booking.get("lang", "uz")
    t = _t(lang)
    await cb.answer()

    if action == "ok":
        booking["status"] = "approved"   # ✅ endi slot band hisoblanadi
        if user_id:
            await cb.message.bot.send_message(user_id, t["aud_user_approved"])
        await cb.message.edit_reply_markup(reply_markup=None)

    elif action == "rt":
        booking["status"] = "retime_requested"
        if user_id:
            PENDING_RETIME[user_id] = bid
            await cb.message.bot.send_message(user_id, t["aud_user_retime"], parse_mode="HTML")
        await cb.message.edit_reply_markup(reply_markup=None)

    elif action == "cn":
        booking["status"] = "canceled"
        if user_id:
            await cb.message.bot.send_message(user_id, t["aud_user_canceled"])
        await cb.message.edit_reply_markup(reply_markup=None)

# --- User sends new time after admin retime request ---
@router.message(F.text)
async def handle_retime_if_pending(message: Message):
    user_id = message.from_user.id
    if user_id not in PENDING_RETIME:
        return

    bid = PENDING_RETIME.pop(user_id)
    booking = BOOKINGS.get(bid)
    if not booking:
        return

    ts = _parse_time(message.text or "")
    if not ts:
        await message.answer("❗️ Noto‘g‘ri vaqt. Namuna: 14:00"); return

    hh, mm = map(int, ts.split(":"))
    minutes = hh * 60 + mm
    if not (8 * 60 <= minutes <= 19 * 60):
        await message.answer("❗️ Vaqt 08:00–19:00 oralig‘ida bo‘lishi kerak."); return

    if _is_taken(booking["year"], booking["month"], booking["day"], ts):
        await message.answer("❗️ Bu vaqt allaqachon band. Iltimos, boshqa vaqt tanlang."); return

    booking["time"] = ts
    booking["status"] = "pending"

    await message.answer("✅ Yangi vaqt qabul qilindi.")
    await message.bot.send_message(
        chat_id=getattr(settings, "ADMIN_GROUP_ID", getattr(settings, "faq_group_id", -1001234567890)),
        text=f"♻️ Booking #{bid} — user updated time to {booking['time']}",
    )
