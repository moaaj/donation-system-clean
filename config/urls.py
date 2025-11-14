from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching
] + i18n_patterns(
    path('', include('myapp.urls')),  # Home page
    path('school-fees/', include('myapp.urls')),  # School fees app
    path('donation/', include('donation2.urls')),  # Donation app
    path('waqaf/', include('waqaf.urls')),  # Waqaf app
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 