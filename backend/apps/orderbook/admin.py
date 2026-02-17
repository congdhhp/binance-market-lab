"""
Django admin for orderbook analytics.
"""
from django.contrib import admin
from apps.orderbook.models import OrderbookAnalysis, ImbalanceAlert


@admin.register(OrderbookAnalysis)
class OrderbookAnalysisAdmin(admin.ModelAdmin):
    """Admin for orderbook analysis."""
    
    list_display = [
        'symbol',
        'timestamp',
        'spread_bps',
        'imbalance_ratio',
        'liquidity_score',
        'has_liquidity_hole',
    ]
    
    list_filter = [
        'symbol',
        'has_liquidity_hole',
        'timestamp',
    ]
    
    search_fields = [
        'symbol__name',
    ]
    
    readonly_fields = [
        'id',
        'symbol',
        'timestamp',
        'bid_price',
        'ask_price',
        'mid_price',
        'spread_absolute',
        'spread_bps',
        'bid_depth_10',
        'ask_depth_10',
        'total_depth_10',
        'imbalance_ratio',
        'imbalance_pct',
        'vwap_buy_1000',
        'vwap_sell_1000',
        'liquidity_score',
        'has_liquidity_hole',
        'levels_analyzed',
    ]
    
    ordering = ['-timestamp']
    
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Disable manual creation."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing."""
        return False


@admin.register(ImbalanceAlert)
class ImbalanceAlertAdmin(admin.ModelAdmin):
    """Admin for imbalance alerts."""
    
    list_display = [
        'symbol',
        'timestamp',
        'alert_type',
        'severity',
        'imbalance_ratio',
        'is_resolved',
        'resolved_at',
    ]
    
    list_filter = [
        'alert_type',
        'severity',
        'is_resolved',
        'symbol',
        'timestamp',
    ]
    
    search_fields = [
        'symbol__name',
        'message',
    ]
    
    readonly_fields = [
        'id',
        'symbol',
        'timestamp',
        'alert_type',
        'imbalance_ratio',
        'bid_depth',
        'ask_depth',
        'threshold_value',
        'message',
    ]
    
    ordering = ['-timestamp']
    
    date_hierarchy = 'timestamp'
    
    actions = ['resolve_alerts']
    
    def resolve_alerts(self, request, queryset):
        """Bulk resolve alerts."""
        from django.utils import timezone
        
        count = queryset.filter(is_resolved=False).update(
            is_resolved=True,
            resolved_at=timezone.now()
        )
        
        self.message_user(request, f'{count} alerts resolved.')
    
    resolve_alerts.short_description = 'Resolve selected alerts'
