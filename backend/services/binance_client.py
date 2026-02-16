"""
Binance API client wrapper with rate limiting, retry logic, and error handling.
"""
import time
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from functools import wraps

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def rate_limit(calls_per_minute=1200):
    """
    Decorator to enforce rate limiting on API calls.
    Binance has a limit of 1200 requests per minute for most endpoints.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            cache_key = f"binance_rate_limit_{func.__name__}"
            
            # Get current count from cache
            current_count = cache.get(cache_key, 0)
            
            if current_count >= calls_per_minute:
                wait_time = 60 - (time.time() % 60)
                logger.warning(f"Rate limit reached for {func.__name__}. Waiting {wait_time:.2f}s")
                time.sleep(wait_time)
                cache.delete(cache_key)
                current_count = 0
            
            # Increment counter
            cache.set(cache_key, current_count + 1, timeout=60)
            
            return func(self, *args, **kwargs)
        
        return wrapper
    return decorator


def retry_on_error(max_retries=3, backoff_factor=2):
    """
    Decorator to retry API calls on transient errors with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (BinanceAPIException, BinanceRequestException) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    
                    # Don't retry on certain errors
                    if isinstance(e, BinanceAPIException):
                        if e.code in [-1021, -1022]:  # Timestamp errors
                            logger.error(f"Timestamp error in {func.__name__}: {e}")
                            raise
                        if e.status_code == 429:  # Rate limit exceeded
                            wait_time = backoff_factor ** (attempt + 1)
                            logger.warning(f"Rate limit hit in {func.__name__}. Retrying after {wait_time}s")
                            time.sleep(wait_time)
                            continue
                    
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying after {wait_time}s")
                    time.sleep(wait_time)
            
            raise Exception(f"{func.__name__} failed after all retries")
        
        return wrapper
    return decorator


class BinanceClientWrapper:
    """
    Wrapper around python-binance Client with additional functionality.
    Supports both Spot and Futures markets.
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, testnet: bool = False):
        """
        Initialize Binance client.
        
        Args:
            api_key: Binance API key (defaults to settings.BINANCE_API_KEY)
            api_secret: Binance API secret (defaults to settings.BINANCE_API_SECRET)
            testnet: Whether to use testnet (defaults to settings.BINANCE_TESTNET)
        """
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        self.testnet = testnet or settings.BINANCE_TESTNET
        
        # Initialize clients
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        
        logger.info(f"BinanceClientWrapper initialized (testnet={self.testnet})")
    
    @rate_limit(calls_per_minute=1200)
    @retry_on_error(max_retries=3)
    def get_exchange_info(self, market='spot') -> Dict[str, Any]:
        """
        Get exchange trading rules and symbol information.
        
        Args:
            market: 'spot' or 'futures'
            
        Returns:
            Exchange info dictionary
        """
        try:
            if market == 'futures':
                return self.client.futures_exchange_info()
            else:
                return self.client.get_exchange_info()
        except Exception as e:
            logger.error(f"Error fetching exchange info for {market}: {e}")
            raise
    
    @rate_limit(calls_per_minute=1200)
    @retry_on_error(max_retries=3)
    def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[List]:
        """
        Get kline/candlestick data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '1m', '1h', '1d')
            start_time: Start datetime (optional)
            end_time: End datetime (optional)
            limit: Number of klines to fetch (max 1000)
            
        Returns:
            List of klines, each kline is a list with format:
            [open_time, open, high, low, close, volume, close_time, quote_volume, 
             trades_count, taker_buy_volume, taker_buy_quote_volume, ignore]
        """
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': min(limit, 1000)  # Binance max is 1000
            }
            
            if start_time:
                params['startTime'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['endTime'] = int(end_time.timestamp() * 1000)
            
            klines = self.client.get_klines(**params)
            logger.debug(f"Fetched {len(klines)} klines for {symbol} {interval}")
            
            return klines
        
        except Exception as e:
            logger.error(f"Error fetching klines for {symbol} {interval}: {e}")
            raise
    
    def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[List]:
        """
        Get historical klines with automatic pagination for large date ranges.
        
        Args:
            symbol: Trading pair
            interval: Kline interval
            start_time: Start datetime
            end_time: End datetime (default: now)
            
        Returns:
            List of all klines in the range
        """
        end_time = end_time or datetime.utcnow()
        all_klines = []
        
        current_start = start_time
        batch_size = 1000
        
        logger.info(f"Fetching historical klines for {symbol} {interval} from {start_time} to {end_time}")
        
        while current_start < end_time:
            try:
                klines = self.get_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=end_time,
                    limit=batch_size
                )
                
                if not klines:
                    break
                
                all_klines.extend(klines)
                
                # Update current_start to the last kline's close time + 1ms
                last_close_time = klines[-1][6]  # close_time is at index 6
                current_start = datetime.fromtimestamp(last_close_time / 1000) + timedelta(milliseconds=1)
                
                logger.debug(f"Fetched batch of {len(klines)} klines, total: {len(all_klines)}")
                
                # If we got fewer than batch_size, we've reached the end
                if len(klines) < batch_size:
                    break
                
            except Exception as e:
                logger.error(f"Error in historical klines pagination: {e}")
                raise
        
        logger.info(f"Fetched total of {len(all_klines)} klines for {symbol} {interval}")
        return all_klines
    
    @rate_limit(calls_per_minute=1200)
    @retry_on_error(max_retries=3)
    def get_aggregate_trades(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get aggregated trade data.
        
        Args:
            symbol: Trading pair
            start_time: Start datetime (optional)
            end_time: End datetime (optional)
            limit: Number of trades to fetch (max 1000)
            
        Returns:
            List of aggregated trades
        """
        try:
            params = {
                'symbol': symbol,
                'limit': min(limit, 1000)
            }
            
            if start_time:
                params['startTime'] = int(start_time.timestamp() * 1000)
            if end_time:
                params['endTime'] = int(end_time.timestamp() * 1000)
            
            trades = self.client.get_aggregate_trades(**params)
            logger.debug(f"Fetched {len(trades)} aggregate trades for {symbol}")
            
            return trades
        
        except Exception as e:
            logger.error(f"Error fetching aggregate trades for {symbol}: {e}")
            raise
    
    @rate_limit(calls_per_minute=1200)
    @retry_on_error(max_retries=3)
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get order book depth.
        
        Args:
            symbol: Trading pair
            limit: Depth limit (5, 10, 20, 50, 100, 500, 1000, 5000)
            
        Returns:
            Order book with bids and asks
        """
        try:
            orderbook = self.client.get_order_book(symbol=symbol, limit=limit)
            logger.debug(f"Fetched order book for {symbol} with {len(orderbook['bids'])} bids and {len(orderbook['asks'])} asks")
            
            return orderbook
        
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            raise
    
    @rate_limit(calls_per_minute=1200)
    @retry_on_error(max_retries=3)
    def get_ticker_24h(self, symbol: Optional[str] = None) -> Any:
        """
        Get 24-hour ticker price change statistics.
        
        Args:
            symbol: Trading pair (if None, returns all symbols)
            
        Returns:
            Ticker data (dict for single symbol, list for all symbols)
        """
        try:
            if symbol:
                ticker = self.client.get_ticker(symbol=symbol)
                logger.debug(f"Fetched 24h ticker for {symbol}")
            else:
                ticker = self.client.get_ticker()
                logger.debug(f"Fetched 24h ticker for all symbols ({len(ticker)} symbols)")
            
            return ticker
        
        except Exception as e:
            logger.error(f"Error fetching 24h ticker: {e}")
            raise
    
    @rate_limit(calls_per_minute=1200)
    @retry_on_error(max_retries=3)
    def get_funding_rate(self, symbol: Optional[str] = None, limit: int = 100) -> Any:
        """
        Get funding rate history for futures contracts.
        
        Args:
            symbol: Futures symbol (if None, returns all symbols)
            limit: Number of records (max 1000)
            
        Returns:
            Funding rate data
        """
        try:
            params = {'limit': min(limit, 1000)}
            if symbol:
                params['symbol'] = symbol
            
            funding_rates = self.client.futures_funding_rate(**params)
            logger.debug(f"Fetched funding rates: {len(funding_rates) if isinstance(funding_rates, list) else 1} records")
            
            return funding_rates
        
        except Exception as e:
            logger.error(f"Error fetching funding rates: {e}")
            raise
    
    @rate_limit(calls_per_minute=1200)
    @retry_on_error(max_retries=3)
    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        Get current open interest for a futures symbol.
        
        Args:
            symbol: Futures symbol
            
        Returns:
            Open interest data
        """
        try:
            oi_data = self.client.futures_open_interest(symbol=symbol)
            logger.debug(f"Fetched open interest for {symbol}")
            
            return oi_data
        
        except Exception as e:
            logger.error(f"Error fetching open interest for {symbol}: {e}")
            raise
    
    @rate_limit(calls_per_minute=1200)
    @retry_on_error(max_retries=3)
    def get_avg_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current average price for a symbol.
        
        Args:
            symbol: Trading pair
            
        Returns:
            Average price data
        """
        try:
            avg_price = self.client.get_avg_price(symbol=symbol)
            logger.debug(f"Fetched average price for {symbol}")
            
            return avg_price
        
        except Exception as e:
            logger.error(f"Error fetching average price for {symbol}: {e}")
            raise


# Singleton instance
_binance_client = None


def get_binance_client() -> BinanceClientWrapper:
    """
    Get singleton instance of BinanceClientWrapper.
    """
    global _binance_client
    
    if _binance_client is None:
        _binance_client = BinanceClientWrapper()
    
    return _binance_client
