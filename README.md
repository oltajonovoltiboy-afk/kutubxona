# Abu Rayhon Beruniy nomidagi Urganch davlat akademik litseyi — Raqamli kutubxona

Django asosidagi responsiv raqamli kutubxona. Mavjud `index.html` asl nusxasi `catalog/templates/catalog/legacy_index.html` ichida saqlangan; yangi interfeys shu loyiha tarkibida alohida Django template sifatida ishlaydi.

## Hozirgi funksiyalar

- Kitob katalogi, qidiruv, kategoriya/fan/til filtrlari va sahifalash.
- O‘quvchi ro‘yxatdan o‘tishi (ro‘yxatdan o‘tishda foydalanuvchi o‘zi administrator yoki o‘qituvchi rolini tanlay olmaydi).
- Django autentifikatsiyasi, shaxsiy kabinet va sevimli kitoblar.
- PDF.js o‘quvchi, sahifaga o‘tish/kattalashtirish va o‘qish jarayonini serverda saqlash.
- Kitob yuborish (o‘qituvchi/kutubxonachi), moderator tasdig‘i va fayl tekshiruvlari.
- Testlar: administrator savol/javob variantlarini boshqaradi, o‘qituvchi test yaratadi, baholash serverda bajariladi.
- Parolni tiklash oqimi (SMTP sozlanganda email orqali yuborish; lokalda xat konsolga chiqariladi).
- PWA manifest va cheklangan statik offline keshlash; shaxsiy sahifalar keshlanmaydi.
- Katalogga asoslangan “AI kutubxonachi” qidiruv yordamchisi. Bu **tashqi generativ AI modeli emas**; haqiqiy LLM/RAG integratsiyasi uchun alohida API, hujjat indekslash va kalitlarni boshqarish kerak.
- Murojaat formasi, bildirishnomalar modeli, Django admin, CSV/Excel eksporti uchun admin ma’lumotlarini ko‘rish.
- Responsive dizayn, mobil navigatsiya, klaviatura fokuslari va accessible label’lar.

## Windows’da ishga tushirish

Python 3.11+ tavsiya qilinadi.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations catalog
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Brauzerda `http://127.0.0.1:8000/` oching. Administrator yaratish uchun alohida terminalda `create_admin_windows.bat` yoki `python manage.py createsuperuser` buyrug‘ini bajaring. Admin: `http://127.0.0.1:8000/admin/`.

## Testlar

```powershell
python manage.py test
python manage.py check
```

## Docker Compose

1. `.env.example` faylidan `.env` yarating, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_DEBUG=0` va `DB_PASSWORD` qiymatlarini o‘rnating.
2. Ishlab chiqish muhitida bir marta `python manage.py makemigrations catalog` bajaring va hosil bo‘lgan `catalog/migrations/` fayllarini loyiha bilan birga saqlang.
3. `docker compose up --build -d` bilan ishga tushiring. Ilova `127.0.0.1:8000` da tinglaydi; tashqi internetga chiqarish uchun Nginx va HTTPS sozlang.
4. Administrator yaratish: `docker compose exec web python manage.py createsuperuser`.

## PostgreSQL va VPS

1. PostgreSQL bazasi va alohida, cheklangan huquqli DB foydalanuvchisini yarating.
2. `.env` ichida `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` qiymatlarini belgilang.
3. `python manage.py migrate` va `python manage.py collectstatic --noinput` bajaring.
4. Gunicorn’ni systemd orqali ishga tushiring, Nginx reverse proxy va HTTPS sertifikatini sozlang. `runserver` production uchun ishlatilmasin.
5. Media fayllarni web-serverdan himoyalangan storage’da saqlang; foydalanuvchiga PDF berishdan oldin ruxsat tekshirilsin.
6. Zaxira nusxa olish va tiklash jarayonini muntazam sinang. `python manage.py check --deploy` natijalarini production muhitiga moslab bartaraf eting.

## Muhim production ishlar

- Email orqali parolni tiklashni SMTP bilan sozlash (Django password reset view/template hali ulanmagan).
- Rate limiting, login urinishlarini monitoring qilish, admin uchun MFA va fayllarni antivirus bilan tekshirish.
- Tashqi AI API kalitini xavfsiz saqlash va haqiqiy RAG (PDF matnini indekslash, sahifa darajasidagi havolalar, prompt-injection himoyasi) qo‘shish.
- PDF.js kutubxonasini CDN o‘rniga lokal statik fayl sifatida pin qilingan versiyada joylashtirish tavsiya etiladi.
- Litsey brendi/logotipi va tasdiqlangan real kitoblar bilan to‘ldirish.
- Docker orqali yangi bazani birinchi marta ishga tushirishdan oldin migration fayllari yaratilgan va versiya nazoratiga kiritilgan bo‘lsin.
- Ma’lumotlar saqlash, foydalanuvchi roziligi, maxfiylik siyosati va yosh foydalanuvchilar bo‘yicha tartiblarni litsey bilan kelishish.

## Eslatma

Loyiha boshlang‘ich ishlab chiqarishga yaqin kod sifatida tayyorlandi; haqiqiy internet serveriga joylash, SMTP, tashqi AI, virus skaneri, to‘liq CI/CD va penetration test hali alohida sozlashni talab qiladi. Demo kitoblar yoki testlar avtomatik qo‘shilmaydi — administrator ularni boshqaruv panelidan kiritadi.

## PDF ko'rinishida o'qish (yangi)

Qidiruv natijasidagi kitobda «PDF o'qish» / «Onlayn O'qish» tugmasi bosilganda kitob sayt ichida PDF.js
ko'rgazmasida ochiladi (sahifa almashtirish, zoom, oxirgi o'qilgan sahifani eslab qolish).

- `/api/pdf/?url=...` — tashqi PDF ni server orqali beradi (CORS muammosiz). Faqat ruxsat etilgan domenlar:
  ziyouz.com, ziyouz.uz, archive.org, openlibrary.org.
- `/api/pdf-topish/?url=...` — Ziyouz kitob sahifasidan PDF havolasini topadi.
- Qo'shimcha domen ruxsat berish uchun `settings.py` ga `PDF_PROXY_EXTRA_HOSTS = ('example.uz',)` qo'shing.
- Django serversiz (faqat `index.html`, Live Server) ishlaganda ham to'g'ridan-to'g'ri PDF ochishga urinadi,
  bo'lmasa zaxira ko'rgazma ishga tushadi. To'liq ishlashi uchun Django serverni ishga tushiring.


## Onlayn kitob qidiruvi va o‘quvchi

Bosh sahifadagi asosiy qidiruv litsey katalogini tekshiradi va kiritilgan so‘rovni tashqi katalog qidiruviga ham avtomatik yuboradi. Alohida “Onlayn kutubxonalardan qidirish” maydoni ham mavjud. Tashqi qidiruv Ziyouz.uz, Ziyouz.com, n.ziyouz.com, Open Library va Google Books manbalarini tekshiradi. Natijalar 10 daqiqaga keshlanadi. PDF havolalari ruxsat etilgan domenlar ro‘yxati orqali server proksisidan o‘tadi va sayt ichidagi PDF.js o‘quvchisida ochiladi. Boshqa turdagi manbalar asl saytida ochiladi.

Eslatma: tashqi kutubxonalar o‘z serveri, robots siyosati va kitobga berilgan kirish huquqiga bog‘liq. Har bir topilgan kitobning to‘liq PDF nusxasi mavjud bo‘lishi kafolatlanmaydi; mualliflik huquqi va manbaning foydalanish shartlariga rioya qiling.
# kutubxona
