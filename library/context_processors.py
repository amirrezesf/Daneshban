from .models import Semester, Lesson


def library_sidebar(request):
    """
    Context processor to provide semesters and lessons for the collapsible GitLab sidebar.
    """
    try:
        semesters = Semester.objects.prefetch_related('lessons').order_by('order', 'id')
        all_lessons = Lesson.objects.select_related('semester').order_by('title')
        return {
            'sidebar_semesters': semesters,
            'sidebar_lessons': all_lessons,
        }
    except Exception:
        return {
            'sidebar_semesters': [],
            'sidebar_lessons': [],
        }
