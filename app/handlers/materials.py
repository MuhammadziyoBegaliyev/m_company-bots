# -*- coding: utf-8 -*-
# app/handlers/materials.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from ..locales import L
from ..storage.memory import get_lang

# DB
try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()

# Reply-triggers (3 til)
BTN_SET = {
    L["uz"]["btn_materials"],
    L["en"]["btn_materials"],
    L["ru"]["btn_materials"],
}

CAT_KEYS = {
    "book":    {"icon": "📘", "lkey": "materials_books"},
    "article": {"icon": "🧠", "lkey": "materials_articles"},
    "video":   {"icon": "🎬", "lkey": "materials_videos"},
    "audio":   {"icon": "🎧", "lkey": "materials_audios"},
}

PAGE_SIZE = 6

# -------- helpers ----------
def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

def _cat_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    rows = [
        [
            InlineKeyboardButton(text=f"{CAT_KEYS['book']['icon']} {t[CAT_KEYS['book']['lkey']]}", callback_data="mat:cat:book:0"),
            InlineKeyboardButton(text=f"{CAT_KEYS['article']['icon']} {t[CAT_KEYS['article']['lkey']]}", callback_data="mat:cat:article:0"),
        ],
        [
            InlineKeyboardButton(text=f"{CAT_KEYS['video']['icon']} {t[CAT_KEYS['video']['lkey']]}", callback_data="mat:cat:video:0"),
            InlineKeyboardButton(text=f"{CAT_KEYS['audio']['icon']} {t[CAT_KEYS['audio']['lkey']]}", callback_data="mat:cat:audio:0"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _list_kb(lang: str, cat: str, page: int, has_prev: bool, has_next: bool, items: list[dict]) -> InlineKeyboardMarkup:
    t = _t(lang)
    rows: list[list[InlineKeyboardButton]] = []
    # items as separate buttons
    for it in items:
        price = int(it.get("price_cents") or 0)
        paid = int(it.get("is_paid") or 0) == 1 or price > 0
        label = f"{'🔒 ' if paid else '✅ '}{it['title']}"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"mat:open:{it['id']}")])

    nav: list[InlineKeyboardButton] = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"mat:cat:{cat}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}", callback_data=f"noop:{page}"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"mat:cat:{cat}:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([InlineKeyboardButton(text=t["materials_back"], callback_data="mat:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def _safe_answer(cb: CallbackQuery):
    try:
        await cb.answer()
    except TelegramBadRequest:
        pass

# -------- entry ----------
@router.message(F.text.in_(BTN_SET))
async def materials_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = _t(lang)
    await message.answer(f"📚 <b>{t['materials_title']}</b>\n\n{t['materials_choose_cat']}",
                         reply_markup=_cat_kb(lang), parse_mode="HTML")

# -------- categories w/ pagination ----------
@router.callback_query(F.data.startswith("mat:cat:"))
async def materials_list(cb: CallbackQuery):
    await _safe_answer(cb)
    _, _, cat, page_s = cb.data.split(":")
    page = int(page_s)
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)

    if not db:
        await cb.message.answer("DB is not configured.")
        return

    offset = page * PAGE_SIZE
    items = db.list_materials(category=cat, lang=lang, offset=offset, limit=PAGE_SIZE + 1)
    has_next = len(items) > PAGE_SIZE
    items = items[:PAGE_SIZE]
    has_prev = page > 0

    if not items:
        await cb.message.answer(t["materials_not_found"], reply_markup=_cat_kb(lang))
        return

    # Header
    title = t[CAT_KEYS[cat]["lkey"]]
    await cb.message.answer(f"{CAT_KEYS[cat]['icon']} <b>{title}</b>",
                            parse_mode="HTML",
                            reply_markup=_list_kb(lang, cat, page, has_prev, has_next, items))

# -------- open material ----------
@router.callback_query(F.data.startswith("mat:open:"))
async def material_open(cb: CallbackQuery):
    await _safe_answer(cb)
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    mat_id = int(cb.data.split(":")[-1])
    if not db:
        return
    it = db.get_material(mat_id)
    if not it:
        await cb.message.answer("❌ Not found.")
        return

    paid = int(it.get("is_paid") or 0) == 1 or int(it.get("price_cents") or 0) > 0
    if paid:
        price = (int(it.get("price_cents") or 0) / 100.0) if it.get("price_cents") else None
        price_str = (f"{price:.2f} $" if price else t["materials_paid_label"])
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t["materials_buy_cta"], url="https://t.me/Narkuziyev")],
            [InlineKeyboardButton(text=t["materials_back"], callback_data="mat:back")]
        ])
        await cb.message.answer(f"🔒 <b>{it['title']}</b>\n\n{it.get('description') or ''}\n\n{t['materials_paid_label']}: {price_str}",
                                parse_mode="HTML", reply_markup=kb)
        return

    # Free: deliver content
    st = it["source_type"]; sr = it["source_ref"]
    desc = (it.get("description") or "").strip()
    caption = f"<b>{it['title']}</b>\n\n{desc}" if desc else f"<b>{it['title']}</b>"
    if st == "file_id":
        # Biz kontent turini (video/audio/document) bilmasak ham, document sifatida berish xavfsiz
        try:
            await cb.message.answer_document(sr, caption=caption, parse_mode="HTML")
        except Exception:
            await cb.message.answer(caption + f"\n\nfile_id: <code>{sr}</code>", parse_mode="HTML")
    elif st == "url":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 URL", url=sr)],
            [InlineKeyboardButton(text=t["materials_back"], callback_data="mat:back")],
        ])
        await cb.message.answer(caption, reply_markup=kb, parse_mode="HTML")
    else:  # text
        await cb.message.answer(f"{caption}\n\n{sr}", parse_mode="HTML")

# -------- back ----------
@router.callback_query(F.data == "mat:back")
async def materials_back(cb: CallbackQuery):
    await _safe_answer(cb)
    lang = get_lang(cb.from_user.id, "uz")
    t = _t(lang)
    await cb.message.answer(f"📚 <b>{t['materials_title']}</b>\n\n{t['materials_choose_cat']}",
                            reply_markup=_cat_kb(lang), parse_mode="HTML")

# no-op (page label)
@router.callback_query(F.data.startswith("noop:"))
async def noop(cb: CallbackQuery):
    await _safe_answer(cb)
