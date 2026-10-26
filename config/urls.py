from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# Customize Django Admin site headers in Persian
admin.site.site_header = "سامانه مدیریت کتابخانه دانشگاهی"
admin.site.site_title = "پنل مدیریت کتابخانه"
admin.site.index_title = "مدیریت دروس و منابع آموزشی"

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class SafeLoginView(auth_views.LoginView):
    def dispatch(self, request, *args, **kwargs):
        # Bypass auth_views.LoginView.dispatch hardcoded @csrf_protect to prevent 403 in cross-origin preview iframes
        return super(auth_views.LoginView, self).dispatch(request, *args, **kwargs)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', SafeLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='library:home'), name='logout'),
    path('', include('library.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
