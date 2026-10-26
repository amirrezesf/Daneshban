import os
import mimetypes
import urllib.parse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.http import FileResponse, Http404, HttpResponse
from django.core.paginator import Paginator
from django.urls import reverse
from .models import Lesson, Resource, Semester
from .forms import LessonForm, ResourceForm, ResourceEditForm, SemesterForm


def home_view(request):
    """
    صفحه اصلی: نمایش کارت‌های دروس دانشگاهی و منابع مستقل همراه با فیلتر ترم و جستجو
    """
    query = request.GET.get("q", "").strip()
    semester_id = request.GET.get("semester", "").strip()

    lessons = Lesson.objects.annotate(
        resources_total=Count("resources")
    ).select_related("semester").order_by("-created_at")

    # منابع مستقل و عمومی (منابعی که درس مشخصی ندارند)
    standalone_resources = Resource.objects.filter(
        lesson__isnull=True
    ).select_related("semester").order_by("-uploaded_at")

    if query:
        lessons = lessons.filter(
            Q(title__icontains=query) |
            Q(professor__icontains=query) |
            Q(description__icontains=query)
        )
        standalone_resources = standalone_resources.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query)
        )

    if semester_id and semester_id.isdigit():
        lessons = lessons.filter(semester_id=int(semester_id))
        standalone_resources = standalone_resources.filter(semester_id=int(semester_id))

    from django.db.models import Sum

    semesters = Semester.objects.all().order_by("order", "id")

    # آمار کلی سامانه برای بخش معرفی هدر
    total_resources_all = Resource.objects.count()
    total_downloads_all = Resource.objects.aggregate(total=Sum("download_count"))["total"] or 0

    # صفحه‌بندی دروس (۱۲ درس در هر صفحه)
    paginator = Paginator(lessons, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "standalone_resources": standalone_resources,
        "total_standalone": standalone_resources.count(),
        "semesters": semesters,
        "selected_semester": semester_id,
        "query": query,
        "total_lessons": paginator.count,
        "total_resources_all": total_resources_all,
        "total_downloads_all": total_downloads_all,
        "total_semesters_all": semesters.count(),
    }
    return render(request, "library/home.html", context)


def lesson_detail_view(request, slug):
    """
    صفحه جزئیات درس: اطلاعات درس و منابع دسته‌بندی شده بر اساس نوع (جزوه، اسلاید، ...)
    و مرتب‌شده بر اساس شماره جلسه و سپس تاریخ بارگذاری
    """
    lesson = get_object_or_404(Lesson.objects.select_related("semester"), slug=slug)

    # گروه‌بندی منابع بر اساس نوع
    all_resources = lesson.resources.all().order_by("session_number", "-uploaded_at")

    groups = []
    kind_labels = dict(Resource.KIND_CHOICES)
    order_kinds = [
        Resource.KIND_HANDOUT,
        Resource.KIND_SLIDES,
        Resource.KIND_ASSIGNMENT,
        Resource.KIND_EXAM,
        Resource.KIND_BOOK,
        Resource.KIND_OTHER,
    ]

    for kind_code in order_kinds:
        items = [r for r in all_resources if r.kind == kind_code]
        if items:
            groups.append({
                "code": kind_code,
                "label": kind_labels.get(kind_code, kind_code),
                "items": items,
                "count": len(items),
            })

    context = {
        "lesson": lesson,
        "resource_groups": groups,
        "total_resources": len(all_resources),
    }
    return render(request, "library/lesson_detail.html", context)


def search_view(request):
    """
    جستجوی جامع در تمامی منابع، دروس، برچسب‌ها و توضیحات
    """
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        results = Resource.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(lesson__title__icontains=query) |
            Q(lesson__professor__icontains=query)
        ).select_related("lesson", "lesson__semester").order_by("-uploaded_at")

    paginator = Paginator(results, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "query": query,
        "page_obj": page_obj,
        "total_results": paginator.count if query else 0,
    }
    return render(request, "library/search_results.html", context)


def download_resource_view(request, pk):
    """
    ویوی دانلود فایل منبع:
    - افزایش شمارنده دانلود
    - تعیین Content-Disposition استاندارد با پشتیبانی نام‌های فارسی (RFC 5987)
    - مدیریت خطای فایل‌های ناموجود در دیسک
    """
    resource = get_object_or_404(Resource, pk=pk)

    if not resource.file or not resource.file.storage.exists(resource.file.name):
        messages.error(
            request,
            f"متأسفانه فایل منبع «{resource.title}» بر روی سرور یافت نشد. لطفاً با مدیر سامانه تماس بگیرید."
        )
        if resource.lesson:
            return redirect(resource.lesson.get_absolute_url())
        return redirect("library:home")

    # افزایش شمارنده دانلود
    Resource.objects.filter(pk=pk).update(download_count=resource.download_count + 1)

    file_path = resource.file.path
    original_filename = os.path.basename(resource.file.name)
    _, ext = os.path.splitext(original_filename)

    # حدس نوع محتوا
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "application/octet-stream"

    # آماده‌سازی نام فایل برای استاندارد RFC 5987
    ascii_fallback = f"resource_{resource.id}{ext}"
    encoded_filename = urllib.parse.quote(original_filename)

    response = FileResponse(open(file_path, "rb"), content_type=content_type)
    response["Content-Disposition"] = (
        f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_filename}'
    )
    return response


# =========================================================================
# بخش مدیریت دروس (نیاز به لاگین)
# =========================================================================

@login_required
def lesson_create_view(request):
    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save()
            messages.success(request, f"درس «{lesson.title}» با موفقیت اضافه شد.")
            return redirect(lesson.get_absolute_url())
    else:
        form = LessonForm()

    return render(request, "library/lesson_form.html", {
        "form": form,
        "title": "افزودن درس جدید",
        "is_edit": False,
    })


@login_required
def lesson_update_view(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save()
            messages.success(request, f"اطلاعات درس «{lesson.title}» با موفقیت به‌روزرسانی شد.")
            return redirect(lesson.get_absolute_url())
    else:
        form = LessonForm(instance=lesson)

    return render(request, "library/lesson_form.html", {
        "form": form,
        "lesson": lesson,
        "title": f"ویرایش درس: {lesson.title}",
        "is_edit": True,
    })


@login_required
def lesson_delete_view(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    if request.method == "POST":
        title = lesson.title
        lesson.delete()
        messages.success(request, f"درس «{title}» و کلیه منابع آن با موفقیت حذف شد.")
        return redirect("library:home")

    return render(request, "library/lesson_confirm_delete.html", {
        "lesson": lesson
    })


# =========================================================================
# بخش مدیریت منابع و فایل‌ها (نیاز به لاگین)
# =========================================================================

@login_required
def resource_create_view(request):
    lesson_id = request.GET.get("lesson")
    semester_id = request.GET.get("semester")
    initial = {}
    if lesson_id and lesson_id.isdigit():
        initial["lesson"] = int(lesson_id)
    if semester_id and semester_id.isdigit():
        initial["semester"] = int(semester_id)

    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save()
            if resource.lesson:
                messages.success(
                    request,
                    f"منبع «{resource.title}» با موفقیت برای درس «{resource.lesson.title}» بارگذاری شد."
                )
                return redirect(resource.lesson.get_absolute_url())
            else:
                messages.success(
                    request,
                    f"منبع مستقل «{resource.title}» با موفقیت بارگذاری شد و در صفحه اصلی قرار گرفت."
                )
                return redirect("library:home")
    else:
        form = ResourceForm(initial=initial)

    return render(request, "library/resource_form.html", {
        "form": form,
        "title": "آپلود منبع جدید",
        "is_edit": False,
    })


@login_required
def resource_update_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if request.method == "POST":
        form = ResourceEditForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            updated = form.save()
            messages.success(request, f"منبع «{updated.title}» با موفقیت به‌روزرسانی شد.")
            if updated.lesson:
                return redirect(updated.lesson.get_absolute_url())
            return redirect("library:home")
    else:
        form = ResourceEditForm(instance=resource)

    return render(request, "library/resource_form.html", {
        "form": form,
        "resource": resource,
        "title": f"ویرایش منبع: {resource.title}",
        "is_edit": True,
    })


@login_required
def resource_delete_view(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    lesson = resource.lesson
    if request.method == "POST":
        title = resource.title
        resource.delete()
        messages.success(request, f"منبع «{title}» با موفقیت حذف شد.")
        if lesson:
            return redirect(lesson.get_absolute_url())
        return redirect("library:home")

    return render(request, "library/resource_confirm_delete.html", {
        "resource": resource,
        "lesson": lesson,
    })


def resource_raw_stream_view(request, pk):
    """
    سرو مستقیم فایل در مرورگر به صورت inline جهت پیش‌نمایش در فریم‌ها و پلیرها
    """
    resource = get_object_or_404(Resource, pk=pk)

    if not resource.file or not resource.file.storage.exists(resource.file.name):
        raise Http404("فایل مورد نظر در سرور موجود نیست.")

    file_path = resource.file.path
    original_filename = os.path.basename(resource.file.name)
    _, ext = os.path.splitext(original_filename)

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        if ext.lower() == '.pdf':
            content_type = 'application/pdf'
        elif ext.lower() in ('.mp4', '.m4v'):
            content_type = 'video/mp4'
        elif ext.lower() == '.mp3':
            content_type = 'audio/mpeg'
        elif ext.lower() in ('.txt', '.md'):
            content_type = 'text/plain; charset=utf-8'
        else:
            content_type = 'application/octet-stream'

    ascii_fallback = f"view_{resource.id}{ext}"
    encoded_filename = urllib.parse.quote(original_filename)

    response = FileResponse(open(file_path, "rb"), content_type=content_type)
    response["Content-Disposition"] = (
        f'inline; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded_filename}'
    )
    return response


def resource_viewer_view(request, pk):
    """
    صفحه پیش‌نمایش اختصاصی منبع با ساختار GitLab Blob Viewer:
    - پیش‌نمایش درون‌مرورگری برای PDF، تصویر، ویدیو، صوت و متون
    - دکمه اتصال و بازگشایی در برنامه‌های ثالث (Google Docs Viewer، Office Apps و ...) برای سایر فرمت‌ها
    """
    resource = get_object_or_404(Resource.objects.select_related("lesson", "lesson__semester", "semester"), pk=pk)
    
    text_content = ""
    if resource.preview_type == "text" and resource.file and resource.file.storage.exists(resource.file.name):
        try:
            with open(resource.file.path, "r", encoding="utf-8", errors="replace") as f:
                text_content = f.read(50000) # خواندن تا ۵۰ کیلوبایت
        except Exception:
            text_content = ""

    # ایجاد آدرس کامل برای پیش‌نمایش آنلاین در گوگل داکس در صورت وجود دامنه عمومی
    raw_url = request.build_absolute_uri(reverse("library:resource_raw_stream", kwargs={"pk": resource.pk}))
    google_docs_url = f"https://docs.google.com/viewer?url={urllib.parse.quote(raw_url)}&embedded=true"

    context = {
        "resource": resource,
        "lesson": resource.lesson,
        "raw_url": raw_url,
        "google_docs_url": google_docs_url,
        "text_content": text_content,
    }
    return render(request, "library/resource_viewer.html", context)


# =========================================================================
# بخش مدیریت ترم‌های تحصیلی (Semester Management)
# =========================================================================

def semester_list_view(request):
    """
    صفحه مدیریت و فهرست ترم‌های تحصیلی:
    - نمایش کلیه ترم‌ها، تاریخ شروع، فصل و سال محاسبه‌شده، و تعداد دروس وابسته
    - دکمه‌های افزودن، ویرایش و حذف برای کاربران مجاز
    """
    semesters = Semester.objects.annotate(
        lessons_total=Count("lessons")
    ).order_by("order", "-start_date", "-id")

    total_lessons_assigned = sum(s.lessons_total for s in semesters)

    context = {
        "semesters": semesters,
        "total_semesters": semesters.count(),
        "total_lessons_assigned": total_lessons_assigned,
    }
    return render(request, "library/semester_list.html", context)


@login_required
def semester_create_view(request):
    """
    ایجاد ترم جدید همراه با تعیین تاریخ شروع و محاسبه خودکار فصل و سال
    """
    if request.method == "POST":
        form = SemesterForm(request.POST)
        if form.is_valid():
            semester = form.save()
            season_desc = f" ({semester.season_and_year})" if semester.season_and_year else ""
            messages.success(
                request,
                f"ترم «{semester.title}»{season_desc} با موفقیت ثبت شد."
            )
            return redirect("library:semester_list")
    else:
        form = SemesterForm()

    return render(request, "library/semester_form.html", {
        "form": form,
        "title": "افزودن ترم تحصیلی جدید",
        "is_edit": False,
    })


@login_required
def semester_update_view(request, pk):
    """
    ویرایش اطلاعات ترم تحصیلی و به‌روزرسانی تاریخ شروع
    """
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == "POST":
        form = SemesterForm(request.POST, instance=semester)
        if form.is_valid():
            updated = form.save()
            season_desc = f" ({updated.season_and_year})" if updated.season_and_year else ""
            messages.success(
                request,
                f"اطلاعات ترم «{updated.title}»{season_desc} با موفقیت به‌روزرسانی شد."
            )
            return redirect("library:semester_list")
    else:
        form = SemesterForm(instance=semester)

    return render(request, "library/semester_form.html", {
        "form": form,
        "semester": semester,
        "title": f"ویرایش ترم: {semester.title}",
        "is_edit": True,
    })


@login_required
def semester_delete_view(request, pk):
    """
    حذف ترم تحصیلی با ارائه پیام هشدار در صورت انتساب دروس به آن
    """
    semester = get_object_or_404(Semester, pk=pk)
    lessons_count = semester.lessons.count()

    if request.method == "POST":
        title = semester.title
        semester.delete()
        messages.success(
            request,
            f"ترم تحصیلی «{title}» با موفقیت حذف شد."
        )
        return redirect("library:semester_list")

    return render(request, "library/semester_confirm_delete.html", {
        "semester": semester,
        "lessons_count": lessons_count,
    })


