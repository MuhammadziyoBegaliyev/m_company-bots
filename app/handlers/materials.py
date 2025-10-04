
from __future__ import annotations

from typing import Optional, List, Dict
from aiogram import Router, F
from aiogram.filters import Command
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
except Exception:
    db = None  # type: ignore

router = Router()

# ===================== Config =====================
PAGE_SIZE = 6

CAT_KEYS = {
    "book":    {"icon": "📘", "lkey": "materials_books"},
    "article": {"icon": "🧠", "lkey": "materials_articles"},
    "video":   {"icon": "🎬", "lkey": "materials_videos"},
    "audio":   {"icon": "🎧", "lkey": "materials_audios"},
}

# ---------- Reply triggerlar (3 til + aliaslar) ----------
def _norm(s: str) -> str:
    return (s or "").strip().lower().replace("’", "'").replace("`", "'")

BTN_SET_RAW = {
    L.get("uz", {}).get("btn_materials", "Materiallar"),
    L.get("en", {}).get("btn_materials", "Materials"),
    L.get("ru", {}).get("btn_materials", "Материалы"),
}
# ehtimoliy yozilishlar:
BTN_ALIASES = {
    "materiallar", "materials", "материалы", "material", "материал",
}
BTN_SET_NORM = {_norm(x) for x in (BTN_SET_RAW | BTN_ALIASES)}

# ===================== Helpers =====================
def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

def _g(t: dict, key: str, default: str) -> str:
    return t.get(key, default)

def _safe_cb_answer(cb: CallbackQuery):
    async def _inner():
        try:
            await cb.answer()
        except TelegramBadRequest as e:
            s = str(e).lower()
            if "query is too old" in s or "query id is invalid" in s:
                return
            raise
    return _inner()

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
        title = it.get("title") or "—"
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

# ===================== Entry =====================

@router.message(Command("materials"))
async def materials_cmd(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = _t(lang)
    await message.answer(
        f"📚 <b>{_g(t, 'materials_title', 'Materiallar')}</b>\n\n{_g(t, 'materials_choose_cat', 'Kategoriya tanlang:')}",
        reply_markup=_cat_kb(lang),
        parse_mode="HTML",
    )

@router.message(F.text.func(lambda s: _norm(s) in BTN_SET_NORM))
async def materials_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = _t(lang)
    await message.answer(
        f"📚 <b>{_g(t, 'materials_title', 'Materiallar')}</b>\n\n{_g(t, 'materials_choose_cat', 'Kategoriya tanlang:')}",
        reply_markup=_cat_kb(lang),
        parse_mode="HTML",
    )

# ===================== List w/ pagination =====================

@router.callback_query(F.data.startswith("mat:cat:"))
async def materials_list(cb: CallbackQuery):
    await _safe_cb_answer(cb)
    try:
        _, _, cat, page_s = cb.data.split(":")
    except Exception:
        return
    if cat not in CAT_KEYS:
        return

    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    page = int(page_s)

    if not db:
        await cb.message.answer(_g(t, "materials_db_missing", "DB sozlanmagan."))
        return

    offset = page * PAGE_SIZE
    items = db.list_materials(category=cat, lang=lang, offset=offset, limit=PAGE_SIZE + 1)  # type: ignore[attr-defined]
    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]
    has_prev = page > 0

    if not items:
        await cb.message.answer(_g(t, "materials_not_found", "Hozircha material yo‘q."), reply_markup=_cat_kb(lang))
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

    if not db:
        await cb.message.answer(_g(t, "materials_db_missing", "DB sozlanmagan."))
        return

    it = db.get_material(mat_id)  # type: ignore[attr-defined]
    if not it:
        await cb.message.answer(_g(t, "materials_not_found_one", "❌ Material topilmadi."))
        return

    title = it.get("title") or "—"
    desc = (it.get("description") or "").strip()
    caption = f"<b>{title}</b>" + (f"\n\n{desc}" if desc else "")

    price_cents = int(it.get("price_cents") or 0)
    paid = bool(it.get("is_paid")) or price_cents > 0

    if paid:
        price_str = f"{price_cents/100:.2f} $" if price_cents > 0 else _g(t, "materials_paid_label", "Pullik")
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_g(t, "materials_buy_cta", "👤 Administrator bilan bog‘lanish"), url="https://t.me/Narkuziyev")],
            [InlineKeyboardButton(text=_g(t, "materials_back", "⬅️ Orqaga"), callback_data="mat:back")],
        ])
        await cb.message.answer(
            f"🔒 {caption}\n\n{_g(t, 'materials_paid_label', 'Pullik')}: {price_str}",
            reply_markup=kb,
            parse_mode="HTML",
        )
        return

    # Free content
    st = (it.get("source_type") or "text").lower()
    sr = (it.get("source_ref") or "").strip()

    if st == "file_id":
        # Formatni bilmasak ham, document ko‘pchilik hollarda ishlaydi
        try:
            await cb.message.answer_document(sr, caption=caption, parse_mode="HTML")
        except Exception:
            # Fallback: matn + file_id
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
