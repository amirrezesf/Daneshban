from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("health/", views.health_check, name="health"),
    path("", views.home_view, name="home"),
    path("search/", views.search_view, name="search"),
    path("lesson/create/", views.lesson_create_view, name="lesson_create"),
    path("lesson/<str:slug>/", views.lesson_detail_view, name="lesson_detail"),
    path("lesson/<str:slug>/edit/", views.lesson_update_view, name="lesson_edit"),
    path("lesson/<str:slug>/delete/", views.lesson_delete_view, name="lesson_delete"),
    path("resource/create/", views.resource_create_view, name="resource_create"),
    path("resource/<int:pk>/delete/", views.resource_delete_view, name="resource_delete"),
    path("resource/<int:pk>/edit/", views.resource_update_view, name="resource_edit"),
    path("resource/<int:pk>/download/", views.download_resource_view, name="resource_download"),
    path("resource/<int:pk>/preview/", views.resource_viewer_view, name="resource_viewer"),
    path("resource/<int:pk>/raw/", views.resource_raw_stream_view, name="resource_raw_stream"),
    # مدیریت ترم‌های تحصیلی
    path("semesters/", views.semester_list_view, name="semester_list"),
    path("semesters/create/", views.semester_create_view, name="semester_create"),
    path("semesters/<int:pk>/edit/", views.semester_update_view, name="semester_edit"),
    path("semesters/<int:pk>/delete/", views.semester_delete_view, name="semester_delete"),
]
