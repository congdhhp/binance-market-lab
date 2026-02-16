"""
Django models for market data storage using TimescaleDB hypertables.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Symbol(models.Model):
    """
    Represents a trading pair (e.g., BTCUSDT).
    """
    name = models.CharField(max_length=20, unique=True, db_index=True)
    base_asset = models.CharField(max_length=10)
    quote_asset = models.CharField(max_length=10)
    status = models.CharField(
        max_length=20,
        choices=[
            ('TRADING', 'Trading'),
            ('BREAK', 'Break'),
            ('HALT', 'Halt'),
            ('AUCTION_MATCH', 'Auction Match'),
        ],
        default='TRADING'
    )
    is_spot = models.BooleanField(default=True)
    is_futures = models.BooleanField(default=False)
    listing_date = models.DateTimeField(null=True, blank=True)
    delisting_date = models.DateTimeField(null=True, blank=True)
    
    # Trading rules
    min_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    max_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    tick_size = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    min_qty = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    max_qty = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    step_size = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    # Metadata
    is_tracked = models.BooleanField(default=True, help_text="Whether to actively ingest data for this symbol")
    priority = models.IntegerField(default=0, help_text="Higher priority symbols get ingested more frequently")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'market_data_symbol'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_tracked', 'priority']),
        ]

    def __str__(self):
        return self.name


class Kline(models.Model):
    """
    OHLCV candlestick data. TimescaleDB hypertable partitioned by open_time.
    """
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='klines')
    interval = models.CharField(
        max_length=5,
        choices=[
            ('1m', '1 minute'),
            ('3m', '3 minutes'),
            ('5m', '5 minutes'),
            ('15m', '15 minutes'),
            ('30m', '30 minutes'),
            ('1h', '1 hour'),
            ('2h', '2 hours'),
            ('4h', '4 hours'),
            ('6h', '6 hours'),
            ('8h', '8 hours'),
            ('12h', '12 hours'),
            ('1d', '1 day'),
            ('3d', '3 days'),
            ('1w', '1 week'),
            ('1M', '1 month'),
        ]
    )
    open_time = models.DateTimeField(db_index=True)
    close_time = models.DateTimeField()
    
    # OHLCV
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=8)
    quote_volume = models.DecimalField(max_digits=30, decimal_places=8)
    
    # Additional metrics
    trades_count = models.IntegerField(validators=[MinValueValidator(0)])
    taker_buy_volume = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    taker_buy_quote_volume = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data_kline'
        unique_together = [['symbol', 'interval', 'open_time']]
        indexes = [
            models.Index(fields=['symbol', 'interval', 'open_time']),
            models.Index(fields=['open_time']),
        ]
        ordering = ['-open_time']

    def __str__(self):
        return f"{self.symbol.name} {self.interval} @ {self.open_time}"


class Trade(models.Model):
    """
    Aggregated trade data for tick-level analysis.
    """
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='trades')
    trade_id = models.BigIntegerField()
    price = models.DecimalField(max_digits=20, decimal_places=8)
    quantity = models.DecimalField(max_digits=30, decimal_places=8)
    quote_quantity = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    timestamp = models.DateTimeField(db_index=True)
    is_buyer_maker = models.BooleanField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data_trade'
        unique_together = [['symbol', 'trade_id', 'timestamp']]
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol.name} Trade #{self.trade_id}"


class OrderBookSnapshot(models.Model):
    """
    Periodic snapshots of order book depth.
    """
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='orderbook_snapshots')
    timestamp = models.DateTimeField(db_index=True)
    
    # JSON fields for efficiency
    bids = models.JSONField(help_text="List of [price, quantity] bid levels")
    asks = models.JSONField(help_text="List of [price, quantity] ask levels")
    
    # Computed metrics
    mid_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    spread = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    spread_bps = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True, help_text="Spread in basis points")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data_orderbook_snapshot'
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol.name} OrderBook @ {self.timestamp}"


class Ticker24h(models.Model):
    """
    24-hour ticker statistics snapshot.
    """
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='ticker_snapshots')
    timestamp = models.DateTimeField(db_index=True)
    
    # Price data
    last_price = models.DecimalField(max_digits=20, decimal_places=8)
    open_price = models.DecimalField(max_digits=20, decimal_places=8)
    high_price = models.DecimalField(max_digits=20, decimal_places=8)
    low_price = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Change metrics
    price_change = models.DecimalField(max_digits=20, decimal_places=8)
    price_change_percent = models.DecimalField(max_digits=10, decimal_places=4)
    
    # Volume
    volume = models.DecimalField(max_digits=30, decimal_places=8)
    quote_volume = models.DecimalField(max_digits=30, decimal_places=8)
    weighted_avg_price = models.DecimalField(max_digits=20, decimal_places=8)
    
    # Additional metrics
    bid_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    ask_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    trades_count = models.IntegerField(validators=[MinValueValidator(0)])
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data_ticker24h'
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol.name} Ticker @ {self.timestamp}"


class FundingRate(models.Model):
    """
    Funding rates for perpetual futures contracts.
    """
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='funding_rates')
    timestamp = models.DateTimeField(db_index=True)
    funding_rate = models.DecimalField(max_digits=20, decimal_places=8)
    funding_time = models.DateTimeField()
    mark_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data_funding_rate'
        unique_together = [['symbol', 'funding_time', 'timestamp']]
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol.name} Funding @ {self.funding_time}"


class OpenInterest(models.Model):
    """
    Open interest data for futures contracts.
    """
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='open_interest_data')
    timestamp = models.DateTimeField(db_index=True)
    open_interest = models.DecimalField(max_digits=30, decimal_places=8, help_text="Open interest in base asset")
    open_interest_value = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True, help_text="Open interest in USDT")
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'market_data_open_interest'
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.symbol.name} OI @ {self.timestamp}"


class IngestionLog(models.Model):
    """
    Tracks data ingestion status and errors.
    """
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='ingestion_logs', null=True, blank=True)
    data_type = models.CharField(
        max_length=50,
        choices=[
            ('kline', 'Kline'),
            ('trade', 'Trade'),
            ('orderbook', 'OrderBook'),
            ('ticker', 'Ticker'),
            ('funding_rate', 'Funding Rate'),
            ('open_interest', 'Open Interest'),
        ]
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('success', 'Success'),
            ('failed', 'Failed'),
            ('partial', 'Partial Success'),
        ],
        default='pending'
    )
    
    # Details
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    records_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'market_data_ingestion_log'
        indexes = [
            models.Index(fields=['symbol', 'data_type', 'status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        symbol_str = self.symbol.name if self.symbol else "ALL"
        return f"{symbol_str} - {self.data_type} - {self.status}"
