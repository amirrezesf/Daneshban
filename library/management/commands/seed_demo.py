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

        l4, _ = Lesson.objects.get_or_create(
            title="هوش مصنوعی و یادگیری ماشین",
            defaults={
                "professor": "دکتر آرش سهرابی",
                "semester": sem3,
                "color": "#8b5cf6",
                "description": "عامل‌های هوشمند، جستجوی آگاهانه، الگوریتم‌های ژنتیک، منطق فازی، شبکه‌های عصبی و یادگیری عمیق.",
            }
        )

        l5, _ = Lesson.objects.get_or_create(
            title="طراحی و مدیریت پایگاه داده‌ها",
            defaults={
                "professor": "دکتر مریم کریمی",
                "semester": sem2,
                "color": "#06b6d4",
                "description": "مدل موجودیت-ارتباط (ER)، جبر رابطه‌ای، زبان SQL استاندارد، نرمال‌سازی و تراکنش‌های ACID.",
            }
        )

        # ۳. ایجاد فایل‌ها و منابع نمونه
        mp3_dummy = (b'\xff\xfb\x90d' + b'\x00' * 413) * 120
        mp4_dummy = b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free\x00\x00\x00\x08mdat' + b'\x00' * 2048

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
            # صوت و ویدیوهای جلسات (برای تست پلیر صوتی مایع و ویدیویی)
            {
                "lesson": l1,
                "title": "صوت ضبط‌شده جلسه ۴: قضیه مقدار میانگین و مشتق مراتب بالا",
                "kind": Resource.KIND_RECORDING,
                "session_number": 4,
                "filename": "math1_session4_audio.mp3",
                "content": mp3_dummy,
                "description": "فایل صوتی کلاس درس ریاضی عمومی ۱ همراه با توضیحات استاد در خصوص مثال‌های کاربردی قضیه رول و مقدار میانگین.",
                "tags": "صوت, جلسه چهارم, ضبط کلاس, mp3",
                "downloads": 42,
            },
            {
                "lesson": l2,
                "title": "صوت جلسه کارگاه برنامه‌نویسی: ساختمان داده‌های توکار پایتون",
                "kind": Resource.KIND_RECORDING,
                "session_number": 5,
                "filename": "python_session5_structures_audio.mp3",
                "content": mp3_dummy,
                "description": "صوت آموزشی نحوه پیمایش تاپل‌ها، دیکشنری‌ها، مجموعه‌ها و مفاهیم پیچیدگی حافظه در پایتون.",
                "tags": "صوت, پایتون, کارگاه, mp3",
                "downloads": 67,
            },
            {
                "lesson": l3,
                "title": "ویدیو آموزشی: کارگاه تحلیل و طراحی مدار در نرم‌افزار Logisim",
                "kind": Resource.KIND_RECORDING,
                "session_number": 6,
                "filename": "logic_circuits_logisim_workshop.mp4",
                "content": mp4_dummy,
                "description": "ویدیو نحوه پیاده‌سازی جمع‌کننده ۴ بیتی، فلیپ‌فلاپ‌های نوع D و JK و تست مدار با پالس ساعت.",
                "tags": "ویدیو, لاجیسیم, مدار, کارگاه, mp4",
                "downloads": 58,
            },

            # هوش مصنوعی
            {
                "lesson": l4,
                "title": "اسلایدهای فصل اول: معرفی هوش مصنوعی و عامل‌های عقلانی",
                "kind": Resource.KIND_SLIDES,
                "session_number": 1,
                "filename": "ai_session1_agents.pdf",
                "content": b"%PDF-1.4 AI Session 1 - Intelligent Agents and Environments",
                "description": "انواع محیط‌های وظیفه (PEAS)، ساختار عامل‌های واکنشی، مبتنی بر مدل و یادگیرنده.",
                "tags": "هوش مصنوعی, اسلاید, جلسه اول",
                "downloads": 39,
            },
            {
                "lesson": l4,
                "title": "صوت ضبط‌شده جلسه ۶: الگوریتم جستجوی A* و هیوریستیک‌های سازگار",
                "kind": Resource.KIND_RECORDING,
                "session_number": 6,
                "filename": "ai_session6_astar_heuristic.mp3",
                "content": mp3_dummy,
                "description": "بررسی شرایط پایداری و بهینگی الگوریتم A*، اثبات admissibility و رسم درخت جستجو.",
                "tags": "صوت, جستجو, هوش مصنوعی, جلسه ششم, mp3",
                "downloads": 73,
            },

            # پایگاه داده‌ها
            {
                "lesson": l5,
                "title": "جزوه مدلسازی داده و دیاگرام ER پیشرفته",
                "kind": Resource.KIND_HANDOUT,
                "session_number": 3,
                "filename": "database_er_diagram_handout.pdf",
                "content": b"%PDF-1.4 Database Systems - ER Modeling Handout",
                "description": "انواع موجودیت‌ها، ویژگی‌های چندمقداره و ترکیبی، روابط بازگشتی و تبدیل به جداول رابطه‌ای.",
                "tags": "پایگاه داده, جزوه, ER",
                "downloads": 45,
            },
            {
                "lesson": l5,
                "title": "اسلایدهای دستورات SQL و کوئری‌های تودرتو",
                "kind": Resource.KIND_SLIDES,
                "session_number": 7,
                "filename": "database_sql_queries_slides.pptx",
                "content": b"Sample PPTX - Advanced SQL Queries and Joins",
                "description": "بررسی انواع JOIN، GROUP BY، HAVING و Subqueryهای همبسته و غیرهمبسته.",
                "tags": "SQL, اسلاید, کوئری",
                "downloads": 61,
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
