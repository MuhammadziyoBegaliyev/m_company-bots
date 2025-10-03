
from typing import List, Optional, Union
import re

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices, field_validator


def _to_int_list(v) -> List[int]:
    """
    Har xil ko'rinishdagi (int/str/list/tuple) qiymatni int ro'yxatiga aylantiradi.
    Str bo'lsa: "111, 222, -100333"
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
            if re.match(r"^[-+]?\d+$", part):
                out.append(int(part))
        return out
    return []


class Settings(BaseSettings):
    # --- Majburiy ---
    BOT_TOKEN: str = Field(
        ...,
        validation_alias=AliasChoices("BOT_TOKEN", "bot_token"),
        description="Telegram bot tokeni",
    )

    # --- Ixtiyoriy / ro'yxatlar ---
    # Admin user ID(lar) – umumiy ro'yxat (foydali: xabar yuborish, moderatsiya va h.k.)
    admin_ids: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ADMIN_IDS", "admin_ids"),
        description="Admin foydalanuvchilar ro'yxati",
    )

    # FAQ yuboriladigan guruh(lar) – bitta yoki ko'p
    faq_group_ids: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices("FAQ_GROUP_ID", "faq_group_id", "FAQ_GROUP_IDS", "faq_group_ids"),
        description="FAQ xabarlari yuboriladigan guruh ID(lar)i",
    )

    # Audit/booking uchun admin guruh(lar)i – bitta yoki ko'p
    # Kodda ko'pincha settings.ADMIN_GROUP_ID ishlatiladi; shuning uchun quyida property bor.
    admin_group_ids: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ADMIN_GROUP_ID", "admin_group_id", "ADMIN_GROUP_IDS", "admin_group_ids"),
        description="Audit/bron bildirishnomalari yuboriladigan guruh(lar)",
    )

    # --- URL/yo'l sozlamalari ---
    AUDIT_WEBSITE_URL: str = Field(
        default="https://mcompany.uz/audit/starter/",
        validation_alias=AliasChoices("AUDIT_WEBSITE_URL", "audit_website_url"),
        description="Audit xizmat sahifasi",
    )

    # Ixtiyoriy: DB ulanishi (agar ishlatsangiz)
    DATABASE_URL: str = Field(
        default="sqlite:///./app/storage/app.db",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
        description="Ma'lumotlar bazasi ulanish satri (sqlite/postgres va h.k.)",
    )

    # Default til (fallback)
    DEFAULT_LANG: str = Field(
        default="uz",
        validation_alias=AliasChoices("DEFAULT_LANG", "default_lang"),
        description="Foydalanuvchi uchun standart til (uz/en/ru)",
    )

    # Logging darajasi
    LOG_LEVEL: str = Field(
        default="INFO",
        validation_alias=AliasChoices("LOG_LEVEL", "log_level"),
        description="Log darajasi: DEBUG/INFO/WARNING/ERROR",
    )

    # Vaqt mintaqasi (ixtiyoriy)
    TIMEZONE: str = Field(
        default="Asia/Tashkent",
        validation_alias=AliasChoices("TIMEZONE", "timezone"),
        description="Bot uchun vaqt mintaqasi",
    )

    # Webhook (ixtiyoriy, polling ishlatyapsiz – lekin keyin kerak bo‘lishi mumkin)
    USE_WEBHOOK: bool = Field(
        default=False,
        validation_alias=AliasChoices("USE_WEBHOOK", "use_webhook"),
        description="True bo'lsa webhook rejimi, aks holda polling",
    )
    WEBHOOK_URL: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WEBHOOK_URL", "webhook_url"),
    )
    WEBHOOK_SECRET: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WEBHOOK_SECRET", "webhook_secret"),
    )

    # --- Validatorlar ---
    @field_validator("admin_ids", "faq_group_ids", "admin_group_ids", mode="before")
    @classmethod
    def _parse_csv_ints(cls, v):
        return _to_int_list(v)

    @field_validator("AUDIT_WEBSITE_URL", mode="before")
    @classmethod
    def _normalize_audit_url(cls, v: Union[str, None]) -> str:
        """
        AUDIT_WEBSITE_URL http/https bilan boshlansin.
        Bo'sh bo'lsa default qaytadi.
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

    # Backward compatibility: eski kodlar uchun bitta qiymatni qaytaruvchi propertylar
    @property
    def ADMIN_GROUP_ID(self) -> Optional[int]:
        """
        Ba'zi handlerlarda settings.ADMIN_GROUP_ID ishlatilgan.
        Agar env da bitta qiymat bo'lsa yoki ro'yxat bo'lsa — birinchisini qaytaradi.
        """
        return self.admin_group_ids[0] if self.admin_group_ids else None

    @property
    def faq_group_id(self) -> Optional[int]:
        """
        Eski kodlar 'faq_group_id' ni so'rashi mumkin — birinchi elementni qaytaramiz.
        """
        return self.faq_group_ids[0] if self.faq_group_ids else None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
