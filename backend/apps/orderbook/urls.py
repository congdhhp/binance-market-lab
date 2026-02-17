"""
URL configuration for orderbook analytics.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.orderbook import views

app_name = 'orderbook'

router = DefaultRouter()
router.register(r'analysis', views.OrderbookAnalysisViewSet, basename='analysis')
router.register(r'alerts', views.ImbalanceAlertViewSet, basename='alerts')
router.register(r'risk', views.RiskMetricsViewSet, basename='risk')
router.register(r'correlation', views.CorrelationViewSet, basename='correlation')
router.register(r'regime', views.RegimeDetectionViewSet, basename='regime')

urlpatterns = [
    path('', include(router.urls)),
]
