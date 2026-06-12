"""
URL Routing for ClassiFind AI
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'documents', views.DocumentUploadViewSet, basename='document')
router.register(r'classifieds', views.ExtractedClassifiedViewSet, basename='classified')

app_name = 'classified_app'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='dashboard_stats'),
]
