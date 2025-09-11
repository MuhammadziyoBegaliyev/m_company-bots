M Company Help Bot

M Company uchun tayyorlangan, aiogram v3 asosidagi ko‘p tilli (UZ / EN / RU) Telegram yordamchi bot.
Botda xizmatlar, loyihalar, aloqa sahifalari hamda FAQ → Guruh → User oqimi mavjud: foydalanuvchi savoli guruhga tushadi, admin guruhda reply yozadi, bot javobni foydalanuvchi DMiga yuboradi.

Qisqacha: ishlaydigan tizimlar. Real natijalar. Bot ham xuddi shu falsafada yozilgan — ortiqcha gap yo‘q, funksional bor.

📌 Funksional

3 til: Uzbek / English / Russian (app/locales.py)

Bo‘limlar:

Xizmatlar: CRM & Avtomatizatsiya, Vebsayt, Lead Generation, Arxitektura, Target & Sotuv, Call-center

Bizning loyihalar (media bilan): Target Pro, Agroboost, RoboticsLab, iService, Falco, Food Quest, IMAC, TATU

Aloqa: manzil, tel, email, ish vaqti, ijtimoiy tarmoqlar

Biz haqimizda: M Company falsafasi va yondashuvi

FAQ:

Foydalanuvchi savoli M Company Group(lar)i ga yuboriladi

Admin guruhda reply qiladi → bot javobni user DMiga yetkazadi

Inline “Orqaga” tugmalari, ikonlar, tilga mos matnlar

/id komandasi: chat ID ni topish

Loglar: loguru orqali bot.log ga yoziladi

🧱 Texnologiyalar

Python 3.12+

aiogram v3 (asynchronous, typed handlers)

pydantic-settings (sozlamalar, .env)

loguru (loglash)

python-dotenv (ixtiyoriy)

📁 Tuzilma
mcompanyhelpbot/
├─ app/
│  ├─ main.py                # kirish nuqtasi
│  ├─ config.py              # .env dan o‘qish, validatsiya
│  ├─ locales.py             # UZ/EN/RU matnlar
│  ├─ handlers/
│  │  ├─ services.py
│  │  ├─ projects.py
│  │  ├─ faq.py              # FAQ → Group → User oqimi
│  │  └─ ...
│  ├─ keyboards/             # inline/reply tugmalar
│  ├─ storage/
│  │  └─ memory.py           # oddiy til xotirasi (in-memory)
│  └─ ...
├─ requirements.txt
├─ .gitignore
└─ README.md


Klonlash
git clone git@github.com:MuhammadziyoBegaliyev/m_company-bots.git
cd m_company-bots/mcompanyhelpbot



----Ishga tushurish ---
python3 -m app.main


❓ FAQ oqimi qanday ishlaydi?

Foydalanuvchi FAQ bo‘limida “Savol berish ✉️” ni bosadi va matn yuboradi.

Bot savolni M Company Group(lar)iga quyidagi formatda jo‘natadi:

Foydalanuvchi: ism, username, user_id, tanlangan til

Savol matni

“Reply qiling — javob user DMiga ketadi” ko‘rsatmasi

Admin guruhda shu xabarga reply yozadi → bot javobni foydalanuvchi DMiga yuboradi va guruhda “✅ yuborildi” deb tasdiqlaydi.

Eslatma: reply bog‘lanishi xotirada saqlanadi. Process qayta ishga tushsa, eski savol-reply juftliklari bekor bo‘lishi mumkin (production uchun Redis/DB kiritish oson).

🔐 Xavfsizlik

Tokenlar va ID’lar .env da saqlanadi; hech qachon gitga qo‘ymang.

.gitignore ichida .env, venv/, __pycache__/, .log, .db va h.k. ko‘rsatilgan.


🧪 Muammolar va yechimlar

Bad Request: chat not found
FAQ_GROUP_ID(S) noto‘g‘ri / bot guruhga qo‘shilmagan / yozishga ruxsat yo‘q.

query is too old / invalid
Callback’larda await cb.answer() chaqirilganini tekshiring, uzoq bloklamang.

ModuleNotFoundError: aiogram / loguru ...
pip install -r requirements.txt (venv ichida).

Externally managed environment
python3 -m venv .venv && source .venv/bin/activate.

🧩 Kelajakdagi kichik reja

Reply bog‘lashni Redis yoki DB ga ko‘chirish

Admin panel: guruhsiz ham javob berish

Analytics: savollar soni, til bo‘yicha statistika

CI/CD (GitHub Actions) va healthcheck

👤 Muallif haqida 

Muhammadziyo Begaliyev
Telegram: @Muhammadziyo7008
