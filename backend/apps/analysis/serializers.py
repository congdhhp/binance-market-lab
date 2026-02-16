"""
DRF Serializers for analysis app.
"""
from rest_framework import serializers
from apps.analysis.models import IndicatorCache, SignalRule, Signal, PatternDetection
from apps.market_data.models import Symbol
from apps.market_data.serializers import SymbolSerializer


class IndicatorCacheSerializer(serializers.ModelSerializer):
    """Serializer for cached indicators."""
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    
    class Meta:
        model = IndicatorCache
        fields = '__all__'
        read_only_fields = ['created_at']


class IndicatorCacheListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing indicators."""
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    
    class Meta:
        model = IndicatorCache
        fields = [
            'id', 'symbol_name', 'interval', 'timestamp',
            'rsi', 'macd', 'macd_signal', 'adx',
            'ema_21', 'sma_50', 'bb_high', 'bb_low', 'vwap'
        ]


class SignalRuleSerializer(serializers.ModelSerializer):
    """Serializer for signal rules."""
    symbols_data = SymbolSerializer(source='symbols', many=True, read_only=True)
    symbol_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Symbol.objects.all(),
        source='symbols',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = SignalRule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_conditions(self, value):
        """Validate conditions JSON structure."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Conditions must be a dictionary")
        
        # Validate condition format
        for indicator, condition in value.items():
            if not isinstance(condition, dict):
                raise serializers.ValidationError(
                    f"Condition for {indicator} must be a dictionary"
                )
            if 'operator' not in condition:
                raise serializers.ValidationError(
                    f"Condition for {indicator} missing 'operator'"
                )
            
            valid_operators = ['gt', 'lt', 'eq', 'gte', 'lte', 'crossover']
            if condition['operator'] not in valid_operators:
                raise serializers.ValidationError(
                    f"Invalid operator for {indicator}: {condition['operator']}"
                )
        
        return value


class SignalSerializer(serializers.ModelSerializer):
    """Serializer for trading signals."""
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Signal
        fields = '__all__'
        read_only_fields = ['created_at']


class SignalListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing signals."""
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    
    class Meta:
        model = Signal
        fields = [
            'id', 'symbol_name', 'timestamp', 'interval',
            'signal_type', 'strength', 'confidence',
            'price_at_signal', 'is_active'
        ]


class PatternDetectionSerializer(serializers.ModelSerializer):
    """Serializer for pattern detection."""
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    
    class Meta:
        model = PatternDetection
        fields = '__all__'
        read_only_fields = ['created_at']


class ComputeIndicatorsRequestSerializer(serializers.Serializer):
    """Request serializer for computing indicators."""
    symbol_id = serializers.IntegerField(required=True)
    interval = serializers.CharField(max_length=5, default='1h')
    lookback_periods = serializers.IntegerField(default=500, min_value=50, max_value=2000)


class GenerateSignalsRequestSerializer(serializers.Serializer):
    """Request serializer for generating signals."""
    symbol_id = serializers.IntegerField(required=True)
    interval = serializers.CharField(max_length=5, default='1h')
