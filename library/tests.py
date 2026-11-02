import os
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from library.models import Semester, Lesson, Resource, validate_file_extension_and_size
from library.templatetags.persian_tags import persian_digits, jalali_date, persian_filesize, split_tags


class TemplateFilterTests(TestCase):
    """
    آزمون فیلترهای تمپلیت: تبدیل ارقام به فارسی، تاریخ جلالی (شمسی) و اندازه فایل
    """
    def test_persian_digits_conversion(self):
        self.assertEqual(persian_digits("0123456789"), "۰۱۲۳۴۵۶۷۸۹")
        self.assertEqual(persian_digits(1404), "۱۴۰۴")
        self.assertEqual(persian_digits("ترم 2 سال 1403"), "ترم ۲ سال ۱۴۰۳")
        self.assertEqual(persian_digits(None), "")
        self.assertEqual(persian_digits(""), "")

    def test_jalali_date_conversion(self):
        # 2026-03-21 is around 1405-01-01 in Jalali
        d = datetime.date(2026, 3, 21)
        j_str = jalali_date(d)
        # Verify it outputs Persian digits and correct format YYYY/MM/DD
        self.assertTrue(len(j_str.split("/")) == 3)
        self.assertTrue(any(ch in "۰۱۲۳۴۵۶۷۸۹" for ch in j_str))

    def test_persian_filesize(self):
        self.assertEqual(persian_filesize(500), "۵۰۰ بایت")
        self.assertEqual(persian_filesize(1024), "۱ کیلوبایت")
        self.assertEqual(persian_filesize(1048576), "۱ مگابایت")
        self.assertEqual(persian_filesize(2621440), "۲٫۵ مگابایت".replace("٫", ".")) # or decimal

    def test_split_tags(self):
        tags = split_tags("جزوه، میان‌ترم, ریاضی ۱")
        self.assertEqual(tags, ["جزوه", "میان‌ترم", "ریاضی ۱"])


class ModelTests(TestCase):
    """
    آزمون مدل‌ها: تولید خودکار اسلاگ فارسی، ذخیره حجم فایل، و ترتیب‌بندی
    """
    def setUp(self):
        self.semester = Semester.objects.create(title="ترم ۱ - پاییز ۱۴۰۴", order=1)

    def test_lesson_slug_generation(self):
        lesson = Lesson.objects.create(
            title="ریاضی عمومی ۱",
            semester=self.semester,
            professor="دکتر احمدی"
        )
        self.assertTrue(lesson.slug.startswith("ریاضی-عمومی-1") or lesson.slug.startswith("ریاضی-عمومی-۱"))

        # Test duplicate slug handling
        lesson2 = Lesson.objects.create(
            title="ریاضی عمومی ۱",
            semester=self.semester,
        )
        self.assertNotEqual(lesson.slug, lesson2.slug)
        self.assertTrue(lesson2.slug.endswith("-1"))

    def test_resource_file_size_saving(self):
        lesson = Lesson.objects.create(title="مبانی کامپیوتر")
        test_file = SimpleUploadedFile("handout.pdf", b"Hello PDF content 1234567890")
        
        resource = Resource.objects.create(
            lesson=lesson,
            title="جزوه پایتون",
            kind=Resource.KIND_HANDOUT,
            file=test_file
        )
        self.assertEqual(resource.file_size, len(b"Hello PDF content 1234567890"))

    def test_invalid_file_extension_rejected(self):
        invalid_file = SimpleUploadedFile("danger.exe", b"binary content")
        with self.assertRaises(ValidationError):
            validate_file_extension_and_size(invalid_file)

    def test_valid_file_extension_accepted(self):
        valid_file = SimpleUploadedFile("slides.pptx", b"Powerpoint presentation bytes")
        # Should not raise
        validate_file_extension_and_size(valid_file)


class ViewTests(TestCase):
    """
    آزمون ویوها: صفحه اصلی، صفحه درس با گروه‌بندی، جستجو، نیاز به ورود، و دانلود فایل
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.semester = Semester.objects.create(title="ترم ۱", order=1)
        self.lesson = Lesson.objects.create(
            title="فیزیک پایه ۱",
            slug="physics-1",
            semester=self.semester,
            professor="دکتر کاظمی"
        )
        
        # Create resources of different kinds
        self.handout = Resource.objects.create(
            lesson=self.lesson,
            title="جزوه مکانیک",
            kind=Resource.KIND_HANDOUT,
            session_number=1,
            file=SimpleUploadedFile("mechanics_جزوه.pdf", b"%PDF test content for physics"),
            tags="فیزیک, مکانیک"
        )
        self.slides = Resource.objects.create(
            lesson=self.lesson,
            title="اسلایدهای جلسه دوم",
            kind=Resource.KIND_SLIDES,
            session_number=2,
            file=SimpleUploadedFile("slides.pptx", b"slides content"),
            tags="اسلاید"
        )

    def test_base_html_rtl_and_lang(self):
        response = self.client.get(reverse("library:home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('dir="rtl"', content)
        self.assertIn('lang="fa"', content)
        self.assertIn("Vazirmatn", content)

    def test_home_view(self):
        response = self.client.get(reverse("library:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "فیزیک پایه ۱")
        self.assertContains(response, "دکتر کاظمی")
        self.assertContains(response, "ترم ۱")

    def test_lesson_detail_view_grouped_by_kind(self):
        response = self.client.get(reverse("library:lesson_detail", kwargs={"slug": self.lesson.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "جزوه مکانیک")
        self.assertContains(response, "اسلایدهای جلسه دوم")
        
        # Check that context resource_groups contains handout and slides groups
        groups = response.context["resource_groups"]
        kinds = [g["code"] for g in groups]
        self.assertIn(Resource.KIND_HANDOUT, kinds)
        self.assertIn(Resource.KIND_SLIDES, kinds)

    def test_search_view(self):
        response = self.client.get(reverse("library:search"), {"q": "مکانیک"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "جزوه مکانیک")
        self.assertNotContains(response, "اسلایدهای جلسه دوم")

    def test_mutating_views_require_login(self):
        # Lesson create
        response = self.client.get(reverse("library:lesson_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

        # Resource create
        response = self.client.get(reverse("library:resource_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_download_view_increments_counter_and_sets_content_disposition(self):
        initial_downloads = self.handout.download_count
        download_url = reverse("library:resource_download", kwargs={"pk": self.handout.pk})
        
        response = self.client.get(download_url)
        self.assertEqual(response.status_code, 200)

        # Verify counter incremented
        self.handout.refresh_from_db()
        self.assertEqual(self.handout.download_count, initial_downloads + 1)

        # Verify Content-Disposition with RFC 5987 UTF-8 encoding
        disposition = response.headers.get("Content-Disposition", "")
        self.assertIn("attachment", disposition)
        self.assertIn("filename*=UTF-8''", disposition)

    def test_raw_stream_view_sets_inline_disposition(self):
        stream_url = reverse("library:resource_raw_stream", kwargs={"pk": self.handout.pk})
        response = self.client.get(stream_url)
        self.assertEqual(response.status_code, 200)
        disposition = response.headers.get("Content-Disposition", "")
        self.assertIn("inline", disposition)

    def test_resource_viewer_view(self):
        viewer_url = reverse("library:resource_viewer", kwargs={"pk": self.handout.pk})
        response = self.client.get(viewer_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "جزوه مکانیک")
        self.assertTrue(self.handout.can_preview_in_browser)


class SemesterSeasonCalculationTests(TestCase):
    """
    آزمون محاسبه خودکار فصل و سال تحصیلی بر اساس تاریخ شروع ترم (شمسی/جلالی)
    """
    def test_autumn_calculation(self):
        # 2025-09-23 corresponds to 1 Mehr 1404 (پاییز ۱۴۰۴)
        sem = Semester.objects.create(
            title="نیم‌سال اول",
            start_date=datetime.date(2025, 9, 23),
            order=1
        )
        self.assertEqual(sem.season, "پاییز")
        self.assertIn("۱۴۰۴", sem.jalali_year)
        self.assertEqual(sem.season_and_year, "پاییز ۱۴۰۴")
        self.assertEqual(sem.season_info["season_code"], "autumn")

    def test_winter_calculation(self):
        # 2026-02-04 corresponds to 15 Bahman 1404 (زمستان ۱۴۰۴)
        sem = Semester.objects.create(
            title="نیم‌سال دوم",
            start_date=datetime.date(2026, 2, 4),
            order=2
        )
        self.assertEqual(sem.season, "زمستان")
        self.assertEqual(sem.season_and_year, "زمستان ۱۴۰۴")
        self.assertEqual(sem.season_info["season_code"], "winter")

    def test_spring_calculation(self):
        # 2026-04-04 corresponds to 15 Farvardin 1405 (بهار ۱۴۰۵)
        sem = Semester.objects.create(
            title="نیم‌سال بهار",
            start_date=datetime.date(2026, 4, 4),
            order=3
        )
        self.assertEqual(sem.season, "بهار")
        self.assertEqual(sem.season_and_year, "بهار ۱۴۰۵")
        self.assertEqual(sem.season_info["season_code"], "spring")

    def test_summer_calculation(self):
        # 2026-07-01 corresponds to 10 Tir 1405 (تابستان ۱۴۰۵)
        sem = Semester.objects.create(
            title="ترم تابستان",
            start_date=datetime.date(2026, 7, 1),
            order=4
        )
        self.assertEqual(sem.season, "تابستان")
        self.assertEqual(sem.season_and_year, "تابستان ۱۴۰۵")
        self.assertEqual(sem.season_info["season_code"], "summer")

    def test_none_start_date(self):
        sem = Semester.objects.create(title="ترم نامشخص", order=5)
        self.assertEqual(sem.season, "")
        self.assertEqual(sem.jalali_year, "")
        self.assertEqual(sem.season_and_year, "")
        self.assertIsNone(sem.season_info)


class SemesterManagementViewsTests(TestCase):
    """
    آزمون ویوهای مدیریت ترم: مشاهده لیست، ایجاد ترم جدید، ویرایش و حذف
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testadmin", password="password123")
        self.sem1 = Semester.objects.create(
            title="ترم ۱ - پاییز ۱۴۰۴",
            start_date=datetime.date(2025, 9, 23),
            order=1
        )

    def test_semester_list_view_public(self):
        response = self.client.get(reverse("library:semester_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "مدیریت ترم‌های تحصیلی")
        self.assertContains(response, "ترم ۱ - پاییز ۱۴۰۴")
        self.assertContains(response, "پاییز ۱۴۰۴")

    def test_semester_create_requires_login(self):
        response = self.client.get(reverse("library:semester_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_semester_create_post(self):
        self.client.login(username="testadmin", password="password123")
        response = self.client.post(reverse("library:semester_create"), {
            "title": "ترم ۲ - بهمن ۱۴۰۴",
            "start_date": "2026-02-04",
            "order": 2,
            "description": "ترم زمستانه",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("library:semester_list"))

        new_sem = Semester.objects.get(title="ترم ۲ - بهمن ۱۴۰۴")
        self.assertEqual(new_sem.start_date, datetime.date(2026, 2, 4))
        self.assertEqual(new_sem.season_and_year, "زمستان ۱۴۰۴")

    def test_semester_update_post(self):
        self.client.login(username="testadmin", password="password123")
        edit_url = reverse("library:semester_edit", kwargs={"pk": self.sem1.pk})
        response = self.client.post(edit_url, {
            "title": "ترم ۱ ویرایش شده",
            "start_date": "2026-07-01", # Change to summer
            "order": 10,
            "description": "توضیحات ویرایش‌شده",
        })
        self.assertEqual(response.status_code, 302)

        self.sem1.refresh_from_db()
        self.assertEqual(self.sem1.title, "ترم ۱ ویرایش شده")
        self.assertEqual(self.sem1.season_and_year, "تابستان ۱۴۰۵")

    def test_semester_delete_post(self):
        self.client.login(username="testadmin", password="password123")
        del_url = reverse("library:semester_delete", kwargs={"pk": self.sem1.pk})
        response = self.client.post(del_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Semester.objects.filter(pk=self.sem1.pk).exists())


class MediaSupportTests(TestCase):
    """
    آزمون پشتیبانی از فایل‌های چندرسانه‌ای (ویدیو mp4 و صوت mp3):
    - اعتبارسنجی پسوند و آپلود
    - تعیین دقیق نوع پیش‌نمایش (video و audio)
    - استریم مستقیم درون‌مرورگری با Content-Type صحیح
    - نوع منبع recording (صوت یا ویدیو جلسه)
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="prof_media", password="password123")
        self.semester = Semester.objects.create(title="ترم بهار ۱۴۰۵", order=1)
        self.lesson = Lesson.objects.create(
            title="هوش مصنوعی پیشرفته",
            semester=self.semester,
            professor="دکتر رضایی"
        )

    def test_mp4_extension_validation_and_preview(self):
        video_content = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42"
        mp4_file = SimpleUploadedFile("lecture_session_1.mp4", video_content, content_type="video/mp4")
        
        # Should not raise validation error
        validate_file_extension_and_size(mp4_file)

        resource = Resource.objects.create(
            lesson=self.lesson,
            title="ویدیو ضبط شده جلسه اول",
            kind=Resource.KIND_RECORDING,
            file=mp4_file,
            session_number=1
        )

        self.assertEqual(resource.file_extension, "mp4")
        self.assertEqual(resource.preview_type, "video")
        self.assertTrue(resource.can_preview_in_browser)
        self.assertEqual(resource.get_kind_display(), "صوت یا ویدیو جلسه")

    def test_mp3_extension_validation_and_preview(self):
        audio_content = b"ID3\x03\x00\x00\x00\x00\x00#dummy mp3 audio payload"
        mp3_file = SimpleUploadedFile("lecture_audio_note.mp3", audio_content, content_type="audio/mpeg")
        
        # Should not raise validation error
        validate_file_extension_and_size(mp3_file)

        resource = Resource.objects.create(
            lesson=self.lesson,
            title="صوت کلاس درس - بخش دوم",
            kind=Resource.KIND_RECORDING,
            file=mp3_file,
            session_number=2
        )

        self.assertEqual(resource.file_extension, "mp3")
        self.assertEqual(resource.preview_type, "audio")
        self.assertTrue(resource.can_preview_in_browser)

    def test_media_viewer_and_stream_views(self):
        # Create MP4 resource
        video_content = b"\x00\x00\x00\x18ftypmp42fake-mp4-data"
        mp4_file = SimpleUploadedFile("sample_clip.mp4", video_content, content_type="video/mp4")
        res_mp4 = Resource.objects.create(
            lesson=self.lesson,
            title="ویدیو آموزشی حل تمرین",
            kind=Resource.KIND_RECORDING,
            file=mp4_file
        )

        # Viewer page contains video element
        viewer_url = reverse("library:resource_viewer", kwargs={"pk": res_mp4.pk})
        response = self.client.get(viewer_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="media-video-element"')
        self.assertContains(response, 'ویدیو آموزشی حل تمرین')

        # Raw stream endpoint returns video/mp4
        stream_url = reverse("library:resource_raw_stream", kwargs={"pk": res_mp4.pk})
        stream_resp = self.client.get(stream_url)
        self.assertEqual(stream_resp.status_code, 200)
        self.assertEqual(stream_resp["Content-Type"], "video/mp4")

        # Create MP3 resource
        audio_content = b"ID3fake-mp3-audio-bytes"
        mp3_file = SimpleUploadedFile("sample_voice.mp3", audio_content, content_type="audio/mpeg")
        res_mp3 = Resource.objects.create(
            lesson=self.lesson,
            title="فایل صوتی پادکست درس",
            kind=Resource.KIND_RECORDING,
            file=mp3_file
        )

        # Viewer page contains audio element
        audio_resp = self.client.get(reverse("library:resource_viewer", kwargs={"pk": res_mp3.pk}))
        self.assertEqual(audio_resp.status_code, 200)
        self.assertContains(audio_resp, 'id="media-audio-element"')
        self.assertContains(audio_resp, 'فایل صوتی پادکست درس')

        # Raw stream returns audio/mpeg
        audio_stream = self.client.get(reverse("library:resource_raw_stream", kwargs={"pk": res_mp3.pk}))
        self.assertEqual(audio_stream.status_code, 200)
        self.assertEqual(audio_stream["Content-Type"], "audio/mpeg")


class LoginRedirectTests(TestCase):
    """
    آزمون هدایت صحیح کاربر پس از ورود (عدم مواجهه با خطای 404 یا مسیر نامعتبر /library/)
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="prof_test", password="password123")

    def test_login_redirect_default_to_home(self):
        # When logging in without any next parameter, user should be redirected to '/'
        response = self.client.post(reverse("login"), {
            "username": "prof_test",
            "password": "password123"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_login_redirect_handles_legacy_library_path(self):
        # Even if next is sent as '/library/', SafeLoginView should redirect to '/'
        response = self.client.post(reverse("login"), {
            "username": "prof_test",
            "password": "password123",
            "next": "/library/"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")

    def test_legacy_library_url_redirects_to_home(self):
        # Direct GET on /library/ should cleanly 302 to '/' rather than 404
        response = self.client.get("/library/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/")



