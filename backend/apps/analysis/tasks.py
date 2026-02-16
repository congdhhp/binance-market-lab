"""
Celery tasks for technical analysis and signal generation.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def compute_indicators_task(self, symbol_id: int, interval: str = '1h', lookback_periods: int = 500):
    """
    Compute all technical indicators for a symbol and interval.
    
    Args:
        symbol_id: Symbol ID
        interval: Kline interval
        lookback_periods: Number of candles to include in calculation
    """
    from apps.market_data.models import Symbol, Kline
    from apps.analysis.models import IndicatorCache
    from apps.analysis.services import IndicatorService
    
    try:
        symbol = Symbol.objects.get(id=symbol_id)
        logger.info(f"Computing indicators for {symbol.name} {interval}")
        
        # Fetch recent klines
        end_time = timezone.now()
        klines = Kline.objects.filter(
            symbol=symbol,
            interval=interval
        ).order_by('-open_time')[:lookback_periods]
        
        if len(klines) < 50:  # Need minimum data
            logger.warning(f"Insufficient data for {symbol.name} {interval}: {len(klines)} candles")
            return {'status': 'insufficient_data', 'candles': len(klines)}
        
        # Convert to DataFrame
        df = pd.DataFrame(list(klines.values(
            'open_time', 'open', 'high', 'low', 'close', 'volume'
        )))
        
        # Reverse to chronological order
        df = df.iloc[::-1].reset_index(drop=True)
        
        # Compute indicators
        indicator_service = IndicatorService(df)
        df_with_indicators = indicator_service.compute_all()
        
        # Save to cache (last N candles)
        saved_count = 0
        for idx, row in df_with_indicators.tail(100).iterrows():
            # Skip if indicators are NaN (warming up period)
            if pd.isna(row['rsi']) or pd.isna(row['macd']):
                continue
            
            IndicatorCache.objects.update_or_create(
                symbol=symbol,
                interval=interval,
                timestamp=row['open_time'],
                defaults={
                    'ema_9': row.get('ema_9'),
                    'ema_21': row.get('ema_21'),
                    'ema_50': row.get('ema_50'),
                    'ema_100': row.get('ema_100'),
                    'ema_200': row.get('ema_200'),
                    'sma_20': row.get('sma_20'),
                    'sma_50': row.get('sma_50'),
                    'sma_200': row.get('sma_200'),
                    'macd': row.get('macd'),
                    'macd_signal': row.get('macd_signal'),
                    'macd_diff': row.get('macd_diff'),
                    'adx': row.get('adx'),
                    'adx_pos': row.get('adx_pos'),
                    'adx_neg': row.get('adx_neg'),
                    'rsi': row.get('rsi'),
                    'stoch_k': row.get('stoch_k'),
                    'stoch_d': row.get('stoch_d'),
                    'williams_r': row.get('williams_r'),
                    'bb_high': row.get('bb_high'),
                    'bb_mid': row.get('bb_mid'),
                    'bb_low': row.get('bb_low'),
                    'bb_width': row.get('bb_width'),
                    'atr': row.get('atr'),
                    'vwap': row.get('vwap'),
                    'obv': row.get('obv'),
                    'hull_ma': row.get('hull_ma'),
                    'supertrend': row.get('supertrend'),
                    'supertrend_direction': row.get('supertrend_direction'),
                }
            )
            saved_count += 1
        
        logger.info(f"Saved {saved_count} indicator records for {symbol.name} {interval}")
        
        return {
            'status': 'success',
            'symbol': symbol.name,
            'interval': interval,
            'indicators_computed': len(df_with_indicators.columns),
            'records_saved': saved_count
        }
        
    except Symbol.DoesNotExist:
        logger.error(f"Symbol {symbol_id} not found")
        return {'status': 'error', 'message': 'Symbol not found'}
    except Exception as e:
        logger.error(f"Error computing indicators for symbol {symbol_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def compute_all_symbols_indicators(interval: str = '1h', limit: int = 50):
    """
    Compute indicators for all tracked symbols.
    
    Args:
        interval: Kline interval
        limit: Maximum number of symbols to process
    """
    from apps.market_data.models import Symbol
    
    symbols = Symbol.objects.filter(is_tracked=True).order_by('-priority')[:limit]
    
    logger.info(f"Computing indicators for {len(symbols)} symbols ({interval})")
    
    results = []
    for symbol in symbols:
        result = compute_indicators_task.delay(symbol.id, interval)
        results.append(result.id)
    
    return {
        'status': 'dispatched',
        'symbols_count': len(symbols),
        'interval': interval,
        'task_ids': results
    }


@shared_task(bind=True, max_retries=3)
def generate_signals_task(self, symbol_id: int, interval: str = '1h'):
    """
    Generate trading signals for a symbol based on latest indicators.
    
    Args:
        symbol_id: Symbol ID
        interval: Time interval
    """
    from apps.market_data.models import Symbol, Kline
    from apps.analysis.models import IndicatorCache, Signal
    from apps.analysis.services import SignalEngine
    
    try:
        symbol = Symbol.objects.get(id=symbol_id)
        
        # Get latest indicators
        latest_indicator = IndicatorCache.objects.filter(
            symbol=symbol,
            interval=interval
        ).order_by('-timestamp').first()
        
        if not latest_indicator:
            logger.warning(f"No indicators found for {symbol.name} {interval}")
            return {'status': 'no_indicators'}
        
        # Get latest price
        latest_kline = Kline.objects.filter(
            symbol=symbol,
            interval=interval
        ).order_by('-open_time').first()
        
        if not latest_kline:
            logger.warning(f"No klines found for {symbol.name} {interval}")
            return {'status': 'no_klines'}
        
        # Convert indicators to dict
        indicators = {}
        for field in latest_indicator._meta.fields:
            if field.name not in ['id', 'symbol', 'interval', 'timestamp', 'created_at']:
                value = getattr(latest_indicator, field.name)
                if value is not None:
                    indicators[field.name] = float(value)
        
        # Initialize signal engine
        signal_engine = SignalEngine()
        
        # Generate signals from rules
        rule_signals = signal_engine.evaluate_symbol(
            symbol=symbol,
            interval=interval,
            indicators=indicators,
            price=float(latest_kline.close)
        )
        
        # Generate composite signal
        composite_signal = signal_engine.generate_composite_signal(
            symbol=symbol,
            interval=interval,
            indicators=indicators,
            price=float(latest_kline.close)
        )
        
        # Save signals
        saved_signals = []
        for signal in rule_signals:
            signal.save()
            saved_signals.append(signal.id)
        
        if composite_signal:
            composite_signal.save()
            saved_signals.append(composite_signal.id)
        
        logger.info(
            f"Generated {len(saved_signals)} signals for {symbol.name} {interval}"
        )
        
        return {
            'status': 'success',
            'symbol': symbol.name,
            'interval': interval,
            'signals_generated': len(saved_signals),
            'signal_ids': saved_signals
        }
        
    except Symbol.DoesNotExist:
        logger.error(f"Symbol {symbol_id} not found")
        return {'status': 'error', 'message': 'Symbol not found'}
    except Exception as e:
        logger.error(f"Error generating signals for symbol {symbol_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def generate_all_signals(interval: str = '1h', limit: int = 50):
    """
    Generate signals for all tracked symbols.
    
    Args:
        interval: Time interval
        limit: Maximum number of symbols to process
    """
    from apps.market_data.models import Symbol
    
    symbols = Symbol.objects.filter(is_tracked=True).order_by('-priority')[:limit]
    
    logger.info(f"Generating signals for {len(symbols)} symbols ({interval})")
    
    results = []
    for symbol in symbols:
        result = generate_signals_task.delay(symbol.id, interval)
        results.append(result.id)
    
    return {
        'status': 'dispatched',
        'symbols_count': len(symbols),
        'interval': interval,
        'task_ids': results
    }


@shared_task
def cleanup_old_indicators(days: int = 90):
    """
    Delete old indicator cache records.
    
    Args:
        days: Keep indicators from last N days
    """
    from apps.analysis.models import IndicatorCache
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted_count, _ = IndicatorCache.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old indicator records")
    
    return {
        'status': 'success',
        'deleted_count': deleted_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task
def cleanup_old_signals(days: int = 30):
    """
    Delete old inactive signals.
    
    Args:
        days: Keep signals from last N days
    """
    from apps.analysis.services import SignalEngine
    
    engine = SignalEngine()
    deleted_count = engine.cleanup_old_signals(days=days)
    
    return {
        'status': 'success',
        'deleted_count': deleted_count
    }
