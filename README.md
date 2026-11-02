<img src="./banner.png">

# Daneshban / سامانه مدیریت کتابخانه دانشگاهی

**Choose your language / زبان را انتخاب کنید:**

- 🇮🇷 [فارسی (Persian)](README.fa.md)
- 🇺🇸 [English](README.en.md)

---

## Quick Links / لینک‌های سریع

| Persian | English |
|---------|---------|
| [راه‌اندازی با Docker](README.fa.md#راهاندازی-با-docker-پیشنهادی-برای-production) | [Docker Setup](README.en.md#docker-setup-recommended-for-production) |
| [نصب و اجرا](README.fa.md#نحوه-راهاندازی-و-اجرای-پروژه) | [Installation](README.en.md#installation--setup-development) |
| [ایجاد ادمین](README.fa.md#ایجاد-حساب-مدیر-superuser) | [Create Admin](README.en.md#creating-admin-user-superuser) |
| [داده‌های نمونه](README.fa.md#ایجاد-دادههای-نمونه-seed-demo) | [Seed Demo](README.en.md#seed-demo-data) |
| [تست‌ها](README.fa.md#اجرای-آزمونها-tests) | [Tests](README.en.md#running-tests) |

---

## Docker Quick Start / راه‌اندازی سریع Docker

```bash
# Clone & configure
git clone https://github.com/amirrezesf/Daneshban.git
cd Daneshban
cp .env.example .env
# Edit .env with your SECRET_KEY, ALLOWED_HOSTS

# Run with Docker Compose (port 2445)
docker compose up --build -d

# Access at http://localhost:2445
```

---

## License / مجوز

MIT License — see [LICENSE](LICENSE) for details.