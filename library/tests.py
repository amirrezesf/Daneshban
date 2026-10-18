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
