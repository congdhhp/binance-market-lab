"""
DRF Serializers for backtest app.
"""
from rest_framework import serializers
from apps.backtest.models import Strategy, BacktestRun, Trade, Portfolio, BacktestMetrics
from apps.market_data.models import Symbol
from apps.market_data.serializers import SymbolSerializer
from apps.analysis.models import SignalRule
from apps.analysis.serializers import SignalRuleSerializer


class StrategySerializer(serializers.ModelSerializer):
    """Serializer for trading strategies."""
    signal_rules_data = SignalRuleSerializer(source='signal_rules', many=True, read_only=True)
    signal_rule_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=SignalRule.objects.all(),
        source='signal_rules',
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Strategy
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class StrategyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing strategies."""
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'strategy_type', 'initial_capital',
            'position_size', 'is_active', 'created_at'
        ]


class BacktestRunSerializer(serializers.ModelSerializer):
    """Serializer for backtest runs."""
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = BacktestRun
        fields = '__all__'
        read_only_fields = [
            'status', 'total_trades', 'winning_trades', 'losing_trades',
            'final_capital', 'total_return', 'max_drawdown', 'sharpe_ratio',
            'win_rate', 'avg_win', 'avg_loss', 'profit_factor',
            'equity_curve', 'error_message', 'started_at', 'completed_at',
            'created_at', 'updated_at'
        ]


class BacktestRunListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing backtest runs."""
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = BacktestRun
        fields = [
            'id', 'name', 'symbol_name', 'strategy_name', 'interval',
            'start_date', 'end_date', 'status', 'total_trades',
            'total_return', 'win_rate', 'created_at'
        ]


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for individual trades."""
    
    class Meta:
        model = Trade
        fields = '__all__'
        read_only_fields = ['created_at']


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for portfolio snapshots."""
    
    class Meta:
        model = Portfolio
        fields = '__all__'
        read_only_fields = ['created_at']


class BacktestMetricsSerializer(serializers.ModelSerializer):
    """Serializer for backtest metrics."""
    
    class Meta:
        model = BacktestMetrics
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class RunBacktestRequestSerializer(serializers.Serializer):
    """Request serializer for running a backtest."""
    strategy_id = serializers.IntegerField(required=True)
    symbol_id = serializers.IntegerField(required=True)
    interval = serializers.CharField(max_length=5, default='1h')
    start_date = serializers.DateTimeField(required=True)
    end_date = serializers.DateTimeField(required=True)
    name = serializers.CharField(max_length=200, required=False)
    
    def validate(self, data):
        """Validate backtest parameters."""
        if data['end_date'] <= data['start_date']:
            raise serializers.ValidationError("End date must be after start date")
        
        # Check if strategy exists
        if not Strategy.objects.filter(id=data['strategy_id']).exists():
            raise serializers.ValidationError("Strategy not found")
        
        # Check if symbol exists
        if not Symbol.objects.filter(id=data['symbol_id']).exists():
            raise serializers.ValidationError("Symbol not found")
        
        return data


class OptimizeStrategyRequestSerializer(serializers.Serializer):
    """Request serializer for strategy optimization."""
    strategy_id = serializers.IntegerField(required=True)
    symbol_id = serializers.IntegerField(required=True)
    interval = serializers.CharField(max_length=5, default='1h')


from apps.analysis.models import SignalRule
