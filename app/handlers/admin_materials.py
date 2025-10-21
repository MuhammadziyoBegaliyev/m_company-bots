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

# --- DB (kutilayotgan API: add_material, list_materials, get_material, update_material, delete_material, count_materials)
try:
    from ..storage.db import db  # type: ignore
except Exception as e:
    db = None  # type: ignore
    logger.warning(f"[admin_materials] DB import failed: {e}")

router = Router()

# ===================== Konfiguratsiya =====================
CATS  = [("book", "📘"), ("article", "🧠"), ("video", "🎬"), ("audio", "🎧")]
LANGS = [("uz", "🇺🇿"), ("en", "🇬🇧"), ("ru", "🇷🇺")]
PAGE_SIZE = 8

# ===================== Util =====================
def _is_admin(uid: int) -> bool:
    return uid in (settings.admin_ids or [])

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

def _ikb(rows: List[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)

def _row(*btns: InlineKeyboardButton) -> List[InlineKeyboardButton]:
    return list(btns)

def _short(text: Optional[str], n: int = 140) -> str:
    s = (text or "").strip()
    return s if len(s) <= n else s[: n - 1] + "…"

def _cat_icon(cat: str) -> str:
    for k, icon in CATS:
        if k == cat:
            return icon
    return "📦"

def _cat_title(cat: str, t: dict) -> str:
    lkey = {
        "book": "materials_books",
        "article": "materials_articles",
        "video": "materials_videos",
        "audio": "materials_audios",
    }.get(cat, "")
    return t.get(lkey, cat.title())

def _has_method(obj: Any, name: str) -> bool:
    return hasattr(obj, name) and callable(getattr(obj, name, None))

# ===================== Klaviaturalar =====================
def _root_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    return _ikb([
        _row(_btn(f"➕ {_g(t, 'adm_mat_add', 'Yangi material qo‘shish')}", "madmin:add")),
        _row(_btn(f"📚 {_g(t, 'adm_mat_list', 'Materiallar ro‘yxati')}", "madmin:catpick:list")),
        _row(_btn(f"📈 {_g(t, 'adm_mat_stats', 'Statistika')}", "madmin:stats")),
        _row(_btn(_g(t, 'back_btn', '◀️ Orqaga'), "adm:back")),
    ])

def _cat_pick_kb(prefix: str) -> InlineKeyboardMarkup:
    # prefix: "madmin:list" yoki "madmin:addpick"
    rows = [
        [
            _btn(f"{CATS[0][1]} {CATS[0][0].title()}", f"{prefix}:{CATS[0][0]}:0"),
            _btn(f"{CATS[1][1]} {CATS[1][0].title()}", f"{prefix}:{CATS[1][0]}:0"),
        ],
        [
            _btn(f"{CATS[2][1]} {CATS[2][0].title()}", f"{prefix}:{CATS[2][0]}:0"),
            _btn(f"{CATS[3][1]} {CATS[3][0].title()}", f"{prefix}:{CATS[3][0]}:0"),
        ],
        [_btn("◀️", "madmin:root")],
    ]
    return _ikb(rows)

def _langs_kb(prefix: str = "madmin:lang") -> InlineKeyboardMarkup:
    return _ikb([[ _btn(f"{flag} {code.upper()}", f"{prefix}:{code}") ] for code, flag in LANGS])

def _list_nav_kb(cat: str, page: int, has_prev: bool, has_next: bool, lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    nav: List[InlineKeyboardButton] = []
    if has_prev:
        nav.append(_btn("⬅️", f"madmin:list:{cat}:{page-1}"))
    nav.append(_btn(f"{page+1}", f"madmin:nop:{page}"))
    if has_next:
        nav.append(_btn("➡️", f"madmin:list:{cat}:{page+1}"))

    rows: List[List[InlineKeyboardButton]] = []
    if nav:
        rows.append(nav)
    rows.append([_btn(_g(t, "back_btn", "◀️ Orqaga"), "madmin:catpick:list")])
    rows.append([_btn("🏠", "madmin:root")])
    return _ikb(rows)

def _item_kb(item: Dict[str, Any], lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    mid = int(item["id"])
    paid = bool(item.get("is_paid"))
    rows = [
        [_btn("👁 Preview (userga)", f"madmin:item:preview:{mid}")],
        [
            _btn("🔓 Bepulga" if paid else "🔒 Pullikka", f"madmin:item:togglepaid:{mid}"),
            _btn("💰 Narx", f"madmin:item:setprice:{mid}"),
        ],
        [
            _btn("✏️ Title", f"madmin:item:edit_title:{mid}"),
            _btn("📝 Desc", f"madmin:item:edit_desc:{mid}"),
        ],
        [_btn("🗑 O‘chirish", f"madmin:item:delete:{mid}")],
        [
            _btn(_g(t, "back_btn", "◀️ Orqaga"), f"madmin:item:back:{item['category']}"),
            _btn("🏠", "madmin:root"),
        ],
    ]
    return _ikb(rows)

# ===================== FSM (qo'shish/tahrirlash) =====================
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
    EDIT_TITLE = State()
    EDIT_DESC = State()
    SET_PRICE = State()

# ===================== ROOT/ENTRY =====================
@router.message(Command("mats"))
async def mats_cmd(message: Message):
    if not _is_admin(message.from_user.id):
        return
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    await message.answer(f"🧰 <b>{_g(_t(lang), 'adm_mat_title', 'Materiallar (Admin)')}</b>",
                         reply_markup=_root_kb(lang), parse_mode="HTML")

@router.callback_query(F.data.in_({"adm:mats", "admin:mats", "adm:materials"}))
async def m_root_from_admin(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await _safe_cb_answer(cb)
    await cb.message.answer(f"🧰 <b>{_g(_t(lang), 'adm_mat_title', 'Materiallar (Admin)')}</b>",
                            reply_markup=_root_kb(lang), parse_mode="HTML")

@router.callback_query(F.data == "madmin:root")
async def m_root(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await _safe_cb_answer(cb)
    await cb.message.answer("🧰 <b>Materiallar (Admin)</b>",
                            reply_markup=_root_kb(lang), parse_mode="HTML")

# ===================== STATISTIKA =====================
@router.callback_query(F.data == "madmin:stats")
async def m_stats(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db:
        return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    await _safe_cb_answer(cb)

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
    await cb.message.answer("\n".join(lines), parse_mode="HTML",
                            reply_markup=_ikb([[_btn("◀️", "madmin:root")]]))

# ===================== ADD FLOW =====================
@router.callback_query(F.data == "madmin:add")
async def m_add_start(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id):
        return
    await _safe_cb_answer(cb)
    await state.clear()
    await state.set_state(AddFSM.CAT)
    await cb.message.answer("⚙️ Kategoriya tanlang:", reply_markup=_cat_pick_kb("madmin:addpick"))

@router.callback_query(AddFSM.CAT, F.data.startswith("madmin:addpick:"))
async def m_add_pick_cat(cb: CallbackQuery, state: FSMContext):
    cat = cb.data.split(":")[2]
    await _safe_cb_answer(cb)
    await state.update_data(cat=cat)
    await state.set_state(AddFSM.LANG)
    await cb.message.answer("🌍 Tilni tanlang:", reply_markup=_langs_kb("madmin:lang"))

@router.callback_query(AddFSM.LANG, F.data.startswith("madmin:lang:"))
async def m_add_pick_lang(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split(":")[2]
    await _safe_cb_answer(cb)
    await state.update_data(lang=lang)
    await state.set_state(AddFSM.TITLE)
    await cb.message.answer("📝 Sarlavha yuboring:")

@router.message(AddFSM.TITLE, F.text)
async def m_add_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AddFSM.DESC)
    await message.answer("📄 Tavsif yuboring (ixtiyoriy) yoki «/skip» yozing.")

@router.message(AddFSM.DESC, F.text == "/skip")
async def m_add_desc_skip(message: Message, state: FSMContext):
    await state.update_data(desc=None)
    await state.set_state(AddFSM.PAID)
    await message.answer("💵 Bu material pullikmi? (ha/yo‘q)")

@router.message(AddFSM.DESC, F.text)
async def m_add_desc(message: Message, state: FSMContext):
    await state.update_data(desc=(message.text or "").strip())
    await state.set_state(AddFSM.PAID)
    await message.answer("💵 Bu material pullikmi? (ha/yo‘q)")

@router.message(AddFSM.PAID)
async def m_add_paid(message: Message, state: FSMContext):
    txt = (message.text or "").strip().lower()
    is_paid = txt in {"ha", "yes", "да", "haa", "true", "1"}
    await state.update_data(is_paid=is_paid)
    if is_paid:
        await state.set_state(AddFSM.PRICE)
        await message.answer("💰 Narxni kiriting (USD, masalan 9.99) yoki «/skip».")
    else:
        await state.set_state(AddFSM.SRC)
        await message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video)\n- URL (havola)\n- matn")

@router.message(AddFSM.PRICE, F.text == "/skip")
async def m_add_price_skip(message: Message, state: FSMContext):
    await state.update_data(price_cents=0)
    await state.set_state(AddFSM.SRC)
    await message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video)\n- URL (havola)\n- matn")

@router.message(AddFSM.PRICE)
async def m_add_price(message: Message, state: FSMContext):
    raw = (message.text or "0").strip().replace(",", ".")
    try:
        usd = float(raw)
        cents = int(round(usd * 100))
    except Exception:
        cents = 0
    await state.update_data(price_cents=cents)
    await state.set_state(AddFSM.SRC)
    await message.answer("📎 Kontent yuboring:\n- file (kitob/audio/video)\n- URL (havola)\n- matn")

@router.message(AddFSM.SRC, F.document | F.video | F.audio)
async def m_add_src_file(message: Message, state: FSMContext):
    file_id = None
    stype = "file_id"
    if message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.audio:
        file_id = message.audio.file_id
    await state.update_data(src_type=stype, src_ref=file_id)
    await _m_add_preview(message, state)

@router.message(AddFSM.SRC, F.text)
async def m_add_src_text_or_url(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    if txt.startswith("http://") or txt.startswith("https://"):
        await state.update_data(src_type="url", src_ref=txt)
    else:
        await state.update_data(src_type="text", src_ref=txt)
    await _m_add_preview(message, state)

async def _m_add_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]
    desc = data.get("desc") or ""
    is_paid = bool(data.get("is_paid"))
    price_cents = int(data.get("price_cents") or 0)
    price = f"{price_cents/100:.2f}$" if is_paid and price_cents else "—"
    txt = (
        f"🧾 <b>Preview</b>\n"
        f"📂 Cat: {data['cat']}\n"
        f"🌍 Lang: {data['lang']}\n"
        f"📝 Title: {_short(title, 200)}\n"
        f"📄 Desc: {_short(desc, 300)}\n"
        f"💵 Paid: {'Yes' if is_paid else 'No'} | Price: {price}\n"
        f"📎 Source: {data['src_type']}"
    )
    kb = _ikb([_row(_btn("✅ Saqlash", "madmin:save"), _btn("❌ Bekor", "madmin:cancel"))])
    await message.answer(txt, parse_mode="HTML", reply_markup=kb)
    await state.set_state(AddFSM.PREVIEW)

@router.callback_query(AddFSM.PREVIEW, F.data == "madmin:cancel")
async def m_add_cancel(cb: CallbackQuery, state: FSMContext):
    await _safe_cb_answer(cb, "❌")
    await state.clear()
    await cb.message.answer("Bekor qilindi.", reply_markup=_ikb([[_btn("◀️", "madmin:root")]]))

@router.callback_query(AddFSM.PREVIEW, F.data == "madmin:save")
async def m_add_save(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await _safe_cb_answer(cb, "💾")
    data = await state.get_data()
    try:
        mid = db.add_material(  # type: ignore[attr-defined]
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
        await cb.message.answer(f"✅ Saqlandi (ID: {mid}).", reply_markup=_ikb([[_btn("◀️", "madmin:root")]]))
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}", reply_markup=_ikb([[_btn("◀️", "madmin:root")]]))

# ===================== RO‘YXAT / ITEM =====================
async def _render_list(cb: CallbackQuery, cat: str, page: int):
    if not db:
        await cb.message.answer("ℹ️ DB mavjud emas.")
        return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)

    offset = page * PAGE_SIZE
    items = db.list_materials(category=cat, lang=lang, offset=offset, limit=PAGE_SIZE + 1)  # type: ignore[attr-defined]
    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]
    has_prev = page > 0

    if not items:
        await cb.message.answer("— Bo‘sh —", reply_markup=_list_nav_kb(cat, page, has_prev, has_next, lang))
        return

    kb_rows: List[List[InlineKeyboardButton]] = []
    for it in items:
        tag = "🔒" if it.get("is_paid") else "✅"
        kb_rows.append([_btn(f"{tag} #{it['id']} — {_short(it['title'], 50)}", f"madmin:item:{int(it['id'])}")])

    kb = _ikb(kb_rows + _list_nav_kb(cat, page, has_prev, has_next, lang).inline_keyboard)
    await cb.message.answer(f"{_cat_icon(cat)} <b>{_cat_title(cat, t)}</b>", parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "madmin:catpick:list")
async def m_list_pick_cat(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    await _safe_cb_answer(cb)
    await cb.message.answer("📚 Kategoriya tanlang:", reply_markup=_cat_pick_kb("madmin:list"))

@router.callback_query(F.data.startswith("madmin:list:"))
async def m_list(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    parts = cb.data.split(":")
    if len(parts) != 4:
        return
    _, _, cat, page_s = parts
    await _safe_cb_answer(cb)
    await _render_list(cb, cat, int(page_s))

def _fmt_item(item: Dict[str, Any], lang: str) -> str:
    cat = item.get("category", "")
    paid = "🔒" if item.get("is_paid") else "✅"
    price = ""
    if item.get("is_paid"):
        cents = int(item.get("price_cents") or 0)
        price = f" | 💰 {cents/100:.2f}$" if cents else ""
    desc = item.get("description") or ""
    src = f"{item.get('source_type', '')}"
    return (
        f"{_cat_icon(cat)} <b>{_short(item.get('title') or '', 180)}</b>\n"
        f"🌍 {item.get('lang', '').upper()} | {paid}{price}\n"
        f"🆔 #{item.get('id')} | {src}\n\n"
        f"{_short(desc, 800)}"
    )

@router.callback_query(F.data.startswith("madmin:item:"))
async def m_item_open(cb: CallbackQuery):
    # faqat "madmin:item:<id>" bo'lsa shu handler; aks holda boshqa handlerlar ishlaydi
    if not _is_admin(cb.from_user.id) or not db:
        return
    parts = cb.data.split(":")
    if len(parts) != 3:
        return  # boshqa actionlar uchun alohida handlerlar bor
    mid = int(parts[-1])
    await _safe_cb_answer(cb)
    it = db.get_material(mid)  # type: ignore[attr-defined]
    if not it:
        await cb.message.answer("❌ Topilmadi.")
        return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
    await cb.message.answer(_fmt_item(it, lang), parse_mode="HTML", reply_markup=_item_kb(it, lang))

@router.callback_query(F.data.startswith("madmin:item:back:"))
async def m_item_back(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return
    cat = cb.data.split(":")[-1]
    await _safe_cb_answer(cb, "◀️")
    await _render_list(cb, cat, 0)

# -------- Item actions --------
@router.callback_query(F.data.startswith("madmin:item:preview:"))
async def m_item_preview(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db:
        return
    mid = int(cb.data.split(":")[-1])
    await _safe_cb_answer(cb, "👁")
    it = db.get_material(mid)  # type: ignore[attr-defined]
    if not it:
        await cb.message.answer("❌ Topilmadi.")
        return

    title = it["title"]
    desc = (it.get("description") or "").strip()
    caption = f"<b>{title}</b>" + (f"\n\n{_short(desc, 900)}" if desc else "")
    st = it.get("source_type"); sr = it.get("source_ref")

    if it.get("is_paid"):
        await cb.message.answer(f"🔒 {caption}", parse_mode="HTML")
        return

    try:
        if st == "file_id":
            await cb.message.answer_document(sr, caption=caption, parse_mode="HTML")
        elif st == "url":
            await cb.message.answer(caption + f"\n\n🔗 <code>{sr}</code>", parse_mode="HTML")
        else:
            await cb.message.answer(caption + (f"\n\n{sr}" if sr else ""), parse_mode="HTML")
    except Exception:
        await cb.message.answer(caption, parse_mode="HTML")

@router.callback_query(F.data.startswith("madmin:item:togglepaid:"))
async def m_item_toggle_paid(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db:
        return
    mid = int(cb.data.split(":")[-1])
    await _safe_cb_answer(cb)
    it = db.get_material(mid)  # type: ignore[attr-defined]
    if not it:
        await cb.message.answer("❌ Topilmadi.")
        return
    if not _has_method(db, "update_material"):
        await cb.message.answer("ℹ️ DB.update_material mavjud emas.")
        return
    new_paid = 0 if it.get("is_paid") else 1
    try:
        db.update_material(mid, is_paid=new_paid)  # type: ignore[attr-defined]
        it = db.get_material(mid)
        lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG)
        await cb.message.answer("✅ Holat o‘zgartirildi.", reply_markup=_item_kb(it, lang))
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}")

@router.callback_query(F.data.startswith("madmin:item:setprice:"))
async def m_item_setprice(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db:
        return
    mid = int(cb.data.split(":")[-1])
    await _safe_cb_answer(cb)
    await state.update_data(edit_mid=mid)
    await state.set_state(EditFSM.SET_PRICE)
    await cb.message.answer("💰 Yangi narxni USD ko‘rinishda yuboring (9.99) yoki 0:")

@router.message(EditFSM.SET_PRICE)
async def m_item_setprice_take(message: Message, state: FSMContext):
    data = await state.get_data()
    mid = int(data.get("edit_mid"))
    raw = (message.text or "0").strip().replace(",", ".")
    try:
        usd = float(raw)
        cents = max(0, int(round(usd * 100)))
    except Exception:
        usd = 0.0
        cents = 0
    await state.clear()
    if not db or not _has_method(db, "update_material"):
        await message.answer("ℹ️ DB.update_material mavjud emas.")
        return
    try:
        db.update_material(mid, price_cents=cents, is_paid=1 if cents > 0 else 0)  # type: ignore[attr-defined]
        await message.answer(f"✅ Narx yangilandi: {usd:.2f}$")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

@router.callback_query(F.data.startswith("madmin:item:edit_title:"))
async def m_item_edit_title(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db:
        return
    mid = int(cb.data.split(":")[-1])
    await _safe_cb_answer(cb)
    await state.update_data(edit_mid=mid)
    await state.set_state(EditFSM.EDIT_TITLE)
    await cb.message.answer("✏️ Yangi sarlavha yuboring:")

@router.message(EditFSM.EDIT_TITLE, F.text)
async def m_item_edit_title_take(message: Message, state: FSMContext):
    if not db or not _has_method(db, "update_material"):
        await state.clear()
        await message.answer("ℹ️ DB.update_material mavjud emas.")
        return
    data = await state.get_data()
    mid = int(data.get("edit_mid"))
    await state.clear()
    title = (message.text or "").strip()
    try:
        db.update_material(mid, title=title)  # type: ignore[attr-defined]
        await message.answer("✅ Sarlavha yangilandi.")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

@router.callback_query(F.data.startswith("madmin:item:edit_desc:"))
async def m_item_edit_desc(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db:
        return
    mid = int(cb.data.split(":")[-1])
    await _safe_cb_answer(cb)
    await state.update_data(edit_mid=mid)
    await state.set_state(EditFSM.EDIT_DESC)
    await cb.message.answer("📝 Yangi tavsif yuboring (bo‘sh qoldirsangiz — tozalanadi):")

@router.message(EditFSM.EDIT_DESC, F.text)
async def m_item_edit_desc_take(message: Message, state: FSMContext):
    if not db or not _has_method(db, "update_material"):
        await state.clear()
        await message.answer("ℹ️ DB.update_material mavjud emas.")
        return
    data = await state.get_data()
    mid = int(data.get("edit_mid"))
    await state.clear()
    desc = (message.text or "").strip()
    try:
        db.update_material(mid, description=desc or None)  # type: ignore[attr-defined]
        await message.answer("✅ Tavsif yangilandi.")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")

@router.callback_query(F.data.startswith("madmin:item:delete:"))
async def m_item_delete(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db:
        return
    mid = int(cb.data.split(":")[-1])
    await _safe_cb_answer(cb)
    if not _has_method(db, "delete_material"):
        await cb.message.answer("ℹ️ DB.delete_material mavjud emas.")
        return
    try:
        db.delete_material(mid)  # type: ignore[attr-defined]
        await cb.message.answer("🗑 O‘chirildi.")
    except Exception as e:
        await cb.message.answer(f"❌ Xato: {e}")

# ===================== NO-OP =====================
@router.callback_query(F.data.startswith("madmin:nop:"))
async def m_noop(cb: CallbackQuery):
    await _safe_cb_answer(cb)
