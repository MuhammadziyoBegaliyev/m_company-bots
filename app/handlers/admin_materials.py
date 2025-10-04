# -*- coding: utf-8 -*-
# app/handlers/admin_materials.py

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from ..config import settings
from ..locales import L
from ..storage.memory import get_lang

try:
    from ..storage.db import db
except Exception:
    db = None  # type: ignore

router = Router()

def _is_admin(uid: int) -> bool:
    return uid in (settings.admin_ids or [])

def _t(lang: str) -> dict:
    return L.get(lang, L["uz"])

CATS = [("book","📘"), ("article","🧠"), ("video","🎬"), ("audio","🎧")]
LANGS = [("uz","🇺🇿"), ("en","🇬🇧"), ("ru","🇷🇺")]

def _adm_root_kb(lang: str) -> InlineKeyboardMarkup:
    t = _t(lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"➕ {t['adm_mat_add']}", callback_data="madmin:add")],
        [InlineKeyboardButton(text=f"📋 {t['adm_mat_list']}", callback_data="madmin:list:book:0")],
    ])

def _cats_kb(prefix: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=f"{icon} {cat.title()}", callback_data=f"{prefix}:{cat}:0") for cat, icon in CATS[:2]],
            [InlineKeyboardButton(text=f"{CATS[2][1]} {CATS[2][0].title()}", callback_data=f"{prefix}:{CATS[2][0]}:0"),
             InlineKeyboardButton(text=f"{CATS[3][1]} {CATS[3][0].title()}", callback_data=f"{prefix}:{CATS[3][0]}:0")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _langs_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{f} {k.upper()}", callback_data=f"madmin:lang:{k}")] for k, f in LANGS
    ])

class AddFSM(StatesGroup):
    CAT = State()
    LANG = State()
    TITLE = State()
    DESC = State()
    PAID = State()
    PRICE = State()
    SRC = State()
    PREVIEW = State()

# entry from /admin or separate:
@router.message(Command("mats"))
async def mats_entry_cmd(message: Message):
    if not _is_admin(message.from_user.id):
        return
    lang = get_lang(message.from_user.id, settings.DEFAULT_LANG)
    t = _t(lang)
    await message.answer(f"🧰 <b>{t['adm_mat_title']}</b>", reply_markup=_adm_root_kb(lang), parse_mode="HTML")

# integrate with admin panel (callback)
@router.callback_query(F.data == "adm:mats")
async def mats_entry_cb(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id): return
    lang = get_lang(cb.from_user.id, settings.DEFAULT_LANG); t = _t(lang)
    await cb.answer()
    await cb.message.answer(f"🧰 <b>{t['adm_mat_title']}</b>", reply_markup=_adm_root_kb(lang), parse_mode="HTML")

# ---- ADD FLOW ----
@router.callback_query(F.data == "madmin:add")
async def m_add_start(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id): return
    await cb.answer()
    await state.clear()
    await state.set_state(AddFSM.CAT)
    await cb.message.answer("⚙️ Kategoriya tanlang:", reply_markup=_cats_kb("madmin:cat"))

@router.callback_query(AddFSM.CAT, F.data.startswith("madmin:cat:"))
async def m_add_cat(cb: CallbackQuery, state: FSMContext):
    cat = cb.data.split(":")[-2] if cb.data.endswith(":0") else cb.data.split(":")[-1]
    await cb.answer()
    await state.update_data(cat=cat)
    await state.set_state(AddFSM.LANG)
    await cb.message.answer("🌍 Tilni tanlang:", reply_markup=_langs_kb())

@router.callback_query(AddFSM.LANG, F.data.startswith("madmin:lang:"))
async def m_add_lang(cb: CallbackQuery, state: FSMContext):
    lang = cb.data.split(":")[-1]
    await cb.answer()
    await state.update_data(lang=lang)
    await state.set_state(AddFSM.TITLE)
    await cb.message.answer("📝 Sarlavha yuboring:")

@router.message(AddFSM.TITLE)
async def m_add_title(message: Message, state: FSMContext):
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AddFSM.DESC)
    await message.answer("📄 Tavsif yuboring (ixtiyoriy) yoki «/skip» yozing.")

@router.message(AddFSM.DESC, F.text == "/skip")
async def m_add_desc_skip(message: Message, state: FSMContext):
    await state.update_data(desc=None)
    await state.set_state(AddFSM.PAID)
    await message.answer("💵 Bu material pullikmi? (ha/yo‘q)")

@router.message(AddFSM.DESC)
async def m_add_desc(message: Message, state: FSMContext):
    await state.update_data(desc=(message.text or "").strip())
    await state.set_state(AddFSM.PAID)
    await message.answer("💵 Bu material pullikmi? (ha/yo‘q)")

@router.message(AddFSM.PAID)
async def m_add_paid(message: Message, state: FSMContext):
    txt = (message.text or "").strip().lower()
    is_paid = txt in {"ha","yes","да","haa","true","1"}
    await state.update_data(is_paid=is_paid)
    if is_paid:
        await state.set_state(AddFSM.PRICE)
        await message.answer("💰 Narxni kiriting (USD, masalan 9.99) yoki «/skip»:")
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
    raw = (message.text or "0").replace(",", ".")
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
    if message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.audio:
        file_id = message.audio.file_id
    await state.update_data(src_type="file_id", src_ref=file_id)
    await _m_preview(message, state)

@router.message(AddFSM.SRC, F.text)
async def m_add_src_text_or_url(message: Message, state: FSMContext):
    txt = (message.text or "").strip()
    if txt.startswith("http://") or txt.startswith("https://"):
        await state.update_data(src_type="url", src_ref=txt)
    else:
        await state.update_data(src_type="text", src_ref=txt)
    await _m_preview(message, state)

async def _m_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data["title"]
    desc  = data.get("desc") or ""
    is_paid = data.get("is_paid")
    price_cents = int(data.get("price_cents") or 0)
    price = f"{price_cents/100:.2f}$" if is_paid and price_cents else "—"
    txt = (
        f"🧾 <b>Preview</b>\n"
        f"📂 Cat: {data['cat']}\n"
        f"🌍 Lang: {data['lang']}\n"
        f"📝 Title: {title}\n"
        f"📄 Desc: {desc[:100]}{'...' if len(desc)>100 else ''}\n"
        f"💵 Paid: {'Yes' if is_paid else 'No'} | Price: {price}\n"
        f"📎 Source: {data['src_type']}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Saqlash", callback_data="madmin:save"),
         InlineKeyboardButton(text="❌ Bekor",  callback_data="madmin:cancel")]
    ])
    await message.answer(txt, parse_mode="HTML", reply_markup=kb)
    await state.set_state(AddFSM.PREVIEW)

@router.callback_query(AddFSM.PREVIEW, F.data == "madmin:cancel")
async def m_add_cancel(cb: CallbackQuery, state: FSMContext):
    await cb.answer("❌")
    await state.clear()
    await cb.message.answer("Bekor qilindi.")

@router.callback_query(AddFSM.PREVIEW, F.data == "madmin:save")
async def m_add_save(cb: CallbackQuery, state: FSMContext):
    if not _is_admin(cb.from_user.id) or not db:
        return
    await cb.answer("💾")
    data = await state.get_data()
    mat_id = db.add_material(
        category=data["cat"],
        lang=data["lang"],
        title=data["title"],
        description=data.get("desc"),
        is_paid=bool(data.get("is_paid")),
        price_cents=int(data.get("price_cents") or 0),
        source_type=data["src_type"],
        source_ref=data["src_ref"],
        created_by=cb.from_user.id
    )
    await state.clear()
    await cb.message.answer(f"✅ Saqlandi (ID: {mat_id}).")

# ---- LIST (quick) ----
@router.callback_query(F.data.startswith("madmin:list:"))
async def m_list(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id) or not db:
        return
    _, _, cat, page_s = cb.data.split(":")
    page = int(page_s)
    lang = get_lang(cb.from_user.id, "uz")
    offset = page * 10
    lst = db.list_materials(category=cat, lang=lang, offset=offset, limit=11)
    has_next = len(lst) > 10
    lst = lst[:10]
    lines = [f"• #{x['id']} — {x['title']} {'🔒' if x['is_paid'] else '✅'}" for x in lst] or ["— empty —"]
    nav: list[InlineKeyboardButton] = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"madmin:list:{cat}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}", callback_data=f"noop:{page}"))
    if has_next: nav.append(InlineKeyboardButton(text="➡️", callback_data=f"madmin:list:{cat}:{page+1}"))
    kb = InlineKeyboardMarkup(inline_keyboard=[nav] if nav else [])
    await cb.answer()
    await cb.message.answer("\n".join(lines), reply_markup=kb)
