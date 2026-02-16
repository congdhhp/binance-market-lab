"""
URL configuration for analysis app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.analysis.views import (
    IndicatorCacheViewSet,
    SignalRuleViewSet,
    SignalViewSet,
    PatternDetectionViewSet,
    ComputeIndicatorsView,
    ComputeAllIndicatorsView,
    GenerateSignalsView,
    GenerateAllSignalsView,
)

app_name = 'analysis'

router = DefaultRouter()
router.register(r'indicators', IndicatorCacheViewSet, basename='indicator')
router.register(r'rules', SignalRuleViewSet, basename='rule')
router.register(r'signals', SignalViewSet, basename='signal')
router.register(r'patterns', PatternDetectionViewSet, basename='pattern')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Action endpoints
    path('compute-indicators/', ComputeIndicatorsView.as_view(), name='compute-indicators'),
    path('compute-all-indicators/', ComputeAllIndicatorsView.as_view(), name='compute-all-indicators'),
    path('generate-signals/', GenerateSignalsView.as_view(), name='generate-signals'),
    path('generate-all-signals/', GenerateAllSignalsView.as_view(), name='generate-all-signals'),
]
