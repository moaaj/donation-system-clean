from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from myapp import views
from accounts.admin import custom_admin_site

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', custom_admin_site.urls),  # Custom admin with dashboard
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('school-fees/', include('myapp.urls')),
    path('form1-admin/', include('myapp.urls_form1_admin')),
    path('form3-admin/', include('myapp.urls_form3_admin')),
    path('donation/', include('donation2.urls')),
    path('waqaf/', include('waqaf.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



