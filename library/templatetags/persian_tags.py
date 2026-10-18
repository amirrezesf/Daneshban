import datetime
import jdatetime
from django import template
from django.utils import timezone

register = template.Library()

PERSIAN_DIGITS_TABLE = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter(name="persian_digits")
def persian_digits(value):
    """
    تبدیل ارقام انگلیسی به ارقام فارسی (۰۱۲۳۴۵۶۷۸۹).
    ورودی می‌تواند عدد، رشته یا شیء دیگری باشد.
    """
    if value is None or value == "":
        return ""
    return str(value).translate(PERSIAN_DIGITS_TABLE)


@register.filter(name="jalali_date")
def jalali_date(value, fmt="%Y/%m/%d"):
    """
    تبدیل تاریخ میلادی به تاریخ شمسی همراه با ارقام فارسی.
    پشتیبانی از datetime و date با منطقه زمانی تهران.
    """
    if not value:
        return ""

    try:
        # اگر datetime است، ابتدا به تایم‌زون محلی تبدیل کنیم
        if isinstance(value, datetime.datetime):
            if timezone.is_aware(value):
                value = timezone.localtime(value)
            j_dt = jdatetime.datetime.fromgregorian(datetime=value)
            formatted = j_dt.strftime(fmt)
        elif isinstance(value, datetime.date):
            j_d = jdatetime.date.fromgregorian(date=value)
            formatted = j_d.strftime(fmt)
        else:
            return str(value)
        return persian_digits(formatted)
    except Exception:
        return str(value)


@register.filter(name="persian_filesize")
def persian_filesize(bytes_size):
    """
    نمایش خوانای حجم فایل به زبان و ارقام فارسی (بایت، کیلوبایت، مگابایت، گیگابایت).
    """
    if bytes_size is None or bytes_size == "":
        return "۰ بایت"

    try:
        num = float(bytes_size)
    except (ValueError, TypeError):
        return "۰ بایت"

    units = ["بایت", "کیلوبایت", "مگابایت", "گیگابایت"]
    idx = 0
    while num >= 1024.0 and idx < len(units) - 1:
        num /= 1024.0
        idx += 1

    if idx == 0:
        formatted = f"{int(num)} {units[idx]}"
    else:
        # اگر رقم اعشار صفر است، اعشار نشان داده نشود
        formatted = f"{num:.1f} {units[idx]}".replace(".0 ", " ")
    
    return persian_digits(formatted)


@register.filter(name="split_tags")
def split_tags(value):
    """
    تفکیک رشته برچسب‌ها با کاما یا ویرگول فارسی
    """
    if not value:
        return []
    # جایگزینی ویرگول فارسی با کامای انگلیسی
    normalized = str(value).replace("،", ",")
    return [t.strip() for t in normalized.split(",") if t.strip()]
