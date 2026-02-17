"""
Orderbook analytics models for Phase 4.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.market_data.models import Symbol


class OrderbookAnalysis(models.Model):
    """
    Pre-computed orderbook analytics metrics.
    Computed from OrderbookSnapshot data.
    """
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='orderbook_analysis')
    timestamp = models.DateTimeField(db_index=True)
    
    # Spread metrics
    bid_price = models.DecimalField(max_digits=20, decimal_places=8)
    ask_price = models.DecimalField(max_digits=20, decimal_places=8)
    mid_price = models.DecimalField(max_digits=20, decimal_places=8)
    spread_absolute = models.DecimalField(max_digits=20, decimal_places=8)
    spread_bps = models.DecimalField(
        max_digits=10, 
        decimal_places=4,
        help_text="Spread in basis points (0.01%)"
    )
    
    # Depth metrics (top 10 levels)
    bid_depth_10 = models.DecimalField(max_digits=30, decimal_places=8, help_text="Total bid volume in top 10 levels")
    ask_depth_10 = models.DecimalField(max_digits=30, decimal_places=8, help_text="Total ask volume in top 10 levels")
    total_depth_10 = models.DecimalField(max_digits=30, decimal_places=8)
    
    # Imbalance metrics
    imbalance_ratio = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="bid_depth / (bid_depth + ask_depth)"
    )
    imbalance_pct = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        help_text="(bid_depth - ask_depth) / total_depth * 100"
    )
    
    # VWAP execution estimates
    vwap_buy_1000 = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Estimated VWAP for buying $1000 worth"
    )
    vwap_sell_1000 = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Estimated VWAP for selling $1000 worth"
    )
    
    # Liquidity metrics
    liquidity_score = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Composite liquidity score (0-100)"
    )
    has_liquidity_hole = models.BooleanField(
        default=False,
        help_text="True if large gap detected in orderbook"
    )
    
    # Metadata
    levels_analyzed = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'orderbook_analysis'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['imbalance_ratio']),
        ]
        unique_together = [['symbol', 'timestamp']]
    
    def __str__(self):
        return f"{self.symbol.name} - {self.timestamp}"


class ImbalanceAlert(models.Model):
    """
    Triggered alerts for significant orderbook imbalance.
    """
    ALERT_TYPE_CHOICES = [
        ('high_bid_pressure', 'High Bid Pressure'),
        ('high_ask_pressure', 'High Ask Pressure'),
        ('extreme_imbalance', 'Extreme Imbalance'),
        ('liquidity_hole', 'Liquidity Hole'),
    ]
    
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='imbalance_alerts')
    timestamp = models.DateTimeField(db_index=True)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    
    # Alert details
    imbalance_ratio = models.DecimalField(max_digits=10, decimal_places=4)
    bid_depth = models.DecimalField(max_digits=30, decimal_places=8)
    ask_depth = models.DecimalField(max_digits=30, decimal_places=8)
    
    threshold_value = models.DecimalField(max_digits=10, decimal_places=4)
    severity = models.CharField(
        max_length=10,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')],
        default='medium'
    )
    
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'imbalance_alert'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['alert_type', 'is_resolved']),
        ]
    
    def __str__(self):
        return f"{self.symbol.name} - {self.alert_type} - {self.timestamp}"
