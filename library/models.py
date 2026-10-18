import os
import re
import datetime
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings
from django.urls import reverse

ALLOWED_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
    'txt', 'md', 'zip', 'rar', '7z', 'png', 'jpg', 'jpeg'
}


def sanitize_filename(filename: str) -> str:
    """
    پاک‌سازی نام فایل ضمن حفظ کاراکترهای فارسی و مجاز،
    و حذف کاراکترهای خطرناک مسیر یا تزریقی.
    """
    base_name, ext = os.path.splitext(filename)
    # حذف نویسه‌های غیرمجاز و کاراکترهای کنترلی
    clean_base = re.sub(r'[\\/*?:"<>|]', '', base_name)
    clean_base = re.sub(r'\s+', '_', clean_base.strip())
    # در صورتی که پس از تمیزسازی خالی شد، نام پیش‌فرضی قرار می‌دهیم
    if not clean_base:
        clean_base = "file"
    # کاراکترهای پسوند را به حروف کوچک تبدیل می‌کنیم
    clean_ext = ext.lower().strip()
    return f"{clean_base}{clean_ext}"


def validate_file_extension_and_size(file):
    """
    اعتبارسنجی پسوند فایل و حداکثر حجم مجاز بر اساس تنظیمات.
    """
    ext = os.path.splitext(file.name)[1][1:].lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed_list = '، '.join(sorted(ALLOWED_EXTENSIONS))
        raise ValidationError(
            f'فرمت فایل «{ext}» مجاز نیست. فرمت‌های معتبر عبارتند از: {allowed_list}'
        )

    max_bytes = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 100) * 1024 * 1024
    if file.size > max_bytes:
        max_mb = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 100)
        raise ValidationError(
            f'حجم فایل بارگذاری شده نمی‌تواند از {max_mb} مگابایت بیشتر باشد.'
        )


def resource_upload_path(instance, filename: str) -> str:
    """
    مسیر ذخیره فایل‌ها بر اساس شناسه درس و سال/ماه:
    resources/<lesson-id>/%Y/%m/<clean-filename>
    """
    clean_name = sanitize_filename(filename)
    now = datetime.datetime.now()
    lesson_id = instance.lesson_id or "general"
    return f"resources/{lesson_id}/{now.strftime('%Y/%m')}/{clean_name}"


class Semester(models.Model):
    """
    مدل ترم تحصیلی برای دسته‌بندی دوره‌ای دروس
    """
    title = models.CharField(
        max_length=150,
        verbose_name="عنوان ترم",
        help_text="مثال: ترم ۱ - پاییز ۱۴۰۴"
    )
    order = models.IntegerField(
        default=0,
        verbose_name="ترتیب نمایش",
        help_text="عدد کمتر در ابتدای لیست قرار می‌گیرد"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی"
    )

    class Meta:
        verbose_name = "ترم تحصیلی"
        verbose_name_plural = "ترم‌های تحصیلی"
        ordering = ["order", "-id"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """
    مدل درس دانشگاهی
    """
    title = models.CharField(
        max_length=200,
        verbose_name="عنوان درس"
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        blank=True,
        allow_unicode=True,
        verbose_name="شناسه یکتا (اسلاگ)",
        help_text="به‌صورت خودکار از روی عنوان درس تولید می‌شود"
    )
    professor = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="استاد درس"
    )
    semester = models.ForeignKey(
        Semester,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lessons",
        verbose_name="ترم تحصیلی"
    )
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات و سرفصل‌ها"
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        default="#2563eb",
        verbose_name="رنگ نشانگر درس",
        help_text="کد رنگ هگز، مانند #2563eb"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی"
    )

    class Meta:
        verbose_name = "درس"
        verbose_name_plural = "درس‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        if self.professor:
            return f"{self.title} ({self.professor})"
        return self.title

    def get_absolute_url(self):
        return reverse("library:lesson_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True) or "lesson"
            slug = base_slug
            counter = 1
            while Lesson.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Resource(models.Model):
    """
    مدل منبع آموزشی (جزوه، اسلاید، تمرین، نمونه سوال و ...)
    """
    KIND_HANDOUT = "handout"
    KIND_SLIDES = "slides"
    KIND_ASSIGNMENT = "assignment"
    KIND_EXAM = "exam"
    KIND_BOOK = "book"
    KIND_OTHER = "other"

    KIND_CHOICES = [
        (KIND_HANDOUT, "جزوه"),
        (KIND_SLIDES, "اسلاید"),
        (KIND_ASSIGNMENT, "تمرین"),
        (KIND_EXAM, "نمونه سوال"),
        (KIND_BOOK, "کتاب"),
        (KIND_OTHER, "سایر"),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="resources",
        verbose_name="درس مربوطه"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="عنوان منبع"
    )
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات تکمیلی"
    )
    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        default=KIND_HANDOUT,
        verbose_name="نوع منبع"
    )
    file = models.FileField(
        upload_to=resource_upload_path,
        validators=[validate_file_extension_and_size],
        verbose_name="فایل پیوست"
    )
    session_number = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="شماره جلسه",
        help_text="برای جزوه‌ها یا اسلایدهای جلسات مشخص (اختیاری)"
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="برچسب‌ها",
        help_text="برچسب‌ها را با کاما جدا کنید (مثال: میان‌ترم، مبحث انتگرال)"
    )
    file_size = models.BigIntegerField(
        default=0,
        verbose_name="حجم فایل (بایت)"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ بارگذاری"
    )
    download_count = models.IntegerField(
        default=0,
        verbose_name="تعداد دانلود"
    )

    class Meta:
        verbose_name = "منبع آموزشی"
        verbose_name_plural = "منابع آموزشی"
        ordering = ["session_number", "-uploaded_at"]

    def __str__(self):
        return f"{self.get_kind_display()} - {self.title}"

    def save(self, *args, **kwargs):
        if self.file and hasattr(self.file, "size"):
            try:
                self.file_size = self.file.size
            except Exception:
                pass
        super().save(*args, **kwargs)

    @property
    def file_extension(self):
        if self.file and self.file.name:
            return os.path.splitext(self.file.name)[1][1:].lower()
        return ""

    @property
    def can_preview_in_browser(self):
        """
        آیا این فرمت مستقیماً در مرورگر قابل مشاهده است (PDF، تصویر، ویدیو، صوت، متن)
        """
        return self.file_extension in {
            'pdf', 'png', 'jpg', 'jpeg', 'webp', 'mp4', 'webm', 'mp3', 'wav', 'ogg', 'txt', 'md'
        }

    @property
    def preview_type(self):
        """
        تعیین نوع پیش‌نمایش فایل برای بارگذاری پلیر یا فریم مناسب
        """
        ext = self.file_extension
        if ext == 'pdf':
            return 'pdf'
        if ext in {'png', 'jpg', 'jpeg', 'webp', 'svg'}:
            return 'image'
        if ext in {'mp4', 'webm'}:
            return 'video'
        if ext in {'mp3', 'wav', 'ogg'}:
            return 'audio'
        if ext in {'txt', 'md'}:
            return 'text'
        if ext in {'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx'}:
            return 'office'
        if ext in {'zip', 'rar', '7z'}:
            return 'archive'
        return 'other'

    @property
    def is_office_file(self):
        return self.file_extension in {'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx'}

    @property
    def office_app_name(self):
        ext = self.file_extension
        if ext in {'doc', 'docx'}:
            return 'Microsoft Word'
        if ext in {'ppt', 'pptx'}:
            return 'Microsoft PowerPoint'
        if ext in {'xls', 'xlsx'}:
            return 'Microsoft Excel'
        return 'نرم‌افزار آفیس'

    @property
    def office_app_protocol(self):
        ext = self.file_extension
        if ext in {'doc', 'docx'}:
            return 'ms-word'
        if ext in {'ppt', 'pptx'}:
            return 'ms-powerpoint'
        if ext in {'xls', 'xlsx'}:
            return 'ms-excel'
        return ''
