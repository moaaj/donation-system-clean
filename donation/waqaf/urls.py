from django.urls import path
from . import views

app_name = 'waqaf'  # Add namespace for the app

urlpatterns = [
    path('dashboard/', views.waqaf_dashboard, name='waqaf_dashboard'),
    path('', views.waqaf, name='waqaf'),
    path('contribute_waqaf/', views.contribute_waqaf, name='contribute_waqaf'),
    path('asset/<int:asset_id>/', views.asset_detail, name='asset_detail'),
    path('certificate/<int:contribution_id>/', views.download_certificate, name='download_certificate'),
    path('ai-analytics/', views.waqaf_ai_analytics, name='waqaf_ai_analytics'),
]
