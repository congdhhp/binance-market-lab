"""
Views for orderbook analytics API.
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from apps.market_data.models import Symbol
from apps.orderbook.models import OrderbookAnalysis, ImbalanceAlert
from apps.orderbook.serializers import (
    OrderbookAnalysisSerializer,
    ImbalanceAlertSerializer,
    RiskMetricsSerializer,
    CorrelationMatrixSerializer,
    RegimeDetectionSerializer,
)
from apps.orderbook.tasks import (
    analyze_orderbook_snapshots,
    calculate_risk_metrics,
    calculate_correlation_matrix,
    detect_regime,
)

logger = logging.getLogger(__name__)


class OrderbookAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for orderbook analysis.
    
    Provides read-only access to orderbook analysis data.
    """
    
    queryset = OrderbookAnalysis.objects.select_related('symbol').all()
    serializer_class = OrderbookAnalysisSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['symbol', 'timestamp']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """
        Trigger orderbook analysis.
        
        POST body:
        {
            "symbol_id": 1,  // Optional
            "levels": 10     // Optional, default 10
        }
        """
        symbol_id = request.data.get('symbol_id')
        levels = request.data.get('levels', 10)
        
        # Trigger async task
        task = analyze_orderbook_snapshots.delay(symbol_id=symbol_id, levels=levels)
        
        return Response({
            'task_id': task.id,
            'message': 'Orderbook analysis started'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get latest orderbook analysis for each symbol.
        """
        symbol_id = request.query_params.get('symbol')
        
        if symbol_id:
            analysis = OrderbookAnalysis.objects.filter(
                symbol_id=symbol_id
            ).order_by('-timestamp').first()
            
            if not analysis:
                return Response(
                    {'error': 'No analysis found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(analysis)
            return Response(serializer.data)
        
        # Get latest for all symbols
        symbols = Symbol.objects.filter(is_active=True)
        results = []
        
        for symbol in symbols:
            analysis = OrderbookAnalysis.objects.filter(
                symbol=symbol
            ).order_by('-timestamp').first()
            
            if analysis:
                serializer = self.get_serializer(analysis)
                results.append(serializer.data)
        
        return Response(results)


class ImbalanceAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for imbalance alerts.
    
    Provides read-only access to imbalance alerts.
    """
    
    queryset = ImbalanceAlert.objects.select_related('symbol').all()
    serializer_class = ImbalanceAlertSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['symbol', 'alert_type', 'severity', 'is_resolved']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """
        Get active (unresolved) alerts.
        """
        symbol_id = request.query_params.get('symbol')
        
        queryset = ImbalanceAlert.objects.filter(is_resolved=False)
        
        if symbol_id:
            queryset = queryset.filter(symbol_id=symbol_id)
        
        queryset = queryset.order_by('-timestamp')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Resolve an alert.
        """
        alert = self.get_object()
        
        if alert.is_resolved:
            return Response(
                {'message': 'Alert already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils import timezone
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)


class RiskMetricsViewSet(viewsets.ViewSet):
    """
    ViewSet for risk metrics calculation.
    """
    
    def list(self, request):
        """
        Get risk metrics for a symbol.
        
        Query params:
        - symbol: Symbol ID (required)
        - lookback_days: Number of days (default 30)
        """
        symbol_id = request.query_params.get('symbol')
        
        if not symbol_id:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lookback_days = int(request.query_params.get('lookback_days', 30))
        
        # Trigger async task
        task = calculate_risk_metrics.delay(
            symbol_id=int(symbol_id),
            lookback_days=lookback_days
        )
        
        # Wait for result (or use task.get() for sync)
        # For now, return task ID
        return Response({
            'task_id': task.id,
            'message': 'Risk metrics calculation started'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calculate risk metrics (async).
        
        POST body:
        {
            "symbol_id": 1,
            "lookback_days": 30
        }
        """
        symbol_id = request.data.get('symbol_id')
        lookback_days = request.data.get('lookback_days', 30)
        
        if not symbol_id:
            return Response(
                {'error': 'symbol_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async task
        task = calculate_risk_metrics.delay(
            symbol_id=symbol_id,
            lookback_days=lookback_days
        )
        
        return Response({
            'task_id': task.id,
            'message': 'Risk metrics calculation started'
        }, status=status.HTTP_202_ACCEPTED)


class CorrelationViewSet(viewsets.ViewSet):
    """
    ViewSet for correlation analysis.
    """
    
    def list(self, request):
        """
        Get correlation matrix.
        
        Query params:
        - lookback_days: Number of days (default 30)
        """
        lookback_days = int(request.query_params.get('lookback_days', 30))
        
        # Trigger async task
        task = calculate_correlation_matrix.delay(lookback_days=lookback_days)
        
        return Response({
            'task_id': task.id,
            'message': 'Correlation matrix calculation started'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """
        Calculate correlation matrix (async).
        
        POST body:
        {
            "lookback_days": 30
        }
        """
        lookback_days = request.data.get('lookback_days', 30)
        
        # Trigger async task
        task = calculate_correlation_matrix.delay(lookback_days=lookback_days)
        
        return Response({
            'task_id': task.id,
            'message': 'Correlation matrix calculation started'
        }, status=status.HTTP_202_ACCEPTED)


class RegimeDetectionViewSet(viewsets.ViewSet):
    """
    ViewSet for market regime detection.
    """
    
    def list(self, request):
        """
        Detect market regime for a symbol.
        
        Query params:
        - symbol: Symbol ID (required)
        - lookback_days: Number of days (default 90)
        """
        symbol_id = request.query_params.get('symbol')
        
        if not symbol_id:
            return Response(
                {'error': 'symbol parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lookback_days = int(request.query_params.get('lookback_days', 90))
        
        # Trigger async task
        task = detect_regime.delay(
            symbol_id=int(symbol_id),
            lookback_days=lookback_days
        )
        
        return Response({
            'task_id': task.id,
            'message': 'Regime detection started'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=['post'])
    def detect(self, request):
        """
        Detect market regime (async).
        
        POST body:
        {
            "symbol_id": 1,
            "lookback_days": 90
        }
        """
        symbol_id = request.data.get('symbol_id')
        lookback_days = request.data.get('lookback_days', 90)
        
        if not symbol_id:
            return Response(
                {'error': 'symbol_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async task
        task = detect_regime.delay(
            symbol_id=symbol_id,
            lookback_days=lookback_days
        )
        
        return Response({
            'task_id': task.id,
            'message': 'Regime detection started'
        }, status=status.HTTP_202_ACCEPTED)
