# -*- coding: utf-8 -*-
# app/handlers/projects.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.exceptions import TelegramBadRequest
from ..locales import L
from ..storage.memory import get_lang
import os

router = Router()

# Reply tugma matnlari (3 tilda)
PROJECTS_BTNS = {L["uz"]["btn_projects"], L["en"]["btn_projects"], L["ru"]["btn_projects"]}

# Inline tugmalardagi emoji(logo-sifatida)
ICONS = {
    "target_pro": "🎯",
    "agroboost": "🌿",
    "roboticslab": "🤖",
    "iservice": "🛠️",
    "falco": "🦅",
    "food_quest": "🍽️",
    "imac": "🧬",
    "tatu": "🏛️",
    "fresh_line": "🧪",  # yangi loyiha (iconni xohlagancha o'zgartirishingiz mumkin)
}

# Har bir loyiha uchun rasm (lokal fayl yo'li)
PROJECT_PHOTOS = {
    "target_pro": "app/assets/projects/target_pro.jpg",
    "agroboost":  "app/assets/projects/agroboost_map.jpg",
    "roboticslab":"app/assets/projects/roboticslab.jpg",
    "iservice":   "app/assets/projects/iservice.jpg",
    "falco":      "app/assets/projects/falco.jpg",
    "food_quest": "app/assets/projects/foodquest.jpg",
    "imac":       "app/assets/projects/imac.jpg",
    "tatu":       "app/assets/projects/tatu.jpg",
    "fresh_line": "app/assets/projects/fresh_line.jpg",  # yangi
}

# "Batafsil" URLlar
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

def _kb_projects(lang: str) -> InlineKeyboardMarkup:
    """Maxsus tartib: 
       1) target_pro | fresh_line
       2) agroboost  | iservice
       3) roboticslab| falco
       4) food_quest
       5) imac
       6) tatu
    """
    t = L.get(lang, L["uz"])

    # Kalit -> sarlavha (locales bo'lmasa defaultga tushadi)
    def title_for(key: str) -> str:
        default_titles = {
            "fresh_line": "Fresh Line",
        }
        return t.get(f"prj_{key}", default_titles.get(key, key.replace("_", " ").title()))

    def btn(key: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            text=f"{ICONS.get(key, '•')} {title_for(key)}",
            callback_data=f"prj:{key}"
        )

    rows = [
        [btn("target_pro"), btn("fresh_line")],    # 1-qator: yonma-yon
        [btn("agroboost"),  btn("iservice")],      # 2-qator: yonma-yon
        [btn("roboticslab"),btn("falco")],         # 3-qator: yonma-yon
        [btn("food_quest")],                       # 4-qator: yakka
        [btn("imac")],                              # 5-qator: yakka
        [btn("tatu")],                              # 6-qator: yakka
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def _kb_detail(lang: str, key: str) -> InlineKeyboardMarkup:
    """Har bir loyiha sahifasida 'Batafsil' va 'Orqaga'."""
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
        # Eski/invalid query bo'lsa bot yiqilmasin
        if "query is too old" in str(e).lower() or "query id is invalid" in str(e).lower():
            return
        raise

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
        return  # yuqorida alohida handler bor

    lang = get_lang(cb.from_user.id, "uz")
    t = L.get(lang, L["uz"])

    title = t.get(f"prj_{key}", "Fresh Line" if key == "fresh_line" else key)
    body  = t.get(f"prj_{key}_body", t["project_selected"].format(name=title))
    caption = f"<b>{title}</b>\n\n{body}"

    await _safe_cb_answer(cb, f"{ICONS.get(key,'•')} {title}")

    photo_path = PROJECT_PHOTOS.get(key)
    if photo_path and os.path.exists(photo_path):
        await cb.message.answer_photo(
            photo=FSInputFile(photo_path),
            caption=caption,
            reply_markup=_kb_detail(lang, key)
        )
    else:
        await cb.message.answer(caption, reply_markup=_kb_detail(lang, key))
