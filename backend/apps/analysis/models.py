"""
Django models for technical analysis and signals.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.market_data.models import Symbol
import json


class IndicatorCache(models.Model):
    """
    Pre-computed technical indicators cache (TimescaleDB hypertable).
    Stores computed indicator values for fast retrieval.
    """
    id = models.BigAutoField(primary_key=True)  # Explicit ID for TimescaleDB compatibility
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='indicators')
    interval = models.CharField(max_length=5, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    
    # Trend Indicators
    ema_9 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ema_21 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ema_50 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ema_100 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ema_200 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    sma_20 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    sma_50 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    sma_200 = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    macd = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    macd_signal = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    macd_diff = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    adx = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    adx_pos = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    adx_neg = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Momentum Indicators
    rsi = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    stoch_k = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    stoch_d = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    williams_r = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Volatility Indicators
    bb_high = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    bb_mid = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    bb_low = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    bb_width = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    atr = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Volume Indicators
    vwap = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    obv = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    
    # Custom Indicators
    hull_ma = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    supertrend = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    supertrend_direction = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analysis_indicator_cache'
        indexes = [
            models.Index(fields=['symbol', 'interval', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.symbol.name} {self.interval} @ {self.timestamp}"


class SignalRule(models.Model):
    """
    Defines trading signal rules based on indicator conditions.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Rule conditions (JSON format)
    # Example: {"rsi": {"operator": "lt", "value": 30}, "macd": {"operator": "crossover", "direction": "up"}}
    conditions = models.JSONField(default=dict)
    
    # Signal properties
    signal_type = models.CharField(
        max_length=20,
        choices=[
            ('buy', 'Buy Signal'),
            ('sell', 'Sell Signal'),
            ('neutral', 'Neutral'),
        ]
    )
    strength = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Signal strength 1-100"
    )
    
    # Applicability
    symbols = models.ManyToManyField(Symbol, blank=True, help_text="Leave empty for all symbols")
    intervals = models.JSONField(
        default=list,
        help_text="List of intervals, e.g. ['1h', '4h']"
    )
    
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority rules evaluated first")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analysis_signal_rule'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.signal_type})"
    
    def evaluate(self, indicators: dict) -> bool:
        """
        Evaluate if the rule conditions are met given indicator values.
        
        Args:
            indicators: Dict of indicator_name -> value
            
        Returns:
            True if all conditions are met, False otherwise
        """
        for indicator_name, condition in self.conditions.items():
            if indicator_name not in indicators:
                return False
            
            value = indicators[indicator_name]
            operator = condition.get('operator')
            threshold = condition.get('value')
            
            if operator == 'gt' and not (value > threshold):
                return False
            elif operator == 'lt' and not (value < threshold):
                return False
            elif operator == 'eq' and not (value == threshold):
                return False
            elif operator == 'gte' and not (value >= threshold):
                return False
            elif operator == 'lte' and not (value <= threshold):
                return False
        
        return True


class Signal(models.Model):
    """
    Generated trading signals based on rules or custom logic.
    """
    id = models.BigAutoField(primary_key=True)  # Explicit ID for TimescaleDB compatibility
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='signals')
    timestamp = models.DateTimeField(db_index=True)
    interval = models.CharField(max_length=5)
    
    # Signal details
    signal_type = models.CharField(
        max_length=20,
        choices=[
            ('buy', 'Buy'),
            ('sell', 'Sell'),
            ('strong_buy', 'Strong Buy'),
            ('strong_sell', 'Strong Sell'),
            ('neutral', 'Neutral'),
        ]
    )
    strength = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    
    # Optional: associated rule
    rule = models.ForeignKey(
        SignalRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_signals'
    )
    
    # Price context
    price_at_signal = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Signal metadata
    indicators_snapshot = models.JSONField(
        default=dict,
        help_text="Snapshot of key indicators at signal time"
    )
    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Confidence score 0-100"
    )
    
    # Tracking
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analysis_signal'
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['signal_type', 'is_active']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.symbol.name} {self.signal_type} @ {self.timestamp}"


class PatternDetection(models.Model):
    """
    Detected candlestick patterns and chart patterns.
    """
    id = models.BigAutoField(primary_key=True)  # Explicit ID for TimescaleDB compatibility
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='patterns')
    timestamp = models.DateTimeField(db_index=True)
    interval = models.CharField(max_length=5)
    
    # Pattern type
    pattern_type = models.CharField(
        max_length=50,
        choices=[
            # Candlestick patterns
            ('doji', 'Doji'),
            ('hammer', 'Hammer'),
            ('inverted_hammer', 'Inverted Hammer'),
            ('hanging_man', 'Hanging Man'),
            ('shooting_star', 'Shooting Star'),
            ('engulfing_bullish', 'Bullish Engulfing'),
            ('engulfing_bearish', 'Bearish Engulfing'),
            ('morning_star', 'Morning Star'),
            ('evening_star', 'Evening Star'),
            ('three_white_soldiers', 'Three White Soldiers'),
            ('three_black_crows', 'Three Black Crows'),
            
            # Chart patterns
            ('double_top', 'Double Top'),
            ('double_bottom', 'Double Bottom'),
            ('head_shoulders', 'Head and Shoulders'),
            ('inverse_head_shoulders', 'Inverse Head and Shoulders'),
            ('triangle_ascending', 'Ascending Triangle'),
            ('triangle_descending', 'Descending Triangle'),
            ('triangle_symmetrical', 'Symmetrical Triangle'),
            ('flag_bullish', 'Bullish Flag'),
            ('flag_bearish', 'Bearish Flag'),
        ]
    )
    
    # Pattern characteristics
    direction = models.CharField(
        max_length=10,
        choices=[
            ('bullish', 'Bullish'),
            ('bearish', 'Bearish'),
            ('neutral', 'Neutral'),
        ]
    )
    
    reliability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Pattern reliability score 1-100"
    )
    
    # Price levels
    price_at_detection = models.DecimalField(max_digits=20, decimal_places=8)
    support_level = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    resistance_level = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Pattern metadata
    metadata = models.JSONField(
        default=dict,
        help_text="Additional pattern-specific data"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analysis_pattern_detection'
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['pattern_type', 'direction']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.symbol.name} {self.pattern_type} ({self.direction}) @ {self.timestamp}"
