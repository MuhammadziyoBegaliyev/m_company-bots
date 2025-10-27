# -*- coding: utf-8 -*-
# app/handlers/materials.py
from __future__ import annotations

from typing import Optional, List, Dict
from loguru import logger
from aiogram import Router, F
from aiogram.filters import Command, StateFilter   # ⬅️ Qo‘shildi
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.exceptions import TelegramBadRequest

from ..locales import L
from ..storage.memory import get_lang

# DB (kutilyotgan API: list_materials(category, lang, offset, limit) va get_material(id))
try:
    from ..storage.db import db  # type: ignore
except Exception as e:
    db = None  # type: ignore
    logger.warning(f"Materials: DB import failed: {e}")

router = Router()
logger.info("📚 Materials router initialized")

# ===================== Config =====================
PAGE_SIZE = 6

CAT_KEYS = {
    "book":    {"icon": "📘", "lkey": "materials_books"},
    "article": {"icon": "🧠", "lkey": "materials_articles"},
    "video":   {"icon": "🎬", "lkey": "materials_videos"},
    "audio":   {"icon": "🎧", "lkey": "materials_audios"},
}

# ---------- Normalize helper ----------
def _norm(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("/"):  # komandalarni inkor qilamiz
        return s
    s = s.replace("’", "'").replace("`", "'")
    s = " ".join(s.split())
    return s.casefold()

# ---------- Reply triggers (3 til + aliaslar) ----------
BTN_SET_RAW = {
    L.get("uz", {}).get("btn_materials", "Materiallar"),
    L.get("en", {}).get("btn_materials", "Materials"),
    L.get("ru", {}).get("btn_materials", "Материалы"),
}
BTN_ALIASES = {"materiallar", "materials", "материалы", "material", "материал"}
BTN_SET_NORM = {_norm(x) for x in (BTN_SET_RAW | BTN_ALIASES)}

# ---------- Category aliaslari ----------
CAT_ALIASES_RAW = {
    # Uzbek
    "kitob": "book", "kitoblar": "book",
    "bilim": "article", "maqola": "article", "maqolalar": "article",
    "video": "video", "audio": "audio",
    # English
    "book": "book", "books": "book",
    "article": "article", "articles": "article",
    "videos": "video", "audios": "audio",
    # Russian
    "книга": "book", "книги": "book",
    "статья": "article", "статьи": "article",
    "видео": "video", "аудио": "audio",
}
CAT_ALIASES = { _norm(k): v for k, v in CAT_ALIASES_RAW.items() }

# ===================== Helpers =====================
def _t(lang: str) -> dict:
    return L.get(lang, L.get("uz", {}))

def _g(t: dict, key: str, default: str) -> str:
    return t.get(key, default)

async def _safe_cb_answer(cb: CallbackQuery):
    try:
        await cb.answer()
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "query is too old" in s or "query id is invalid" in s:
            return
        raise

def _cat_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    rows = [
        [
            InlineKeyboardButton(
                text=f"{CAT_KEYS['book']['icon']} {_g(t, CAT_KEYS['book']['lkey'], 'Kitoblar')}",
                callback_data="mat:cat:book:0",
            ),
            InlineKeyboardButton(
                text=f"{CAT_KEYS['article']['icon']} {_g(t, CAT_KEYS['article']['lkey'], 'Bilim')}",
                callback_data="mat:cat:article:0",
            ),
        ],
        [
            InlineKeyboardButton(
                text=f"{CAT_KEYS['video']['icon']} {_g(t, CAT_KEYS['video']['lkey'], 'Video')}",
                callback_data="mat:cat:video:0",
            ),
            InlineKeyboardButton(
                text=f"{CAT_KEYS['audio']['icon']} {_g(t, CAT_KEYS['audio']['lkey'], 'Audio')}",
                callback_data="mat:cat:audio:0",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _list_kb(
    lang: str,
    cat: str,
    page: int,
    has_prev: bool,
    has_next: bool,
    items: List[Dict],
) -> InlineKeyboardMarkup:
    t = _t(lang)
    rows: List[List[InlineKeyboardButton]] = []

    for it in items:
        mat_id = it.get("id")
        title = (it.get("title") or "—").strip()
        price_cents = int(it.get("price_cents") or 0)
        paid = bool(it.get("is_paid")) or price_cents > 0
        prefix = "🔒" if paid else "✅"
        rows.append([InlineKeyboardButton(text=f"{prefix} {title}", callback_data=f"mat:open:{mat_id}")])

    nav: List[InlineKeyboardButton] = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"mat:cat:{cat}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}", callback_data=f"noop:{page}"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"mat:cat:{cat}:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text=_g(t, "materials_back", "⬅️ Orqaga"), callback_data="mat:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def _send_category_list_by_message(message: Message, lang: str, cat: str, page: int = 0):
    t = _t(lang)
    if not db or not hasattr(db, "list_materials"):
        await message.answer(_g(t, "materials_db_missing", "DB sozlanmagan."))
        return

    offset = page * PAGE_SIZE
    try:
        items = db.list_materials(category=cat, lang=lang, offset=offset, limit=PAGE_SIZE + 1)  # type: ignore[attr-defined]
    except Exception as e:
        logger.error(f"Materials DB error: {e}")
        await message.answer(_g(t, "materials_db_missing", "DBda xatolik yuz berdi."))
        return

    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]
    has_prev = page > 0

    if not items:
        await message.answer(_g(t, "materials_not_found", "Hozircha material yo'q."), reply_markup=_cat_kb(lang))
        return

    title = _g(t, CAT_KEYS[cat]["lkey"], cat.title())
    await message.answer(
        f"{CAT_KEYS[cat]['icon']} <b>{title}</b>",
        parse_mode="HTML",
        reply_markup=_list_kb(lang, cat, page, has_prev, has_next, items),
    )

# ===================== Entry =====================

@router.message(StateFilter(None), Command("materials"))     # ⬅️ FSM bo‘lmaganda
async def materials_cmd(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = _t(lang)
    await message.answer(
        f"📚 <b>{_g(t, 'materials_title', 'Materiallar')}</b>\n\n{_g(t, 'materials_choose_cat', 'Kategoriya tanlang:')}",
        reply_markup=_cat_kb(lang),
        parse_mode="HTML",
    )

def is_materials_button(text: str) -> bool:
    if not text or text.startswith("/"):
        return False
    normalized = _norm(text)
    return normalized in BTN_SET_NORM

@router.message(StateFilter(None), F.text.func(is_materials_button))   # ⬅️ FSM bo‘lmaganda
async def materials_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = _t(lang)
    await message.answer(
        f"📚 <b>{_g(t, 'materials_title', 'Materiallar')}</b>\n\n{_g(t, 'materials_choose_cat', 'Kategoriya tanlang:')}",
        reply_markup=_cat_kb(lang),
        parse_mode="HTML",
    )

def is_category_alias(text: str) -> bool:
    if not text or text.startswith("/"):
        return False
    return _norm(text) in CAT_ALIASES

@router.message(StateFilter(None), F.text.func(is_category_alias))     # ⬅️ FSM bo‘lmaganda
async def materials_entry_by_alias(message: Message):
    cat = CAT_ALIASES.get(_norm(message.text or ""), "")
    if cat in CAT_KEYS:
        lang = get_lang(message.from_user.id, "uz")
        await _send_category_list_by_message(message, lang, cat, page=0)

# ===================== List w/ pagination (callbacks) =====================

@router.callback_query(F.data.startswith("mat:cat:"))
async def materials_list(cb: CallbackQuery):
    await _safe_cb_answer(cb)
    try:
        _, _, cat, page_s = cb.data.split(":")
        page = int(page_s)
    except Exception:
        return
    if cat not in CAT_KEYS:
        return

    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)

    if not db or not hasattr(db, "list_materials"):
        await cb.message.answer(_g(t, "materials_db_missing", "DB sozlanmagan."))
        return

    offset = page * PAGE_SIZE
    try:
        items = db.list_materials(category=cat, lang=lang, offset=offset, limit=PAGE_SIZE + 1)  # type: ignore[attr-defined]
    except Exception as e:
        logger.error(f"Materials DB error: {e}")
        await cb.message.answer(_g(t, "materials_db_missing", "DBda xatolik yuz berdi."))
        return

    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]
    has_prev = page > 0

    if not items:
        await cb.message.answer(_g(t, "materials_not_found", "Hozircha material yo'q."), reply_markup=_cat_kb(lang))
        return

    title = _g(t, CAT_KEYS[cat]["lkey"], cat.title())
    await cb.message.answer(
        f"{CAT_KEYS[cat]['icon']} <b>{title}</b>",
        parse_mode="HTML",
        reply_markup=_list_kb(lang, cat, page, has_prev, has_next, items),
    )

# ===================== Open material =====================

@router.callback_query(F.data.startswith("mat:open:"))
async def material_open(cb: CallbackQuery):
    await _safe_cb_answer(cb)
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)

    try:
        mat_id = int(cb.data.split(":")[-1])
    except Exception:
        return

    if not db or not hasattr(db, "get_material"):
        await cb.message.answer(_g(t, "materials_db_missing", "DB sozlanmagan."))
        return

    it = db.get_material(mat_id)  # type: ignore[attr-defined]
    if not it:
        await cb.message.answer(_g(t, "materials_not_found_one", "❌ Material topilmadi."))
        return

    title = (it.get("title") or "—").strip()
    desc = (it.get("description") or "").strip()
    caption = f"<b>{title}</b>" + (f"\n\n{desc}" if desc else "")

    price_cents = int(it.get("price_cents") or 0)
    paid = bool(it.get("is_paid")) or price_cents > 0

    if paid:
        price_str = f"{price_cents/100:.2f} $" if price_cents > 0 else _g(t, "materials_paid_label", "Pullik")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_g(t, "materials_buy_cta", "👤 Administrator bilan bog'lanish"), url="https://t.me/Narkuziyev")],
            [InlineKeyboardButton(text=_g(t, "materials_back", "⬅️ Orqaga"), callback_data="mat:back")],
        ])
        await cb.message.answer(
            f"🔒 {caption}\n\n{_g(t, 'materials_paid_label', 'Pullik')}: {price_str}",
            reply_markup=kb,
            parse_mode="HTML",
        )
        return

    st = (it.get("source_type") or "text").lower()
    sr = (it.get("source_ref") or "").strip()

    if st == "file_id":
        try:
            await cb.message.answer_document(sr, caption=caption, parse_mode="HTML")
        except Exception:
            await cb.message.answer(f"{caption}\n\nfile_id: <code>{sr}</code>", parse_mode="HTML")

    elif st == "url":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 URL", url=sr)],
            [InlineKeyboardButton(text=_g(t, "materials_back", "⬅️ Orqaga"), callback_data="mat:back")],
        ])
        await cb.message.answer(caption, reply_markup=kb, parse_mode="HTML")

    else:  # text
        body = sr or _g(t, "materials_no_content", "Kontent topilmadi.")
        await cb.message.answer(f"{caption}\n\n{body}", parse_mode="HTML")

# ===================== Back / Noop =====================

@router.callback_query(F.data == "mat:back")
async def materials_back(cb: CallbackQuery):
    await _safe_cb_answer(cb)
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await cb.message.answer(
        f"📚 <b>{_g(t, 'materials_title', 'Materiallar')}</b>\n\n{_g(t, 'materials_choose_cat', 'Kategoriya tanlang:')}",
        reply_markup=_cat_kb(lang),
        parse_mode="HTML",
    )

@router.callback_query(F.data.startswith("noop:"))
async def materials_noop(cb: CallbackQuery):
    await _safe_cb_answer(cb)
