# -*- coding: utf-8 -*-
# app/handlers/projects.py

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
)
from aiogram.exceptions import TelegramBadRequest
from ..locales import L
from ..storage.memory import get_lang
import os

# === Yangi: Pillow bilan oldindan konvertatsiya ===
try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except Exception:
    HAS_PIL = False

router = Router()

# Reply tugma matnlari (3 tilda)
PROJECTS_BTNS = {L["uz"]["btn_projects"], L["en"]["btn_projects"], L["ru"]["btn_projects"]}

ICONS = {
    "target_pro": "🎯",
    "agroboost": "🌿",
    "roboticslab": "🤖",
    "iservice": "🛠️",
    "falco": "🦅",
    "food_quest": "🍽️",
    "imac": "🧬",
    "tatu": "🏛️",
    "fresh_line": "🧪",
}

PROJECT_PHOTOS = {
    "target_pro": "app/assets/projects/target_pro.jpg",
    "agroboost":  "app/assets/projects/agroboost_map.jpg",
    "roboticslab":"app/assets/projects/roboticslab.jpg",
    "iservice":   "app/assets/projects/iservice.jpg",
    "falco":      "app/assets/projects/falco.jpg",
    "food_quest": "app/assets/projects/foodquest.jpg",
    "imac":       "app/assets/projects/imac.jpg",
    "tatu":       "app/assets/projects/tatu.jpg",
    "fresh_line": "app/assets/projects/fresh_line.jpg",
}

PROJECT_URLS = {
    "target_pro": "https://mcompany.uz/#",
    "agroboost":  "https://mcompany.uz/#",
    "roboticslab":"https://roboticslab.uz/",
    "iservice":   "https://crm-iservice.uz/users/?next=/attendanceEmp/%3Fnext%3D/",
    "falco":      "https://www.falco.uz/",
    "food_quest": "https://foodquest.uz/",
    "imac":       "https://icma.uz/en/",
    "tatu":       "https://global-tuit.uz/en/",
    "fresh_line": "https://www.fresh-line.uz/",
}

# --- Maxsus tartib (siz xohlagan joylashuv) ---
def _kb_projects(lang: str) -> InlineKeyboardMarkup:
    t = L.get(lang, L["uz"])

    def title_for(key: str) -> str:
        default_titles = {"fresh_line": "Fresh Line"}
        return t.get(f"prj_{key}", default_titles.get(key, key.replace("_", " ").title()))

    def btn(key: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=f"{ICONS.get(key, '•')} {title_for(key)}",
            callback_data=f"prj:{key}"
        )

    rows = [
        [btn("target_pro"), btn("fresh_line")],    # 1
        [btn("agroboost"),  btn("iservice")],      # 2
        [btn("roboticslab"),btn("falco")],         # 3
        [btn("food_quest")],                       # 4
        [btn("imac")],                              # 5
        [btn("tatu")],                              # 6
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _kb_detail(lang: str, key: str) -> InlineKeyboardMarkup:
    t = L.get(lang, L["uz"])
    url = PROJECT_URLS.get(key, "https://mcompany.uz/#")
    rows = [
        [InlineKeyboardButton(text=t.get("svc_more", "More ↗️"), url=url)],
        [InlineKeyboardButton(text=t["back_btn"], callback_data="prj:back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def _safe_cb_answer(cb: CallbackQuery, *args, **kwargs):
    try:
        await cb.answer(*args, **kwargs)
    except TelegramBadRequest as e:
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            return
        raise

MAX_CAPTION = 1024
def _split_caption(text: str, limit: int = MAX_CAPTION):
    text = (text or "").strip()
    if len(text) <= limit:
        return text, None
    cut = text.rfind("\n\n", 0, limit)
    if cut == -1:
        cut = limit
    return text[:cut].strip(), text[cut:].strip() or None

# === FOTO doimiy chiqishi uchun oldindan transkod ===
def _prepare_photo(path: str, key: str) -> FSInputFile | None:
    """
    Rasmni RGB/JPEG (≤2560px) ga transkod qiladi va FSInputFile qaytaradi.
    Hajm > 9.5MB bo‘lsa sifatni pasaytirib qayta saqlaydi.
    Pillow bo'lmasa, original faylni sinab ko'radi.
    """
    if not path or not os.path.isfile(path):
        return None

    if not HAS_PIL:
        return FSInputFile(path)

    try:
        os.makedirs("app/.cache/projects", exist_ok=True)
        out_path = os.path.join("app/.cache/projects", f"{key}.jpg")

        with Image.open(path) as im:
            # EXIF orientatsiya
            try:
                im = ImageOps.exif_transpose(im)
            except Exception:
                pass

            # RGB ga o'tkazish
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            elif im.mode == "L":
                im = im.convert("RGB")

            # O'lchamni cheklash
            try:
                resample = Image.Resampling.LANCZOS  # Pillow >=10
            except Exception:
                resample = Image.LANCZOS
            im.thumbnail((2560, 2560), resample)

            # Sifatni iterativ kamaytirish (hajm limiti uchun)
            for quality in (85, 80, 75, 70, 65, 60):
                im.save(out_path, format="JPEG", quality=quality, optimize=True)
                if os.path.getsize(out_path) <= 9_500_000:  # ~9.5 MB
                    break

        return FSInputFile(out_path)
    except Exception:
        # Muammo bo'lsa, originalni sinaymiz (baribir photo sifatida)
        return FSInputFile(path)

@router.message(F.text.in_(PROJECTS_BTNS))
async def projects_entry(message: Message):
    lang = get_lang(message.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    await message.answer(t["projects_title"], reply_markup=_kb_projects(lang))

@router.callback_query(F.data == "prj:back")
async def projects_back(cb: CallbackQuery):
    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])
    await _safe_cb_answer(cb)
    await cb.message.answer(t["projects_title"], reply_markup=_kb_projects(lang))

@router.callback_query(F.data.startswith("prj:"))
async def project_selected(cb: CallbackQuery):
    key = cb.data.split(":", 1)[1]
    if key == "back":
        return

    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])

    title = t.get(f"prj_{key}", "Fresh Line" if key == "fresh_line" else key.replace("_", " ").title())
    body  = t.get(f"prj_{key}_body", t["project_selected"].format(name=title))
    caption_full = f"<b>{title}</b>\n\n{body}"
    caption_head, caption_tail = _split_caption(caption_full)

    await _safe_cb_answer(cb, f"{ICONS.get(key,'•')} {title}")

    photo_path = PROJECT_PHOTOS.get(key)
    kb = _kb_detail(lang, key)

    file = _prepare_photo(photo_path, key) if photo_path else None
    if file:
        # Doim PHOTO yuboramiz (HTML formatida)
        await cb.message.answer_photo(photo=file, caption=caption_head, reply_markup=kb, parse_mode="HTML")
        if caption_tail:
            await cb.message.answer(caption_tail, parse_mode="HTML")
        return

    # Agar rasm yo'q bo'lsa — matn (HTML)
    await cb.message.answer(caption_full, reply_markup=kb, parse_mode="HTML")
