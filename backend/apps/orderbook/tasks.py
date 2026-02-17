"""
Celery tasks for orderbook analytics.
"""
import logging
from decimal import Decimal
from datetime import timedelta
from typing import List, Optional
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
import numpy as np
import pandas as pd

from apps.market_data.models import Symbol, OrderBookSnapshot, Kline
from apps.orderbook.models import OrderbookAnalysis, ImbalanceAlert
from apps.orderbook.services import analyze_orderbook
from apps.orderbook.services.risk_metrics import calculate_portfolio_risk
from apps.orderbook.services.correlation import analyze_correlation
from apps.orderbook.services.regime_detection import detect_market_regime

logger = logging.getLogger(__name__)


@shared_task(name='orderbook.analyze_orderbook_snapshots')
def analyze_orderbook_snapshots(symbol_id: Optional[int] = None, levels: int = 10):
    """
    Analyze recent orderbook snapshots.
    
    Args:
        symbol_id: Optional symbol ID (None = all symbols)
        levels: Number of price levels to analyze
    """
    logger.info(f"Starting orderbook analysis for symbol_id={symbol_id}, levels={levels}")
    
    # Get symbols
    if symbol_id:
        symbols = Symbol.objects.filter(id=symbol_id, is_active=True)
    else:
        symbols = Symbol.objects.filter(is_active=True)
    
    analyzed_count = 0
    
    for symbol in symbols:
        try:
            # Get latest unanalyzed snapshot
            analyzed_timestamps = OrderbookAnalysis.objects.filter(
                symbol=symbol
            ).values_list('timestamp', flat=True)
            
            snapshot = OrderBookSnapshot.objects.filter(
                symbol=symbol
            ).exclude(
                timestamp__in=analyzed_timestamps
            ).order_by('-timestamp').first()
            
            if not snapshot:
                logger.debug(f"No new snapshots for {symbol.name}")
                continue
            
            # Analyze snapshot
            analysis = analyze_orderbook(snapshot, levels=levels)
            analyzed_count += 1
            
            logger.info(f"Analyzed orderbook for {symbol.name} at {snapshot.timestamp}")
            
        except Exception as e:
            logger.error(f"Error analyzing orderbook for {symbol.name}: {e}", exc_info=True)
    
    logger.info(f"Orderbook analysis completed. Analyzed {analyzed_count} snapshots")
    
    return {
        'analyzed_count': analyzed_count,
        'symbols_processed': symbols.count()
    }


@shared_task(name='orderbook.calculate_risk_metrics')
def calculate_risk_metrics(symbol_id: int, lookback_days: int = 30):
    """
    Calculate risk metrics for a symbol.
    
    Args:
        symbol_id: Symbol ID
        lookback_days: Number of days to analyze
    """
    logger.info(f"Calculating risk metrics for symbol_id={symbol_id}, lookback={lookback_days}d")
    
    try:
        symbol = Symbol.objects.get(id=symbol_id, is_active=True)
        
        # Get historical klines
        start_time = timezone.now() - timedelta(days=lookback_days)
        klines = Kline.objects.filter(
            symbol=symbol,
            interval='1d',
            open_time__gte=start_time
        ).order_by('open_time')
        
        if klines.count() < 10:
            logger.warning(f"Insufficient data for {symbol.name}: {klines.count()} klines")
            return {'error': 'Insufficient data'}
        
        # Extract prices and calculate returns
        prices = np.array([float(k.close_price) for k in klines])
        returns = np.diff(np.log(prices))
        
        # Calculate risk metrics
        metrics = calculate_portfolio_risk(
            returns=returns,
            prices=prices,
            confidence_level=0.95,
            risk_free_rate=0.02,
            periods_per_year=365
        )
        
        logger.info(f"Risk metrics calculated for {symbol.name}: Sharpe={metrics['sharpe_ratio']:.2f}")
        
        return {
            'symbol': symbol.name,
            'lookback_days': lookback_days,
            'metrics': metrics
        }
        
    except Symbol.DoesNotExist:
        logger.error(f"Symbol not found: {symbol_id}")
        return {'error': 'Symbol not found'}
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task(name='orderbook.calculate_correlation_matrix')
def calculate_correlation_matrix(lookback_days: int = 30):
    """
    Calculate correlation matrix for all active symbols.
    
    Args:
        lookback_days: Number of days to analyze
    """
    logger.info(f"Calculating correlation matrix, lookback={lookback_days}d")
    
    try:
        # Get active symbols
        symbols = Symbol.objects.filter(is_active=True)
        
        if symbols.count() < 2:
            logger.warning("Need at least 2 symbols for correlation")
            return {'error': 'Insufficient symbols'}
        
        # Get historical klines for all symbols
        start_time = timezone.now() - timedelta(days=lookback_days)
        
        returns_data = {}
        
        for symbol in symbols:
            klines = Kline.objects.filter(
                symbol=symbol,
                interval='1d',
                open_time__gte=start_time
            ).order_by('open_time')
            
            if klines.count() < 10:
                continue
            
            prices = np.array([float(k.close_price) for k in klines])
            returns = np.diff(np.log(prices))
            
            # Use timestamps as index
            timestamps = [k.open_time for k in klines][1:]  # Skip first (no return)
            
            returns_data[symbol.name] = pd.Series(returns, index=timestamps)
        
        if len(returns_data) < 2:
            logger.warning("Insufficient data for correlation matrix")
            return {'error': 'Insufficient data'}
        
        # Create DataFrame
        returns_df = pd.DataFrame(returns_data)
        
        # Calculate correlation analysis
        analysis = analyze_correlation(returns_df, method='pearson', min_periods=10)
        
        logger.info(f"Correlation matrix calculated for {len(returns_data)} symbols")
        
        return {
            'symbols': list(returns_data.keys()),
            'lookback_days': lookback_days,
            'analysis': {
                'heatmap_data': analysis['heatmap_data'],
                'highly_correlated_pairs': analysis['highly_correlated_pairs'],
                'diversification_ratio': analysis['diversification_ratio'],
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task(name='orderbook.detect_regime')
def detect_regime(symbol_id: int, lookback_days: int = 90):
    """
    Detect market regime for a symbol using HMM.
    
    Args:
        symbol_id: Symbol ID
        lookback_days: Number of days to analyze
    """
    logger.info(f"Detecting market regime for symbol_id={symbol_id}, lookback={lookback_days}d")
    
    try:
        symbol = Symbol.objects.get(id=symbol_id, is_active=True)
        
        # Get historical klines
        start_time = timezone.now() - timedelta(days=lookback_days)
        klines = Kline.objects.filter(
            symbol=symbol,
            interval='1d',
            open_time__gte=start_time
        ).order_by('open_time')
        
        if klines.count() < 30:
            logger.warning(f"Insufficient data for {symbol.name}: {klines.count()} klines")
            return {'error': 'Insufficient data (need at least 30 days)'}
        
        # Extract prices and volumes
        prices = np.array([float(k.close_price) for k in klines])
        volumes = np.array([float(k.volume) for k in klines])
        
        # Detect regime
        regime_info = detect_market_regime(
            prices=prices,
            volumes=volumes,
            n_regimes=4,
            window=20
        )
        
        current_regime = regime_info['current_regime']
        
        logger.info(
            f"Market regime detected for {symbol.name}: "
            f"{current_regime['regime_label']} (ID: {current_regime['regime_id']})"
        )
        
        return {
            'symbol': symbol.name,
            'lookback_days': lookback_days,
            'current_regime': current_regime,
            'transition_analysis': regime_info['transition_analysis']
        }
        
    except Symbol.DoesNotExist:
        logger.error(f"Symbol not found: {symbol_id}")
        return {'error': 'Symbol not found'}
    except Exception as e:
        logger.error(f"Error detecting regime: {e}", exc_info=True)
        return {'error': str(e)}


@shared_task(name='orderbook.cleanup_old_alerts')
def cleanup_old_alerts(days_to_keep: int = 7):
    """
    Clean up old resolved alerts.
    
    Args:
        days_to_keep: Number of days to keep resolved alerts
    """
    logger.info(f"Cleaning up alerts older than {days_to_keep} days")
    
    cutoff_time = timezone.now() - timedelta(days=days_to_keep)
    
    deleted_count, _ = ImbalanceAlert.objects.filter(
        is_resolved=True,
        resolved_at__lt=cutoff_time
    ).delete()
    
    logger.info(f"Deleted {deleted_count} old alerts")
    
    return {'deleted_count': deleted_count}


@shared_task(name='orderbook.resolve_stale_alerts')
def resolve_stale_alerts(max_age_hours: int = 24):
    """
    Auto-resolve stale alerts that haven't been updated.
    
    Args:
        max_age_hours: Maximum age in hours before auto-resolving
    """
    logger.info(f"Resolving alerts older than {max_age_hours} hours")
    
    cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
    
    stale_alerts = ImbalanceAlert.objects.filter(
        is_resolved=False,
        timestamp__lt=cutoff_time
    )
    
    updated_count = stale_alerts.update(
        is_resolved=True,
        resolved_at=timezone.now()
    )
    
    logger.info(f"Auto-resolved {updated_count} stale alerts")
    
    return {'resolved_count': updated_count}
