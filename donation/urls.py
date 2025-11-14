from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from . import views
from waqaf.waqaf_admin import waqaf_admin_site

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # Language switching
] + i18n_patterns(
    path('', include(('myapp.urls', 'myapp'), namespace='myapp')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/create-donation-event/', views.create_donation_event, name='create_donation_event'),
    path('donation2/', include('donation2.urls')),
    path('waqaf/', include('waqaf.urls')),
    path('waqaf-admin/', waqaf_admin_site.urls),  # Waqaf admin site
) 