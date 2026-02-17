"""
Serializers for orderbook analytics API.
"""
from rest_framework import serializers
from apps.orderbook.models import OrderbookAnalysis, ImbalanceAlert


class OrderbookAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for orderbook analysis."""
    
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    
    class Meta:
        model = OrderbookAnalysis
        fields = [
            'id',
            'symbol',
            'symbol_name',
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
        read_only_fields = ['id']


class ImbalanceAlertSerializer(serializers.ModelSerializer):
    """Serializer for imbalance alerts."""
    
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    
    class Meta:
        model = ImbalanceAlert
        fields = [
            'id',
            'symbol',
            'symbol_name',
            'timestamp',
            'alert_type',
            'severity',
            'imbalance_ratio',
            'bid_depth',
            'ask_depth',
            'threshold_value',
            'message',
            'is_resolved',
            'resolved_at',
        ]
        read_only_fields = ['id']


class RiskMetricsSerializer(serializers.Serializer):
    """Serializer for risk metrics."""
    
    symbol = serializers.CharField()
    lookback_days = serializers.IntegerField()
    
    # Volatility
    volatility_daily = serializers.FloatField()
    volatility_annual = serializers.FloatField()
    
    # VaR
    var_historical_95 = serializers.FloatField()
    var_parametric_95 = serializers.FloatField()
    var_monte_carlo_95 = serializers.FloatField()
    cvar_95 = serializers.FloatField()
    
    # Ratios
    sharpe_ratio = serializers.FloatField()
    sortino_ratio = serializers.FloatField()
    calmar_ratio = serializers.FloatField()
    
    # Drawdown
    max_drawdown = serializers.FloatField()
    max_drawdown_duration = serializers.IntegerField()
    
    # Distribution
    skewness = serializers.FloatField()
    kurtosis = serializers.FloatField()
    
    # Summary
    mean_return = serializers.FloatField()
    median_return = serializers.FloatField()
    std_return = serializers.FloatField()
    min_return = serializers.FloatField()
    max_return = serializers.FloatField()


class CorrelationPairSerializer(serializers.Serializer):
    """Serializer for correlated pairs."""
    
    symbol1 = serializers.CharField()
    symbol2 = serializers.CharField()
    correlation = serializers.FloatField()
    relationship = serializers.CharField()


class CorrelationMatrixSerializer(serializers.Serializer):
    """Serializer for correlation matrix."""
    
    symbols = serializers.ListField(child=serializers.CharField())
    lookback_days = serializers.IntegerField()
    heatmap_data = serializers.DictField()
    highly_correlated_pairs = CorrelationPairSerializer(many=True)
    diversification_ratio = serializers.FloatField()


class RegimeDetectionSerializer(serializers.Serializer):
    """Serializer for market regime detection."""
    
    symbol = serializers.CharField()
    lookback_days = serializers.IntegerField()
    
    current_regime = serializers.DictField()
    transition_analysis = serializers.DictField()
