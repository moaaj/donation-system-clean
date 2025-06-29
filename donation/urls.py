from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('myapp.urls', 'myapp'), namespace='myapp')),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/create-donation-event/', views.create_donation_event, name='create_donation_event'),
] 