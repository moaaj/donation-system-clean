from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('school-fees/', include('myapp.urls')),  # School fees app
    path('donation/', include('donation2.urls')),  # Donation app
    path('waqaf/', include('waqaf.urls')),  # Waqaf app
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 