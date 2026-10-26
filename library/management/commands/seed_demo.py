from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from library.models import Semester, Lesson, Resource


class Command(BaseCommand):
    help = "ایجاد داده‌های نمونه دانشگاهی برای نمایش اولیه سامانه (ترم‌ها، دروس، و فایل‌ها)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="پاک‌کردن داده‌های قبلی قبل از ایجاد داده‌های نمونه",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("در حال پاک‌سازی داده‌های قبلی...")
            Resource.objects.all().delete()
            Lesson.objects.all().delete()
            Semester.objects.all().delete()

        # ایجاد کاربر ادمین در صورت عدم وجود
        admin_user, created = User.objects.get_or_create(username="admin")
        if created:
            admin_user.set_password("admin123")
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("کاربر مدیر با نام کاربری admin و رمز admin123 ایجاد شد."))

        import datetime

        # ۱. ترم‌های تحصیلی
        sem1, _ = Semester.objects.get_or_create(
            title="ترم ۱ - پاییز ۱۴۰۳",
            defaults={
                "order": 1,
                "start_date": datetime.date(2024, 9, 22), # ۱ مهر ۱۴۰۳
                "description": "نیم‌سال اول تحصیلی سال ۱۴۰۳-۱۴۰۴ با تمرکز بر دروس پایه ریاضی و فیزیک",
            }
        )
        if not sem1.start_date:
            sem1.start_date = datetime.date(2024, 9, 22)
            sem1.save()

        sem2, _ = Semester.objects.get_or_create(
            title="ترم ۲ - بهار ۱۴۰۴",
            defaults={
                "order": 2,
                "start_date": datetime.date(2025, 4, 4), # ۱۶ فروردین ۱۴۰۴
                "description": "نیم‌سال دوم تحصیلی سال ۱۴۰۳-۱۴۰۴ شامل دروس تخصصی مقدماتی",
            }
        )
        if not sem2.start_date:
            sem2.start_date = datetime.date(2025, 4, 4)
            sem2.save()

        sem3, _ = Semester.objects.get_or_create(
            title="ترم ۳ - پاییز ۱۴۰۴",
            defaults={
                "order": 3,
                "start_date": datetime.date(2025, 9, 23), # ۱ مهر ۱۴۰۴
                "description": "نیم‌سال اول تحصیلی سال ۱۴۰۴-۱۴۰۵ شامل دروس پیشرفته و کارگاهی",
            }
        )
        if not sem3.start_date:
            sem3.start_date = datetime.date(2025, 9, 23)
            sem3.save()

        # ۲. دروس دانشگاهی
        l1, _ = Lesson.objects.get_or_create(
            title="ریاضی عمومی ۱",
            defaults={
                "professor": "دکتر محمد حسینی",
                "semester": sem1,
                "color": "#2563eb",
                "description": "سرفصل‌ها شامل: تابع، حد و پیوستگی، مشتق و کاربردهای هندسی و فیزیکی، انتگرال معین و نامعین و کاربردهای انتگرال‌گیری در محاسبه مساحت و حجم.",
            }
        )

        l2, _ = Lesson.objects.get_or_create(
            title="مبانی کامپیوتر و برنامه‌نویسی",
            defaults={
                "professor": "دکتر زهرا رضایی",
                "semester": sem1,
                "color": "#059669",
                "description": "مفاهیم بنیادی الگوریتم، فلوچارت، ساختارهای کنترلی، توابع، مدیریت حافظه، ساختمان داده‌های پایه و برنامه‌نویسی به زبان پایتون.",
            }
        )

        l3, _ = Lesson.objects.get_or_create(
            title="مدارهای منطقی و سیستم‌های دیجیتال",
            defaults={
                "professor": "دکتر علیرضا نادری",
                "semester": sem2,
                "color": "#d97706",
                "description": "جبر بول، گیت‌های منطقی، ساده‌سازی توابع با جدول کارنو، مدارهای ترکیبی (جمع‌کننده، دیکدر، مالتی‌پلکسر) و مدارهای ترتیبی (فلیپ‌فلاپ‌ها و شمارنده‌ها).",
            }
        )

        # ۳. ایجاد فایل‌ها و منابع نمونه
        sample_resources = [
            # ریاضی عمومی ۱
            {
                "lesson": l1,
                "title": "جزوه دست‌نویس جلسه اول و دوم - حد و پیوستگی",
                "kind": Resource.KIND_HANDOUT,
                "session_number": 1,
                "filename": "math1_session1_limits.pdf",
                "content": b"%PDF-1.4 Math 1 Handout - Limits and Continuity (Persian Handout Sample)",
                "description": "شامل تعاریف اپسیلون-دلتا، قضایای فشردگی، حدهای یک‌طرفه و نمونه مثال‌های حل‌شده در کلاس.",
                "tags": "حد, پیوستگی, جلسه اول, دست نویس",
                "downloads": 14,
            },
            {
                "lesson": l1,
                "title": "جزوه مبحث مشتق و قاعده زنجیره‌ای",
                "kind": Resource.KIND_HANDOUT,
                "session_number": 5,
                "filename": "math1_session5_derivatives.pdf",
                "content": b"%PDF-1.4 Math 1 Handout - Derivatives and Chain Rule",
                "description": "فرمول‌های مشتق‌گیری، مشتق ضمنی، مشتق مراتب بالاتر و تقریب خطی.",
                "tags": "مشتق, قاعده زنجیره ای, جلسه پنجم",
                "downloads": 8,
            },
            {
                "lesson": l1,
                "title": "اسلایدهای فصل سوم - کاربردهای مشتق و بهینه‌سازی",
                "kind": Resource.KIND_SLIDES,
                "session_number": 7,
                "filename": "math1_slides_optimization.pptx",
                "content": b"Sample PPTX - Optimization and Curve Sketching",
                "description": "نقاط بحرانی، اکسترمم‌های نسبی و مطلق، آزمون مشتق اول و دوم، رسم نمودار توابع.",
                "tags": "اسلاید, بهینه سازی, رسم نمودار",
                "downloads": 22,
            },
            {
                "lesson": l1,
                "title": "تمرین سری دوم - مشتق‌گیری و تقریب تیلور",
                "kind": Resource.KIND_ASSIGNMENT,
                "session_number": None,
                "filename": "math1_assignment_2.pdf",
                "content": b"%PDF-1.4 Math 1 Homework 2",
                "description": "مهلت تحویل تا پایان هفته هفتم ترم تحصیلی.",
                "tags": "تمرین, مشتق, تیلور",
                "downloads": 35,
            },
            {
                "lesson": l1,
                "title": "نمونه سوالات امتحان میان‌ترم ترم‌های گذشته با پاسخ",
                "kind": Resource.KIND_EXAM,
                "session_number": None,
                "filename": "math1_midterm_exams_archive.pdf",
                "content": b"%PDF-1.4 Math 1 Midterm Archive with Solutions",
                "description": "آرشیو نمونه سوالات میان‌ترم سال‌های ۱۴۰۰ الی ۱۴۰۳ همراه با حل تشریحی و بارم‌بندی.",
                "tags": "نمونه سوال, میان ترم, آرشیو, حل تشریحی",
                "downloads": 64,
            },

            # مبانی برنامه‌نویسی
            {
                "lesson": l2,
                "title": "اسلایدهای جلسه اول - مقدمه و نصب محیط پایتون",
                "kind": Resource.KIND_SLIDES,
                "session_number": 1,
                "filename": "python_basics_session_1.pdf",
                "content": b"%PDF-1.4 Python Basics Session 1",
                "description": "راهنمای نصب مفسر پایتون، VS Code، آشنایی با مفهوم متغیر و دستورات ورودی/خروجی.",
                "tags": "پایتون, جلسه اول, اسلاید, نصب",
                "downloads": 19,
            },
            {
                "lesson": l2,
                "title": "جزوه مبحث توابع، دامنه متغیرها و بازگشت",
                "kind": Resource.KIND_HANDOUT,
                "session_number": 6,
                "filename": "python_functions_recursion.pdf",
                "content": b"%PDF-1.4 Python Functions and Recursion Handout",
                "description": "نحوه تعریف تابع، پارامترهای پیش‌فرض، *args و **kwargs و نحوه عملکرد توابع بازگشتی.",
                "tags": "تابع, بازگشت, جزوه",
                "downloads": 27,
            },
            {
                "lesson": l2,
                "title": "پروژه تمرینی پیاده‌سازی سیستم مدیریت نمرات",
                "kind": Resource.KIND_ASSIGNMENT,
                "session_number": None,
                "filename": "python_grades_project.zip",
                "content": b"PK\x03\x04 Sample ZIP archive for Python Grades Project",
                "description": "فایل‌های ورودی نمونه و ساختار کدهای خواسته شده در قالب فایل فشرده.",
                "tags": "پروژه, فایل فشرده, تمرین",
                "downloads": 11,
            },
            {
                "lesson": l2,
                "title": "کتاب مرجع یادگیری پایتون (نسخه الکترونیکی)",
                "kind": Resource.KIND_BOOK,
                "session_number": None,
                "filename": "python_programming_reference.pdf",
                "content": b"%PDF-1.4 Python Programming Reference Book",
                "description": "کتاب الکترونیکی فارسی آموزش جامع زبان برنامه‌نویسی پایتون برای دانشجویان کارشناسی.",
                "tags": "کتاب, رفرنس, پایتون",
                "downloads": 48,
            },

            # مدارهای منطقی
            {
                "lesson": l3,
                "title": "جزوه کامل جبر بول و جدول کارنو",
                "kind": Resource.KIND_HANDOUT,
                "session_number": 2,
                "filename": "digital_circuits_boolean_karnaugh.pdf",
                "content": b"%PDF-1.4 Logic Circuits - Boolean Algebra and Karnaugh Maps",
                "description": "اصول جبر بول، فرم‌های SOP و POS و روش بهینه‌سازی توابع چندمتغیره.",
                "tags": "کارنو, جبر بول, مدار منطقی",
                "downloads": 31,
            },
            {
                "lesson": l3,
                "title": "نمونه سوالات آزمون پایان‌ترم مدارهای منطقی",
                "kind": Resource.KIND_EXAM,
                "session_number": None,
                "filename": "logic_circuits_final_exams.pdf",
                "content": b"%PDF-1.4 Logic Circuits Final Exams with solutions",
                "description": "نمونه سوالات تحلیلی و طراحی مدارهای ترتیبی همگام و ناهمگام با پاسخ تشریحی.",
                "tags": "امتحان, پایان ترم, سوالات",
                "downloads": 52,
            },
            # منابع مستقل (بدون درس)
            {
                "lesson": None,
                "semester": sem1,
                "title": "چارت تحصیلی و تقویم آموزشی نیم‌سال اول",
                "kind": Resource.KIND_BOOK,
                "session_number": None,
                "filename": "academic_calendar_fall_chart.pdf",
                "content": b"%PDF-1.4 Academic Calendar and Course Catalog Chart",
                "description": "چارت مصوب، آیین‌نامه ثبت‌نام، تاریخ‌های حذف و اضافه و تقویم امتحانات نیم‌سال اول.",
                "tags": "چارت, تقویم آموزشی, آیین نامه",
                "downloads": 48,
            },
            {
                "lesson": None,
                "semester": None,
                "title": "شیوه‌نامه جامع نگارش مقالات و گزارش‌های دانشگاهی",
                "kind": Resource.KIND_HANDOUT,
                "session_number": None,
                "filename": "university_writing_guidelines.pdf",
                "content": b"%PDF-1.4 University Research and Technical Writing Style Guide",
                "description": "راهنمای قالب‌بندی فونت، ارجاع‌دهی مراجع به سبک IEEE و ساختار استانداردهای فنی.",
                "tags": "شیوه نامه, نگارش, مقاله, پایان نامه",
                "downloads": 89,
            },
        ]

        count_created = 0
        for data in sample_resources:
            # بررسی اینکه منبعی با این عنوان قبلا ایجاد نشده باشد
            if not Resource.objects.filter(lesson=data["lesson"], title=data["title"]).exists():
                r = Resource(
                    lesson=data["lesson"],
                    semester=data.get("semester"),
                    title=data["title"],
                    kind=data["kind"],
                    session_number=data["session_number"],
                    description=data["description"],
                    tags=data["tags"],
                    download_count=data["downloads"],
                )
                r.file.save(data["filename"], ContentFile(data["content"]), save=True)
                count_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"داده‌های نمونه با موفقیت ایجاد شد! ({Semester.objects.count()} ترم، {Lesson.objects.count()} درس، {Resource.objects.count()} منبع)"
            )
        )
