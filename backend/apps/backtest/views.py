"""
DRF Views for backtest app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.utils import timezone

from apps.backtest.models import Strategy, BacktestRun, Trade, Portfolio, BacktestMetrics
from apps.backtest.serializers import (
    StrategySerializer,
    StrategyListSerializer,
    BacktestRunSerializer,
    BacktestRunListSerializer,
    TradeSerializer,
    PortfolioSerializer,
    BacktestMetricsSerializer,
    RunBacktestRequestSerializer,
    OptimizeStrategyRequestSerializer,
)
from apps.backtest.tasks import run_backtest_task, run_strategy_optimization, generate_backtest_report
import logging

logger = logging.getLogger(__name__)


class StrategyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing trading strategies.
    
    list: Get all strategies
    create: Create a new strategy
    retrieve: Get specific strategy
    update: Update a strategy
    destroy: Delete a strategy
    """
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['strategy_type', 'is_active']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    search_fields = ['name', 'description']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return StrategyListSerializer
        return StrategySerializer


class BacktestRunViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing backtest runs.
    
    list: Get all backtest runs
    retrieve: Get specific backtest run
    """
    queryset = BacktestRun.objects.all()
    serializer_class = BacktestRunSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['strategy', 'symbol', 'interval', 'status']
    ordering_fields = ['created_at', 'total_return', 'sharpe_ratio']
    ordering = ['-created_at']
    search_fields = ['name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BacktestRunListSerializer
        return BacktestRunSerializer
    
    @action(detail=True, methods=['get'])
    def trades(self, request, pk=None):
        """Get all trades for this backtest run."""
        backtest_run = self.get_object()
        trades = backtest_run.trades.all()
        
        page = self.paginate_queryset(trades)
        if page is not None:
            serializer = TradeSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def portfolio(self, request, pk=None):
        """Get portfolio snapshots for this backtest run."""
        backtest_run = self.get_object()
        snapshots = backtest_run.portfolio_snapshots.all()
        serializer = PortfolioSerializer(snapshots, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def metrics(self, request, pk=None):
        """Get detailed metrics for this backtest run."""
        backtest_run = self.get_object()
        
        try:
            metrics = backtest_run.metrics
            serializer = BacktestMetricsSerializer(metrics)
            return Response(serializer.data)
        except BacktestMetrics.DoesNotExist:
            # Generate metrics if not exists
            task = generate_backtest_report.delay(backtest_run.id)
            return Response({
                'status': 'generating',
                'task_id': task.id
            }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'])
    def equity_curve(self, request, pk=None):
        """Get equity curve data."""
        backtest_run = self.get_object()
        return Response({
            'equity_curve': backtest_run.equity_curve,
            'initial_capital': backtest_run.initial_capital,
            'final_capital': backtest_run.final_capital
        })


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing individual trades.
    """
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['backtest_run', 'side', 'is_open', 'exit_reason']
    ordering_fields = ['entry_time', 'pnl', 'pnl_pct']
    ordering = ['-entry_time']


class RunBacktestView(APIView):
    """
    API view to trigger a backtest run.
    """
    
    @extend_schema(request=RunBacktestRequestSerializer)
    def post(self, request):
        """Run a backtest."""
        serializer = RunBacktestRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Get strategy
        strategy = Strategy.objects.get(id=data['strategy_id'])
        symbol = Symbol.objects.get(id=data['symbol_id'])
        
        # Create backtest run
        backtest_name = data.get('name') or f"{strategy.name} - {symbol.name} {data['interval']}"
        
        backtest_run = BacktestRun.objects.create (
            name=backtest_name,
            strategy=strategy,
            symbol=symbol,
            interval=data['interval'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            initial_capital=strategy.initial_capital,
            status='pending'
        )
        
        # Trigger Celery task
        task = run_backtest_task.delay(backtest_run.id)
        
        return Response({
            'status': 'task_dispatched',
            'task_id': task.id,
            'backtest_run_id': backtest_run.id,
            'backtest_run_name': backtest_run.name
        }, status=status.HTTP_202_ACCEPTED)


class OptimizeStrategyView(APIView):
    """
    API view to trigger strategy parameter optimization.
    """
    
    @extend_schema(request=OptimizeStrategyRequestSerializer)
    def post(self, request):
        """Optimize strategy parameters."""
        serializer = OptimizeStrategyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Trigger Celery task
        task = run_strategy_optimization.delay(
            strategy_id=data['strategy_id'],
            symbol_id=data['symbol_id'],
            interval=data['interval']
        )
        
        return Response({
            'status': 'task_dispatched',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)


class BacktestStatsView(APIView):
    """
    API view to get aggregated backtest statistics.
    """
    
    def get(self, request):
        """Get backtest statistics."""
        from django.db.models import Count, Avg, Max, Min
        
        # Overall stats
        total_runs = BacktestRun.objects.count()
        completed_runs = BacktestRun.objects.filter(status='completed').count()
        
        # Performance stats
        avg_return = BacktestRun.objects.filter(
            status='completed',
            total_return__isnull=False
        ).aggregate(Avg('total_return'))['total_return__avg']
        
        best_run = BacktestRun.objects.filter(
            status='completed',
            total_return__isnull=False
        ).order_by('-total_return').first()
        
        # Strategy stats
        strategy_stats = Strategy.objects.annotate(
            runs_count=Count('runs'),
            avg_return=Avg('runs__total_return', filter=models.Q(runs__status='completed'))
        ).values('id', 'name', 'runs_count', 'avg_return')
        
        return Response({
            'total_runs': total_runs,
            'completed_runs': completed_runs,
            'avg_return': avg_return,
            'best_run': {
                'id': best_run.id,
                'name': best_run.name,
                'total_return': best_run.total_return,
                'sharpe_ratio': best_run.sharpe_ratio
            } if best_run else None,
            'strategy_stats': list(strategy_stats)
        })


from apps.market_data.models import Symbol
from django.db import models
