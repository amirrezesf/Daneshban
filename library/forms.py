from django import forms
from .models import Lesson, Resource, Semester


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
        fields = ["lesson", "title", "kind", "session_number", "file", "description", "tags"]
        widgets = {
            "lesson": forms.Select(attrs={
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
                "accept": ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md,.zip,.rar,.7z,.png,.jpg,.jpeg",
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


class ResourceEditForm(forms.ModelForm):
    """
    فرم ویرایش منبع با امکان اختیاری بودن فایل در صورت عدم تغییر فایل قبلی
    """
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            "class": "form-input",
            "accept": ".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.txt,.md,.zip,.rar,.7z,.png,.jpg,.jpeg",
        }),
        label="تغییر فایل (اختیاری)"
    )

    class Meta:
        model = Resource
        fields = ["lesson", "title", "kind", "session_number", "file", "description", "tags"]
        widgets = {
            "lesson": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-input", "dir": "auto"}),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "session_number": forms.NumberInput(attrs={"class": "form-input", "min": "1"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3, "dir": "auto"}),
            "tags": forms.TextInput(attrs={"class": "form-input", "dir": "auto"}),
        }
