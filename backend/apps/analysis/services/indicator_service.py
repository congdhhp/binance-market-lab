"""
Technical Indicator Service - Computes all technical indicators using pandas and ta library.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from ta.trend import EMAIndicator, SMAIndicator, MACD, ADXIndicator, IchimokuIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannel
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice
import logging

logger = logging.getLogger(__name__)


class IndicatorService:
    """
    Service for computing technical indicators on OHLCV data.
    Uses ta (Technical Analysis) library with pandas DataFrames.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV DataFrame.
        
        Args:
            df: DataFrame with columns: open, high, low, close, volume, open_time
        """
        self.df = df.copy()
        self._validate_df()
        
    def _validate_df(self):
        """Validate that DataFrame has required columns."""
        required = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            raise ValueError(f"DataFrame missing required columns: {missing}")
        
        # Ensure sorted by time
        if 'open_time' in self.df.columns:
            self.df = self.df.sort_values('open_time')
    
    # ==================== TREND INDICATORS ====================
    
    def add_ema(self, periods: List[int] = [9, 21, 50, 100, 200]) -> pd.DataFrame:
        """Add Exponential Moving Averages."""
        for period in periods:
            ema = EMAIndicator(close=self.df['close'], window=period)
            self.df[f'ema_{period}'] = ema.ema_indicator()
        return self.df
    
    def add_sma(self, periods: List[int] = [20, 50, 200]) -> pd.DataFrame:
        """Add Simple Moving Averages."""
        for period in periods:
            sma = SMAIndicator(close=self.df['close'], window=period)
            self.df[f'sma_{period}'] = sma.sma_indicator()
        return self.df
    
    def add_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """Add MACD (Moving Average Convergence Divergence)."""
        macd = MACD(
            close=self.df['close'],
            window_slow=slow,
            window_fast=fast,
            window_sign=signal
        )
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_diff'] = macd.macd_diff()
        return self.df
    
    def add_adx(self, window: int = 14) -> pd.DataFrame:
        """Add Average Directional Index (ADX) and DI+ DI-."""
        adx = ADXIndicator(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=window
        )
        self.df['adx'] = adx.adx()
        self.df['adx_pos'] = adx.adx_pos()
        self.df['adx_neg'] = adx.adx_neg()
        return self.df
    
    def add_ichimoku(self) -> pd.DataFrame:
        """Add Ichimoku Cloud indicators."""
        ichimoku = IchimokuIndicator(
            high=self.df['high'],
            low=self.df['low'],
            window1=9,
            window2=26,
            window3=52
        )
        self.df['ichimoku_a'] = ichimoku.ichimoku_a()
        self.df['ichimoku_b'] = ichimoku.ichimoku_b()
        self.df['ichimoku_base'] = ichimoku.ichimoku_base_line()
        self.df['ichimoku_conversion'] = ichimoku.ichimoku_conversion_line()
        return self.df
    
    # ==================== MOMENTUM INDICATORS ====================
    
    def add_rsi(self, window: int = 14) -> pd.DataFrame:
        """Add Relative Strength Index."""
        rsi = RSIIndicator(close=self.df['close'], window=window)
        self.df['rsi'] = rsi.rsi()
        return self.df
    
    def add_stochastic(self, window: int = 14, smooth_window: int = 3) -> pd.DataFrame:
        """Add Stochastic Oscillator."""
        stoch = StochasticOscillator(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=window,
            smooth_window=smooth_window
        )
        self.df['stoch_k'] = stoch.stoch()
        self.df['stoch_d'] = stoch.stoch_signal()
        return self.df
    
    def add_williams_r(self, lbp: int = 14) -> pd.DataFrame:
        """Add Williams %R."""
        williams = WilliamsRIndicator(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            lbp=lbp
        )
        self.df['williams_r'] = williams.williams_r()
        return self.df
    
    # ==================== VOLATILITY INDICATORS ====================
    
    def add_bollinger_bands(self, window: int = 20, window_dev: int = 2) -> pd.DataFrame:
        """Add Bollinger Bands."""
        bollinger = BollingerBands(
            close=self.df['close'],
            window=window,
            window_dev=window_dev
        )
        self.df['bb_high'] = bollinger.bollinger_hband()
        self.df['bb_mid'] = bollinger.bollinger_mavg()
        self.df['bb_low'] = bollinger.bollinger_lband()
        self.df['bb_width'] = bollinger.bollinger_wband()
        self.df['bb_pct'] = bollinger.bollinger_pband()
        return self.df
    
    def add_atr(self, window: int = 14) -> pd.DataFrame:
        """Add Average True Range."""
        atr = AverageTrueRange(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=window
        )
        self.df['atr'] = atr.average_true_range()
        return self.df
    
    def add_keltner_channel(self, window: int = 20, window_atr: int = 10) -> pd.DataFrame:
        """Add Keltner Channel."""
        keltner = KeltnerChannel(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            window=window,
            window_atr=window_atr
        )
        self.df['kc_high'] = keltner.keltner_channel_hband()
        self.df['kc_mid'] = keltner.keltner_channel_mband()
        self.df['kc_low'] = keltner.keltner_channel_lband()
        self.df['kc_width'] = keltner.keltner_channel_wband()
        return self.df
    
    # ==================== VOLUME INDICATORS ====================
    
    def add_vwap(self) -> pd.DataFrame:
        """Add Volume Weighted Average Price."""
        vwap = VolumeWeightedAveragePrice(
            high=self.df['high'],
            low=self.df['low'],
            close=self.df['close'],
            volume=self.df['volume']
        )
        self.df['vwap'] = vwap.volume_weighted_average_price()
        return self.df
    
    def add_obv(self) -> pd.DataFrame:
        """Add On Balance Volume."""
        obv = OnBalanceVolumeIndicator(
            close=self.df['close'],
            volume=self.df['volume']
        )
        self.df['obv'] = obv.on_balance_volume()
        return self.df
    
    def add_volume_profile(self, bins: int = 10) -> pd.DataFrame:
        """Add simplified Volume Profile (volume distribution by price level)."""
        price_min = self.df['low'].min()
        price_max = self.df['high'].max()
        price_bins = np.linspace(price_min, price_max, bins + 1)
        
        # Assign each candle to a price bin
        self.df['price_bin'] = pd.cut(self.df['close'], bins=price_bins, labels=False)
        
        # Volume profile: sum volume per price level
        volume_profile = self.df.groupby('price_bin')['volume'].sum()
        self.df['volume_profile'] = self.df['price_bin'].map(volume_profile)
        
        return self.df
    
    # ==================== CUSTOM INDICATORS ====================
    
    def add_squeeze_momentum(self, bb_window: int = 20, kc_window: int = 20) -> pd.DataFrame:
        """
        Add Squeeze Momentum Indicator (TTM Squeeze).
        Detects when Bollinger Bands are inside Keltner Channels.
        """
        # Calculate BB and KC
        self.add_bollinger_bands(window=bb_window)
        self.add_keltner_channel(window=kc_window)
        
        # Squeeze: BB inside KC
        self.df['squeeze_on'] = (
            (self.df['bb_low'] > self.df['kc_low']) & 
            (self.df['bb_high'] < self.df['kc_high'])
        ).astype(int)
        
        # Momentum calculation
        highest_high = self.df['high'].rolling(window=kc_window).max()
        lowest_low = self.df['low'].rolling(window=kc_window).min()
        avg_hl = (highest_high + lowest_low) / 2
        avg_close_hl = (avg_hl + self.df.rolling(window=kc_window).mean()['close']) / 2
        
        self.df['squeeze_momentum'] = self.df['close'] - avg_close_hl
        
        return self.df
    
    def add_hull_ma(self, window: int = 20) -> pd.DataFrame:
        """Add Hull Moving Average (faster MA with less lag)."""
        half_window = int(window / 2)
        sqrt_window = int(np.sqrt(window))
        
        wma_half = self.df['close'].rolling(window=half_window).mean()
        wma_full = self.df['close'].rolling(window=window).mean()
        
        raw_hma = 2 * wma_half - wma_full
        self.df['hull_ma'] = raw_hma.rolling(window=sqrt_window).mean()
        
        return self.df
    
    def add_supertrend(self, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """Add SuperTrend indicator."""
        self.add_atr(window=period)
        
        hl_avg = (self.df['high'] + self.df['low']) / 2
        upper_band = hl_avg + (multiplier * self.df['atr'])
        lower_band = hl_avg - (multiplier * self.df['atr'])
        
        supertrend = pd.Series(index=self.df.index, dtype=float)
        direction = pd.Series(index=self.df.index, dtype=int)
        
        for i in range(1, len(self.df)):
            if self.df['close'].iloc[i] > upper_band.iloc[i-1]:
                supertrend.iloc[i] = lower_band.iloc[i]
                direction.iloc[i] = 1
            elif self.df['close'].iloc[i] < lower_band.iloc[i-1]:
                supertrend.iloc[i] = upper_band.iloc[i]
                direction.iloc[i] = -1
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]
        
        self.df['supertrend'] = supertrend
        self.df['supertrend_direction'] = direction
        
        return self.df
    
    # ==================== ALL INDICATORS ====================
    
    def compute_all(self) -> pd.DataFrame:
        """Compute all major technical indicators."""
        logger.info("Computing all technical indicators...")
        
        try:
            # Trend
            self.add_ema()
            self.add_sma()
            self.add_macd()
            self.add_adx()
            
            # Momentum
            self.add_rsi()
            self.add_stochastic()
            self.add_williams_r()
            
            # Volatility
            self.add_bollinger_bands()
            self.add_atr()
            self.add_keltner_channel()
            
            # Volume
            self.add_vwap()
            self.add_obv()
            
            # Custom
            self.add_hull_ma()
            self.add_supertrend()
            
            logger.info(f"Computed {len(self.df.columns)} indicators")
            
        except Exception as e:
            logger.error(f"Error computing indicators: {e}")
            raise
        
        return self.df
    
    def get_latest_values(self) -> Dict[str, float]:
        """Get the latest value of all computed indicators."""
        if len(self.df) == 0:
            return {}
        
        latest = self.df.iloc[-1]
        return {
            col: float(latest[col]) if pd.notna(latest[col]) else None
            for col in self.df.columns
            if col not in ['open', 'high', 'low', 'close', 'volume', 'open_time', 'price_bin']
        }
    
    def get_signals(self) -> Dict[str, str]:
        """
        Generate basic trading signals based on indicators.
        Returns dict with signal type and strength.
        """
        if len(self.df) < 2:
            return {}
        
        signals = {}
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        # RSI signals
        if 'rsi' in self.df.columns:
            rsi = latest['rsi']
            if rsi < 30:
                signals['rsi'] = 'oversold'
            elif rsi > 70:
                signals['rsi'] = 'overbought'
            else:
                signals['rsi'] = 'neutral'
        
        # MACD crossover
        if 'macd' in self.df.columns and 'macd_signal' in self.df.columns:
            if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                signals['macd'] = 'bullish_crossover'
            elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                signals['macd'] = 'bearish_crossover'
            else:
                signals['macd'] = 'no_crossover'
        
        # Bollinger Bands
        if 'bb_pct' in self.df.columns:
            bb_pct = latest['bb_pct']
            if bb_pct < 0:
                signals['bollinger'] = 'below_lower_band'
            elif bb_pct > 1:
                signals['bollinger'] = 'above_upper_band'
            else:
                signals['bollinger'] = 'within_bands'
        
        # SuperTrend
        if 'supertrend_direction' in self.df.columns:
            direction = latest['supertrend_direction']
            if direction == 1:
                signals['supertrend'] = 'bullish'
            elif direction == -1:
                signals['supertrend'] = 'bearish'
        
        return signals
