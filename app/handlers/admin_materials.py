# -*- coding: utf-8 -*-
# app/handlers/admin_materials.py

from __future__ import annotations
from typing import Optional, List, Dict, Any

from loguru import logger
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData

from ..config import settings
from ..locales import L
from ..storage.memory import get_lang

# --- DB (mavjud bo'lsa ishlatamiz) ---
try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()
logger.info("🧰 admin_materials router loaded")

# ===================== Config =====================
CATS = [("book", "📘"), ("article", "🧠"), ("video", "🎬"), ("audio", "🎧")]
LANGS = [("uz", "🇺🇿"), ("en", "🇬🇧"), ("ru", "🇷🇺")]
PAGE_SIZE = 8

# ===================== Helpers =====================
def _is_admin(uid: int) -> bool:
    return uid in (settings.admin_ids or [])

def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

def _g(t: dict, key: str, default: str) -> str:
    return t.get(key, default)

async def _safe(cb: CallbackQuery, text: Optional[str] = None):
    try:
        await cb.answer(text)
    except TelegramBadRequest:
        pass

def _ikb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)

def _short(s: str | None, n: int = 120) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"

def _cat_icon(cat: str) -> str:
    for k, icon in CATS:
        if k == cat:
            return icon
    return "📦"

def _has_method(obj: Any, name: str) -> bool:
    return hasattr(obj, name) and callable(getattr(obj, name, None))

def _split_blocks(text: str, max_len: int = 3800) -> list[str]:
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

# ===================== CallbackData Factory =====================
class MAdm(CallbackData, prefix="madmin"):
    act: str               # root | add | add_cat | add_lang | list_pick | list | item | back | stats | save | cancel | preview | tpaid | setprice | etitle | edesc | delete | publish | dup | nop
    cat: Optional[str] = None
    lang: Optional[str] = None
    mid: Optional[int] = None
    page: Optional[int] = None

# ===================== FSM =====================
class AddFSM(StatesGroup):
    FLOW = State()     # guard
    CAT = State()
    LANG = State()
    TITLE = State()
    DESC = State()
    PAID = State()
    PRICE = State()
    SRC = State()
    PREVIEW = State()

class EditFSM(StatesGroup):
    MID = State()
    TITLE = State()
    DESC = State()
    PRICE = State()

# ===================== Keyboards =====================
def _root_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    return _ikb([
        [_btn(f"➕ {_g(t, 'adm_mat_add', 'Yangi material qo‘shish')}", MAdm(act="add").pack())],
        [_btn(f"📚 {_g(t, 'adm_mat_list', 'Ro‘yxat')}", MAdm(act="list_pick").pack())],
        [_btn(f"📈 {_g(t, 'adm_mat_stats', 'Statistika')}", MAdm(act="stats").pack())],
    ])

def _cats_kb(next_act: str) -> InlineKeyboardMarkup:
    rows = [
        [
            _btn(f"{CATS[0][1]} {CATS[0][0].title()}", MAdm(act=next_act, cat=CATS[0][0]).pack()),
            _btn(f"{CATS[1][1]} {CATS[1][0].title()}", MAdm(act=next_act, cat=CATS[1][0]).pack()),
        ],
        [
            _btn(f"{CATS[2][1]} {CATS[2][0].title()}", MAdm(act=next_act, cat=CATS[2][0]).pack()),
            _btn(f"{CATS[3][1]} {CATS[3][0].title()}", MAdm(act=next_act, cat=CATS[3][0]).pack()),
        ],
        [_btn("🏠", MAdm(act="root").pack())],
    ]
    return _ikb(rows)

def _langs_kb(next_act: str) -> InlineKeyboardMarkup:
    rows = [[_btn(f"{flag} {code.upper()}", MAdm(act=next_act, lang=code).pack())] for code, flag in LANGS]
    rows.append([_btn("🏠", MAdm(act="root").pack())])
    return _ikb(rows)

def _list_nav_kb(cat: str, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    nav: list[InlineKeyboardButton] = []
    if has_prev:
        nav.append(_btn("⬅️", MAdm(act="list", cat=cat, page=page - 1).pack()))
    nav.append(_btn(f"{page+1}", MAdm(act="nop", page=page).pack()))
    if has_next:
        nav.append(_btn("➡️", MAdm(act="list", cat=cat, page=page + 1).pack()))
    rows: list[list[InlineKeyboardButton]] = []
    if nav:
        rows.append(nav)
    rows.append([_btn("◀️", MAdm(act="list_pick").pack()), _btn("🏠", MAdm(act="root").pack())])
    return _ikb(rows)

def _item_kb(item: Dict[str, Any]) -> InlineKeyboardMarkup:
    mid = int(item["id"])
    paid = bool(item.get("is_paid"))
    return _ikb([
        [_btn("👁 Preview", MAdm(act="preview", mid=mid).pack()),
         _btn("📤 Publish", MAdm(act="publish", mid=mid).pack())],
        [_btn(("🔓 Bepulga" if paid else "🔒 Pullikka"), MAdm(act="tpaid", mid=mid).pack()),
         _btn("💰 Narx", MAdm(act="setprice", mid=mid).pack())],
        [_btn("✏️ Title", MAdm(act="etitle", mid=mid).pack()),
         _btn("📝 Desc", MAdm(act="edesc", mid=mid).pack())],
        [_btn("🧬 Duplicate", MAdm(act="dup", mid=mid).pack()),
         _btn("🗑 O‘chirish", MAdm(act="delete", mid=mid).pack())],
        [_btn("◀️", MAdm(act="list_pick").pack()), _btn("🏠", MAdm(act="root").pack())],
    ])

# ===================== Guards =====================
async def _ensure_flow(state: FSMContext) -> dict:
    """Add flow guard and ensure CAT/LANG as needed."""
    data = await state.get_data()
    return data

async def _require_add_ctx(message_or_cb, state: FSMContext, need_cat=False, need_lang=False) -> bool:
    data = await state.get_data()
    has_cat = "cat" in data and data["cat"]
    has_lang = "lang" in data and data["lang"]
    if need_cat and not has_cat:
        await state.set_state(AddFSM.CAT)
        if isinstance(message_or_cb, Message):
            await message_or_cb.answer("⚙️ Kategoriya tanlang:", reply_markup=_cats_kb("add_cat"))
        else:
            await message_or_cb.message.answer("⚙️ Kategoriya tanlang:", reply_markup=_cats_kb("add_cat"))
        return False
    if need_lang and not has_lang:
        await state.set_state(AddFSM.LANG)
        if isinstance(message_or_cb, Message):
            await message_or_cb.answer("🌍 Tilni tanlang:", reply_markup=_langs_kb("add_lang"))
        else:
            await message_or_cb.message.answer("🌍 Tilni tanlang:", reply_markup=_langs_kb("add_lang"))
        return False
    return True

# ===================== ENTRY (from /mats or admin panel) =====================
@router.message(Command("mats"))
async def mats_cmd(message: Message):
    if not _is_admin(message.from_user.id):
        return
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    await message.answer(f"🧰 <b>{_t(lang).get('adm_mat_title', 'Materiallar (Admin)')}</b>",
                         reply_markup=_root_kb(lang))

# From admin panel: adm:mats
@router.callback_query(F.data.in_({"adm:mats", "admin:mats", "adm:materials"}))
async def m_from_admin(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await _safe(cb)
    await cb.message.answer(f"🧰 <b>{_t(lang).get('adm_mat_title', 'Materiallar (Admin)')}</b>",
                            reply_markup=_root_kb(lang))

# Root menu (also “home”)
@router.callback_query(MAdm.filter(F.act == "root"))
async def m_root(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await _safe(cb)
    await cb.message.answer("🧰 <b>Materiallar (Admin)</b>", reply_markup=_root_kb(lang))

# ===================== STATS =====================
@router.callback_query(MAdm.filter(F.act == "stats"))
async def m_stats(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb)
    if not _has_method(db, "count_materials"):
        await cb.message.answer("ℹ️ DB.count_materials mavjud emas.")
        return
    lines = ["📈 <b>Statistika</b>"]
    for cat, icon in CATS:
        for code, flag in LANGS:
            try:
                cnt = db.count_materials(category=cat, lang=code)
            except Exception:
                cnt = "?"
            lines.append(f"{icon} {cat.title()} — {flag} {code.upper()}: <b>{cnt}</b> ta")
    for i, chunk in enumerate(_split_blocks("\n".join(lines))):
        await cb.message.answer(chunk, parse_mode="HTML")

# ===================== ADD FLOW =====================
@router.callback_query(MAdm.filter(F.act == "add"))
async def add_start(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    await _safe(cb)
    await state.clear()
    await state.set_state(AddFSM.CAT)
    await cb.message.answer("⚙️ Kategoriya tanlang:", reply_markup=_cats_kb("add_cat"))

# Catch category pick (with or without state) — robust
@router.callback_query(MAdm.filter(F.act == "add_cat"))
async def add_pick_cat(cb: CallbackQuery, callback_data: MAdm, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    cat = callback_data.cat
    if cat not in {c for c, _ in CATS}:
        await _safe(cb, "❌ Noto‘g‘ri kategoriya.")
        return
    await _safe(cb)
    await state.update_data(cat=cat)
    await state.set_state(AddFSM.LANG)
    await cb.message.answer("🌍 Tilni tanlang:", reply_markup=_langs_kb("add_lang"))

@router.callback_query(MAdm.filter(F.act == "add_lang"))
async def add_pick_lang(cb: CallbackQuery, callback_data: MAdm, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    lang = callback_data.lang
    if lang not in {l for l, _ in LANGS}:
        await _safe(cb, "❌ Noto‘g‘ri til.")
        return
    await _safe(cb)
    await state.update_data(lang=lang)
    await state.set_state(AddFSM.TITLE)
    await cb.message.answer("📝 Sarlavha yuboring:")

@router.message(AddFSM.TITLE)
async def add_title(message: Message, state: FSMContext):
    if not await _require_add_ctx(message, state, need_cat=True, need_lang=True):
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("❌ Sarlavha bo‘sh bo‘lishi mumkin emas. Qayta yuboring.")
        return
    await state.update_data(title=title)
    await state.set_state(AddFSM.DESC)
    await message.answer("📄 Tavsif yuboring (ixtiyoriy) yoki «/skip» yozing.")

@router.message(AddFSM.DESC, F.text == "/skip")
async def add_desc_skip(message: Message, state: FSMContext):
    if not await _require_add_ctx(message, state, need_cat=True, need_lang=True):
        return
    await state.update_data(desc=None)
    await state.set_state(AddFSM.PAID)
    await message.answer("💵 Bu material pullikmi? (ha/yo‘q)")

@router.message(AddFSM.DESC)
async def add_desc(message: Message, state: FSMContext):
    if not await _require_add_ctx(message, state, need_cat=True, need_lang=True):
        return
    await state.update_data(desc=(message.text or "").strip())
    await state.set_state(AddFSM.PAID)
    await message.answer("💵 Bu material pullikmi? (ha/yo‘q)")

@router.message(AddFSM.PAID)
async def add_paid(message: Message, state: FSMContext):
    if not await _require_add_ctx(message, state, need_cat=True, need_lang=True):
        return
    txt = (message.text or "").strip().lower()
    is_paid = txt in {"ha", "haa", "yes", "да", "true", "1"}
    await state.update_data(is_paid=is_paid)
    if is_paid:
        await state.set_state(AddFSM.PRICE)
        await message.answer("💰 Narxni kiriting (USD, masalan 9.99) yoki «/skip».")
    else:
        await state.set_state(AddFSM.SRC)
        await message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video)\n- URL (havola)\n- matn")

@router.message(AddFSM.PRICE, F.text == "/skip")
async def add_price_skip(message: Message, state: FSMContext):
    if not await _require_add_ctx(message, state, need_cat=True, need_lang=True):
        return
    await state.update_data(price_cents=0)
    await state.set_state(AddFSM.SRC)
    await message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video)\n- URL (havola)\n- matn")

@router.message(AddFSM.PRICE)
async def add_price(message: Message, state: FSMContext):
    if not await _require_add_ctx(message, state, need_cat=True, need_lang=True):
        return
    raw = (message.text or "0").strip().replace(",", ".")
    try:
        usd = float(raw)
        cents = max(0, int(round(usd * 100)))
    except Exception:
        cents = 0
    await state.update_data(price_cents=cents)
    await state.set_state(AddFSM.SRC)
    await message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video)\n- URL (havola)\n- matn")

@router.message(AddFSM.SRC, F.document | F.video | F.audio)
async def add_src_file(message: Message, state: FSMContext):
    if not await _require_add_ctx(message, state, need_cat=True, need_lang=True):
        return
    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.audio:
        file_id = message.audio.file_id
    await state.update_data(src_type="file_id", src_ref=file_id)
    await _preview_and_confirm(message, state)

@router.message(AddFSM.SRC, F.text)
async def add_src_text_or_url(message: Message, state: FSMContext):
    if not await _require_add_ctx(message, state, need_cat=True, need_lang=True):
        return
    txt = (message.text or "").strip()
    if txt.startswith("http://") or txt.startswith("https://"):
        await state.update_data(src_type="url", src_ref=txt)
    else:
        await state.update_data(src_type="text", src_ref=txt)
    await _preview_and_confirm(message, state)

async def _preview_and_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data.get("title") or ""
    desc = data.get("desc") or ""
    is_paid = bool(data.get("is_paid"))
    cents = int(data.get("price_cents") or 0)
    price = f"{cents/100:.2f}$" if (is_paid and cents) else "—"
    txt = (
        f"🧾 <b>Preview</b>\n"
        f"📂 Cat: {data['cat']}\n"
        f"🌍 Lang: {data['lang']}\n"
        f"📝 Title: {_short(title, 200)}\n"
        f"📄 Desc: {_short(desc, 500)}\n"
        f"💵 Paid: {'Yes' if is_paid else 'No'} | Price: {price}\n"
        f"📎 Source: {data['src_type']}"
    )
    kb = _ikb([
        [_btn("✅ Saqlash", MAdm(act="save").pack()),
         _btn("❌ Bekor", MAdm(act="cancel").pack())],
        [_btn("◀️", MAdm(act="add").pack()), _btn("🏠", MAdm(act="root").pack())],
    ])
    await message.answer(txt, reply_markup=kb)
    await state.set_state(AddFSM.PREVIEW)

@router.callback_query(AddFSM.PREVIEW, MAdm.filter(F.act == "cancel"))
async def add_cancel(cb: CallbackQuery, state: FSMContext):
    await _safe(cb, "❌")
    await state.clear()
    await cb.message.answer("Bekor qilindi.", reply_markup=_ikb([[_btn("🏠", MAdm(act="root").pack())]]))

@router.callback_query(AddFSM.PREVIEW, MAdm.filter(F.act == "save"))
async def add_save(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb, "💾")
    data = await state.get_data()
    try:
        mid = db.add_material(
            category=data["cat"],
            lang=data["lang"],
            title=data["title"],
            description=data.get("desc"),
            is_paid=bool(data.get("is_paid")),
            price_cents=int(data.get("price_cents") or 0),
            source_type=data["src_type"],
            source_ref=data["src_ref"],
            created_by=cb.from_user.id,
        )
        await state.clear()
        await cb.message.answer(f"✅ Saqlandi (ID: {mid}).", reply_markup=_ikb([
            [_btn("📤 Publish", MAdm(act="publish", mid=mid).pack()),
             _btn("👁 Preview", MAdm(act="preview", mid=mid).pack())],
            [_btn("🏠", MAdm(act="root").pack())]
        ]))
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}", reply_markup=_ikb([[_btn("🏠", MAdm(act="root").pack())]]))

# ===================== LIST / ITEMS =====================
@router.callback_query(MAdm.filter(F.act == "list_pick"))
async def list_pick_cat(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    await _safe(cb)
    await cb.message.answer("📚 Kategoriya tanlang:", reply_markup=_cats_kb("list"))

@router.callback_query(MAdm.filter(F.act == "list"))
async def list_cat(cb: CallbackQuery, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb)
    cat = callback_data.cat or ""
    page = int(callback_data.page or 0)
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    offset = page * PAGE_SIZE
    try:
        items = db.list_materials(category=cat, lang=lang, offset=offset, limit=PAGE_SIZE + 1)
    except Exception as e:
        await cb.message.answer(f"❌ DB xato: {e}")
        return
    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]
    has_prev = page > 0

    if not items:
        await cb.message.answer("— Bo‘sh —", reply_markup=_list_nav_kb(cat, page, has_prev, has_next))
        return

    header = f"{_cat_icon(cat)} <b>{t.get({'book':'materials_books','article':'materials_articles','video':'materials_videos','audio':'materials_audios'}.get(cat,''), cat.title())}</b>"
    kb_rows: List[List[InlineKeyboardButton]] = []
    for it in items:
        tag = "🔒" if it.get("is_paid") else "✅"
        kb_rows.append([_btn(f"{tag} #{it['id']} — {_short(it['title'], 60)}", MAdm(act="item", mid=int(it['id'])).pack())])
    kb = _ikb(kb_rows + _list_nav_kb(cat, page, has_prev, has_next).inline_keyboard)
    await cb.message.answer(header, reply_markup=kb, parse_mode="HTML")

@router.callback_query(MAdm.filter(F.act == "item"))
async def item_open(cb: CallbackQuery, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb)
    mid = int(callback_data.mid or 0)
    it = db.get_material(mid)
    if not it:
        await cb.message.answer("❌ Topilmadi.")
        return
    txt = (
        f"{_cat_icon(it.get('category',''))} <b>{_short(it.get('title'), 180)}</b>\n"
        f"🌍 {str(it.get('lang','')).upper()} | {'🔒' if it.get('is_paid') else '✅'}"
        f"{' | 💰 ' + f'{(it.get('price_cents') or 0)/100:.2f}$' if it.get('is_paid') else ''}\n"
        f"🆔 #{it.get('id')} | {it.get('source_type','')}\n\n"
        f"{_short(it.get('description'), 900)}"
    )
    await cb.message.answer(txt, reply_markup=_item_kb(it), parse_mode="HTML")

# ===== Item actions =====
@router.callback_query(MAdm.filter(F.act == "preview"))
async def item_preview(cb: CallbackQuery, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb, "👁")
    mid = int(callback_data.mid or 0)
    it = db.get_material(mid)
    if not it:
        await cb.message.answer("❌ Topilmadi.")
        return
    title = it.get("title") or ""
    desc = (it.get("description") or "").strip()
    caption = f"<b>{title}</b>" + (f"\n\n{_short(desc, 900)}" if desc else "")
    if it.get("is_paid"):
        await cb.message.answer(f"🔒 {caption}", parse_mode="HTML")
        return
    st = it.get("source_type"); sr = it.get("source_ref")
    try:
        if st == "file_id":
            await cb.message.answer_document(sr, caption=caption, parse_mode="HTML")
        elif st == "url":
            await cb.message.answer(caption + f"\n\n🔗 <code>{sr}</code>", parse_mode="HTML")
        else:
            await cb.message.answer(caption + f"\n\n{sr}", parse_mode="HTML")
    except Exception:
        await cb.message.answer(caption, parse_mode="HTML")

@router.callback_query(MAdm.filter(F.act == "tpaid"))
async def item_toggle_paid(cb: CallbackQuery, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb)
    mid = int(callback_data.mid or 0)
    it = db.get_material(mid)
    if not it:
        await cb.message.answer("❌ Topilmadi.")
        return
    if not _has_method(db, "update_material"):
        await cb.message.answer("ℹ️ DB.update_material mavjud emas.")
        return
    try:
        new_paid = 0 if it.get("is_paid") else 1
        db.update_material(mid, is_paid=new_paid, price_cents=it.get("price_cents") or 0)
        it = db.get_material(mid)
        await cb.message.answer("✅ Holat o‘zgartirildi.", reply_markup=_item_kb(it))
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}")

@router.callback_query(MAdm.filter(F.act == "setprice"))
async def item_setprice(cb: CallbackQuery, state: FSMContext, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb)
    await state.update_data(edit_mid=int(callback_data.mid or 0))
    await state.set_state(EditFSM.PRICE)
    await cb.message.answer("💰 Yangi narxni USD ko‘rinishda yuboring (9.99) yoki 0:")

@router.message(EditFSM.PRICE)
async def item_setprice_take(message: Message, state: FSMContext):
    if not db or not _has_method(db, "update_material"):
        await message.answer("ℹ️ DB.update_material mavjud emas.")
        await state.clear()
        return
    data = await state.get_data()
    mid = int(data.get("edit_mid") or 0)
    raw = (message.text or "0").strip().replace(",", ".")
    try:
        usd = float(raw)
        cents = max(0, int(round(usd * 100)))
    except Exception:
        cents = 0
    try:
        db.update_material(mid, price_cents=cents, is_paid=1 if cents > 0 else 0)
        await message.answer(f"✅ Narx yangilandi: {cents/100:.2f}$")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    await state.clear()

@router.callback_query(MAdm.filter(F.act == "etitle"))
async def item_edit_title(cb: CallbackQuery, state: FSMContext, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb)
    await state.update_data(edit_mid=int(callback_data.mid or 0))
    await state.set_state(EditFSM.TITLE)
    await cb.message.answer("✏️ Yangi sarlavha yuboring:")

@router.message(EditFSM.TITLE)
async def item_edit_title_take(message: Message, state: FSMContext):
    if not db or not _has_method(db, "update_material"):
        await message.answer("ℹ️ DB.update_material mavjud emas.")
        await state.clear()
        return
    data = await state.get_data()
    mid = int(data.get("edit_mid") or 0)
    title = (message.text or "").strip()
    if not title:
        await message.answer("❌ Sarlavha bo‘sh bo‘lmasin.")
        return
    try:
        db.update_material(mid, title=title)
        await message.answer("✅ Sarlavha yangilandi.")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    await state.clear()

@router.callback_query(MAdm.filter(F.act == "edesc"))
async def item_edit_desc(cb: CallbackQuery, state: FSMContext, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb)
    await state.update_data(edit_mid=int(callback_data.mid or 0))
    await state.set_state(EditFSM.DESC)
    await cb.message.answer("📝 Yangi tavsif yuboring (bo‘sh qoldirsangiz — tozalanadi):")

@router.message(EditFSM.DESC)
async def item_edit_desc_take(message: Message, state: FSMContext):
    if not db or not _has_method(db, "update_material"):
        await message.answer("ℹ️ DB.update_material mavjud emas.")
        await state.clear()
        return
    data = await state.get_data()
    mid = int(data.get("edit_mid") or 0)
    desc = (message.text or "").strip()
    try:
        db.update_material(mid, description=desc or None)
        await message.answer("✅ Tavsif yangilandi.")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    await state.clear()

@router.callback_query(MAdm.filter(F.act == "delete"))
async def item_delete(cb: CallbackQuery, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb)
    mid = int(callback_data.mid or 0)
    if not _has_method(db, "delete_material"):
        await cb.message.answer("ℹ️ DB.delete_material mavjud emas.")
        return
    try:
        db.delete_material(mid)
        await cb.message.answer("🗑 O‘chirildi.")
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}")

@router.callback_query(MAdm.filter(F.act == "publish"))
async def item_publish(cb: CallbackQuery, callback_data: MAdm):
    """Minimal publish flag (agar db da 'status' mavjud bo'lsa, 'published' deb qo'yish mumkin).
       Hozircha faqat xabar."""
    if not _is_admin(cb.from_user.id):
        return
    await _safe(cb, "📤")
    await cb.message.answer("✅ Publish qilingan (simulyatsiya). Agar DB’da status maydoni bo‘lsa, shu yerda update qiling.")

@router.callback_query(MAdm.filter(F.act == "dup"))
async def item_dup(cb: CallbackQuery, callback_data: MAdm):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe(cb, "🧬")
    mid = int(callback_data.mid or 0)
    it = db.get_material(mid)
    if not it:
        await cb.message.answer("❌ Topilmadi.")
        return
    try:
        new_id = db.add_material(
            category=it.get("category"),
            lang=it.get("lang"),
            title=f"{it.get('title')} (copy)",
            description=it.get("description"),
            is_paid=bool(it.get("is_paid")),
            price_cents=int(it.get("price_cents") or 0),
            source_type=it.get("source_type"),
            source_ref=it.get("source_ref"),
            created_by=cb.from_user.id,
        )
        await cb.message.answer(f"✅ Nusxa yaratildi (ID: {new_id}).", reply_markup=_ikb([
            [_btn("✏️ Title", MAdm(act="etitle", mid=new_id).pack()),
             _btn("📝 Desc", MAdm(act="edesc", mid=new_id).pack())],
            [_btn("👁 Preview", MAdm(act="preview", mid=new_id).pack())],
        ]))
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}")

# ===================== No-op =====================
@router.callback_query(MAdm.filter(F.act == "nop"))
async def nop(cb: CallbackQuery):
    await _safe(cb)
