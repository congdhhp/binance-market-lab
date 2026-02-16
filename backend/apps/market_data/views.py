"""
DRF views for market_data app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    Symbol, Kline, Trade, OrderBookSnapshot,
    Ticker24h, FundingRate, OpenInterest, IngestionLog
)
from .serializers import (
    SymbolSerializer, KlineSerializer, TradeSerializer,
    OrderBookSnapshotSerializer, Ticker24hSerializer,
    FundingRateSerializer, OpenInterestSerializer,
    IngestionLogSerializer, BackfillRequestSerializer
)

logger = logging.getLogger(__name__)


class SymbolViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Symbol model.
    """
    queryset = Symbol.objects.all()
    serializer_class = SymbolSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['is_tracked', 'is_spot', 'is_futures', 'status']
    ordering_fields = ['name', 'priority', 'created_at']
    ordering = ['-priority', 'name']


class KlineViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Kline model. Read-only, data ingested by Celery tasks.
    """
    queryset = Kline.objects.select_related('symbol').all()
    serializer_class = KlineSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['symbol', 'interval']
    ordering_fields = ['open_time']
    ordering = ['-open_time']

    def get_queryset(self):
        """Custom queryset with time range filtering."""
        queryset = super().get_queryset()
        
        # Filter by symbol name if provided
        symbol_name = self.request.query_params.get('symbol_name', None)
        if symbol_name:
            queryset = queryset.filter(symbol__name=symbol_name)
        
        # Filter by time range
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        
        if start_time:
            queryset = queryset.filter(open_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(open_time__lte=end_time)
        
        return queryset

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest kline for each symbol."""
        symbol_name = request.query_params.get('symbol_name')
        interval = request.query_params.get('interval', '1h')
        
        if not symbol_name:
            return Response(
                {'error': 'symbol_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            symbol = Symbol.objects.get(name=symbol_name)
            latest_kline = Kline.objects.filter(
                symbol=symbol,
                interval=interval
            ).order_by('-open_time').first()
            
            if not latest_kline:
                return Response(
                    {'error': 'No data found for this symbol and interval'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(latest_kline)
            return Response(serializer.data)
        
        except Symbol.DoesNotExist:
            return Response(
                {'error': 'Symbol not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Trade model.
    """
    queryset = Trade.objects.select_related('symbol').all()
    serializer_class = TradeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['symbol', 'is_buyer_maker']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Custom queryset with time range filtering."""
        queryset = super().get_queryset()
        
        symbol_name = self.request.query_params.get('symbol_name', None)
        if symbol_name:
            queryset = queryset.filter(symbol__name=symbol_name)
        
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        
        if start_time:
            queryset = queryset.filter(timestamp__gte=start_time)
        if end_time:
            queryset = queryset.filter(timestamp__lte=end_time)
        
        return queryset


class OrderBookSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for OrderBookSnapshot model.
    """
    queryset = OrderBookSnapshot.objects.select_related('symbol').all()
    serializer_class = OrderBookSnapshotSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['symbol']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Custom queryset with filtering."""
        queryset = super().get_queryset()
        
        symbol_name = self.request.query_params.get('symbol_name', None)
        if symbol_name:
            queryset = queryset.filter(symbol__name=symbol_name)
        
        return queryset

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest orderbook snapshot for a symbol."""
        symbol_name = request.query_params.get('symbol_name')
        
        if not symbol_name:
            return Response(
                {'error': 'symbol_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            symbol = Symbol.objects.get(name=symbol_name)
            latest_snapshot = OrderBookSnapshot.objects.filter(
                symbol=symbol
            ).order_by('-timestamp').first()
            
            if not latest_snapshot:
                return Response(
                    {'error': 'No orderbook data found for this symbol'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(latest_snapshot)
            return Response(serializer.data)
        
        except Symbol.DoesNotExist:
            return Response(
                {'error': 'Symbol not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class Ticker24hViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Ticker24h model.
    """
    queryset = Ticker24h.objects.select_related('symbol').all()
    serializer_class = Ticker24hSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['symbol']
    ordering_fields = ['timestamp', 'price_change_percent', 'volume']
    ordering = ['-timestamp']

    @action(detail=False, methods=['get'])
    def latest_all(self, request):
        """Get latest ticker for all tracked symbols."""
        # Get latest ticker for each symbol (subquery)
        from django.db.models import OuterRef, Subquery
        
        latest_tickers = Ticker24h.objects.filter(
            symbol=OuterRef('symbol')
        ).order_by('-timestamp')
        
        symbols = Symbol.objects.filter(is_tracked=True).annotate(
            latest_ticker_id=Subquery(latest_tickers.values('id')[:1])
        )
        
        ticker_ids = [s.latest_ticker_id for s in symbols if s.latest_ticker_id]
        tickers = Ticker24h.objects.filter(id__in=ticker_ids).select_related('symbol')
        
        serializer = self.get_serializer(tickers, many=True)
        return Response(serializer.data)


class FundingRateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for FundingRate model.
    """
    queryset = FundingRate.objects.select_related('symbol').all()
    serializer_class = FundingRateSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['symbol']
    ordering_fields = ['funding_time']
    ordering = ['-funding_time']

    def get_queryset(self):
        """Custom queryset with filtering."""
        queryset = super().get_queryset()
        
        symbol_name = self.request.query_params.get('symbol_name', None)
        if symbol_name:
            queryset = queryset.filter(symbol__name=symbol_name)
        
        return queryset


class OpenInterestViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for OpenInterest model.
    """
    queryset = OpenInterest.objects.select_related('symbol').all()
    serializer_class = OpenInterestSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['symbol']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        """Custom queryset with filtering."""
        queryset = super().get_queryset()
        
        symbol_name = self.request.query_params.get('symbol_name', None)
        if symbol_name:
            queryset = queryset.filter(symbol__name=symbol_name)
        
        return queryset


class IngestionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for IngestionLog model.
    """
    queryset = IngestionLog.objects.select_related('symbol').all()
    serializer_class = IngestionLogSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['symbol', 'data_type', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']


class TriggerBackfillView(APIView):
    """
    API endpoint to trigger manual backfill of historical data.
    """
    def post(self, request):
        serializer = BackfillRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        symbol_name = data['symbol']
        interval = data['interval']
        start_date = data['start_date']
        end_date = data.get('end_date', timezone.now())
        
        # Verify symbol exists
        try:
            symbol = Symbol.objects.get(name=symbol_name)
        except Symbol.DoesNotExist:
            return Response(
                {'error': f'Symbol {symbol_name} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Import and trigger Celery task
        from .tasks import bulk_backfill_task
        
        task = bulk_backfill_task.delay(
            symbol=symbol_name,
            interval=interval,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        logger.info(f"Backfill task triggered: {task.id} for {symbol_name} {interval}")
        
        return Response({
            'message': 'Backfill task triggered successfully',
            'task_id': task.id,
            'symbol': symbol_name,
            'interval': interval,
            'start_date': start_date,
            'end_date': end_date
        }, status=status.HTTP_202_ACCEPTED)


class IngestionStatusView(APIView):
    """
    API endpoint to check overall ingestion health status.
    """
    def get(self, request):
        # Get recent ingestion logs
        recent_logs = IngestionLog.objects.all()[:100]
        
        # Stats by data type
        stats = {}
        for data_type, _ in IngestionLog._meta.get_field('data_type').choices:
            recent_type_logs = recent_logs.filter(data_type=data_type)
            stats[data_type] = {
                'total': recent_type_logs.count(),
                'success': recent_type_logs.filter(status='success').count(),
                'failed': recent_type_logs.filter(status='failed').count(),
                'running': recent_type_logs.filter(status='running').count(),
            }
        
        # Check for recent failures
        recent_failures = IngestionLog.objects.filter(
            status='failed',
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Overall health
        health = 'healthy' if recent_failures < 10 else 'degraded' if recent_failures < 50 else 'unhealthy'
        
        return Response({
            'health': health,
            'recent_failures_24h': recent_failures,
            'stats_by_type': stats,
            'timestamp': timezone.now()
        })
