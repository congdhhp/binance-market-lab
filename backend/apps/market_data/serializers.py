"""
DRF serializers for market_data app.
"""
from rest_framework import serializers
from .models import (
    Symbol, Kline, Trade, OrderBookSnapshot,
    Ticker24h, FundingRate, OpenInterest, IngestionLog
)


class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = [
            'id', 'name', 'base_asset', 'quote_asset', 'status',
            'is_spot', 'is_futures', 'listing_date', 'delisting_date',
            'min_price', 'max_price', 'tick_size',
            'min_qty', 'max_qty', 'step_size',
            'is_tracked', 'priority', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class KlineSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)

    class Meta:
        model = Kline
        fields = [
            'id', 'symbol', 'symbol_name', 'interval', 'open_time', 'close_time',
            'open', 'high', 'low', 'close', 'volume', 'quote_volume',
            'trades_count', 'taker_buy_volume', 'taker_buy_quote_volume',
            'created_at'
        ]
        read_only_fields = ['created_at']


class TradeSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)

    class Meta:
        model = Trade
        fields = [
            'id', 'symbol', 'symbol_name', 'trade_id', 'price', 'quantity',
            'quote_quantity', 'timestamp', 'is_buyer_maker', 'created_at'
        ]
        read_only_fields = ['created_at']


class OrderBookSnapshotSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)

    class Meta:
        model = OrderBookSnapshot
        fields = [
            'id', 'symbol', 'symbol_name', 'timestamp',
            'bids', 'asks', 'mid_price', 'spread', 'spread_bps',
            'created_at'
        ]
        read_only_fields = ['created_at']


class Ticker24hSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)

    class Meta:
        model = Ticker24h
        fields = [
            'id', 'symbol', 'symbol_name', 'timestamp',
            'last_price', 'open_price', 'high_price', 'low_price',
            'price_change', 'price_change_percent',
            'volume', 'quote_volume', 'weighted_avg_price',
            'bid_price', 'ask_price', 'trades_count',
            'created_at'
        ]
        read_only_fields = ['created_at']


class FundingRateSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)

    class Meta:
        model = FundingRate
        fields = [
            'id', 'symbol', 'symbol_name', 'timestamp',
            'funding_rate', 'funding_time', 'mark_price',
            'created_at'
        ]
        read_only_fields = ['created_at']


class OpenInterestSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)

    class Meta:
        model = OpenInterest
        fields = [
            'id', 'symbol', 'symbol_name', 'timestamp',
            'open_interest', 'open_interest_value',
            'created_at'
        ]
        read_only_fields = ['created_at']


class IngestionLogSerializer(serializers.ModelSerializer):
    symbol_name = serializers.CharField(source='symbol.name', read_only=True, allow_null=True)

    class Meta:
        model = IngestionLog
        fields = [
            'id', 'symbol', 'symbol_name', 'data_type', 'status',
            'start_time', 'end_time', 'records_count', 'error_message',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class BackfillRequestSerializer(serializers.Serializer):
    """
    Serializer for manual backfill trigger requests.
    """
    symbol = serializers.CharField(required=True, help_text="Symbol name (e.g., BTCUSDT)")
    interval = serializers.ChoiceField(
        required=True,
        choices=['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'],
        help_text="Kline interval"
    )
    start_date = serializers.DateTimeField(required=True, help_text="Start date for backfill")
    end_date = serializers.DateTimeField(required=False, help_text="End date for backfill (default: now)")

    def validate(self, data):
        """Validate that start_date is before end_date."""
        if data.get('end_date') and data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("start_date must be before end_date")
        return data
