# -*- coding: utf-8 -*-
# app/locales.py

L = {
    # =========================================================
    # O'ZBEKCHA
    # =========================================================
    "uz": {
        # ---------- Common / Lang ----------
        "choose_lang": "Iltimos, tilni tanlang:",
        "greet_prompt": "Iltimos, tilni tanlang:",
        "lang_ok": "✅ Tanlandi",
        "chosen": "✅ Tanlangan til: O'zbekcha",
        "back_btn": "⬅️ Orqaga",
        "stub": "Bu bo'lim tez orada to'ldiriladi. 🙌",

        # ---------- Main menu (reply buttons) ----------
        "menu_title": "Quyidagi bo'limlardan birini tanlang:",
        "main_menu_placeholder": "Quyidagi bo‘limlardan birini tanlang:",
        "menu_hint": "🟡 Asosiy menyu:",
        "btn_services": "Xizmatlar",
        "btn_projects": "Bizning loyihalar",
        "btn_faq": "Ko'p beriladigan savollar",
        "btn_contact": "Biz bilan bog'laning",
        "btn_about": "Biz haqimizda",
        "btn_audit": "Audit xizmat / Bron",

        # ---------- Welcome ----------
        "welcome_caption": "<b>M company’ga xush kelibsiz!</b>\n\nBiz bilan tezkor aloqa va xizmatlar — barchasi shu yerda.",
        "welcome_btn_about": "ℹ️ Biz haqimizda",
        "welcome_btn_projects": "🧩 Bizning loyihalar",
        "welcome_btn_contact": "☎️ Biz bilan aloqa",
        "welcome_back_to_main": "⬅️ Asosiy menyu",

        # ---------- Onboarding ----------
        "ob_ask_name": "👋 Ismingizni yozing:",
        "ob_ask_phone": (
            "📞 Bog‘lanish uchun ishlaydigan telefon raqamingizni yuboring.\n\n"
            "Eng osoni — «📲 Raqamni ulashish» tugmasini bosing."
        ),
        "ob_share_phone_btn": "📲 Raqamni ulashish",
        "share_phone_btn": "📲 Raqamni ulashish",
        "ob_saved_ok": "✅ Ma’lumotlar saqlandi.",
        "ob_bad_phone": "❗️ Raqam formati noto‘g‘ri. Masalan: +998 90 123 45 67",
        "ob_saved": "✅ Ma’lumotlar saqlandi.",
        # backward-compat kalitlar
        "onb_ask_name": "👋 Ismingizni yozing:",
        "onb_ask_phone": (
            "📞 Bog‘lanish uchun ishlaydigan telefon raqamingizni yuboring.\n\n"
            "Eng osoni — «📲 Raqamni ulashish» tugmasini bosing."
        ),
        "onb_btn_share_phone": "📲 Raqamni ulashish",
        "onb_bad_phone": "❗️ Raqam formati noto‘g‘ri. Masalan: +998 90 123 45 67",
        "onb_saved": "✅ Ma’lumotlar saqlandi.",

        # ---------- Services ----------
        "services_intro": (
            "Har bir xizmat — real natija uchun yaratilgan, maslahat uchun emas.\n\n"
            "Biznes egasi sifatida sizga navbatdagi maslahat emas — ishlaydigan tizimlar kerak. "
            "Quyida bizning asosiy yo'nalishlarimiz bilan tanishing."
        ),
        "svc_more": "Batafsil ↗️",
        "svc_crm": "CRM & Avtomatlashtirish",
        "svc_site": "Veb-sayt va landing",
        "svc_leads": "Lead generation",
        "svc_arch": "Audit / Arxitektura",
        "svc_ads": "Target reklama & sotuv strategiyasi",
        "svc_call": "Call center tizimi & tayyorlov",
        "svc_crm_body": (
            "🤖 <b>Biznesingizni Avtomatlashtirish uchun Tizimlashtirish</b>\n\n"
            "<b>CRM nima?</b> Mijozlar, sotuvlar va jamoani <b>bitta joyda</b> boshqarish tizimi.\n\n"
            "📦 <b>Hammasi bir joyda</b>: kontaktlar, vazifalar, pul aylanmasi, avtomatik xabarlar va h.k.\n\n"
            "🎯 <b>Natija</b>: Nazorat • Avtomatlashtirish • Tezlik • O‘lchov."
        ),
        "svc_site_body": (
            "🕸️ <b>Vebsayt — 24/7 sotuvchi</b>\n"
            "Chiroyli dizayn emas, <b>sotuvchi tizim</b> muhim: jalb qiladi, ishontiradi, sotadi.\n"
            "Paketlar: Tezkor / Pro / Premium (SEO, blog, integratsiyalar, analitika)."
        ),
        "svc_leads_body": (
            "🎯 <b>Lead generatsiya</b>\n"
            "Har kuni <b>filtrlangan, qiziqqan</b> lidlar. Joylashuv, qiziqish va niyat bo‘yicha nishonlash."
        ),
        "svc_arch_body": (
            "🏗️ <b>Audit / Arxitektura</b>\n"
            "🚀 45 daqiqalik bepul sessiya: mavjud tizimlarni tahlil qilamiz, yo‘l xaritasi beramiz."
        ),
        "svc_ads_body": (
            "📢 <b>Target + strategiya</b>\n"
            "To‘g‘ri auditoriya, voronka va skriptlar — natija bo‘yicha optimizatsiya."
        ),
        "svc_call_body": (
            "📞 <b>Call center tizimi</b>\n"
            "Skriptlar, monitoring, hisobotlar va treninglar bilan joriy qilamiz."
        ),

        # ---------- Projects ----------
        "projects_title": "Bizning loyihalar",
        "projects_hint": "Pastdan loyihani tanlang:",
        "project_selected": "Tanlangan loyiha: {name}",
        "prj_target_pro": "Target Pro",
        "prj_agroboost": "Agroboost",
        "prj_roboticslab": "RoboticsLab",
        "prj_iservice": "iService CRM",
        "prj_falco": "Falco",
        "prj_food_quest": "Food Quest For Your Taste",
        "prj_imac": "International Molecular Allergology Center",
        "prj_tatu": "Toshkent ATU (TATU)",
        "prj_fresh_line": "Fresh Line",
        "prj_target_pro_body": "Target reklama va sotuv strategiyasi bo‘yicha kompleks yechimlar.",
        "prj_agroboost_body": "Agro yo‘nalishida avtomatlashtirish va CRM.",
        "prj_roboticslab_body": "Robototexnika va STEM loyihalari platformasi.",
        "prj_iservice_body": "Servis kompaniyalarga mos CRM va ichki jarayonlar boshqaruvi.",
        "prj_falco_body": "Talantlarni kuchaytirish va startaplar fabrikasi.",
        "prj_food_quest_body": "Qidiruv va buyurtma qulayliklari bilan ovqat servisi ekotizimi.",
        "prj_imac_body": "Tibbiy markaz uchun CRM, navbat va hisobot yechimlari.",
        "prj_tatu_body": "Talabalar uchun raqamli platformalar va boshqaruv tizimlari.",
        "prj_fresh_line_body": "Yangi brendlar uchun marketing va IT tezkor start paketi.",

        # ---------- FAQ ----------
        "faq_title": "Ko‘p beriladigan savollar (FAQ)",
        "faq_btn_ask": "Savol berish",
        "faq_ask_prompt": "✍️ Savolingizni yozib yuboring.",
        "faq_ask_received": "✅ Savolingiz qabul qilindi. Tez orada javob beramiz.",
        "faq_no_admin": "Hozircha adminlar ulanmagan. Keyinroq urinib ko‘ring.",
        "faq_q1": "Qanday bizneslar bilan ishlaysiz?",
        "faq_a1": "Kichik do‘konlardan yirik korxonalargacha — real o‘sishni xohlaganlar bilan.",
        "faq_q2": "Marketing agentligidan nimasi bilan farq qiladi?",
        "faq_a2": "Biz xizmat sotmaymiz, tizimlar quramiz: voronka, CRM, avtomatlashtirish, lead’lar.",
        "faq_q3": "Moslashtirasizmi?",
        "faq_a3": "Albatta. Har bir yechim biznesingizga moslanadi.",
        "faq_q4": "Narxlar qanday?",
        "faq_a4": "Loyihaga qarab. Ba’zilar $500 dan, murakkablari yuqoriroq. Bepul auditdan boshlang.",
        "faq_q5": "Natijani qachon ko‘raman?",
        "faq_a5": "Ko‘pchilik 30 kun ichida sezadi.",
        "faq_q6": "Faqat bitta xizmat tanlasam bo‘ladimi?",
        "faq_a6": "Ha, masalan faqat sayt yoki CRM bilan boshlash mumkin.",
        "faq_q7": "Bepul audittan keyin nima bo‘ladi?",
        "faq_a7": "Aniq yo‘l xaritasi va taklif beramiz — majburiyatsiz.",

        # ---------- Contact ----------
        "contact_title": "Biz bilan bog‘laning",
        "contact_addr_btn": "Ofis manzilimiz",
        "contact_email_btn": "Pochta orqali yozish",
        "contact_call_btn": "To‘g‘ridan-to‘g‘ri bog‘lanish",
        "contact_hours_btn": "Ish vaqti",
        "contact_social_btn": "Ijtimoiy tarmoqlar",
        "contact_address_text": "Bog‘ishamol ko‘chasi, Yunusobod, Toshkent",
        "open_in_maps_btn": "Xaritada ochish",
        "contact_more_opts": "Kerakli bo‘limni tanlang:",
        "contact_email_text": "Bizga: info@mcompany.uz",
        "contact_phone_text": "+998 (90) 808-6383",
        "call_now_btn": "📞 Qo‘ng‘iroq qilish",
        "open_in_gmail_btn": "📨 Gmail’da yozish",
        "contact_hours_text": (
            "🕒 Haftalik jadval:\n"
            "Dush–Juma (⚡ Fokus): 09:00–18:00\n"
            "Shanba (🌟 Qulay xizmat): 09:00–18:00\n"
            "Yakshanba (😴 Dam olish): Dam olish kuni\n"
        ),
        "contact_social_title": "Ijtimoiy tarmoqlarimiz:",
        "contact_tg_text": "@Narkuziyev — M Company General Manager",

        # ---------- Audit / Booking ----------
        "audit_title": "🧪 Audit xizmatlari",
        "audit_choose": "Quyidagidan birini tanlang:",
        "audit_web": "🌐 Veb-sayt",
        "audit_book": "🗓️ Bron",
        "audit_web_desc": (
            "🌐 <b>Audit xizmati — biznesingizni tahlil qilish va aniq yo‘l xaritasi</b>\n\n"
            "— Biznes jarayonlar tahlili\n"
            "— Voronka, CRM, avtomatizatsiya bo‘yicha takliflar\n"
            "— Natijaga yo‘naltirilgan reja"
        ),
        "more_btn": "Batafsil",

        "aud_ask_biz_name": "🏢 Biznes nomini yozing:",
        "aud_ask_biz_desc": "📝 Biznes tafsilotini qisqacha yozing:",
        "aud_ask_revenue": "💰 Oylik daromad diapazonini tanlang:",
        "aud_rev_low": "0–$5k",
        "aud_rev_mid": "$5k–$20k",
        "aud_rev_high": "$20k+",
        "aud_pick_month": "📅 Oy tanlang:",
        "aud_pick_day": "📆 Kun tanlang:",
        "aud_pick_time": "⏰ Vaqt tanlang (08:00–19:00, 1 soat oralig‘ida):",
        "aud_time_manual": "⌨️ Qo‘lda kiritish",
        "aud_enter_time_prompt": "⌨️ Vaqtni <b>HH:MM</b> ko‘rinishida yuboring (masalan 14:00):",
        "aud_time_invalid": "❗️ Noto‘g‘ri vaqt. Iltimos HH:MM formatida yuboring (08:00–19:00 oralig‘ida).",
        "aud_review_title": "✅ Tekshirib tasdiqlang:",
        "aud_review_confirm": "✅ Tasdiqlash",
        "aud_review_edit": "✏️ O‘zgartirish",
        "aud_review_cancel": "❌ Rad etish",
        "aud_edit_which": "Qaysi qismni o‘zgartirasiz?",
        "aud_edit_biz_name": "🏢 Biznes nomi",
        "aud_edit_biz_desc": "📝 Biznes tafsiloti",
        "aud_edit_revenue": "💰 Oylik daromad",
        "aud_edit_datetime": "📅 Sana & vaqt",
        "aud_sent_to_admins": "📨 So‘rovingiz adminga yuborildi. Javobni kuting.",
        "aud_canceled": "❌ So‘rov bekor qilindi.",

        # Adminlar uchun audit kartasi va xabarlari
        "aud_admin_title": "🧪 Audit bron so‘rovi",
        "aud_admin_approve": "✅ Tasdiqlash",
        "aud_admin_retime": "⏰ Vaqtni o‘zgartirish",
        "aud_admin_cancel": "🛑 Bekor qilish",
        "aud_user_approved": "✅ So‘rovingiz tasdiqlandi!",
        "aud_user_retime": "⏰ Admin vaqtni o‘zgartirishni so‘radi. Iltimos yangi vaqtni HH:MM ko‘rinishida yuboring:",
        "aud_user_canceled": "🛑 So‘rovingiz bekor qilindi.",

        # ---------- Admin panel ----------
        "adm_not_admin": "❌ Siz admin emassiz.",
        "adm_send_msg": "Xabar yuborish",
        "adm_users_list": "Foydalanuvchilar roʻyxati",
        "adm_send_choose": "Qaysi turdagi xabar?",
        "adm_send_one": "1 foydalanuvchi",
        "adm_send_all": "Hammaga",
        "adm_ask_user": "ID yoki @username yuboring (yoki xabarini forward qiling):",
        "adm_send_media": "Rasm yoki video jo‘nating (ixtiyoriy).",
        "adm_skip_or_send": "Yoki ⏭ O‘tkazib yuborish tugmasini bosing:",
        "skip_btn": "O‘tkazib yuborish",
        "adm_ask_text": "Matn/caption kiriting (ixtiyoriy).",
        "send_btn": "Yuborish",
        "edit_btn": "O‘zgartirish",
        "cancel_btn": "Bekor qilish",
        "adm_broadcast_canceled": "Yuborish bekor qilindi.",
        "adm_broadcast_done": "Tarqatma yakunlandi. ✅: {ok}, ❌: {fail}",
        "adm_user_not_found": "Foydalanuvchi topilmadi.",
        "adm_user_show_btn": "Foydalanuvchini ko‘rish",
        "adm_find_prompt": "Forward / @username / user_id yuboring:",
        "adm_msg_this_user": "Shu foydalanuvchiga yozish",
    },

    # =========================================================
    # ENGLISH
    # =========================================================
    "en": {
        # ---------- Common / Lang ----------
        "choose_lang": "Please choose your language:",
        "greet_prompt": "Please choose your language:",
        "lang_ok": "✅ Saved",
        "chosen": "✅ Selected language: English",
        "back_btn": "⬅️ Back",
        "stub": "This section will be filled soon. 🙌",

        # ---------- Main menu ----------
        "menu_title": "Please choose a section:",
        "main_menu_placeholder": "Please choose a section:",
        "menu_hint": "🟡 Main menu:",
        "btn_services": "Services",
        "btn_projects": "Our projects",
        "btn_faq": "FAQ",
        "btn_contact": "Contact us",
        "btn_about": "About us",
        "btn_audit": "Audit / Booking",

        # ---------- Welcome ----------
        "welcome_caption": "<b>Welcome to M company!</b>\n\nQuick contact & services — all here.",
        "welcome_btn_about": "ℹ️ About us",
        "welcome_btn_projects": "🧩 Our projects",
        "welcome_btn_contact": "☎️ Contact us",
        "welcome_back_to_main": "⬅️ Main menu",

        # ---------- Onboarding ----------
        "ob_ask_name": "👋 Please enter your full name:",
        "ob_ask_phone": (
            "📞 Send your active phone number for contact.\n\n"
            "Easiest — tap «📲 Share phone»."
        ),
        "ob_share_phone_btn": "📲 Share phone",
        "share_phone_btn": "📲 Share phone",
        "ob_saved_ok": "✅ Saved.",
        "ob_bad_phone": "❗️ Invalid phone format. Example: +1 415 555 2671",
        "ob_saved": "✅ Saved.",
        # compatibility
        "onb_ask_name": "👋 Please enter your full name:",
        "onb_ask_phone": (
            "📞 Send your active phone number for contact.\n\n"
            "Easiest — tap «📲 Share phone»."
        ),
        "onb_btn_share_phone": "📲 Share phone",
        "onb_bad_phone": "❗️ Invalid phone format. Example: +1 415 555 2671",
        "onb_saved": "✅ Saved.",

        # ---------- Services ----------
        "services_intro": (
            "Every service is built for real results — not just advice.\n\n"
            "You need working systems. Explore our core directions below."
        ),
        "svc_more": "More ↗️",
        "svc_crm": "CRM & Automation",
        "svc_site": "Website & landing",
        "svc_leads": "Lead generation",
        "svc_arch": "Audit / Architecture",
        "svc_ads": "Target ads & sales strategy",
        "svc_call": "Call-center system & training",
        "svc_crm_body": (
            "🤖 <b>Automation & CRM</b>\n\n"
            "One place to manage customers, sales and team.\n"
            "🎯 Result: Control • Automation • Speed • Measurement."
        ),
        "svc_site_body": (
            "🕸️ <b>Website — your 24/7 sales engine</b>\n"
            "Not only design but a system that attracts, convinces and sells."
        ),
        "svc_leads_body": (
            "🎯 <b>Lead generation</b>\n"
            "Daily flow of filtered, interested leads with proper targeting."
        ),
        "svc_arch_body": (
            "🏗️ <b>Audit / Architecture</b>\n"
            "🚀 Free 45-min session with a tailored roadmap."
        ),
        "svc_ads_body": (
            "📢 <b>Targeted ads & sales strategy</b>\n"
            "Right audience, funnel & scripts — optimized for outcomes."
        ),
        "svc_call_body": (
            "📞 <b>Call-center system</b>\n"
            "Scripts, monitoring, reports and team training."
        ),

        # ---------- Projects ----------
        "projects_title": "Our projects",
        "projects_hint": "Pick a project below:",
        "project_selected": "Selected project: {name}",
        "prj_target_pro": "Target Pro",
        "prj_agroboost": "Agroboost",
        "prj_roboticslab": "RoboticsLab",
        "prj_iservice": "iService CRM",
        "prj_falco": "Falco",
        "prj_food_quest": "Food Quest For Your Taste",
        "prj_imac": "International Molecular Allergology Center",
        "prj_tatu": "Tashkent University of Information Technologies (TUIT)",
        "prj_fresh_line": "Fresh Line",
        "prj_target_pro_body": "Full-stack solution for paid traffic and sales strategy.",
        "prj_agroboost_body": "Automation and CRM for agricultural businesses.",
        "prj_roboticslab_body": "Platform and community for robotics & STEM projects.",
        "prj_iservice_body": "Orders and workforce management for service companies.",
        "prj_falco_body": "Community & startup factory turning ideas into real products.",
        "prj_food_quest_body": "Food service ecosystem with smart search and ordering.",
        "prj_imac_body": "CRM, queue and reporting for a medical center.",
        "prj_tatu_body": "Digital platforms and management systems for students.",
        "prj_fresh_line_body": "Fast start pack for new brands: marketing + IT.",

        # ---------- FAQ ----------
        "faq_title": "Frequently Asked Questions (FAQ)",
        "faq_btn_ask": "Ask a question",
        "faq_ask_prompt": "✍️ Send your question.",
        "faq_ask_received": "Your question has been received!",
        "faq_no_admin": "Admins are not configured yet. Please try later.",
        "faq_q1": "What kinds of businesses do you work with?",
        "faq_a1": "From small shops to enterprises — owners who want real growth.",
        "faq_q2": "How are you different from a marketing agency?",
        "faq_a2": "We build systems (funnels/CRM/automation), not one-off services.",
        "faq_q3": "Are your services customized?",
        "faq_a3": "Yes. Every solution is tailored.",
        "faq_q4": "How much does it cost?",
        "faq_a4": "Depends on scope. Some start from $500. Start with a free audit.",
        "faq_q5": "When will I see results?",
        "faq_a5": "Most clients notice changes within 30 days.",
        "faq_q6": "Can I choose only one service?",
        "faq_a6": "Sure — website, CRM, etc.",
        "faq_q7": "What happens after the free audit?",
        "faq_a7": "You get a clear growth plan without obligation.",

        # ---------- Contact ----------
        "contact_title": "Contact us",
        "contact_addr_btn": "Our office address",
        "contact_email_btn": "Write via email",
        "contact_call_btn": "Contact directly",
        "contact_hours_btn": "Working hours",
        "contact_social_btn": "Our social links",
        "contact_address_text": "Bog‘ishamol Street, Yunusabad, Tashkent",
        "open_in_maps_btn": "Open in Maps",
        "contact_more_opts": "Choose an option:",
        "contact_email_text": "info@mcompany.uz",
        "contact_phone_text": "+998 (90) 808-6383",
        "call_now_btn": "📞 Call now",
        "open_in_gmail_btn": "📨 Open in Gmail",
        "contact_hours_text": (
            "🕒 Weekly hours:\n"
            "Mon–Fri (⚡ Focus mode): 09:00–18:00\n"
            "Saturday (🌟 Easy service): 09:00–18:00\n"
            "Sunday (😴 Recharge day): Closed\n"
        ),
        "contact_social_title": "Our social links:",
        "contact_tg_text": "@Narkuziyev — M Company General Manager",

        # ---------- Audit / Booking ----------
        "audit_title": "🧪 Audit Services",
        "audit_choose": "Choose one:",
        "audit_web": "🌐 Website",
        "audit_book": "🗓️ Book",
        "audit_web_desc": (
            "🌐 <b>Audit — business diagnostics & clear roadmap</b>\n\n"
            "— Process analysis\n"
            "— Funnel, CRM, automation recommendations\n"
            "— Outcome-focused plan"
        ),
        "more_btn": "More",
        "aud_ask_biz_name": "🏢 Enter your business name:",
        "aud_ask_biz_desc": "📝 Briefly describe your business:",
        "aud_ask_revenue": "💰 Select monthly revenue range:",
        "aud_rev_low": "0–$5k",
        "aud_rev_mid": "$5k–$20k",
        "aud_rev_high": "$20k+",
        "aud_pick_month": "📅 Choose a month:",
        "aud_pick_day": "📆 Choose a day:",
        "aud_pick_time": "⏰ Choose a time (08:00–19:00, every 1h):",
        "aud_time_manual": "⌨️ Enter manually",
        "aud_enter_time_prompt": "⌨️ Send time in <b>HH:MM</b> (e.g. 14:00):",
        "aud_time_invalid": "❗️ Invalid time. Please use HH:MM (between 08:00 and 19:00).",
        "aud_review_title": "✅ Review and confirm:",
        "aud_review_confirm": "✅ Confirm",
        "aud_review_edit": "✏️ Edit",
        "aud_review_cancel": "❌ Cancel",
        "aud_edit_which": "Which part to edit?",
        "aud_edit_biz_name": "🏢 Business name",
        "aud_edit_biz_desc": "📝 Business details",
        "aud_edit_revenue": "💰 Monthly revenue",
        "aud_edit_datetime": "📅 Date & time",
        "aud_sent_to_admins": "📨 Your request was sent to admins. Please wait.",
        "aud_canceled": "❌ Request canceled.",
        "aud_admin_title": "🧪 Audit booking request",
        "aud_admin_approve": "✅ Approve",
        "aud_admin_retime": "⏰ Change time",
        "aud_admin_cancel": "🛑 Cancel",
        "aud_user_approved": "✅ Your booking has been approved!",
        "aud_user_retime": "⏰ Admin asked to change time. Please send a new HH:MM:",
        "aud_user_canceled": "🛑 Your booking was canceled.",

        # ---------- Admin panel ----------
        "adm_not_admin": "❌ You are not an admin.",
        "adm_send_msg": "Send message",
        "adm_users_list": "Users list",
        "adm_send_choose": "What kind of message?",
        "adm_send_one": "One user",
        "adm_send_all": "Broadcast",
        "adm_ask_user": "Send ID or @username (or forward his message):",
        "adm_send_media": "Send a photo/video (optional).",
        "adm_skip_or_send": "Or press ⏭ Skip:",
        "skip_btn": "Skip",
        "adm_ask_text": "Send text/caption (optional).",
        "send_btn": "Send",
        "edit_btn": "Edit",
        "cancel_btn": "Cancel",
        "adm_broadcast_canceled": "Broadcast canceled.",
        "adm_broadcast_done": "Broadcast finished. ✅: {ok}, ❌: {fail}",
        "adm_user_not_found": "User not found.",
        "adm_user_show_btn": "Find user",
        "adm_find_prompt": "Send forward / @username / user_id:",
        "adm_msg_this_user": "Message this user",
    },

    # =========================================================
    # RUSSIAN
    # =========================================================
    "ru": {
        # ---------- Common / Lang ----------
        "choose_lang": "Пожалуйста, выберите язык:",
        "greet_prompt": "Пожалуйста, выберите язык:",
        "lang_ok": "✅ Сохранено",
        "chosen": "✅ Выбранный язык: Русский",
        "back_btn": "⬅️ Назад",
        "stub": "Раздел скоро будет заполнен. 🙌",

        # ---------- Main menu ----------
        "menu_title": "Пожалуйста, выберите раздел:",
        "main_menu_placeholder": "Пожалуйста, выберите раздел:",
        "menu_hint": "🟡 Главное меню:",
        "btn_services": "Услуги",
        "btn_projects": "Наши проекты",
        "btn_faq": "FAQ",
        "btn_contact": "Связаться с нами",
        "btn_about": "О нас",
        "btn_audit": "Аудит / Бронь",

        # ---------- Welcome ----------
        "welcome_caption": "<b>Добро пожаловать в M company!</b>\n\nБыстрая связь и услуги — всё здесь.",
        "welcome_btn_about": "ℹ️ О нас",
        "welcome_btn_projects": "🧩 Наши проекты",
        "welcome_btn_contact": "☎️ Связаться с нами",
        "welcome_back_to_main": "⬅️ Главное меню",

        # ---------- Onboarding ----------
        "ob_ask_name": "👋 Введите ваше полное имя:",
        "ob_ask_phone": (
            "📞 Отправьте рабочий номер телефона для связи.\n\n"
            "Проще всего — нажать «📲 Поделиться номером»."
        ),
        "ob_share_phone_btn": "📲 Поделиться номером",
        "share_phone_btn": "📲 Поделиться номером",
        "ob_saved_ok": "✅ Сохранено.",
        "ob_bad_phone": "❗️ Неверный формат номера. Пример: +7 999 123 45 67",
        "ob_saved": "✅ Данные сохранены.",
        # compatibility
        "onb_ask_name": "👋 Введите ваше полное имя:",
        "onb_ask_phone": (
            "📞 Отправьте рабочий номер телефона для связи.\n\n"
            "Проще всего — нажать «📲 Поделиться номером»."
        ),
        "onb_btn_share_phone": "📲 Поделиться номером",
        "onb_bad_phone": "❗️ Неверный формат номера. Пример: +7 999 123 45 67",
        "onb_saved": "✅ Данные сохранены.",

        # ---------- Services ----------
        "services_intro": (
            "Каждая услуга создана ради результата, а не ради советов.\n\n"
            "Вам нужны работающие системы. Ниже — основные направления."
        ),
        "svc_more": "Подробнее ↗️",
        "svc_crm": "CRM и автоматизация",
        "svc_site": "Сайт и лендинг",
        "svc_leads": "Лидогенерация",
        "svc_arch": "Аудит / Архитектура",
        "svc_ads": "Таргет и стратегия продаж",
        "svc_call": "Колл-центр и обучение",
        "svc_crm_body": (
            "🤖 <b>Автоматизация и CRM</b>\n\n"
            "Единая система клиентов, продаж и команды.\n"
            "🎯 Результат: Контроль • Автоматизация • Скорость • Измеримость."
        ),
        "svc_site_body": (
            "🕸️ <b>Сайт — продавец 24/7</b>\n"
            "Не просто дизайн, а система, что привлекает, убеждает и продаёт."
        ),
        "svc_leads_body": (
            "🎯 <b>Лидогенерация</b>\n"
            "Ежедневный поток фильтрованных, заинтересованных лидов."
        ),
        "svc_arch_body": (
            "🏗️ <b>Аудит / Архитектура</b>\n"
            "🚀 Бесплатная 45-мин сессия и дорожная карта."
        ),
        "svc_ads_body": (
            "📢 <b>Таргет + стратегия продаж</b>\n"
            "Точная аудитория, воронка и скрипты — оптимизация под результат."
        ),
        "svc_call_body": (
            "📞 <b>Колл-центр</b>\n"
            "Скрипты, мониторинг, отчёты и обучение команды."
        ),

        # ---------- Projects ----------
        "projects_title": "Наши проекты",
        "projects_hint": "Выберите проект ниже:",
        "project_selected": "Выбранный проект: {name}",
        "prj_target_pro": "Target Pro",
        "prj_agroboost": "Agroboost",
        "prj_roboticslab": "RoboticsLab",
        "prj_iservice": "iService CRM",
        "prj_falco": "Falco",
        "prj_food_quest": "Food Quest For Your Taste",
        "prj_imac": "International Molecular Allergology Center",
        "prj_tatu": "Ташкентский университет ИТ (ТУИТ)",
        "prj_fresh_line": "Fresh Line",
        "prj_target_pro_body": "Комплекс по таргет-рекламе и стратегии продаж.",
        "prj_agroboost_body": "Автоматизация и CRM для агробизнеса.",
        "prj_roboticslab_body": "Платформа и сообщество робототехники и STEM.",
        "prj_iservice_body": "Управление заказами и персоналом для сервис-компаний.",
        "prj_falco_body": "Сообщество и фабрика стартапов — идеи в реальные продукты.",
        "prj_food_quest_body": "Экосистема фуд-сервиса с умным поиском и заказом.",
        "prj_imac_body": "CRM, электронная очередь и отчётность для медцентра.",
        "prj_tatu_body": "Цифровые платформы и системы управления для студентов.",
        "prj_fresh_line_body": "Быстрый старт для новых брендов: маркетинг + IT.",

        # ---------- FAQ ----------
        "faq_title": "Частые вопросы (FAQ)",
        "faq_btn_ask": "Задать вопрос",
        "faq_ask_prompt": "✍️ Отправьте ваш вопрос.",
        "faq_ask_received": "Ваш вопрос получен!",
        "faq_no_admin": "Администраторы ещё не подключены. Попробуйте позже.",
        "faq_q1": "С какими бизнесами вы работаете?",
        "faq_a1": "От небольших магазинов до крупных компаний — с теми, кто хочет роста.",
        "faq_q2": "Чем вы отличаетесь от маркетингового агентства?",
        "faq_a2": "Мы строим системы (воронки/CRM/автоматизация), а не разовые услуги.",
        "faq_q3": "Услуги индивидуализируются?",
        "faq_a3": "Да, каждое решение адаптируем.",
        "faq_q4": "Сколько это стоит?",
        "faq_a4": "Зависит от объёма. Часть проектов от $500. Начните с бесплатного аудита.",
        "faq_q5": "Когда будут результаты?",
        "faq_a5": "Обычно изменения заметны в течение 30 дней.",
        "faq_q6": "Можно выбрать только одну услугу?",
        "faq_a6": "Да — например, только сайт или CRM.",
        "faq_q7": "Что после бесплатного аудита?",
        "faq_a7": "Получите чёткий план роста без обязательств.",

        # ---------- Contact ----------
        "contact_title": "Свяжитесь с нами",
        "contact_addr_btn": "Адрес офиса",
        "contact_email_btn": "Написать на почту",
        "contact_call_btn": "Связаться напрямую",
        "contact_hours_btn": "Часы работы",
        "contact_social_btn": "Мы в соцсетях",
        "contact_address_text": "улица Богишамол, Юнусабад, Ташкент",
        "open_in_maps_btn": "Открыть в картах",
        "contact_more_opts": "Выберите нужный раздел:",
        "contact_email_text": "info@mcompany.uz",
        "contact_phone_text": "+998 (90) 808-6383",
        "call_now_btn": "📞 Позвонить",
        "open_in_gmail_btn": "📨 Открыть в Gmail",
        "contact_hours_text": (
            "🕒 График недели:\n"
            "Пн–Пт (⚡ Фокус): 09:00–18:00\n"
            "Суббота (🌟 Удобно): 09:00–18:00\n"
            "Воскресенье (😴 Перезагрузка): Выходной\n"
        ),
        "contact_social_title": "Наши соцсети:",
        "contact_tg_text": "@Narkuziyev — M Company General Manager",

        # ---------- Audit / Booking ----------
        "audit_title": "🧪 Услуги аудита",
        "audit_choose": "Выберите:",
        "audit_web": "🌐 Веб-сайт",
        "audit_book": "🗓️ Забронировать",
        "audit_web_desc": (
            "🌐 <b>Аудит — диагностика бизнеса и четкая дорожная карта</b>\n\n"
            "— Анализ процессов\n"
            "— Рекомендации по воронке, CRM, автоматизации\n"
            "— План, ориентированный на результат"
        ),
        "more_btn": "Подробнее",
        "aud_ask_biz_name": "🏢 Название бизнеса:",
        "aud_ask_biz_desc": "📝 Краткое описание бизнеса:",
        "aud_ask_revenue": "💰 Укажите месячный оборот:",
        "aud_rev_low": "0–$5k",
        "aud_rev_mid": "$5k–$20k",
        "aud_rev_high": "$20k+",
        "aud_pick_month": "📅 Выберите месяц:",
        "aud_pick_day": "📆 Выберите день:",
        "aud_pick_time": "⏰ Выберите время (08:00–19:00, шаг 1ч):",
        "aud_time_manual": "⌨️ Ввести вручную",
        "aud_enter_time_prompt": "⌨️ Отправьте время в формате <b>HH:MM</b> (например 14:00):",
        "aud_time_invalid": "❗️ Неверный формат. Используйте HH:MM (между 08:00 и 19:00).",
        "aud_review_title": "✅ Проверьте и подтвердите:",
        "aud_review_confirm": "✅ Подтвердить",
        "aud_review_edit": "✏️ Изменить",
        "aud_review_cancel": "❌ Отменить",
        "aud_edit_which": "Что изменить?",
        "aud_edit_biz_name": "🏢 Название",
        "aud_edit_biz_desc": "📝 Описание",
        "aud_edit_revenue": "💰 Оборот",
        "aud_edit_datetime": "📅 Дата и время",
        "aud_sent_to_admins": "📨 Запрос отправлен администраторам. Ожидайте.",
        "aud_canceled": "❌ Запрос отменен.",
        "aud_admin_title": "🧪 Запрос на бронь аудита",
        "aud_admin_approve": "✅ Подтвердить",
        "aud_admin_retime": "⏰ Сменить время",
        "aud_admin_cancel": "🛑 Отменить",
        "aud_user_approved": "✅ Ваша бронь одобрена!",
        "aud_user_retime": "⏰ Админ запросил новое время. Отправьте HH:MM:",
        "aud_user_canceled": "🛑 Ваша бронь отменена.",

        # ---------- Admin panel ----------
        "adm_not_admin": "❌ Вы не администратор.",
        "adm_send_msg": "Отправить сообщение",
        "adm_users_list": "Список пользователей",
        "adm_send_choose": "Какой тип сообщения?",
        "adm_send_one": "Одному пользователю",
        "adm_send_all": "Всем (рассылка)",
        "adm_ask_user": "Отправьте ID или @username (или перешлите его сообщение):",
        "adm_send_media": "Отправьте фото/видео (по желанию).",
        "adm_skip_or_send": "Либо нажмите ⏭ Пропустить:",
        "skip_btn": "Пропустить",
        "adm_ask_text": "Отправьте текст/подпись (по желанию).",
        "send_btn": "Отправить",
        "edit_btn": "Изменить",
        "cancel_btn": "Отменить",
        "adm_broadcast_canceled": "Рассылка отменена.",
        "adm_broadcast_done": "Рассылка завершена. ✅: {ok}, ❌: {fail}",
        "adm_user_not_found": "Пользователь не найден.",
        "adm_user_show_btn": "Посмотреть пользователя",
        "adm_find_prompt": "Отправьте forward / @username / user_id:",
        "adm_msg_this_user": "Написать этому пользователю",
    },
}
