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
import hashlib
from typing import Optional, Tuple

# === Pillow: rasmni tayyorlash (convert/resize/compress) ===
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

# Rasm yo'llari (mavjud bo'lishi kerak)
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
        [btn("target_pro"), btn("fresh_line")],    # 1: yonma-yon
        [btn("agroboost"),  btn("iservice")],      # 2: yonma-yon
        [btn("roboticslab"),btn("falco")],         # 3: yonma-yon
        [btn("food_quest")],                       # 4: yakka
        [btn("imac")],                              # 5: yakka
        [btn("tatu")],                              # 6: yakka
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
def _split_caption(text: str, limit: int = MAX_CAPTION) -> Tuple[str, Optional[str]]:
    text = (text or "").strip()
    if len(text) <= limit:
        return text, None
    cut = text.rfind("\n\n", 0, limit)
    if cut == -1:
        cut = limit
    return text[:cut].strip(), text[cut:].strip() or None

# === Rasm tayyorlash: og'ir fayllarni ham foto sifatida yuborish uchun “ko'p variantli” pipeline ===

_CACHE_DIR = "app/.cache/projects"
os.makedirs(_CACHE_DIR, exist_ok=True)

def _hash_key(path: str, key: str, tag: str) -> str:
    """Path + key + variant tag bo'yicha deterministik fayl nomi."""
    h = hashlib.sha256(f"{os.path.abspath(path)}::{key}::{tag}".encode("utf-8")).hexdigest()[:16]
    return os.path.join(_CACHE_DIR, f"{key}_{tag}_{h}.jpg")

def _prepare_variant(
    src_path: str,
    key: str,
    *,
    max_side: int,
    target_max_bytes: int,
    start_quality: int,
    min_quality: int,
    step_quality: int = 8,
    progressive: bool = True,
    optimize: bool = True,
) -> Optional[FSInputFile]:
    """
    Bitta variant bo'yicha: RGBA->RGB, EXIF transpose, resize <= max_side,
    so'ng JPEG sifatini pasaytirib target_max_bytes ga tushirish.
    """
    if not HAS_PIL:
        # Pillow yo'q — baribir originalni yuborib ko'ramiz
        return FSInputFile(src_path)

    try:
        with Image.open(src_path) as im:
            # EXIF orientatsiya
            try:
                im = ImageOps.exif_transpose(im)
            except Exception:
                pass

            # RGBA/LA/P -> oq fon bilan RGB; CMYK/L -> RGB
            if im.mode in ("RGBA", "LA", "P"):
                base = Image.new("RGB", im.size, (255, 255, 255))
                if im.mode == "P":
                    im = im.convert("RGBA")
                base.paste(im, mask=im.split()[-1] if im.mode in ("RGBA", "LA") else None)
                im = base
            elif im.mode not in ("RGB",):
                im = im.convert("RGB")

            # Dastlabki resize
            w, h = im.size
            long_side = max(w, h)
            if long_side > max_side:
                scale = max_side / float(long_side)
                new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
                try:
                    resample = Image.Resampling.LANCZOS
                except Exception:
                    resample = Image.LANCZOS
                im = im.resize(new_size, resample=resample)

            # Iterativ quality & resize kichraytirish
            out_path = _hash_key(src_path, key, f"s{max_side}_t{target_max_bytes//1_000_000}mb_p{int(progressive)}_o{int(optimize)}")
            q = start_quality
            tries = 0
            while True:
                tries += 1
                # Saqlab ko'ramiz
                im.save(
                    out_path,
                    format="JPEG",
                    quality=q,
                    optimize=optimize,
                    progressive=progressive,
                )
                size = os.path.getsize(out_path)
                if size <= target_max_bytes:
                    return FSInputFile(out_path, filename=f"{key}.jpg")

                # Agar juda katta chiqayotgan bo'lsa: avval quality pasaytirish
                if q > min_quality:
                    q = max(min_quality, q - step_quality)
                else:
                    # Quality past — endi yana 15% ga kichraytiramiz
                    nw, nh = im.size
                    new_size2 = (max(1, int(nw * 0.85)), max(1, int(nh * 0.85)))
                    if new_size2 == im.size or min(new_size2) < 50:
                        # Juda kichik bo'lib ketdi — shunisi bilan qaytamiz
                        return FSInputFile(out_path, filename=f"{key}.jpg")
                    try:
                        resample = Image.Resampling.LANCZOS
                    except Exception:
                        resample = Image.LANCZOS
                    im = im.resize(new_size2, resample=resample)
                    # Quality’ni biroz ko'tarib, yana pasaytirish imkonini qoldiramiz
                    q = min(start_quality, q + int(step_quality // 2))

                if tries >= 10:
                    # Juda ko'p urindik — hozirgi variantni qaytaramiz
                    return FSInputFile(out_path, filename=f"{key}.jpg")

    except Exception:
        # Favqulodda: originalni qaytarib yuboramiz (baribir photo sifatida sinab ko'riladi)
        return FSInputFile(src_path)

def _prepare_photo_multi(src_path: str, key: str) -> Optional[FSInputFile]:
    """
    Bir necha "variant" bilan tayyorlaydi. Birinchisi odatdagidek, keyingilari
    tobora agressivroq siqadi. Birinchisi odatda yetadi.
    """
    if not src_path or not os.path.isfile(src_path):
        return None

    # Variant 1: 2000px, ~9MB, quality 85->55, progressive+optimize (odatda yetadi)
    v1 = _prepare_variant(
        src_path, key,
        max_side=2000,
        target_max_bytes=9_000_000,
        start_quality=85,
        min_quality=55,
        progressive=True,
        optimize=True,
    )
    return v1

async def _send_photo_resilient(cb: CallbackQuery, file: FSInputFile, *, caption: str, kb: InlineKeyboardMarkup):
    """
    IMAGE_PROCESS_FAILED bo'lsa, avtomatik ravishda boshqa tayyorlash variantlarini
    sinab ko'radi (progressive/baseline, yanada kichikroq o'lcham va hajm).
    """
    try:
        await cb.message.answer_photo(photo=file, caption=caption, reply_markup=kb, parse_mode="HTML")
        return
    except TelegramBadRequest as e:
        if "IMAGE_PROCESS_FAILED" not in str(e):
            raise

    # 2-variant: 1600px, ~5MB, baseline (progressive=False), optimize=True
    src_real = file.path if hasattr(file, "path") else None
    key_guess = os.path.splitext(os.path.basename(src_real or "photo"))[0]
    if src_real and HAS_PIL:
        v2 = _prepare_variant(
            src_real, key_guess,
            max_side=1600,
            target_max_bytes=5_000_000,
            start_quality=80,
            min_quality=50,
            progressive=False,
            optimize=True,
        )
        try:
            await cb.message.answer_photo(photo=v2, caption=caption, reply_markup=kb, parse_mode="HTML")
            return
        except TelegramBadRequest as e2:
            if "IMAGE_PROCESS_FAILED" not in str(e2):
                raise

        # 3-variant: 1280px, ~2.5MB, baseline, optimize=False
        v3 = _prepare_variant(
            src_real, key_guess,
            max_side=1280,
            target_max_bytes=2_500_000,
            start_quality=75,
            min_quality=45,
            progressive=False,
            optimize=False,
        )
        await cb.message.answer_photo(photo=v3, caption=caption, reply_markup=kb, parse_mode="HTML")
        return

    # Agar Pillow bo'lmasa/patni topa olmasak — qayta urinishning iloji yo‘q
    # (Bunday holat kam uchraydi). Matn bilan davom etamiz:
    await cb.message.answer(caption, reply_markup=kb, parse_mode="HTML")

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

    # Rasmni tayyorlash (variant 1 dan boshlaydi)
    file = _prepare_photo_multi(photo_path, key) if photo_path else None
    if file:
        await _send_photo_resilient(cb, file, caption=caption_head, kb=kb)
        if caption_tail:
            await cb.message.answer(caption_tail, parse_mode="HTML")
        return

    # Agar rasm yo'q bo'lsa — matn
    await cb.message.answer(caption_full, reply_markup=kb, parse_mode="HTML")
