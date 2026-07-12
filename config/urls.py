from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("kitchen/", include("apps.kitchen.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", include("apps.core.urls")),
]

handler404 = "apps.core.views.custom_404_view"
handler500 = "apps.core.views.custom_500_view"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
