# app/handlers/__init__.py
# Barcha handler modullarni import qilamiz va bitta setup() orqali ulaymiz.

from aiogram import Dispatcher

# Mavjud handler modullarni shu yerda import qiling:
from . import lang
from . import onboarding
from . import main_menu
from . import services
from . import projects
from . import faq
# agar boshqalar bo‘lsa, xuddi shunday qo‘shing:
# from . import contact
# from . import about

# Routerlar ro‘yxati tartib bilan:
ALL_ROUTERS = (
    lang.router,
    onboarding.router,
    main_menu.router,
    services.router,
    projects.router,
    faq.router,
    # contact.router,
    # about.router,
)

def setup(dp: Dispatcher) -> None:
    """Routerlarni dispetcherga faqat bir marta ulaydi."""
    for r in ALL_ROUTERS:
        # Agar router hali ulanmagan bo‘lsa, parent_router None bo‘ladi
        if getattr(r, "parent_router", None) is None:
            dp.include_router(r)
