"""
DRF Views for analysis app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.analysis.models import IndicatorCache, SignalRule, Signal, PatternDetection
from apps.analysis.serializers import (
    IndicatorCacheSerializer,
    IndicatorCacheListSerializer,
    SignalRuleSerializer,
    SignalSerializer,
    SignalListSerializer,
    PatternDetectionSerializer,
    ComputeIndicatorsRequestSerializer,
    GenerateSignalsRequestSerializer,
)
from apps.analysis.tasks import (
    compute_indicators_task,
    generate_signals_task,
    compute_all_symbols_indicators,
    generate_all_signals,
)
import logging

logger = logging.getLogger(__name__)


class IndicatorCacheViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing cached technical indicators.
    
    list: Get list of cached indicators
    retrieve: Get specific indicator record
    latest: Get latest indicators for a symbol
    """
    queryset = IndicatorCache.objects.all()
    serializer_class = IndicatorCacheSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['symbol', 'interval', 'timestamp']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    search_fields = ['symbol__name']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return IndicatorCacheListSerializer
        return IndicatorCacheSerializer
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='symbol_id', type=OpenApiTypes.INT, required=True),
            OpenApiParameter(name='interval', type=OpenApiTypes.STR, default='1h'),
        ]
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest indicators for a symbol."""
        symbol_id = request.query_params.get('symbol_id')
        interval = request.query_params.get('interval', '1h')
        
        if not symbol_id:
            return Response(
                {'error': 'symbol_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        indicator = self.queryset.filter(
            symbol_id=symbol_id,
            interval=interval
        ).order_by('-timestamp').first()
        
        if not indicator:
            return Response(
                {'error': 'No indicators found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(indicator)
        return Response(serializer.data)


class SignalRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing signal rules.
    
    list: Get all signal rules
    create: Create a new signal rule
    retrieve: Get specific signal rule
    update: Update a signal rule
    destroy: Delete a signal rule
    """
    queryset = SignalRule.objects.all()
    serializer_class = SignalRuleSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['signal_type', 'is_active']
    ordering_fields = ['priority', 'created_at']
    ordering = ['-priority', 'name']
    search_fields = ['name', 'description']


class SignalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing trading signals.
    
    list: Get list of signals
    retrieve: Get specific signal
    latest: Get latest signals
    active: Get active signals only
    """
    queryset = Signal.objects.all()
    serializer_class = SignalSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['symbol', 'interval', 'signal_type', 'is_active']
    ordering_fields = ['timestamp', 'strength', 'confidence']
    ordering = ['-timestamp']
    search_fields = ['symbol__name', 'notes']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SignalListSerializer
        return SignalSerializer
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active signals only."""
        signals = self.queryset.filter(is_active=True)
        
        # Optional filters
        symbol_id = request.query_params.get('symbol_id')
        interval = request.query_params.get('interval')
        signal_type = request.query_params.get('signal_type')
        
        if symbol_id:
            signals = signals.filter(symbol_id=symbol_id)
        if interval:
            signals = signals.filter(interval=interval)
        if signal_type:
            signals = signals.filter(signal_type=signal_type)
        
        page = self.paginate_queryset(signals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(signals, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='symbol_id', type=OpenApiTypes.INT),
            OpenApiParameter(name='interval', type=OpenApiTypes.STR, default='1h'),
            OpenApiParameter(name='limit', type=OpenApiTypes.INT, default=10),
        ]
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest signals."""
        limit = int(request.query_params.get('limit', 10))
        symbol_id = request.query_params.get('symbol_id')
        interval = request.query_params.get('interval')
        
        signals = self.queryset.all()
        
        if symbol_id:
            signals = signals.filter(symbol_id=symbol_id)
        if interval:
            signals = signals.filter(interval=interval)
        
        signals = signals[:limit]
        serializer = self.get_serializer(signals, many=True)
        return Response(serializer.data)


class PatternDetectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing detected patterns.
    
    list: Get list of detected patterns
    retrieve: Get specific pattern
    latest: Get latest patterns
    """
    queryset = PatternDetection.objects.all()
    serializer_class = PatternDetectionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['symbol', 'interval', 'pattern_type', 'direction']
    ordering_fields = ['timestamp', 'reliability']
    ordering = ['-timestamp']
    search_fields = ['symbol__name', 'pattern_type']
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest detected patterns."""
        limit = int(request.query_params.get('limit', 20))
        symbol_id = request.query_params.get('symbol_id')
        pattern_type = request.query_params.get('pattern_type')
        
        patterns = self.queryset.all()
        
        if symbol_id:
            patterns = patterns.filter(symbol_id=symbol_id)
        if pattern_type:
            patterns = patterns.filter(pattern_type=pattern_type)
        
        patterns = patterns[:limit]
        serializer = self.get_serializer(patterns, many=True)
        return Response(serializer.data)


class ComputeIndicatorsView(APIView):
    """
    API view to trigger indicator computation.
    """
    
    @extend_schema(request=ComputeIndicatorsRequestSerializer)
    def post(self, request):
        """Trigger indicator computation for a symbol."""
        serializer = ComputeIndicatorsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        symbol_id = serializer.validated_data['symbol_id']
        interval = serializer.validated_data['interval']
        lookback_periods = serializer.validated_data['lookback_periods']
        
        # Trigger Celery task
        task = compute_indicators_task.delay(symbol_id, interval, lookback_periods)
        
        return Response({
            'status': 'task_dispatched',
            'task_id': task.id,
            'symbol_id': symbol_id,
            'interval': interval,
            'lookback_periods': lookback_periods
        }, status=status.HTTP_202_ACCEPTED)


class ComputeAllIndicatorsView(APIView):
    """
    API view to compute indicators for all tracked symbols.
    """
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='interval', type=OpenApiTypes.STR, default='1h'),
            OpenApiParameter(name='limit', type=OpenApiTypes.INT, default=50),
        ]
    )
    def post(self, request):
        """Compute indicators for all tracked symbols."""
        interval = request.query_params.get('interval', '1h')
        limit = int(request.query_params.get('limit', 50))
        
        # Trigger Celery task
        task = compute_all_symbols_indicators.delay(interval, limit)
        
        return Response({
            'status': 'task_dispatched',
            'task_id': task.id,
            'interval': interval,
            'limit': limit
        }, status=status.HTTP_202_ACCEPTED)


class GenerateSignalsView(APIView):
    """
    API view to trigger signal generation.
    """
    
    @extend_schema(request=GenerateSignalsRequestSerializer)
    def post(self, request):
        """Generate signals for a symbol."""
        serializer = GenerateSignalsRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        symbol_id = serializer.validated_data['symbol_id']
        interval = serializer.validated_data['interval']
        
        # Trigger Celery task
        task = generate_signals_task.delay(symbol_id, interval)
        
        return Response({
            'status': 'task_dispatched',
            'task_id': task.id,
            'symbol_id': symbol_id,
            'interval': interval
        }, status=status.HTTP_202_ACCEPTED)


class GenerateAllSignalsView(APIView):
    """
    API view to generate signals for all tracked symbols.
    """
    
    @extend_schema(
        parameters=[
            OpenApiParameter(name='interval', type=OpenApiTypes.STR, default='1h'),
            OpenApiParameter(name='limit', type=OpenApiTypes.INT, default=50),
        ]
    )
    def post(self, request):
        """Generate signals for all tracked symbols."""
        interval = request.query_params.get('interval', '1h')
        limit = int(request.query_params.get('limit', 50))
        
        # Trigger Celery task
        task = generate_all_signals.delay(interval, limit)
        
        return Response({
            'status': 'task_dispatched',
            'task_id': task.id,
            'interval': interval,
            'limit': limit
        }, status=status.HTTP_202_ACCEPTED)
