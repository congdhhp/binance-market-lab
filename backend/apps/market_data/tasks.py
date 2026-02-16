"""
Celery tasks for market data ingestion.
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import Symbol, Kline, Trade, OrderBookSnapshot, Ticker24h, FundingRate, OpenInterest, IngestionLog
from services.binance_client import get_binance_client

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def ingest_klines_task(self, symbol: str, interval: str, start_time: str = None, end_time: str = None):
    """
    Ingest kline/candlestick data for a symbol.
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        interval: Kline interval (e.g., '1m', '1h', '1d')
        start_time: Start datetime ISO format (optional)
        end_time: End datetime ISO format (optional)
    """
    log_entry = None
    
    try:
        # Get or create symbol
        symbol_obj, created = Symbol.objects.get_or_create(
            name=symbol,
            defaults={'is_tracked': True}
        )
        
        # Create ingestion log
        log_entry = IngestionLog.objects.create(
            symbol=symbol_obj,
            data_type='kline',
            status='running',
            metadata={'interval': interval}
        )
        
        # Parse datetimes if provided
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        # Fetch klines from Binance
        client = get_binance_client()
        
        if start_dt:
            klines = client.get_historical_klines(symbol, interval, start_dt, end_dt)
        else:
            # Get last 100 klines if no start time specified
            klines = client.get_klines(symbol, interval, limit=100)
        
        # Process and save klines
        created_count = 0
        updated_count = 0
        
        for kline_data in klines:
            open_time = datetime.fromtimestamp(kline_data[0] / 1000, tz=timezone.utc)
            close_time = datetime.fromtimestamp(kline_data[6] / 1000, tz=timezone.utc)
            
            kline_obj, created = Kline.objects.update_or_create(
                symbol=symbol_obj,
                interval=interval,
                open_time=open_time,
                defaults={
                    'close_time': close_time,
                    'open': Decimal(str(kline_data[1])),
                    'high': Decimal(str(kline_data[2])),
                    'low': Decimal(str(kline_data[3])),
                    'close': Decimal(str(kline_data[4])),
                    'volume': Decimal(str(kline_data[5])),
                    'quote_volume': Decimal(str(kline_data[7])),
                    'trades_count': int(kline_data[8]),
                    'taker_buy_volume': Decimal(str(kline_data[9])),
                    'taker_buy_quote_volume': Decimal(str(kline_data[10])),
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        # Update log as success
        log_entry.status = 'success'
        log_entry.records_count = len(klines)
        log_entry.metadata.update({
            'created': created_count,
            'updated': updated_count
        })
        log_entry.save()
        
        logger.info(f"Successfully ingested {len(klines)} klines for {symbol} {interval} (created: {created_count}, updated: {updated_count})")
        
        return {
            'symbol': symbol,
            'interval': interval,
            'total': len(klines),
            'created': created_count,
            'updated': updated_count
        }
    
    except Exception as e:
        logger.error(f"Error ingesting klines for {symbol} {interval}: {e}")
        
        if log_entry:
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.save()
        
        # Retry task
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def ingest_all_symbols_klines(interval: str = '1h', limit: int = 50):
    """
    Ingest klines for all tracked symbols.
    
    Args:
        interval: Kline interval
        limit: Number of top priority symbols to process
    """
    symbols = Symbol.objects.filter(is_tracked=True).order_by('-priority', 'name')[:limit]
    
    logger.info(f"Starting klines ingestion for {symbols.count()} symbols with interval {interval}")
    
    for symbol in symbols:
        # Trigger task for each symbol (last 2 periods to fill gaps)
        ingest_klines_task.delay(symbol.name, interval)
    
    return f"Triggered klines ingestion for {symbols.count()} symbols"


@shared_task(bind=True, max_retries=3)
def ingest_trades_task(self, symbol: str, start_time: str = None, end_time: str = None, limit: int = 1000):
    """
    Ingest aggregated trade data for a symbol.
    """
    log_entry = None
    
    try:
        symbol_obj = Symbol.objects.get(name=symbol)
        
        log_entry = IngestionLog.objects.create(
            symbol=symbol_obj,
            data_type='trade',
            status='running'
        )
        
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None
        
        client = get_binance_client()
        trades = client.get_aggregate_trades(symbol, start_dt, end_dt, limit)
        
        created_count = 0
        
        for trade_data in trades:
            trade_time = datetime.fromtimestamp(trade_data['T'] / 1000, tz=timezone.utc)
            
            trade_obj, created = Trade.objects.get_or_create(
                symbol=symbol_obj,
                trade_id=trade_data['a'],
                defaults={
                    'price': Decimal(str(trade_data['p'])),
                    'quantity': Decimal(str(trade_data['q'])),
                    'timestamp': trade_time,
                    'is_buyer_maker': trade_data['m'],
                }
            )
            
            if created:
                created_count += 1
        
        log_entry.status = 'success'
        log_entry.records_count = len(trades)
        log_entry.save()
        
        logger.info(f"Successfully ingested {len(trades)} trades for {symbol} (new: {created_count})")
        
        return {'symbol': symbol, 'total': len(trades), 'created': created_count}
    
    except Exception as e:
        logger.error(f"Error ingesting trades for {symbol}: {e}")
        
        if log_entry:
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.save()
        
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def ingest_orderbook_snapshot(self, symbol: str, depth: int = 100):
    """
    Ingest order book snapshot for a symbol.
    """
    try:
        symbol_obj = Symbol.objects.get(name=symbol)
        
        client = get_binance_client()
        orderbook = client.get_order_book(symbol, limit=depth)
        
        # Calculate mid price and spread
        best_bid = Decimal(str(orderbook['bids'][0][0])) if orderbook['bids'] else Decimal('0')
        best_ask = Decimal(str(orderbook['asks'][0][0])) if orderbook['asks'] else Decimal('0')
        
        mid_price = (best_bid + best_ask) / 2 if best_bid and best_ask else None
        spread = best_ask - best_bid if best_bid and best_ask else None
        spread_bps = (spread / mid_price * 10000) if mid_price and spread else None
        
        # Create snapshot
        OrderBookSnapshot.objects.create(
            symbol=symbol_obj,
            timestamp=timezone.now(),
            bids=orderbook['bids'][:depth],
            asks=orderbook['asks'][:depth],
            mid_price=mid_price,
            spread=spread,
            spread_bps=spread_bps
        )
        
        logger.debug(f"Ingested orderbook snapshot for {symbol}")
        
        return {'symbol': symbol, 'mid_price': float(mid_price) if mid_price else None}
    
    except Symbol.DoesNotExist:
        logger.warning(f"Symbol {symbol} not found in database")
        return {'error': f'Symbol {symbol} not found'}
    
    except Exception as e:
        logger.error(f"Error ingesting orderbook for {symbol}: {e}")
        raise self.retry(exc=e, countdown=30)


@shared_task
def ingest_orderbook_snapshots(limit: int = 10):
    """
    Ingest orderbook snapshots for top priority symbols.
    """
    symbols = Symbol.objects.filter(is_tracked=True).order_by('-priority')[:limit]
    
    for symbol in symbols:
        ingest_orderbook_snapshot.delay(symbol.name)
    
    return f"Triggered orderbook ingestion for {symbols.count()} symbols"


@shared_task(bind=True, max_retries=3)
def ingest_ticker_24h(self):
    """
    Ingest 24-hour ticker data for all symbols.
    """
    log_entry = None
    
    try:
        log_entry = IngestionLog.objects.create(
            data_type='ticker',
            status='running'
        )
        
        client = get_binance_client()
        tickers = client.get_ticker_24h()  # Get all symbols
        
        created_count = 0
        timestamp = timezone.now()
        
        for ticker_data in tickers:
            symbol_name = ticker_data['symbol']
            
            # Get or create symbol
            symbol_obj, _ = Symbol.objects.get_or_create(
                name=symbol_name,
                defaults={'is_tracked': False}  # Don't auto-track all symbols
            )
            
            # Create ticker snapshot
            Ticker24h.objects.create(
                symbol=symbol_obj,
                timestamp=timestamp,
                last_price=Decimal(str(ticker_data['lastPrice'])),
                open_price=Decimal(str(ticker_data['openPrice'])),
                high_price=Decimal(str(ticker_data['highPrice'])),
                low_price=Decimal(str(ticker_data['lowPrice'])),
                price_change=Decimal(str(ticker_data['priceChange'])),
                price_change_percent=Decimal(str(ticker_data['priceChangePercent'])),
                volume=Decimal(str(ticker_data['volume'])),
                quote_volume=Decimal(str(ticker_data['quoteVolume'])),
                weighted_avg_price=Decimal(str(ticker_data['weightedAvgPrice'])),
                bid_price=Decimal(str(ticker_data['bidPrice'])) if 'bidPrice' in ticker_data else None,
                ask_price=Decimal(str(ticker_data['askPrice'])) if 'askPrice' in ticker_data else None,
                trades_count=int(ticker_data['count']),
            )
            created_count += 1
        
        log_entry.status = 'success'
        log_entry.records_count = created_count
        log_entry.save()
        
        logger.info(f"Successfully ingested 24h tickers for {created_count} symbols")
        
        return {'total': created_count}
    
    except Exception as e:
        logger.error(f"Error ingesting 24h tickers: {e}")
        
        if log_entry:
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.save()
        
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def ingest_funding_rates(self):
    """
    Ingest funding rates for all futures symbols.
    """
    log_entry = None
    
    try:
        log_entry = IngestionLog.objects.create(
            data_type='funding_rate',
            status='running'
        )
        
        client = get_binance_client()
        funding_data_list = client.get_funding_rate()  # Get all futures symbols
        
        created_count = 0
        timestamp = timezone.now()
        
        for funding_data in funding_data_list:
            symbol_name = funding_data['symbol']
            
            # Get or create symbol (mark as futures)
            symbol_obj, _ = Symbol.objects.get_or_create(
                name=symbol_name,
                defaults={'is_tracked': False, 'is_spot': False, 'is_futures': True}
            )
            
            funding_time = datetime.fromtimestamp(funding_data['fundingTime'] / 1000, tz=timezone.utc)
            
            # Create funding rate record
            FundingRate.objects.update_or_create(
                symbol=symbol_obj,
                funding_time=funding_time,
                defaults={
                    'timestamp': timestamp,
                    'funding_rate': Decimal(str(funding_data['fundingRate'])),
                    'mark_price': Decimal(str(funding_data.get('markPrice', 0))) if 'markPrice' in funding_data else None,
                }
            )
            created_count += 1
        
        log_entry.status = 'success'
        log_entry.records_count = created_count
        log_entry.save()
        
        logger.info(f"Successfully ingested funding rates for {created_count} symbols")
        
        return {'total': created_count}
    
    except Exception as e:
        logger.error(f"Error ingesting funding rates: {e}")
        
        if log_entry:
            log_entry.status = 'failed'
            log_entry.error_message = str(e)
            log_entry.save()
        
        raise self.retry(exc=e, countdown=120)


@shared_task
def ingest_open_interest():
    """
    Ingest open interest for tracked futures symbols.
    """
    symbols = Symbol.objects.filter(is_tracked=True, is_futures=True)
    
    client = get_binance_client()
    timestamp = timezone.now()
    created_count = 0
    
    for symbol in symbols:
        try:
            oi_data = client.get_open_interest(symbol.name)
            
            OpenInterest.objects.create(
                symbol=symbol,
                timestamp=timestamp,
                open_interest=Decimal(str(oi_data['openInterest'])),
                open_interest_value=Decimal(str(oi_data.get('sumOpenInterestValue', 0))) if 'sumOpenInterestValue' in oi_data else None,
            )
            created_count += 1
        
        except Exception as e:
            logger.warning(f"Error fetching open interest for {symbol.name}: {e}")
            continue
    
    logger.info(f"Successfully ingested open interest for {created_count} symbols")
    
    return {'total': created_count}


@shared_task
def bulk_backfill_task(symbol: str, interval: str, start_date: str, end_date: str = None):
    """
    Bulk backfill historical klines for a symbol.
    
    This task chains multiple ingest_klines_task calls to handle large date ranges.
    """
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
    
    logger.info(f"Starting bulk backfill for {symbol} {interval} from {start_dt} to {end_dt}")
    
    # Call the single ingestion task (which handles pagination internally)
    result = ingest_klines_task.delay(symbol, interval, start_date, end_date)
    
    return {
        'symbol': symbol,
        'interval': interval,
        'start_date': start_date,
        'end_date': end_date,
        'task_id': result.id
    }


@shared_task
def data_quality_check():
    """
    Check data quality and detect gaps in klines.
    """
    logger.info("Running data quality check...")
    
    issues = []
    
    # Check for gaps in klines for tracked symbols
    tracked_symbols = Symbol.objects.filter(is_tracked=True)[:20]  # Check top 20
    
    for symbol in tracked_symbols:
        for interval in ['1h', '4h', '1d']:
            # Get the latest 100 klines
            klines = Kline.objects.filter(
                symbol=symbol,
                interval=interval
            ).order_by('-open_time')[:100]
            
            if klines.count() < 2:
                continue
            
            # Check for gaps
            klines_list = list(klines)
            for i in range(len(klines_list) - 1):
                current = klines_list[i]
                next_kline = klines_list[i + 1]
                
                # Calculate expected time difference based on interval
                interval_map = {
                    '1m': timedelta(minutes=1),
                    '5m': timedelta(minutes=5),
                    '15m': timedelta(minutes=15),
                    '30m': timedelta(minutes=30),
                    '1h': timedelta(hours=1),
                    '4h': timedelta(hours=4),
                    '1d': timedelta(days=1),
                }
                
                expected_diff = interval_map.get(interval)
                if not expected_diff:
                    continue
                
                actual_diff = current.open_time - next_kline.open_time
                
                # If gap is larger than expected, trigger backfill
                if actual_diff > expected_diff * 1.5:
                    logger.warning(f"Gap detected in {symbol.name} {interval} between {next_kline.open_time} and {current.open_time}")
                    
                    issues.append({
                        'symbol': symbol.name,
                        'interval': interval,
                        'gap_start': next_kline.open_time,
                        'gap_end': current.open_time
                    })
                    
                    # Trigger backfill for this gap
                    ingest_klines_task.delay(
                        symbol.name,
                        interval,
                        next_kline.open_time.isoformat(),
                        current.open_time.isoformat()
                    )
    
    logger.info(f"Data quality check complete. Found {len(issues)} gaps.")
    
    return {
        'issues_found': len(issues),
        'issues': issues[:10]  # Return first 10 issues
    }
