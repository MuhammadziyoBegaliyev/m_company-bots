# app/config.py
from typing import List, Optional
import re

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices, field_validator


class Settings(BaseSettings):
    # Bot token (BOT_TOKEN yoki bot_token)
    BOT_TOKEN: str = Field(
        ...,
        validation_alias=AliasChoices("BOT_TOKEN", "bot_token"),
    )

    # Adminlar ro‘yxati (vergul bilan): "111,222,-100333"
    # ADMIN_IDS yoki admin_ids orqali berish mumkin
    admin_ids: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ADMIN_IDS", "admin_ids"),
    )

    # FAQ savollari yuboriladigan guruh(lar) ID: bitta yoki bir nechta
    # FAQ_GROUP_ID / faq_group_id (yoki FAQ_GROUP_IDS / faq_group_ids)
    faq_group_ids: List[int] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "FAQ_GROUP_ID",
            "faq_group_id",
            "FAQ_GROUP_IDS",
            "faq_group_ids",
        ),
    )

    # CSV/qatlamlardan int ro‘yxatiga konvertatsiya
    @field_validator("admin_ids", "faq_group_ids", mode="before")
    @classmethod
    def _parse_csv_ints(cls, v):
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
                # faqat signed raqamni tortib olish (mas: '-100123…')
                m = re.match(r"^[-+]?\d+$", part)
                if m:
                    out.append(int(part))
            return out
        return []

    # Backward compatibility: eski kod faq_group_id (bitta) ni o‘qisa — birinchisini qaytaramiz
    @property
    def faq_group_id(self) -> Optional[int]:
        return self.faq_group_ids[0] if self.faq_group_ids else None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
