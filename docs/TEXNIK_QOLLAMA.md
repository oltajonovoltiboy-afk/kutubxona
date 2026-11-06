# Abu Rayhon Beruniy nomidagi Urganch davlat akademik litseyi  
## Raqamli kutubxona — Texnik qo‘llanma

**Versiya:** 1.0  
**Til:** O‘zbek (lotin)

---

## 1. Loyiha tuzilmasi

```
urganch-raqamli-kutubxona/
├── manage.py
├── library_project/          # Django project sozlamalari
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── catalog/                  # Asosiy ilova
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── admin.py
│   ├── tests.py
│   ├── templates/
│   ├── static/
│   └── migrations/
├── docs/                     # Qo‘llanmalar (ushbu papka)
├── deploy/                   # Production skriptlari
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── start_windows.bat
├── create_admin_windows.bat
├── start_linux.sh
└── README.md
```

---

## 2. Texnologiyalar

| Qatlam          | Texnologiya                  |
|-----------------|------------------------------|
| Backend         | Python 3.11+, Django 5.2     |
| Ma’lumotlar bazasi | SQLite (dev), PostgreSQL (prod) |
| Frontend        | HTML5, CSS3, JavaScript, Bootstrap 5 |
| PDF o‘qish      | PDF.js                       |
| Statik fayllar  | WhiteNoise / Nginx           |
| Production      | Gunicorn + Nginx             |
| Konteyner       | Docker / Docker Compose      |

---

## 3. O‘rnatish (qisqacha)

### Windows

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

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations catalog
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Docker

```bash
cp .env.example .env
# .env ni tahrirlang
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

---

## 4. Muhit o‘zgaruvchilari (.env)

| O‘zgaruvchi            | Tavsif                              | Misol                          |
|------------------------|-------------------------------------|--------------------------------|
| DJANGO_SECRET_KEY      | Maxfiy kalit                        | uzun tasodifiy satr            |
| DJANGO_DEBUG           | Debug rejimi (0 yoki 1)             | 0 (production)                 |
| DJANGO_ALLOWED_HOSTS   | Ruxsat etilgan hostlar              | 127.0.0.1,localhost,domain.uz  |
| DB_NAME                | PostgreSQL baza nomi (bo‘sh = SQLite) | library_db                   |
| DB_USER                | DB foydalanuvchi                    | library_user                   |
| DB_PASSWORD            | DB parol                            | kuchli_parol                   |
| DB_HOST                | DB host                             | 127.0.0.1                      |
| DB_PORT                | DB port                             | 5432                           |

---

## 5. Asosiy buyruqlar

```bash
# Migratsiya
python manage.py makemigrations
python manage.py migrate

# Superuser
python manage.py createsuperuser

# Testlar
python manage.py test
python manage.py check

# Statik fayllar (production)
python manage.py collectstatic --noinput

# Server
python manage.py runserver
```

---

## 6. Xavfsizlik eslatmalari

- Productionda `DEBUG=False` qiling.
- `SECRET_KEY` ni hech qachon kodga yozmang.
- Media fayllarni to‘g‘ridan-to‘g‘ri ochiq qoldirmang.
- CSRF, XSS va SQL injection himoyalari Django tomonidan ta’minlanadi.
- Fayl yuklashda MIME turi, hajm va kengaytma tekshiriladi.
- Login urinishlariga cheklov qo‘yish tavsiya etiladi (qo‘shimcha middleware yoki django-axes).

---

## 7. Zaxira nusxa

PostgreSQL uchun:

```bash
# deploy/backup_postgres.sh skriptidan foydalaning
# yoki
pg_dump -U library_user library_db > backup_$(date +%Y%m%d).sql
```

SQLite uchun oddiy fayl nusxasini oling (`db.sqlite3`).

---

## 8. Testlash

```bash
python manage.py test catalog
```

Testlar ro‘yxatdan o‘tish, login, kitob qidirish, sevimlilar, o‘qish tarixi va ruxsatlar tekshiruvlarini o‘z ichiga oladi.

---

## 9. Ma’lumotlar bazasi modellari (asosiy)

- CustomUser / User (rol, profil)
- Book
- Category
- Author (agar alohida)
- Favorite
- ReadingProgress / ReadingSession
- LoginEvent
- Quiz / Question / Answer (testlar)
- AuditLog (agar mavjud)

Batafsil maydonlar uchun `catalog/models.py` faylini ko‘ring.

---

## 10. Tashqi API’lar

Loyihada Open Library, Google Books va Gutendex kabi tashqi API’lar uchun integratsiya tayyorlangan bo‘lishi mumkin.  
API kalitlari `.env` da saqlanadi va frontendga ochilmaydi.  
API ishlamasa, sayt to‘xtab qolmaydi — fallback xabarlar ko‘rsatiladi.

---

## 11. Qo‘shimcha hujjatlar

- `README.md` — asosiy o‘rnatish
- `docs/FOYDALANUVCHI_QOLLAMA.md`
- `docs/ADMINISTRATOR_QOLLAMA.md`
- `docs/OQITUVCHI_QOLLAMA.md`

---

**Eslatma:** Ushbu qo‘llanmalar mavjud kodni o‘zgartirmasdan qo‘shilgan.  
Kod o‘zgarmagan holda faqat `docs/` papkasi va qo‘llanma fayllari qo‘shildi.
