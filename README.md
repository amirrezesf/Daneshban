<img src="./banner.png">

# Daneshban / سامانه مدیریت کتابخانه دانشگاهی

**Choose your language / زبان را انتخاب کنید:**

- 🇮🇷 [فارسی (Persian)](README.fa.md)
- 🇺🇸 [English](README.en.md)

---

## Quick Links / لینک‌های سریع

| Persian | English |
|---------|---------|
| [نصب با Docker](README.fa.md#نصب-و-اجرا-با-docker-روش-پیشنهادی) | [Install with Docker](README.en.md#install--run-with-docker-recommended) |
| [توسعه محلی](README.fa.md#توسعه-محلی-clone-و-اجرا-از-سورس) | [Local Development](README.en.md#local-development-clone--run-from-source) |
| [ایجاد ادمین](README.fa.md#ایجاد-حساب-مدیر-superuser) | [Create Admin](README.en.md#creating-admin-user-superuser) |
| [داده‌های نمونه](README.fa.md#ایجاد-دادههای-نمونه-seed-demo) | [Seed Demo](README.en.md#seed-demo-data) |
| [تست‌ها](README.fa.md#اجرای-آزمونها-tests) | [Tests](README.en.md#running-tests) |

---

## Docker Quick Start / راه‌اندازی سریع Docker (بدون کلون کردن)

این روش از ایمیج‌های از پیش ساخته شده در **GitHub Container Registry** استفاده می‌کند.

```bash
# 1. دریافت فایل‌های پیکربندی
curl -O https://raw.githubusercontent.com/amirrezesf/Daneshban/main/.env.example
curl -O https://raw.githubusercontent.com/amirrezesf/Daneshban/main/docker-compose.yml

# 2. تنظیم متغیرهای محیطی
mv .env.example .env
# فایل .env را ویرایش کنید: SECRET_KEY، ALLOWED_HOSTS و ...

# 3. اجرای با Docker Compose
docker compose up -d

# 4. دسترسی در http://localhost:2445
```

**یا اجرای کانتینر مستقل:**
```bash
docker pull ghcr.io/amirrezesf/daneshban:latest
docker run -d \
  --name daneshban \
  -p 2445:2445 \
  -e SECRET_KEY="your-secret-key" \
  -e DEBUG=False \
  -e ALLOWED_HOSTS="*" \
  -v $(pwd)/media:/app/media \
  -v $(pwd)/staticfiles:/app/staticfiles \
  ghcr.io/amirrezesf/daneshban:latest
```

---

## License / مجوز

MIT License — see [LICENSE](LICENSE) for details.