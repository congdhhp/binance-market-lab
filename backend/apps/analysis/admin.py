"""
Django Admin for analysis app.
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.analysis.models import IndicatorCache, SignalRule, Signal, PatternDetection


@admin.register(IndicatorCache)
class IndicatorCacheAdmin(admin.ModelAdmin):
    """Admin for cached indicators."""
    list_display = [
        'symbol', 'interval', 'timestamp',
        'rsi_display', 'macd_display', 'adx_display',
        'ema_21_display', 'bb_display', 'created_at'
    ]
    list_filter = ['interval', 'timestamp', 'created_at']
    search_fields = ['symbol__name']
    date_hierarchy = 'timestamp'
    readonly_fields = [
        'symbol', 'interval', 'timestamp', 'created_at',
        # Individual indicators
        'rsi', 'macd', 'macd_signal', 'macd_diff',
        'adx', 'adx_pos', 'adx_neg',
        'ema_9', 'ema_21', 'ema_50', 'ema_100', 'ema_200',
        'sma_20', 'sma_50', 'sma_200',
        'bb_high', 'bb_mid', 'bb_low', 'bb_width',
        'atr', 'vwap', 'obv',
        'stoch_k', 'stoch_d', 'williams_r',
        'hull_ma', 'supertrend', 'supertrend_direction'
    ]
    
    def rsi_display(self, obj):
        """Display RSI with color coding."""
        if obj.rsi:
            color = 'red' if obj.rsi > 70 else 'green' if obj.rsi < 30 else 'black'
            return format_html(
                '<span style="color: {};">{:.2f}</span>',
                color, obj.rsi
            )
        return '-'
    rsi_display.short_description = 'RSI'
    
    def macd_display(self, obj):
        """Display MACD."""
        if obj.macd and obj.macd_signal:
            return f"{obj.macd:.4f} / {obj.macd_signal:.4f}"
        return '-'
    macd_display.short_description = 'MACD/Signal'
    
    def adx_display(self, obj):
        """Display ADX."""
        if obj.adx:
            return f"{obj.adx:.2f}"
        return '-'
    adx_display.short_description = 'ADX'
    
    def ema_21_display(self, obj):
        """Display EMA 21."""
        if obj.ema_21:
            return f"${obj.ema_21:.2f}"
        return '-'
    ema_21_display.short_description = 'EMA 21'
    
    def bb_display(self, obj):
        """Display Bollinger Bands."""
        if obj.bb_high and obj.bb_low:
            return f"${obj.bb_high:.2f} - ${obj.bb_low:.2f}"
        return '-'
    bb_display.short_description = 'BB Range'
    
    def has_add_permission(self, request):
        """Disable manual adding - indicators are computed automatically."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing - indicators are computed automatically."""
        return False


@admin.register(SignalRule)
class SignalRuleAdmin(admin.ModelAdmin):
    """Admin for signal rules."""
    list_display = [
        'name', 'signal_type', 'priority', 'is_active',
        'symbols_count', 'created_at', 'updated_at'
    ]
    list_filter = ['signal_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['symbols']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'signal_type', 'is_active', 'priority')
        }),
        ('Conditions', {
            'fields': ('conditions', 'operator', 'min_confidence')
        }),
        ('Symbols', {
            'fields': ('symbols',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def symbols_count(self, obj):
        """Display number of symbols."""
        count = obj.symbols.count()
        return f"{count} symbol(s)"
    symbols_count.short_description = 'Symbols'


@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    """Admin for trading signals."""
    list_display = [
        'symbol', 'timestamp', 'interval', 'signal_type',
        'strength_display', 'confidence_display', 'price_display',
        'is_active', 'created_at'
    ]
    list_filter = ['signal_type', 'is_active', 'interval', 'timestamp', 'created_at']
    search_fields = ['symbol__name', 'notes']
    date_hierarchy = 'timestamp'
    readonly_fields = [
        'symbol', 'timestamp', 'interval', 'signal_type',
        'strength', 'confidence', 'price_at_signal',
        'rule', 'indicators_snapshot',
        'notes', 'is_active', 'created_at'
    ]
    
    fieldsets = (
        ('Signal Information', {
            'fields': (
                'symbol', 'timestamp', 'interval', 'signal_type',
                'strength', 'confidence', 'is_active'
            )
        }),
        ('Price Levels', {
            'fields': ('price_at_signal',)
        }),
        ('Context', {
            'fields': ('rule', 'indicators_snapshot', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def strength_display(self, obj):
        """Display strength with color coding."""
        if obj.strength:
            if obj.strength >= 0.7:
                color = 'green'
            elif obj.strength >= 0.4:
                color = 'orange'
            else:
                color = 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1%}</span>',
                color, obj.strength
            )
        return '-'
    strength_display.short_description = 'Strength'
    
    def confidence_display(self, obj):
        """Display confidence with color coding."""
        if obj.confidence:
            if obj.confidence >= 0.7:
                color = 'green'
            elif obj.confidence >= 0.4:
                color = 'orange'
            else:
                color = 'red'
            return format_html(
                '<span style="color: {};">{:.1%}</span>',
                color, obj.confidence
            )
        return '-'
    confidence_display.short_description = 'Confidence'
    
    def price_display(self, obj):
        """Display price at signal."""
        if obj.price_at_signal:
            return f"${obj.price_at_signal:,.2f}"
        return '-'
    price_display.short_description = 'Price'
    
    def has_add_permission(self, request):
        """Disable manual adding - signals are generated automatically."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing - signals are generated automatically."""
        return False


@admin.register(PatternDetection)
class PatternDetectionAdmin(admin.ModelAdmin):
    """Admin for pattern detection."""
    list_display = [
        'symbol', 'timestamp', 'interval', 'pattern_type',
        'direction_display', 'reliability_display',
        'price_range', 'created_at'
    ]
    list_filter = ['pattern_type', 'direction', 'interval', 'timestamp', 'created_at']
    search_fields = ['symbol__name', 'pattern_type']
    date_hierarchy = 'timestamp'
    readonly_fields = [
        'symbol', 'timestamp', 'interval', 'pattern_type',
        'direction', 'reliability', 'price_at_detection',
        'support_level', 'resistance_level', 'metadata', 'created_at'
    ]
    
    fieldsets = (
        ('Pattern Information', {
            'fields': (
                'symbol', 'timestamp', 'interval',
                'pattern_type', 'direction', 'reliability'
            )
        }),
        ('Price Levels', {
            'fields': ('price_at_detection', 'support_level', 'resistance_level')
        }),
        ('Metadata', {
            'fields': ('metadata',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def direction_display(self, obj):
        """Display direction with arrow."""
        if obj.direction == 'bullish':
            return format_html('<span style="color: green;">↑ Bullish</span>')
        elif obj.direction == 'bearish':
            return format_html('<span style="color: red;">↓ Bearish</span>')
        else:
            return format_html('<span style="color: gray;">→ Neutral</span>')
    direction_display.short_description = 'Direction'
    
    def reliability_display(self, obj):
        """Display reliability with color coding."""
        if obj.reliability:
            if obj.reliability >= 0.7:
                color = 'green'
            elif obj.reliability >= 0.4:
                color = 'orange'
            else:
                color = 'gray'
            return format_html(
                '<span style="color: {};">{:.1%}</span>',
                color, obj.reliability
            )
        return '-'
    reliability_display.short_description = 'Reliability'
    
    def price_range(self, obj):
        """Display price range."""
        if obj.support_level and obj.resistance_level:
            return f"${obj.support_level:,.2f} → ${obj.resistance_level:,.2f}"
        return '-'
    price_range.short_description = 'Price Range'
    
    def has_add_permission(self, request):
        """Disable manual adding - patterns are detected automatically."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing - patterns are detected automatically."""
        return False
