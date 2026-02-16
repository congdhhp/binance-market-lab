"""
URL configuration for market_data app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'symbols', views.SymbolViewSet, basename='symbol')
router.register(r'klines', views.KlineViewSet, basename='kline')
router.register(r'trades', views.TradeViewSet, basename='trade')
router.register(r'orderbook', views.OrderBookSnapshotViewSet, basename='orderbook')
router.register(r'tickers', views.Ticker24hViewSet, basename='ticker')
router.register(r'funding-rates', views.FundingRateViewSet, basename='funding-rate')
router.register(r'open-interest', views.OpenInterestViewSet, basename='open-interest')
router.register(r'ingestion-logs', views.IngestionLogViewSet, basename='ingestion-log')

app_name = 'market_data'

urlpatterns = [
    path('', include(router.urls)),
    path('ingest/backfill/', views.TriggerBackfillView.as_view(), name='trigger-backfill'),
    path('ingest/status/', views.IngestionStatusView.as_view(), name='ingestion-status'),
]
