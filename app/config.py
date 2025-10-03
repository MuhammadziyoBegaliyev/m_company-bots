# app/config.py
from typing import List, Optional, Union
import re

from pydantic import Field, AliasChoices, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- Ichki yordamchi: CSV -> List[int] ---
def _to_int_list(v) -> List[int]:
    """
    Har xil ko‘rinishdagi qiymatni int ro‘yxatiga aylantiradi.
    Qo‘llab-quvvatlaydi: int | str("111, 222, -100333") | list/tuple
    """
    if v is None or v == "":
        return []
    if isinstance(v, int):
        return [v]
    if isinstance(v, (list, tuple)):
        out: List[int] = []
        for x in v:
            try:
                out.append(int(str(x).strip().strip('"').strip("'")))
            except Exception:
                pass
        return out
    if isinstance(v, str):
        s = v.strip().strip('"').strip("'")
        if not s:
            return []
        out: List[int] = []
        for part in s.split(","):
            part = part.strip()
            if not part:
                continue
            # signed integer (ixtiyoriy minus bilan)
            if re.match(r"^[-+]?\d+$", part):
                out.append(int(part))
        return out
    return []


class Settings(BaseSettings):
    # === Majburiy ===
    BOT_TOKEN: str = Field(
        ...,
        validation_alias=AliasChoices("BOT_TOKEN", "bot_token"),
        description="Telegram bot tokeni",
    )

    # === Ixtiyoriy ro‘yxatlar ===
    # Admin user ID(lar)i (mass-message, moderatsiya va hokazo)
    admin_ids: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ADMIN_IDS", "admin_ids"),
        description="Admin foydalanuvchilar ro‘yxati",
    )

    # FAQ yuboriladigan guruh(lar)
    faq_group_ids: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "FAQ_GROUP_ID", "faq_group_id",
            "FAQ_GROUP_IDS", "faq_group_ids"
        ),
        description="FAQ xabarlari yuboriladigan guruh ID(lar)i",
    )

    # Audit/booking bildirishnomalari yuboriladigan guruh(lar)
    admin_group_ids: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "ADMIN_GROUP_ID", "admin_group_id",
            "ADMIN_GROUP_IDS", "admin_group_ids"
        ),
        description="Audit/bron bildirishnomalari uchun guruh(lar)",
    )

    # === URL / yo‘l sozlamalari ===
    AUDIT_WEBSITE_URL: str = Field(
        default="https://mcompany.uz/audit/starter/",
        validation_alias=AliasChoices("AUDIT_WEBSITE_URL", "audit_website_url"),
        description="Audit xizmat sahifasi",
    )

    # Ma’lumotlar bazasi ulanish satri (agar ishlatilyapti)
    DATABASE_URL: str = Field(
        default="sqlite:///./app/storage/app.db",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
        description="DB ulanish satri (sqlite/postgres va hokazo)",
    )

    # === Qo‘shimcha umumiy sozlamalar ===
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

    # Webhook (kelajakda kerak bo‘lishi mumkin)
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
    @field_validator("admin_ids", "faq_group_ids", "admin_group_ids", mode="before")
    @classmethod
    def _parse_csv_ints(cls, v):
        return _to_int_list(v)

    @field_validator("AUDIT_WEBSITE_URL", mode="before")
    @classmethod
    def _normalize_url(cls, v: Union[str, None]) -> str:
        """
        AUDIT_WEBSITE_URL http/https bilan boshlansin.
        Bo‘sh bo‘lsa default qaytadi.
        """
        if not v:
            return "https://mcompany.uz/audit/starter/"
        v = str(v).strip()
        if not re.match(r"^https?://", v, flags=re.IGNORECASE):
            v = "https://" + v
        return v

    @field_validator("DEFAULT_LANG", mode="before")
    @classmethod
    def _check_lang(cls, v: Union[str, None]) -> str:
        v = (v or "uz").lower().strip()
        return v if v in {"uz", "en", "ru"} else "uz"

    # === Backward-compat properties (eski kodni qo‘llab-quvvatlash) ===
    @property
    def ADMIN_GROUP_ID(self) -> Optional[int]:
        """
        Eski handlerlarda `settings.ADMIN_GROUP_ID` ishlatilgan.
        Ro‘yxatdan birinchisini qaytaramiz (yo‘q bo‘lsa None).
        """
        return self.admin_group_ids[0] if self.admin_group_ids else None

    @property
    def faq_group_id(self) -> Optional[int]:
        """
        Eski kodlar uchun bitta qiymat.
        """
        return self.faq_group_ids[0] if self.faq_group_ids else None

    # Qo‘lay yordamchi
    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
