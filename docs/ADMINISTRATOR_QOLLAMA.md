# Abu Rayhon Beruniy nomidagi Urganch davlat akademik litseyi  
## Raqamli kutubxona — Administrator qo‘llanmasi

**Versiya:** 1.0  
**Til:** O‘zbek (lotin)

---

## 1. Kirish

Ushbu qo‘llanma Django Admin paneli va saytning o‘zida mavjud boshqaruv imkoniyatlaridan foydalanish uchun mo‘ljallangan.

Admin panel manzili (lokal):  
`http://127.0.0.1:8000/admin/`

---

## 2. Administrator yaratish

### Windows

1. Loyiha papkasida `create_admin_windows.bat` faylini ishga tushiring  
   **yoki**
2. Terminalda:
   ```powershell
   .venv\Scripts\Activate.ps1
   python manage.py createsuperuser
   ```
3. Username, email va kuchli parol kiriting.

### Linux / macOS

```bash
source .venv/bin/activate
python manage.py createsuperuser
```

### Docker

```bash
docker compose exec web python manage.py createsuperuser
```

---

## 3. Django Admin paneli

### 3.1. Foydalanuvchilarni boshqarish

- Foydalanuvchilar ro‘yxatini ko‘rish
- O‘qituvchi akkauntlarini tasdiqlash (agar modelda `is_teacher_approved` yoki shunga o‘xshash maydon bo‘lsa)
- Foydalanuvchini faolsizlantirish / bloklash
- Parolni o‘zgartirish (faqat zarur hollarda)

**Muhim:** Oddiy foydalanuvchi URL ni o‘zgartirib admin sahifasiga kira olmaydi. Faqat `is_staff=True` va tegishli ruxsatlarga ega foydalanuvchilar kiradi.

### 3.2. Kitoblarni boshqarish

1. **Books** (yoki «Kitoblar») bo‘limiga o‘ting.
2. **«Add»** tugmasi orqali yangi kitob qo‘shing.
3. To‘ldiriladigan maydonlar (misol):
   - Nomi
   - Muallif(lar)
   - Kategoriya / fan
   - Tavsif
   - Muqova rasmi
   - PDF / EPUB fayl
   - Til, nashr yili, ISBN (mavjud bo‘lsa)
   - Tavsiya etilgan deb belgilash
4. Fayl yuklashda:
   - Faqat ruxsat etilgan formatlar (PDF, EPUB va h.k.)
   - Hajm limiti tekshiriladi
   - Zararli fayl xavfi uchun server tomonida tekshiruvlar mavjud

### 3.3. Kategoriyalar

- Yangi kategoriya (fan) qo‘shish
- Tahrirlash va o‘chirish
- Kitoblarni kategoriyaga bog‘lash

### 3.4. Testlar va quizlar

- Savol va javob variantlarini boshqarish
- O‘qituvchilar yaratgan testlarni ko‘rish / tasdiqlash
- Natijalarni kuzatish

### 3.5. Statistika va audit

- Umumiy foydalanuvchilar soni
- Kitoblar soni
- O‘qish faolligi
- Muhim amallar bo‘yicha audit jurnali (agar model mavjud bo‘lsa)

---

## 4. Kitob qo‘shish bo‘yicha tavsiyalar

1. Muqova rasmini optimallashtiring (hajmi katta bo‘lmasin).
2. Tavsifni aniq va qisqa yozing.
3. To‘g‘ri kategoriyani tanlang.
4. Litsenziya / foydalanish huquqi haqida ma’lumot kiriting.
5. Faqat qonuniy tarqatishga ruxsat etilgan fayllarni yuklang.

---

## 5. O‘qituvchi akkauntlarini tasdiqlash

1. Foydalanuvchilar ro‘yxatidan o‘qituvchini toping.
2. Tegishli maydonni (`is_approved`, `teacher_status` va h.k.) o‘zgartiring.
3. Saqlang.

Tasdiqlanmagan o‘qituvchi to‘liq imkoniyatlardan foydalana olmaydi.

---

## 6. Xavfsizlik tavsiyalari

- DEBUG rejimini productionda o‘chirib qo‘ying (`DJANGO_DEBUG=0`).
- Kuchli va noyob `DJANGO_SECRET_KEY` ishlating.
- `ALLOWED_HOSTS` ni to‘g‘ri sozlang.
- HTTPS ishlating.
- Muntazam zaxira nusxa oling (PostgreSQL uchun `deploy/backup_postgres.sh` skriptidan foydalaning).
- Admin parolini kuchli qiling va vaqti-vaqti bilan o‘zgartiring.
- Login urinishlarini kuzatib boring.

---

## 7. Productionga joylashtirish qisqacha

1. `.env` faylini to‘ldiring (SECRET_KEY, DB sozlamalari, ALLOWED_HOSTS).
2. `python manage.py migrate`
3. `python manage.py collectstatic --noinput`
4. Gunicorn + Nginx + HTTPS sozlang.
5. Media fayllarni xavfsiz saqlang.
6. Zaxira nusxa rejasini tuzing.

Batafsil ma’lumot uchun asosiy `README.md` fayliga qarang.

---

## 8. Tez-tez so‘raladigan savollar (Admin)

**Q: Foydalanuvchi admin paneliga kira olmayapti.**  
A: Uning `is_staff` va `is_superuser` (yoki kerakli permission) maydonlarini tekshiring.

**Q: Kitob yuklanmayapti.**  
A: Fayl formati, hajmi va serverdagi media papka ruxsatlarini tekshiring.

**Q: Migration xatolari.**  
A: `python manage.py makemigrations catalog` va `python manage.py migrate` ni qayta bajaring.

---

## 9. Qo‘shimcha hujjatlar

- `README.md` — o‘rnatish va ishga tushirish
- `docs/FOYDALANUVCHI_QOLLAMA.md` — oddiy foydalanuvchi qo‘llanmasi
- `docs/OQITUVCHI_QOLLAMA.md` — o‘qituvchi qo‘llanmasi
- `docs/TEXNIK_QOLLAMA.md` — texnik va ishlab chiqish qo‘llanmasi

---

**Eslatma:** Ushbu qo‘llanma kodni o‘zgartirmasdan qo‘shilgan. Barcha funksiyalar mavjud kod asosida ishlaydi.
