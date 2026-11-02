import re
import datetime
from django import forms
from .models import Lesson, Resource, Semester


class SemesterForm(forms.ModelForm):
    start_date = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "type": "date",
            "id": "id_start_date",
        }),
        label="تاریخ شروع ترم",
        help_text="تاریخ آغاز ترم را انتخاب یا وارد نمایید. فصل و سال به صورت خودکار محاسبه خواهد شد."
    )

    class Meta:
        model = Semester
        fields = ["title", "start_date", "order", "description"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "مثال: نیم‌سال اول ۱۴۰۴ - ۱۴۰۵ (یا ترم مهر)",
                "dir": "auto",
                "id": "id_semester_title",
            }),
            "order": forms.NumberInput(attrs={
                "class": "form-input",
                "placeholder": "مثلاً: ۱ (اولویت نمایش)",
                "min": "0",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "توضیحات تکمیلی، تقویم آموزشی یا یادداشت‌های مربوط به این ترم...",
                "dir": "auto",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.start_date:
            self.initial["start_date"] = self.instance.start_date.strftime("%Y-%m-%d")

    def clean_start_date(self):
        val = self.cleaned_data.get("start_date")
        if not val:
            return None
        
        # اگر شیء date است، مستقیماً برگردانیم
        if isinstance(val, (datetime.date, datetime.datetime)):
            return val if isinstance(val, datetime.date) else val.date()

        val_str = str(val).strip()
        # تبدیل اعداد فارسی/عربی به انگلیسی
        fa_to_en = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
        val_str = val_str.translate(fa_to_en)

        # بررسی فرمت استاندارد میلادی YYYY-MM-DD
        iso_match = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", val_str)
        if iso_match:
            y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            # اگر سال بین ۱۳۰۰ تا ۱۵۰۰ است، تاریخ شمسی وارد شده
            if 1300 <= y <= 1500:
                try:
                    import jdatetime
                    j_date = jdatetime.date(y, m, d)
                    return j_date.togregorian()
                except Exception as e:
                    raise forms.ValidationError("تاریخ شمسی وارد شده معتبر نمی‌باشد.")
            else:
                try:
                    return datetime.date(y, m, d)
                except ValueError:
                    raise forms.ValidationError("تاریخ میلادی وارد شده معتبر نمی‌باشد.")
        
        raise forms.ValidationError("فرمت تاریخ نامعتبر است. لطفاً از تقویم یا ساختار YYYY-MM-DD استفاده نمایید.")


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["title", "professor", "semester", "description", "color"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "مثال: ریاضی عمومی ۱",
                "dir": "auto",
            }),
            "professor": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "مثال: دکتر حسینی",
                "dir": "auto",
            }),
            "semester": forms.Select(attrs={
                "class": "form-select",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 4,
                "placeholder": "سرفصل‌ها، ساعات تشکیل کلاس یا مراجع درس...",
                "dir": "auto",
            }),
            "color": forms.TextInput(attrs={
                "class": "form-input",
                "type": "color",
                "style": "height: 44px; padding: 4px; cursor: pointer;",
            }),
        }


class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ["lesson", "semester", "title", "kind", "session_number", "file", "description", "tags"]
        widgets = {
            "lesson": forms.Select(attrs={
                "class": "form-select",
            }),
            "semester": forms.Select(attrs={
                "class": "form-select",
            }),
            "title": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "مثال: جزوه دست‌نویس فصل دوم - ماتریس‌ها",
                "dir": "auto",
            }),
            "kind": forms.Select(attrs={
                "class": "form-select",
            }),
            "session_number": forms.NumberInput(attrs={
                "class": "form-input",
                "placeholder": "شماره جلسه، مثلاً ۲",
                "min": "1",
            }),
            "file": forms.FileInput(attrs={
                "class": "form-input",
                "accept": ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md,.zip,.rar,.7z,.png,.jpg,.jpeg,.mp4,.mp3,.m4a,.wav,.ogg,.webm,audio/*,video/*",
            }),
            "description": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
                "placeholder": "نکات مهم این فایل یا مباحث پوشش داده شده...",
                "dir": "auto",
            }),
            "tags": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "مثال: میان‌ترم، مبحث انتگرال، حل تمرین",
                "dir": "auto",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lesson"].required = False
        self.fields["lesson"].empty_label = "--- بدون درس (منبع مستقل / عمومی دانشگاه) ---"
        self.fields["semester"].required = False
        self.fields["semester"].empty_label = "--- بدون ترم (عمومی کلیه ترم‌ها) ---"


class ResourceEditForm(forms.ModelForm):
    """
    فرم ویرایش منبع با امکان اختیاری بودن فایل در صورت عدم تغییر فایل قبلی
    """
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            "class": "form-input",
            "accept": ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md,.zip,.rar,.7z,.png,.jpg,.jpeg,.mp4,.mp3,.m4a,.wav,.ogg,.webm,audio/*,video/*",
        }),
        label="تغییر فایل (اختیاری)"
    )

    class Meta:
        model = Resource
        fields = ["lesson", "semester", "title", "kind", "session_number", "file", "description", "tags"]
        widgets = {
            "lesson": forms.Select(attrs={"class": "form-select"}),
            "semester": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-input", "dir": "auto"}),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "session_number": forms.NumberInput(attrs={"class": "form-input", "min": "1"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3, "dir": "auto"}),
            "tags": forms.TextInput(attrs={"class": "form-input", "dir": "auto"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["lesson"].required = False
        self.fields["lesson"].empty_label = "--- بدون درس (منبع مستقل / عمومی دانشگاه) ---"
        self.fields["semester"].required = False
        self.fields["semester"].empty_label = "--- بدون ترم (عمومی کلیه ترم‌ها) ---"

