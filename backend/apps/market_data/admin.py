from django.contrib import admin
from .models import (
    Symbol, Kline, Trade, OrderBookSnapshot, 
    Ticker24h, FundingRate, OpenInterest, IngestionLog
)


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_asset', 'quote_asset', 'status', 'is_tracked', 'priority', 'is_spot', 'is_futures']
    list_filter = ['status', 'is_tracked', 'is_spot', 'is_futures']
    search_fields = ['name', 'base_asset', 'quote_asset']
    ordering = ['-priority', 'name']
    list_editable = ['is_tracked', 'priority']


@admin.register(Kline)
class KlineAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'interval', 'open_time', 'open', 'high', 'low', 'close', 'volume']
    list_filter = ['interval', 'symbol']
    search_fields = ['symbol__name']
    date_hierarchy = 'open_time'
    ordering = ['-open_time']
    readonly_fields = ['created_at']


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'trade_id', 'price', 'quantity', 'timestamp', 'is_buyer_maker']
    list_filter = ['symbol', 'is_buyer_maker']
    search_fields = ['symbol__name', 'trade_id']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(OrderBookSnapshot)
class OrderBookSnapshotAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timestamp', 'mid_price', 'spread', 'spread_bps']
    list_filter = ['symbol']
    search_fields = ['symbol__name']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(Ticker24h)
class Ticker24hAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timestamp', 'last_price', 'price_change_percent', 'volume', 'quote_volume']
    list_filter = ['symbol']
    search_fields = ['symbol__name']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(FundingRate)
class FundingRateAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'funding_time', 'funding_rate', 'mark_price']
    list_filter = ['symbol']
    search_fields = ['symbol__name']
    date_hierarchy = 'funding_time'
    ordering = ['-funding_time']


@admin.register(OpenInterest)
class OpenInterestAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'timestamp', 'open_interest', 'open_interest_value']
    list_filter = ['symbol']
    search_fields = ['symbol__name']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']


@admin.register(IngestionLog)
class IngestionLogAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'data_type', 'status', 'records_count', 'created_at', 'updated_at']
    list_filter = ['data_type', 'status', 'created_at']
    search_fields = ['symbol__name', 'error_message']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
