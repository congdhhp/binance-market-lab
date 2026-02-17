"""
Django Admin for backtest app.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from apps.backtest.models import Strategy, BacktestRun, Trade, Portfolio, BacktestMetrics


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    """Admin for trading strategies."""
    list_display = [
        'name', 'strategy_type', 'initial_capital_display',
        'position_size_display', 'stop_loss_pct', 'take_profit_pct',
        'rules_count', 'is_active', 'created_at'
    ]
    list_filter = ['strategy_type', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'created_by']
    filter_horizontal = ['signal_rules']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'strategy_type', 'is_active', 'created_by')
        }),
        ('Signal Rules', {
            'fields': ('signal_rules',),
            'classes': ('collapse',)
        }),
        ('Parameters', {
            'fields': ('parameters',)
        }),
        ('Risk Management', {
            'fields': (
                'initial_capital', 'position_size',
                'stop_loss_pct', 'take_profit_pct'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def initial_capital_display(self, obj):
        """Display initial capital."""
        return f"${obj.initial_capital:,.2f}"
    initial_capital_display.short_description = 'Initial Capital'
    
    def position_size_display(self, obj):
        """Display position size."""
        return f"{obj.position_size * 100:.1f}%"
    position_size_display.short_description = 'Position Size'
    
    def rules_count(self, obj):
        """Display number of signal rules."""
        count = obj.signal_rules.count()
        return f"{count} rule(s)"
    rules_count.short_description = 'Signal Rules'


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):
    """Admin for backtest runs."""
    list_display = [
        'name', 'strategy', 'symbol', 'interval',
        'status_display', 'total_trades', 'return_display',
        'win_rate_display', 'sharpe_display', 'created_at'
    ]
    list_filter = ['status', 'interval', 'created_at']
    search_fields = ['name', 'strategy__name', 'symbol__name']
    readonly_fields = [
        'status', 'total_trades', 'winning_trades', 'losing_trades',
        'initial_capital', 'final_capital', 'total_return', 'max_drawdown',
        'sharpe_ratio', 'win_rate', 'avg_win', 'avg_loss', 'profit_factor',
        'equity_curve', 'error_message', 'started_at', 'completed_at',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Configuration', {
            'fields': ('name', 'strategy', 'symbol', 'interval', 'start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('status', 'started_at', 'completed_at', 'error_message')
        }),
        ('Performance', {
            'fields': (
                'initial_capital', 'final_capital', 'total_return',
                'max_drawdown', 'sharpe_ratio'
            )
        }),
        ('Trade Statistics', {
            'fields': (
                'total_trades', 'winning_trades', 'losing_trades',
                'win_rate', 'avg_win', 'avg_loss', 'profit_factor'
            )
        }),
        ('Equity Curve', {
            'fields': ('equity_curve',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display status with color."""
        colors = {
            'pending': 'gray',
            'running': 'blue',
            'completed': 'green',
            'failed': 'red',
            'cancelled': 'orange'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_display.short_description = 'Status'
    
    def return_display(self, obj):
        """Display return with color."""
        if obj.total_return is None:
            return '-'
        
        color = 'green' if obj.total_return > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:+.2f}%</span>',
            color, obj.total_return
        )
    return_display.short_description = 'Total Return'
    
    def win_rate_display(self, obj):
        """Display win rate."""
        if obj.win_rate is None:
            return '-'
        
        if obj.win_rate >= 50:
            color = 'green'
        elif obj.win_rate >= 40:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color, obj.win_rate
        )
    win_rate_display.short_description = 'Win Rate'
    
    def sharpe_display(self, obj):
        """Display Sharpe ratio."""
        if obj.sharpe_ratio is None:
            return '-'
        
        if obj.sharpe_ratio >= 1.5:
            color = 'green'
        elif obj.sharpe_ratio >= 1.0:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.2f}</span>',
            color, obj.sharpe_ratio
        )
    sharpe_display.short_description = 'Sharpe'
    
    def has_add_permission(self, request):
        """Disable manual adding - use API to create backtests."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing - backtests are read-only."""
        return False


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    """Admin for trades."""
    list_display = [
        'backtest_run', 'side', 'entry_time', 'exit_time',
        'quantity_display', 'entry_price', 'exit_price',
        'pnl_display', 'exit_reason', 'is_open'
    ]
    list_filter = ['side', 'is_open', 'exit_reason', 'entry_time']
    search_fields = ['backtest_run__name']
    readonly_fields = [
        'backtest_run', 'side', 'entry_time', 'entry_price', 'entry_signal',
        'exit_time', 'exit_price', 'exit_reason', 'quantity', 'position_size_quote',
        'pnl', 'pnl_pct', 'entry_fee', 'exit_fee', 'is_open', 'created_at'
    ]
    
    fieldsets = (
        ('Trade Information', {
            'fields': ('backtest_run', 'side', 'is_open')
        }),
        ('Entry', {
            'fields': ('entry_time', 'entry_price', 'entry_signal', 'entry_fee')
        }),
        ('Exit', {
            'fields': ('exit_time', 'exit_price', 'exit_reason', 'exit_fee')
        }),
        ('Position', {
            'fields': ('quantity', 'position_size_quote')
        }),
        ('P&L', {
            'fields': ('pnl', 'pnl_pct')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def quantity_display(self, obj):
        """Display quantity."""
        return f"{obj.quantity:.8f}"
    quantity_display.short_description = 'Quantity'
    
    def pnl_display(self, obj):
        """Display P&L with color."""
        if obj.pnl is None:
            return '-'
        
        color = 'green' if obj.pnl > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">${:,.2f} ({:+.2f}%)</span>',
            color, obj.pnl, obj.pnl_pct or 0
        )
    pnl_display.short_description = 'P&L'
    
    def has_add_permission(self, request):
        """Disable manual adding."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing."""
        return False


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """Admin for portfolio snapshots."""
    list_display = [
        'backtest_run', 'timestamp', 'cash_display',
        'position_value_display', 'total_value_display',
        'return_display', 'drawdown_display'
    ]
    list_filter = ['backtest_run', 'timestamp']
    readonly_fields = [
        'backtest_run', 'timestamp', 'cash', 'position_value',
        'total_value', 'open_positions', 'total_return_pct',
        'drawdown_pct', 'created_at'
    ]
    
    def cash_display(self, obj):
        return f"${obj.cash:,.2f}"
    cash_display.short_description = 'Cash'
    
    def position_value_display(self, obj):
        return f"${obj.position_value:,.2f}"
    position_value_display.short_description = 'Positions'
    
    def total_value_display(self, obj):
        return f"${obj.total_value:,.2f}"
    total_value_display.short_description = 'Total Value'
    
    def return_display(self, obj):
        if obj.total_return_pct is None:
            return '-'
        color = 'green' if obj.total_return_pct > 0 else 'red'
        return format_html(
            '<span style="color: {};">{:+.2f}%</span>',
            color, obj.total_return_pct
        )
    return_display.short_description = 'Return'
    
    def drawdown_display(self, obj):
        if obj.drawdown_pct is None:
            return '-'
        return f"{obj.drawdown_pct:.2f}%"
    drawdown_display.short_description = 'Drawdown'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(BacktestMetrics)
class BacktestMetricsAdmin(admin.ModelAdmin):
    """Admin for backtest metrics."""
    list_display = [
        'backtest_run', 'total_return', 'sharpe_ratio',
        'max_drawdown', 'win_rate', 'profit_factor'
    ]
    readonly_fields = [
        'backtest_run', 'total_return', 'annual_return', 'monthly_return_avg',
        'max_drawdown', 'max_drawdown_duration_days', 'volatility', 'downside_deviation',
        'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
        'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
        'avg_win', 'avg_loss', 'largest_win', 'largest_loss',
        'profit_factor', 'expectancy', 'avg_holding_period_hours',
        'max_holding_period_hours', 'max_consecutive_wins', 'max_consecutive_losses',
        'additional_metrics', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Backtest Run', {
            'fields': ('backtest_run',)
        }),
        ('Return Metrics', {
            'fields': ('total_return', 'annual_return', 'monthly_return_avg')
        }),
        ('Risk Metrics', {
            'fields': (
                'max_drawdown', 'max_drawdown_duration_days',
                'volatility', 'downside_deviation'
            )
        }),
        ('Risk-Adjusted Returns', {
            'fields': ('sharpe_ratio', 'sortino_ratio', 'calmar_ratio')
        }),
        ('Trade Statistics', {
            'fields': (
                'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
                'avg_win', 'avg_loss', 'largest_win', 'largest_loss',
                'profit_factor', 'expectancy'
            )
        }),
        ('Holding Period', {
            'fields': ('avg_holding_period_hours', 'max_holding_period_hours')
        }),
        ('Consecutive Stats', {
            'fields': ('max_consecutive_wins', 'max_consecutive_losses')
        }),
        ('Additional', {
            'fields': ('additional_metrics',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
