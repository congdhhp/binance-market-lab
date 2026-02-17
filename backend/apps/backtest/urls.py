"""
URL configuration for backtest app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.backtest.views import (
    StrategyViewSet,
    BacktestRunViewSet,
    TradeViewSet,
    RunBacktestView,
    OptimizeStrategyView,
    BacktestStatsView,
)

app_name = 'backtest'

router = DefaultRouter()
router.register(r'strategies', StrategyViewSet, basename='strategy')
router.register(r'runs', BacktestRunViewSet, basename='run')
router.register(r'trades', TradeViewSet, basename='trade')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Action endpoints
    path('run/', RunBacktestView.as_view(), name='run-backtest'),
    path('optimize/', OptimizeStrategyView.as_view(), name='optimize-strategy'),
    path('stats/', BacktestStatsView.as_view(), name='stats'),
]
