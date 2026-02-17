"""
Django models for backtesting engine.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from apps.market_data.models import Symbol
from apps.analysis.models import SignalRule
from decimal import Decimal
import json


class Strategy(models.Model):
    """
    Trading strategy definition for backtesting.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Strategy type
    strategy_type = models.CharField(
        max_length=20,
        choices=[
            ('signal_based', 'Signal-Based'),
            ('indicator', 'Indicator-Based'),
            ('ml_model', 'ML Model'),
            ('custom', 'Custom Logic'),
        ],
        default='signal_based'
    )
    
    # Signal-based strategy
    signal_rules = models.ManyToManyField(
        SignalRule,
        blank=True,
        help_text="Signal rules to use for this strategy"
    )
    
    # Strategy parameters (JSON)
    parameters = models.JSONField(
        default=dict,
        help_text="Strategy-specific parameters"
    )
    
    # Risk management
    initial_capital = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('10000.00'),
        help_text="Starting capital in quote currency"
    )
    position_size = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal('0.1000'),
        validators=[MinValueValidator(Decimal('0.0001')), MaxValueValidator(Decimal('1.0000'))],
        help_text="Position size as fraction of capital (0.1 = 10%)"
    )
    stop_loss_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Stop loss percentage (e.g., 2.00 = 2%)"
    )
    take_profit_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Take profit percentage (e.g., 5.00 = 5%)"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'backtest_strategy'
        ordering = ['-created_at']
        verbose_name_plural = 'Strategies'
    
    def __str__(self):
        return f"{self.name} ({self.strategy_type})"


class BacktestRun(models.Model):
    """
    A single backtest execution run.
    """
    name = models.CharField(max_length=200)
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='runs')
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='backtest_runs')
    interval = models.CharField(max_length=5)
    
    # Time range
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Execution status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending'
    )
    
    # Performance metrics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    
    initial_capital = models.DecimalField(max_digits=20, decimal_places=2)
    final_capital = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    total_return = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Total return %")
    
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Max drawdown %")
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Win rate %")
    
    avg_win = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    avg_loss = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    profit_factor = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Equity curve (JSON array of timestamps and values)
    equity_curve = models.JSONField(default=list, blank=True)
    
    # Execution details
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'backtest_run'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['strategy', 'status']),
            models.Index(fields=['symbol', 'interval']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.symbol.name} ({self.status})"
    
    def calculate_metrics(self):
        """Calculate performance metrics from trades."""
        trades = self.trades.all()
        
        if not trades:
            return
        
        # Basic counts
        self.total_trades = trades.count()
        self.winning_trades = trades.filter(pnl__gt=0).count()
        self.losing_trades = trades.filter(pnl__lt=0).count()
        
        # Win rate
        if self.total_trades > 0:
            self.win_rate = Decimal(self.winning_trades) / Decimal(self.total_trades) * 100
        
        # Average win/loss
        winning = trades.filter(pnl__gt=0)
        losing = trades.filter(pnl__lt=0)
        
        if winning.exists():
            self.avg_win = winning.aggregate(models.Avg('pnl'))['pnl__avg']
        if losing.exists():
            self.avg_loss = abs(losing.aggregate(models.Avg('pnl'))['pnl__avg'])
        
        # Profit factor
        if self.avg_loss and self.avg_loss > 0:
            self.profit_factor = self.avg_win / self.avg_loss if self.avg_win else Decimal('0')
        
        # Total return
        if self.initial_capital > 0 and self.final_capital:
            self.total_return = ((self.final_capital - self.initial_capital) / self.initial_capital) * 100
        
        self.save()


class Trade(models.Model):
    """
    Individual trade executed during backtest.
    """
    backtest_run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='trades')
    
    # Trade details
    side = models.CharField(
        max_length=4,
        choices=[
            ('buy', 'Buy'),
            ('sell', 'Sell'),
        ]
    )
    
    # Entry
    entry_time = models.DateTimeField()
    entry_price = models.DecimalField(max_digits=20, decimal_places=8)
    entry_signal = models.CharField(max_length=100, blank=True, help_text="Signal that triggered entry")
    
    # Exit
    exit_time = models.DateTimeField(null=True, blank=True)
    exit_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    exit_reason = models.CharField(
        max_length=20,
        choices=[
            ('signal', 'Exit Signal'),
            ('stop_loss', 'Stop Loss'),
            ('take_profit', 'Take Profit'),
            ('end_of_backtest', 'End of Backtest'),
        ],
        blank=True
    )
    
    # Position
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    position_size_quote = models.DecimalField(max_digits=20, decimal_places=2, help_text="Position size in quote currency")
    
    # P&L
    pnl = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True, help_text="Profit/Loss in quote currency")
    pnl_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="P&L percentage")
    
    # Fees
    entry_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    exit_fee = models.DecimalField(max_digits=20, decimal_places=8, default=Decimal('0'))
    
    # Status
    is_open = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'backtest_trade'
        ordering = ['entry_time']
        indexes = [
            models.Index(fields=['backtest_run', 'entry_time']),
            models.Index(fields=['is_open']),
        ]
    
    def __str__(self):
        status = "Open" if self.is_open else "Closed"
        return f"{self.side.upper()} {self.quantity} @ {self.entry_price} ({status})"
    
    def close_trade(self, exit_time, exit_price, exit_reason):
        """Close the trade and calculate P&L."""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        self.is_open = False
        
        # Calculate P&L
        if self.side == 'buy':
            self.pnl = (self.exit_price - self.entry_price) * self.quantity
        else:  # sell/short
            self.pnl = (self.entry_price - self.exit_price) * self.quantity
        
        # Subtract fees
        self.pnl -= (self.entry_fee + self.exit_fee)
        
        # Calculate P&L percentage
        if self.position_size_quote > 0:
            self.pnl_pct = (self.pnl / self.position_size_quote) * 100
        
        self.save()


class Portfolio(models.Model):
    """
    Portfolio state snapshot during backtest.
    """
    backtest_run = models.ForeignKey(BacktestRun, on_delete=models.CASCADE, related_name='portfolio_snapshots')
    timestamp = models.DateTimeField(db_index=True)
    
    # Portfolio values
    cash = models.DecimalField(max_digits=20, decimal_places=2)
    position_value = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0'))
    total_value = models.DecimalField(max_digits=20, decimal_places=2)
    
    # Open positions
    open_positions = models.JSONField(default=dict, help_text="Current open positions")
    
    # Performance
    total_return_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    drawdown_pct = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'backtest_portfolio'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['backtest_run', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Portfolio @ {self.timestamp}: ${self.total_value}"


class BacktestMetrics(models.Model):
    """
    Detailed metrics and statistics for a backtest run.
    """
    backtest_run = models.OneToOneField(BacktestRun, on_delete=models.CASCADE, related_name='metrics')
    
    # Return metrics
    total_return = models.DecimalField(max_digits=10, decimal_places=4)
    annual_return = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    monthly_return_avg = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Risk metrics
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4)
    max_drawdown_duration_days = models.IntegerField(null=True, blank=True)
    volatility = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    downside_deviation = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Risk-adjusted returns
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    sortino_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    calmar_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Trade statistics
    total_trades = models.IntegerField()
    winning_trades = models.IntegerField()
    losing_trades = models.IntegerField()
    win_rate = models.DecimalField(max_digits=5, decimal_places=2)
    
    avg_win = models.DecimalField(max_digits=20, decimal_places=2)
    avg_loss = models.DecimalField(max_digits=20, decimal_places=2)
    largest_win = models.DecimalField(max_digits=20, decimal_places=2)
    largest_loss = models.DecimalField(max_digits=20, decimal_places=2)
    
    profit_factor = models.DecimalField(max_digits=10, decimal_places=4)
    expectancy = models.DecimalField(max_digits=20, decimal_places=2, help_text="Average profit per trade")
    
    # Holding period
    avg_holding_period_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_holding_period_hours = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Consecutive stats
    max_consecutive_wins = models.IntegerField(default=0)
    max_consecutive_losses = models.IntegerField(default=0)
    
    # Additional metrics (JSON)
    additional_metrics = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'backtest_metrics'
        verbose_name_plural = 'Backtest Metrics'
    
    def __str__(self):
        return f"Metrics for {self.backtest_run.name}"
