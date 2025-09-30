# -*- coding: utf-8 -*-
# app/handlers/services.py

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
)
from ..locales import L
from ..storage.memory import get_lang
import os

# --- (ixtiyoriy) Pillow: rasmlarni xavfsiz formatga keltirish ---
try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except Exception:
    HAS_PIL = False

router = Router()

# Reply tugma matnlari
SERVICES_BTNS = {L["uz"]["btn_services"], L["en"]["btn_services"], L["ru"]["btn_services"]}

# Xizmat kalitlari (locales va callbacklar uchun)
SERVICE_KEYS = ["crm", "site", "leads", "arch", "ads", "call"]

ICONS = {
    "crm": "🤖",
    "site": "🕸️",
    "leads": "🎯",
    "arch": "🏗️",
    "ads": "📢",
    "call": "📞",
}

DETAIL_URLS = {
    "crm": "https://mcompany.uz/crm/",
    "site": "https://mcompany.uz/website/",
    "leads": "https://mcompany.uz/client/",
    "arch": "https://mcompany.uz/audit/starter/",
    "ads": "https://mcompany.uz/#res3",
    "call": "https://mcompany.uz/callCenter/",
}

# --- Inline menyu: har qatorga bitta tugma
def _services_menu_kb(lang: str) -> InlineKeyboardMarkup:
    t = L.get(lang, L["uz"])
    titles = [
        t["svc_crm"], t["svc_site"], t["svc_leads"],
        t["svc_arch"], t["svc_ads"], t["svc_call"],
    ]
    btns = [
        InlineKeyboardButton(text=f"{ICONS[k]} {ttl}", callback_data=f"svc:{k}")
        for k, ttl in zip(SERVICE_KEYS, titles)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[[b] for b in btns])

# --- “Batafsil” va “Orqaga” tugmalari
def _detail_kb(lang: str, key: str) -> InlineKeyboardMarkup:
    t = L.get(lang, L["uz"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["svc_more"], url=DETAIL_URLS[key])],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="svc:back")],
    ])

# --- Rasmni topish: app/assets/services/{key}.(jpg|jpeg|png|webp)
def _find_image_for_service(key: str) -> str | None:
    base = f"app/assets/services/{key}"
    for ext in ("jpg", "jpeg", "png", "webp", "JPG", "JPEG", "PNG", "WEBP"):
        p = f"{base}.{ext}"
        if os.path.isfile(p):
            return p
    return None

# --- Rasmni yuborishga tayyorlash (RGB/JPEG, ≤2560px, ≤~9.5MB)
def _prepare_photo(path: str, cache_key: str) -> FSInputFile | None:
    if not path or not os.path.isfile(path):
        return None
    if not HAS_PIL:
        return FSInputFile(path)
    try:
        os.makedirs("app/.cache/services", exist_ok=True)
        out_path = os.path.join("app/.cache/services", f"{cache_key}.jpg")
        with Image.open(path) as im:
            # EXIF orientatsiya
            try:
                im = ImageOps.exif_transpose(im)
            except Exception:
                pass

            # RGB
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            elif im.mode == "L":
                im = im.convert("RGB")

            # O'lcham cheklovi
            try:
                resample = Image.Resampling.LANCZOS
            except Exception:
                resample = Image.LANCZOS
            im.thumbnail((2560, 2560), resample)

            # Hajmni pasaytirib saqlash
            for q in (85, 80, 75, 70, 65, 60):
                im.save(out_path, format="JPEG", quality=q, optimize=True)
                if os.path.getsize(out_path) <= 9_500_000:  # ~9.5 MB
                    break
        return FSInputFile(out_path)
    except Exception:
        return FSInputFile(path)

# --- Caption limit (1024) ichida bitta xabarga joylash
CAPTION_LIMIT = 1024
def _one_message_caption(title: str, body: str, limit: int = CAPTION_LIMIT) -> str:
    prefix = f"<b>{title}</b>\n\n"
    room = max(0, limit - len(prefix))
    if len(body) <= room:
        return prefix + body
    short = body[: max(0, room - 1)].rstrip() + "…"
    return prefix + short

# === Handlers ===
@router.message(F.text.in_(SERVICES_BTNS))
async def services_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    await message.answer(t["services_intro"], reply_markup=_services_menu_kb(lang))

@router.callback_query(F.data == "svc:back")
async def services_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    await cb.answer()
    await cb.message.answer(t["services_intro"], reply_markup=_services_menu_kb(lang))

@router.callback_query(F.data.startswith("svc:"))
async def service_detail(cb: CallbackQuery):
    """
    Har bir xizmat uchun BIRTA xabar:
    - photo (agar bor bo'lsa)
    - caption: <b>Title</b> + to'liq/shrunk body
    - pastida inline tugmalar
    """
    key = cb.data.split(":", 1)[1]
    if key not in SERVICE_KEYS:
        await cb.answer("...")
        return

    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    title = t.get(f"svc_{key}", key.title())
    body  = t.get(f"svc_{key}_body", t["stub"])
    caption = _one_message_caption(title, body)
    kb = _detail_kb(lang, key)

    # Rasmni topish va tayyorlash
    img_path = _find_image_for_service(key)
    file = _prepare_photo(img_path, f"svc_{key}") if img_path else None

    await cb.answer(f"{ICONS.get(key, '•')} {title}")
    if file:
        await cb.message.answer_photo(photo=file, caption=caption, parse_mode="HTML", reply_markup=kb)
    else:
        await cb.message.answer(caption, parse_mode="HTML", reply_markup=kb)
