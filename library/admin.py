from django.contrib import admin
from django.utils.html import format_html
from .models import Semester, Lesson, Resource
from .templatetags.persian_tags import persian_digits, persian_filesize, jalali_date


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("title", "season_year_badge", "start_date_display", "order_display", "lessons_count", "created_at_jalali")
    search_fields = ("title", "description")
    ordering = ("order", "-id")

    @admin.display(description="فصل و سال")
    def season_year_badge(self, obj):
        info = obj.season_info
        if info:
            return format_html(
                '<span style="display:inline-flex; align-items:center; gap:4px; padding:2px 8px; border-radius:12px; font-size:12px; font-weight:600; background:{}; color:#fff;">{} {}</span>',
                info["color"],
                info["icon"],
                info["label"],
            )
        return "-"

    @admin.display(description="تاریخ شروع", ordering="start_date")
    def start_date_display(self, obj):
        if obj.start_date:
            info = obj.season_info
            return info["j_date_str"] if info else jalali_date(obj.start_date)
        return "مشخص نشده"

    @admin.display(description="ترتیب نمایش", ordering="order")
    def order_display(self, obj):
        return persian_digits(obj.order)

    @admin.display(description="تعداد دروس")
    def lessons_count(self, obj):
        return persian_digits(obj.lessons.count())

    @admin.display(description="تاریخ ایجاد", ordering="created_at")
    def created_at_jalali(self, obj):
        return jalali_date(obj.created_at)


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 1
    fields = ("title", "kind", "session_number", "file", "download_count")
    readonly_fields = ("download_count",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "color_badge", "professor", "semester", "resources_count", "created_at_jalali")
    list_filter = ("semester",)
    search_fields = ("title", "professor", "description")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ResourceInline]

    @admin.display(description="نشانگر")
    def color_badge(self, obj):
        color = obj.color or "#2563eb"
        return format_html(
            '<span style="display:inline-block; width:18px; height:18px; border-radius:4px; background-color:{}; vertical-align:middle;"></span>',
            color
        )

    @admin.display(description="تعداد منابع")
    def resources_count(self, obj):
        return persian_digits(obj.resources.count())

    @admin.display(description="تاریخ ایجاد", ordering="created_at")
    def created_at_jalali(self, obj):
        return jalali_date(obj.created_at)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson_or_standalone", "semester_display", "kind_badge", "session_display", "size_display", "download_count_display", "uploaded_at_jalali")
    list_filter = ("kind", "semester", "lesson__semester", "lesson")
    search_fields = ("title", "description", "tags", "lesson__title")
    autocomplete_fields = ("lesson",)
    readonly_fields = ("file_size", "download_count", "uploaded_at")

    @admin.display(description="درس / وابستگی")
    def lesson_or_standalone(self, obj):
        if obj.lesson:
            return obj.lesson.title
        return format_html('<span style="color:#64748b; font-style:italic;">مستقل / عمومی</span>')

    @admin.display(description="ترم")
    def semester_display(self, obj):
        sem = obj.effective_semester
        return sem.title if sem else "—"

    @admin.display(description="نوع", ordering="kind")
    def kind_badge(self, obj):
        return obj.get_kind_display()

    @admin.display(description="جلسه", ordering="session_number")
    def session_display(self, obj):
        if obj.session_number:
            return f"جلسه {persian_digits(obj.session_number)}"
        return "—"

    @admin.display(description="حجم", ordering="file_size")
    def size_display(self, obj):
        return persian_filesize(obj.file_size)

    @admin.display(description="دانلودها", ordering="download_count")
    def download_count_display(self, obj):
        return persian_digits(obj.download_count)

    @admin.display(description="تاریخ بارگذاری", ordering="uploaded_at")
    def uploaded_at_jalali(self, obj):
        return jalali_date(obj.uploaded_at)
