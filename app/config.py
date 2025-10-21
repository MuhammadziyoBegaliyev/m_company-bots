# -*- coding: utf-8 -*-
# app/config.py

from typing import List, Optional, Union, Any
import re
import json

from pydantic import Field, AliasChoices, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _to_int_list(v: Any) -> List[int]:
    """
    Har xil ko'rinishdagi qiymatni int ro'yxatiga aylantiradi.
    Qo'llab-quvvatlaydi:
      - int
      - list/tuple (raqamlar yoki raqam-str)
      - str: "111, 222, -100333" yoki "[111, 222]" (JSON ham)
    """
    if v is None or v == "":
        return []
    if isinstance(v, (list, tuple)):
        out: List[int] = []
        for x in v:
            sx = str(x).strip().strip('"').strip("'")
            if sx.lstrip("+-").isdigit():
                out.append(int(sx))
        return out
    if isinstance(v, int):
        return [v]
    if isinstance(v, str):
        s = v.strip()
        # JSON bo'lishi mumkin
        if s.startswith("[") and s.endswith("]"):
            try:
                arr = json.loads(s)
                return _to_int_list(arr)
            except Exception:
                pass
        # CSV
        out: List[int] = []
        for part in s.split(","):
            part = part.strip().strip('"').strip("'")
            if part and re.match(r"^[-+]?\d+$", part):
                out.append(int(part))
        return out
    return []


class Settings(BaseSettings):
    """
    .env namuna:
      BOT_TOKEN=123:ABC
      ADMIN_IDS=6824528065,7567219498
      FAQ_GROUP_ID=-1002976616999
      ADMIN_GROUP_ID=-1002976616999
      AUDIT_WEBSITE_URL=https://mcompany.uz/audit/starter/
    """

    # === Majburiy ===
    BOT_TOKEN: str = Field(
        ...,
        validation_alias=AliasChoices("BOT_TOKEN", "bot_token"),
        description="Telegram bot tokeni",
    )

    # === Env dagi raw qiymatlar (string) — keyin pars qilamiz ===
    admin_ids_env: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ADMIN_IDS", "admin_ids"),
        description="Adminlar ro'yxati (CSV yoki JSON)",
    )
    faq_group_ids_env: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("FAQ_GROUP_ID", "faq_group_id", "FAQ_GROUP_IDS", "faq_group_ids"),
        description="FAQ guruh(lar)i (CSV/JSON)",
    )
    admin_group_ids_env: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("ADMIN_GROUP_ID", "admin_group_id", "ADMIN_GROUP_IDS", "admin_group_ids"),
        description="Audit/bron guruh(lar)i (CSV/JSON)",
    )

    # === Biz ishlatadigan tayyor ro'yxatlar ===
    admin_ids: List[int] = Field(default_factory=list)
    faq_group_ids: List[int] = Field(default_factory=list)
    admin_group_ids: List[int] = Field(default_factory=list)

    # === URL / yo'l sozlamalari ===
    AUDIT_WEBSITE_URL: str = Field(
        default="https://mcompany.uz/audit/starter/",
        validation_alias=AliasChoices("AUDIT_WEBSITE_URL", "audit_website_url"),
        description="Audit xizmat sahifasi",
    )

    DATABASE_URL: str = Field(
        default="sqlite:///./app/storage/app.db",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
        description="DB ulanish satri (sqlite/postgres va hokazo)",
    )

    # === Qo'shimcha umumiy sozlamalar ===
    DEFAULT_LANG: str = Field(
        default="uz",
        validation_alias=AliasChoices("DEFAULT_LANG", "default_lang"),
        description="Standart til (uz/en/ru)",
    )

    LOG_LEVEL: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL", "log_level"),
        description="Log darajasi: DEBUG/INFO/WARNING/ERROR",
    )

    TIMEZONE: str = Field(
        default="Asia/Tashkent",
        validation_alias=AliasChoices("TIMEZONE", "timezone"),
        description="Bot uchun vaqt mintaqasi",
    )

    USE_WEBHOOK: bool = Field(
        default=False,
        validation_alias=AliasChoices("USE_WEBHOOK", "use_webhook"),
    )
    WEBHOOK_URL: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WEBHOOK_URL", "webhook_url"),
    )
    WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WEBHOOK_SECRET", "webhook_secret"),
    )

    # === Validatorlar ===
    @field_validator("AUDIT_WEBSITE_URL", mode="before")
    @classmethod
    def _normalize_url(cls, v: Union[str, None]) -> str:
        if not v:
            return "https://mcompany.uz/audit/starter/"
        s = str(v).strip()
        if not re.match(r"^https?://", s, flags=re.IGNORECASE):
            s = "https://" + s
        return s

    @field_validator("DEFAULT_LANG", mode="before")
    @classmethod
    def _check_lang(cls, v: Union[str, None]) -> str:
        v = (v or "uz").lower().strip()
        return v if v in {"uz", "en", "ru"} else "uz"

    # Raw maydonlardan haqiqiy ro'yxatlarni yig'ib qo'yamiz
    @model_validator(mode="after")
    def _build_lists_from_env(self):
        if not self.admin_ids and self.admin_ids_env:
            self.admin_ids = _to_int_list(self.admin_ids_env)

        if not self.faq_group_ids and self.faq_group_ids_env:
            self.faq_group_ids = _to_int_list(self.faq_group_ids_env)

        if not self.admin_group_ids and self.admin_group_ids_env:
            self.admin_group_ids = _to_int_list(self.admin_group_ids_env)

        return self

    # === Backward-compat properties (eski kodni qo'llab-quvvatlash) ===
    @property
    def ADMIN_GROUP_ID(self) -> Optional[int]:
        """Eski handlerlarda settings.ADMIN_GROUP_ID ishlatilgan bo'lishi mumkin."""
        return self.admin_group_ids[0] if self.admin_group_ids else None

    @property
    def faq_group_id(self) -> Optional[int]:
        """Eski kodlar uchun yagona qiymatga mos props."""
        return self.faq_group_ids[0] if self.faq_group_ids else None

    # Qulay yordamchi
    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ===== SETTINGS INSTANCE =====
# Bu faylning oxirida yaratamiz
settings = Settings()

# Debug output (ixtiyoriy - kerak bo'lsa o'chirish mumkin)
if __name__ == "__main__":
    print(f"✅ Config loaded")
    print(f"👥 Admin IDs: {settings.admin_ids}")
    print(f"📚 FAQ Groups: {settings.faq_group_ids}")
    print(f"🛠  Admin Groups: {settings.admin_group_ids}")