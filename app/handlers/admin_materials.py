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

from ..config import settings
from ..locales import L
from ..storage.memory import get_lang

# --- DB ---
try:
    from ..storage.db import db  # type: ignore
except Exception:
    db = None  # type: ignore

router = Router()

# ===================== CONST =====================
PAGE_SIZE = 8
CATS = [("book", "📘"), ("article", "🧠"), ("video", "🎬"), ("audio", "🎧")]
LANGS = [("uz", "🇺🇿"), ("en", "🇬🇧"), ("ru", "🇷🇺")]
CAT_SET = {c for c, _ in CATS}
LANG_SET = {c for c, _ in LANGS}

# ===================== UTILS =====================
def _is_admin(uid: int) -> bool:
    return uid in (settings.admin_ids or [])

def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

async def _safe(cb: CallbackQuery, text: Optional[str] = None):
    try:
        await cb.answer(text)
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "query is too old" in s or "query id is invalid" in s:
            return
        raise

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)

def _ikb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _short(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"

def _cat_icon(cat: str) -> str:
    for c, ic in CATS:
        if c == cat:
            return ic
    return "📦"

def _cat_title(cat: str, t: dict) -> str:
    key = {
        "book": "materials_books",
        "article": "materials_articles",
        "video": "materials_videos",
        "audio": "materials_audios",
    }.get(cat, "")
    return t.get(key, cat.title())

def _has(obj: Any, name: str) -> bool:
    return hasattr(obj, name) and callable(getattr(obj, name, None))

# ===================== KEYBOARDS =====================
def _root_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    return _ikb([
        [_btn("➕ " + t.get("adm_mat_add", "Yangi material qo‘shish"), "madmin:add")],
        [_btn("📚 " + t.get("adm_mat_list", "Ro‘yxat"), "madmin:list:pickcat")],
        [_btn(t.get("back_btn", "◀️ Orqaga"), "adm:back")],
    ])

def _pick_cat_kb(prefix: str) -> InlineKeyboardMarkup:
    # prefix: madmin:add:cat yoki madmin:list:cat
    return _ikb([
        [
            _btn(f"{CATS[0][1]} {CATS[0][0].title()}", f"{prefix}:{CATS[0][0]}"),
            _btn(f"{CATS[1][1]} {CATS[1][0].title()}", f"{prefix}:{CATS[1][0]}"),
        ],
        [
            _btn(f"{CATS[2][1]} {CATS[2][0].title()}", f"{prefix}:{CATS[2][0]}"),
            _btn(f"{CATS[3][1]} {CATS[3][0].title()}", f"{prefix}:{CATS[3][0]}"),
        ],
        [_btn("🏠", "madmin:root")]
    ])

def _langs_kb(prefix: str) -> InlineKeyboardMarkup:
    return _ikb([[ _btn(f"{flag} {code.upper()}", f"{prefix}:{code}") ] for code, flag in LANGS] + [[_btn("🏠", "madmin:root")]])

def _paid_kb() -> InlineKeyboardMarkup:
    return _ikb([
        [_btn("🔒 Ha (pullik)", "madmin:add:paid:yes"),
         _btn("🔓 Yo‘q (bepul)", "madmin:add:paid:no")],
        [_btn("🏠", "madmin:root")],
    ])

def _list_nav_kb(cat: str, page: int, has_prev: bool, has_next: bool, lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    nav: List[InlineKeyboardButton] = []
    if has_prev:
        nav.append(_btn("⬅️", f"madmin:list:cat:{cat}:{page-1}"))
    nav.append(_btn(f"{page+1}", f"madmin:nop:{page}"))
    if has_next:
        nav.append(_btn("➡️", f"madmin:list:cat:{cat}:{page+1}"))
    rows: List[List[InlineKeyboardButton]] = []
    if nav:
        rows.append(nav)
    rows += [[_btn(t.get("back_btn", "◀️ Orqaga"), "madmin:list:pickcat")],
             [_btn("🏠", "madmin:root")]]
    return _ikb(rows)

def _item_kb(item: Dict[str, Any], lang: str) -> InlineKeyboardMarkup:
    paid = bool(item.get("is_paid"))
    return _ikb([
        [_btn("👁 Preview (userga)", f"madmin:item:preview:{item['id']}")],
        [_btn("🔄 " + ("Bepulga o‘tkazish" if paid else "Pullikka o‘tkazish"), f"madmin:item:togglepaid:{item['id']}")],
        [_btn("💰 Narx (USD)", f"madmin:item:setprice:{item['id']}")],
        [_btn("✏️ Title", f"madmin:item:edittitle:{item['id']}"),
         _btn("📝 Desc", f"madmin:item:editdesc:{item['id']}")],
        [_btn("🗑 O‘chirish", f"madmin:item:delete:{item['id']}")],
        [_btn("◀️ Ro‘yxatga", f"madmin:item:back:{item['category']}"),
         _btn("🏠", "madmin:root")],
    ])

# ===================== FSM =====================
class AddFSM(StatesGroup):
    CAT = State()
    LANG = State()
    TITLE = State()
    DESC = State()
    PAID = State()
    PRICE = State()
    SRC = State()
    PREVIEW = State()

class EditFSM(StatesGroup):
    TITLE = State()
    DESC = State()
    PRICE = State()

# ===================== ENTRY =====================
@router.message(Command("mats"))
async def mats_cmd(message: Message):
    if not _is_admin(message.from_user.id): return
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    await message.answer("🧰 <b>Materiallar (Admin)</b>", parse_mode="HTML", reply_markup=_root_kb(lang))

@router.callback_query(F.data.in_({"adm:mats", "admin:mats"}))
async def m_root_from_admin(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id): return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await _safe(cb)
    await cb.message.answer("🧰 <b>Materiallar (Admin)</b>", parse_mode="HTML", reply_markup=_root_kb(lang))

@router.callback_query(F.data == "madmin:root")
async def m_root(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id): return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await _safe(cb)
    await cb.message.answer("🧰 <b>Materiallar (Admin)</b>", parse_mode="HTML", reply_markup=_root_kb(lang))

# ===================== STATS (ixtiyoriy) =====================
@router.callback_query(F.data == "madmin:stats")
async def m_stats(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db: return
    await _safe(cb)
    if not _has(db, "count_materials"):
        await cb.message.answer("ℹ️ DB.count_materials mavjud emas.")
        return
    lines = ["📈 <b>Statistika</b>"]
    for cat, icon in CATS:
        for code, flag in LANGS:
            try:
                cnt = db.count_materials(category=cat, lang=code)
            except Exception:
                cnt = "?"
            lines.append(f"{icon} {cat.title()} — {flag} {code.upper()}: <b>{cnt}</b>")
    await cb.message.answer("\n".join(lines), parse_mode="HTML", reply_markup=_ikb([[ _btn("🏠", "madmin:root") ]]))

# ===================== ADD FLOW =====================
@router.callback_query(F.data == "madmin:add")
async def add_start(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id): return
    await _safe(cb)
    await state.clear()
    await state.set_state(AddFSM.CAT)
    await cb.message.answer("⚙️ Kategoriya tanlang:", reply_markup=_pick_cat_kb("madmin:add:cat"))

@router.callback_query(AddFSM.CAT, F.data.startswith("madmin:add:cat:"))
async def add_pick_cat(cb: CallbackQuery, state: FSMContext):
    cat = cb.data.split(":")[3]
    if cat not in CAT_SET:
        await _safe(cb, "❌ Noto‘g‘ri kategoriya")
        return
    await _safe(cb)
    await state.update_data(cat=cat)
    await state.set_state(AddFSM.LANG)
    await cb.message.answer("🌍 Tilni tanlang:", reply_markup=_langs_kb("madmin:add:lang"))

@router.callback_query(AddFSM.LANG, F.data.startswith("madmin:add:lang:"))
async def add_pick_lang(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split(":")[3]
    if lang not in LANG_SET:
        await _safe(cb, "❌ Noto‘g‘ri til")
        return
    await _safe(cb)
    await state.update_data(lang=lang)
    await state.set_state(AddFSM.TITLE)
    await cb.message.answer("📝 Sarlavha yuboring:")

@router.message(AddFSM.TITLE)
async def add_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AddFSM.DESC)
    await message.answer("📄 Tavsif yuboring (ixtiyoriy) yoki <code>/skip</code> yozing.", parse_mode="HTML")

@router.message(AddFSM.DESC, F.text == "/skip")
async def add_desc_skip(message: Message, state: FSMContext):
    await state.update_data(desc=None)
    await state.set_state(AddFSM.PAID)
    await message.answer("💵 Bu material pullikmi?", reply_markup=_paid_kb())

@router.message(AddFSM.DESC)
async def add_desc(message: Message, state: FSMContext):
    await state.update_data(desc=(message.text or "").strip())
    await state.set_state(AddFSM.PAID)
    await message.answer("💵 Bu material pullikmi?", reply_markup=_paid_kb())

@router.callback_query(AddFSM.PAID, F.data.startswith("madmin:add:paid:"))
async def add_paid(cb: CallbackQuery, state: FSMContext):
    val = cb.data.split(":")[3]
    is_paid = (val == "yes")
    await _safe(cb)
    await state.update_data(is_paid=is_paid)
    if is_paid:
        await state.set_state(AddFSM.PRICE)
        await cb.message.answer("💰 Narxni USD ko‘rinishda yuboring (masalan 9.99) yoki <code>/skip</code>.", parse_mode="HTML")
    else:
        await state.set_state(AddFSM.SRC)
        await cb.message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video/photo)\n- URL (http…)\n- matn")

@router.message(AddFSM.PRICE, F.text == "/skip")
async def add_price_skip(message: Message, state: FSMContext):
    await state.update_data(price_cents=0)
    await state.set_state(AddFSM.SRC)
    await message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video/photo)\n- URL (http…)\n- matn")

@router.message(AddFSM.PRICE)
async def add_price(message: Message, state: FSMContext):
    raw = (message.text or "0").strip().replace(",", ".")
    try:
        usd = float(raw); cents = int(round(usd * 100))
    except Exception:
        usd, cents = 0.0, 0
    await state.update_data(price_cents=cents)
    await state.set_state(AddFSM.SRC)
    await message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video/photo)\n- URL (http…)\n- matn")

@router.message(AddFSM.SRC, F.photo | F.document | F.video | F.audio)
async def add_src_file(message: Message, state: FSMContext):
    file_id = None
    if message.photo:    file_id = message.photo[-1].file_id
    elif message.document: file_id = message.document.file_id
    elif message.video:    file_id = message.video.file_id
    elif message.audio:    file_id = message.audio.file_id
    await state.update_data(src_type="file_id", src_ref=file_id)
    await _preview_and_confirm(message, state)

@router.message(AddFSM.SRC, F.text)
async def add_src_text_or_url(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    if txt.startswith("http://") or txt.startswith("https://"):
        await state.update_data(src_type="url", src_ref=txt)
    else:
        await state.update_data(src_type="text", src_ref=txt)
    await _preview_and_confirm(message, state)

async def _preview_and_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    price_cents = int(data.get("price_cents") or 0)
    is_paid = bool(data.get("is_paid"))
    price = f"{price_cents/100:.2f}$" if is_paid and price_cents else "—"
    txt = (
        "🧾 <b>Preview</b>\n"
        f"📂 Cat: {data['cat']}\n"
        f"🌍 Lang: {data['lang']}\n"
        f"📝 Title: {_short(data.get('title') or '', 200)}\n"
        f"📄 Desc: {_short(data.get('desc') or '', 300)}\n"
        f"💵 Paid: {'Yes' if is_paid else 'No'} | Price: {price}\n"
        f"📎 Source: {data['src_type']}"
    )
    kb = _ikb([[ _btn("✅ Saqlash", "madmin:add:save"), _btn("❌ Bekor", "madmin:add:cancel") ]])
    await message.answer(txt, parse_mode="HTML", reply_markup=kb)
    await state.set_state(AddFSM.PREVIEW)

@router.callback_query(AddFSM.PREVIEW, F.data == "madmin:add:cancel")
async def add_cancel(cb: CallbackQuery, state: FSMContext):
    await _safe(cb, "❌")
    await state.clear()
    await cb.message.answer("Bekor qilindi.", reply_markup=_ikb([[ _btn("🏠", "madmin:root") ]]))

@router.callback_query(AddFSM.PREVIEW, F.data == "madmin:add:save")
async def add_save(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db: return
    await _safe(cb, "💾")
    data = await state.get_data()
    try:
        mid = db.add_material(
            category=data["cat"],
            lang=data["lang"],
            title=data["title"],
            description=data.get("desc"),
            is_paid=1 if data.get("is_paid") else 0,
            price_cents=int(data.get("price_cents") or 0),
            source_type=data["src_type"],
            source_ref=data["src_ref"],
            created_by=cb.from_user.id,
        )
        await state.clear()
        await cb.message.answer(f"✅ Saqlandi (ID: {mid}).", reply_markup=_ikb([[ _btn("🏠", "madmin:root") ]]))
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}", reply_markup=_ikb([[ _btn("🏠", "madmin:root") ]]))

# ===================== LIST =====================
@router.callback_query(F.data == "madmin:list:pickcat")
async def list_pick_cat(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id): return
    await _safe(cb)
    await cb.message.answer("📚 Kategoriya tanlang:", reply_markup=_pick_cat_kb("madmin:list:cat"))

@router.callback_query(F.data.startswith("madmin:list:cat:"))
async def materials_list(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db: return
    parts = cb.data.split(":")
    # madmin:list:cat:<cat>[:<page>]
    cat = parts[3]
    page = int(parts[4]) if len(parts) >= 5 else 0
    if cat not in CAT_SET:
        await _safe(cb, "❌ Noto‘g‘ri kategoriya")
        return

    await _safe(cb)
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    offset = page * PAGE_SIZE
    try:
        items = db.list_materials(category=cat, lang=lang, offset=offset, limit=PAGE_SIZE + 1)
    except Exception as e:
        await cb.message.answer(f"❌ DB xato: {e}")
        return

    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]
    has_prev = page > 0

    t = _t(lang)
    header = f"{_cat_icon(cat)} <b>{_cat_title(cat, t)}</b>"
    kb_rows: List[List[InlineKeyboardButton]] = []
    if not items:
        kb = _list_nav_kb(cat, page, has_prev, has_next, lang)
        await cb.message.answer(header + "\n— Bo‘sh —", parse_mode="HTML", reply_markup=kb)
        return

    for it in items:
        tag = "🔒" if it.get("is_paid") else "✅"
        kb_rows.append([ _btn(f"{tag} #{it['id']} — {_short(it.get('title',''), 48)}", f"madmin:item:{int(it['id'])}") ])

    kb = _ikb(kb_rows + _list_nav_kb(cat, page, has_prev, has_next, lang).inline_keyboard)
    await cb.message.answer(header, parse_mode="HTML", reply_markup=kb)

# ===================== ITEM VIEW + ACTIONS =====================
def _fmt_item(it: Dict[str, Any], lang: str) -> str:
    paid = "🔒" if it.get("is_paid") else "✅"
    cents = int(it.get("price_cents") or 0)
    price = f" | 💰 {cents/100:.2f}$" if cents else ""
    desc = _short((it.get("description") or ""), 900)
    return (
        f"{_cat_icon(it.get('category') or '')} <b>{_short(it.get('title') or '', 180)}</b>\n"
        f"🌍 {(it.get('lang') or '').upper()} | {paid}{price}\n"
        f"🆔 #{it.get('id')} | {it.get('source_type')}\n\n"
        f"{desc}"
    )

@router.callback_query(F.data.startswith("madmin:item:") & ~F.data.startswith("madmin:item:preview:") &
                       ~F.data.startswith("madmin:item:togglepaid:") & ~F.data.startswith("madmin:item:setprice:") &
                       ~F.data.startswith("madmin:item:edittitle:") & ~F.data.startswith("madmin:item:editdesc:") &
                       ~F.data.startswith("madmin:item:delete:") & ~F.data.startswith("madmin:item:back:"))
async def item_open(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db: return
    mid = int(cb.data.split(":")[-1])
    await _safe(cb)
    it = db.get_material(mid)
    if not it:
        await cb.message.answer("❌ Topilmadi.")
        return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await cb.message.answer(_fmt_item(it, lang), parse_mode="HTML", reply_markup=_item_kb(it, lang))

@router.callback_query(F.data.startswith("madmin:item:back:"))
async def item_back(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id): return
    cat = cb.data.split(":")[-1]
    await _safe(cb, "◀️")
    # qayta ro‘yxatning 1-sahifasini ko‘rsatamiz
    fake = cb.model_copy(update={"data": f"madmin:list:cat:{cat}:0"})
    await materials_list(fake)

@router.callback_query(F.data.startswith("madmin:item:preview:"))
async def item_preview(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db: return
    mid = int(cb.data.split(":")[-1])
    await _safe(cb, "👁")
    it = db.get_material(mid)
    if not it:
        await cb.message.answer("❌ Topilmadi."); return

    title = it.get("title") or "—"
    desc = (it.get("description") or "").strip()
    caption = f"<b>{title}</b>" + (f"\n\n{_short(desc, 900)}" if desc else "")
    if it.get("is_paid"):
        await cb.message.answer("🔒 " + caption, parse_mode="HTML")
        return

    st, sr = it.get("source_type"), it.get("source_ref")
    try:
        if st == "file_id":
            await cb.message.answer_document(sr, caption=caption, parse_mode="HTML")
        elif st == "url":
            await cb.message.answer(caption + f"\n\n🔗 <code>{sr}</code>", parse_mode="HTML")
        else:
            await cb.message.answer(caption + f"\n\n{sr}", parse_mode="HTML")
    except Exception:
        await cb.message.answer(caption, parse_mode="HTML")

@router.callback_query(F.data.startswith("madmin:item:togglepaid:"))
async def item_toggle_paid(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db: return
    mid = int(cb.data.split(":")[-1])
    await _safe(cb)
    it = db.get_material(mid)
    if not it: await cb.message.answer("❌ Topilmadi."); return
    if not _has(db, "update_material"):
        await cb.message.answer("ℹ️ DB.update_material mavjud emas."); return
    new_paid = 0 if it.get("is_paid") else 1
    try:
        db.update_material(mid, is_paid=new_paid)
        it2 = db.get_material(mid)
        lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
        await cb.message.answer("✅ Holat o‘zgardi.", reply_markup=_item_kb(it2, lang))
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}")

@router.callback_query(F.data.startswith("madmin:item:setprice:"))
async def item_set_price(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db: return
    mid = int(cb.data.split(":")[-1])
    await _safe(cb)
    await state.update_data(edit_mid=mid)
    await state.set_state(EditFSM.PRICE)
    await cb.message.answer("💰 Narxni USD ko‘rinishda yuboring (9.99) yoki 0:")

@router.message(EditFSM.PRICE)
async def item_set_price_take(message: Message, state: FSMContext):
    if not db or not _has(db, "update_material"):
        await state.clear(); await message.answer("ℹ️ DB.update_material mavjud emas."); return
    data = await state.get_data(); mid = int(data.get("edit_mid"))
    raw = (message.text or "0").strip().replace(",", ".")
    try:
        usd = float(raw); cents = max(0, int(round(usd * 100)))
    except Exception:
        usd, cents = 0.0, 0
    await state.clear()
    try:
        db.update_material(mid, price_cents=cents, is_paid=1 if cents > 0 else 0)
        await message.answer(f"✅ Narx yangilandi: {usd:.2f}$")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

@router.callback_query(F.data.startswith("madmin:item:edittitle:"))
async def item_edit_title(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db: return
    mid = int(cb.data.split(":")[-1])
    await _safe(cb)
    await state.update_data(edit_mid=mid)
    await state.set_state(EditFSM.TITLE)
    await cb.message.answer("✏️ Yangi sarlavha yuboring (istalgan matn, cheklov yo‘q):")

@router.message(EditFSM.TITLE)
async def item_edit_title_take(message: Message, state: FSMContext):
    if not db or not _has(db, "update_material"):
        await state.clear(); await message.answer("ℹ️ DB.update_material mavjud emas."); return
    data = await state.get_data(); mid = int(data.get("edit_mid"))
    await state.clear()
    try:
        db.update_material(mid, title=(message.text or "").strip())
        await message.answer("✅ Sarlavha yangilandi.")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

@router.callback_query(F.data.startswith("madmin:item:editdesc:"))
async def item_edit_desc(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db: return
    mid = int(cb.data.split(":")[-1])
    await _safe(cb)
    await state.update_data(edit_mid=mid)
    await state.set_state(EditFSM.DESC)
    await cb.message.answer("📝 Yangi tavsif yuboring (bo‘sh qoldirsangiz — tozalanadi):")

@router.message(EditFSM.DESC)
async def item_edit_desc_take(message: Message, state: FSMContext):
    if not db or not _has(db, "update_material"):
        await state.clear(); await message.answer("ℹ️ DB.update_material mavjud emas."); return
    data = await state.get_data(); mid = int(data.get("edit_mid"))
    await state.clear()
    try:
        desc = (message.text or "").strip()
        db.update_material(mid, description=desc or None)
        await message.answer("✅ Tavsif yangilandi.")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

@router.callback_query(F.data.startswith("madmin:item:delete:"))
async def item_delete(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db: return
    mid = int(cb.data.split(":")[-1])
    await _safe(cb)
    if not _has(db, "delete_material"):
        await cb.message.answer("ℹ️ DB.delete_material mavjud emas."); return
    try:
        db.delete_material(mid)
        await cb.message.answer("🗑 O‘chirildi.")
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}")

# ===================== NO-OP =====================
@router.callback_query(F.data.startswith("madmin:nop:"))
async def noop(cb: CallbackQuery):
    await _safe(cb)
