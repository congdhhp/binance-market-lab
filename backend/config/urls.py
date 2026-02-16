"""
Django URL Configuration for binance-market-lab project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1
    path('api/v1/market-data/', include('apps.market_data.urls')),
    path('api/v1/analysis/', include('apps.analysis.urls')),
    path('api/v1/backtest/', include('apps.backtest.urls')),
    path('api/v1/orderbook/', include('apps.orderbook.urls')),
    path('api/v1/alerts/', include('apps.alerts.urls')),
    path('api/v1/anomaly/', include('apps.anomaly.urls')),
    path('api/v1/factors/', include('apps.factors.urls')),
    
    # Health check
    path('api/health/', lambda request: JsonResponse({'status': 'healthy'})),
]

# Serve static files in development/production via Django
if settings.DEBUG or True:  # Always serve static files for now
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
