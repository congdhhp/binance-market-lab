"""
Backtesting engine services.
"""
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
import pandas as pd
import numpy as np
import logging

from apps.backtest.models import Strategy, BacktestRun, Trade, Portfolio, BacktestMetrics
from apps.market_data.models import Symbol, Kline
from apps.analysis.models import IndicatorCache, Signal
from apps.analysis.services import SignalEngine

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Core backtesting engine for strategy evaluation.
    """
    
    def __init__(self, backtest_run: BacktestRun):
        self.backtest_run = backtest_run
        self.strategy = backtest_run.strategy
        self.symbol = backtest_run.symbol
        self.interval = backtest_run.interval
        
        # Portfolio state
        self.cash = float(self.strategy.initial_capital)
        self.positions = {}  # {symbol: {'quantity': float, 'avg_price': float}}
        self.equity_curve = []
        self.portfolio_snapshots = []
        
        # Trading state
        self.current_trade = None
        self.trades = []
        
        # Fees
        self.maker_fee = Decimal('0.001')  # 0.1%
        self.taker_fee = Decimal('0.001')  # 0.1%
    
    def run(self) -> Dict:
        """
        Execute the backtest.
        
        Returns:
            Dict with backtest results
        """
        logger.info(f"Starting backtest: {self.backtest_run.name}")
        
        try:
            # Update status
            self.backtest_run.status = 'running'
            self.backtest_run.started_at = timezone.now()
            self.backtest_run.save()
            
            # Load historical data
            klines = self._load_klines()
            if len(klines) == 0:
                raise ValueError("No kline data available for backtest period")
            
            logger.info(f"Loaded {len(klines)} klines for backtest")
            
            # Load indicators
            indicators = self._load_indicators()
            logger.info(f"Loaded {len(indicators)} indicator records")
            
            # Iterate through time
            for idx, kline in klines.iterrows():
                timestamp = kline['open_time']
                close_price = float(kline['close'])
                
                # Get indicators for this timestamp
                indicator_data = indicators.get(timestamp, {})
                
                # Check for signals
                signal = self._generate_signal(timestamp, close_price, indicator_data)
                
                # Execute trades
                if signal:
                    self._execute_signal(signal, timestamp, close_price)
                
                # Check stop loss / take profit
                if self.current_trade:
                    self._check_exit_conditions(timestamp, kline)
                
                # Record portfolio state
                self._record_portfolio_state(timestamp, close_price)
            
            # Close any open positions at end
            if self.current_trade:
                last_kline = klines.iloc[-1]
                self._close_trade(
                    last_kline['open_time'],
                    float(last_kline['close']),
                    'end_of_backtest'
                )
            
            # Calculate final metrics
            self._calculate_metrics()
            
            # Save results
            self._save_results()
            
            # Update status
            self.backtest_run.status = 'completed'
            self.backtest_run.completed_at = timezone.now()
            self.backtest_run.final_capital = Decimal(str(self.cash))
            self.backtest_run.save()
            
            logger.info(f"Backtest completed: {self.backtest_run.name}")
            
            return {
                'status': 'success',
                'total_trades': len(self.trades),
                'final_capital': self.cash,
                'total_return': self.backtest_run.total_return
            }
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}", exc_info=True)
            self.backtest_run.status = 'failed'
            self.backtest_run.error_message = str(e)
            self.backtest_run.completed_at = timezone.now()
            self.backtest_run.save()
            raise
    
    def _load_klines(self) -> pd.DataFrame:
        """Load kline data for backtest period."""
        klines = Kline.objects.filter(
            symbol=self.symbol,
            interval=self.interval,
            open_time__gte=self.backtest_run.start_date,
            open_time__lte=self.backtest_run.end_date
        ).order_by('open_time').values('open_time', 'open', 'high', 'low', 'close', 'volume')
        
        df = pd.DataFrame(list(klines))
        
        # Convert Decimal to float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].astype(float)
        
        return df
    
    def _load_indicators(self) -> Dict:
        """Load pre-computed indicators."""
        indicators = IndicatorCache.objects.filter(
            symbol=self.symbol,
            interval=self.interval,
            timestamp__gte=self.backtest_run.start_date,
            timestamp__lte=self.backtest_run.end_date
        ).order_by('timestamp')
        
        # Create dict keyed by timestamp
        indicator_dict = {}
        for ind in indicators:
            data = {}
            # Get all indicator fields
            for field in ind._meta.fields:
                field_name = field.name
                if field_name not in ['id', 'symbol', 'interval', 'timestamp', 'created_at']:
                    value = getattr(ind, field_name)
                    if value is not None:
                        data[field_name] = float(value)
            
            indicator_dict[ind.timestamp] = data
        
        return indicator_dict
    
    def _generate_signal(self, timestamp: datetime, price: float, indicators: Dict) -> Optional[str]:
        """
        Generate trading signal based on strategy.
        
        Returns:
            'buy', 'sell', or None
        """
        if self.strategy.strategy_type == 'signal_based':
            # Use signal rules
            for rule in self.strategy.signal_rules.filter(is_active=True):
                if rule.evaluate(indicators):
                    return rule.signal_type
        
        elif self.strategy.strategy_type == 'indicator':
            # Custom indicator logic
            params = self.strategy.parameters
            
            # RSI strategy (support both naming conventions)
            if ('rsi_oversold' in params and 'rsi_overbought' in params) or \
               ('buy_threshold' in params and 'sell_threshold' in params):
                rsi = indicators.get('rsi')
                if rsi:
                    oversold = params.get('rsi_oversold', params.get('buy_threshold'))
                    overbought = params.get('rsi_overbought', params.get('sell_threshold'))
                    
                    if rsi < oversold:
                        return 'buy'
                    elif rsi > overbought:
                        return 'sell'
        
        return None
    
    def _execute_signal(self, signal: str, timestamp: datetime, price: float):
        """Execute a trading signal."""
        # Only allow one position at a time (simple strategy)
        if self.current_trade:
            # Already in position - check if signal is opposite
            if (self.current_trade.side == 'buy' and signal == 'sell') or \
               (self.current_trade.side == 'sell' and signal == 'buy'):
                # Close current position
                self._close_trade(timestamp, price, 'signal')
            else:
                return  # Same direction, do nothing
        
        # Open new position
        if signal in ['buy', 'sell']:
            self._open_trade(signal, timestamp, price)
    
    def _open_trade(self, side: str, timestamp: datetime, price: float):
        """Open a new trade."""
        # Calculate position size
        position_size_quote = self.cash * float(self.strategy.position_size)
        
        if position_size_quote < 10:  # Minimum position size
            logger.warning(f"Position size too small: ${position_size_quote}")
            return
        
        # Calculate quantity
        quantity = position_size_quote / price
        
        # Calculate fees
        fee = Decimal(str(position_size_quote)) * self.taker_fee
        
        # Deduct from cash
        self.cash -= (position_size_quote + float(fee))
        
        if self.cash < 0:
            logger.warning("Insufficient cash for trade")
            self.cash += (position_size_quote + float(fee))  # Revert
            return
        
        # Create trade
        trade = Trade(
            backtest_run=self.backtest_run,
            side=side,
            entry_time=timestamp,
            entry_price=Decimal(str(price)),
            entry_signal=f"{side}_signal",
            quantity=Decimal(str(quantity)),
            position_size_quote=Decimal(str(position_size_quote)),
            entry_fee=fee,
            is_open=True
        )
        
        self.current_trade = trade
        self.trades.append(trade)
        
        logger.info(f"Opened {side} trade: {quantity:.8f} @ ${price:.2f}")
    
    def _close_trade(self, timestamp: datetime, price: float, reason: str):
        """Close the current trade."""
        if not self.current_trade:
            return
        
        trade = self.current_trade
        
        # Calculate exit value
        exit_value = float(trade.quantity) * price
        
        # Calculate fees
        exit_fee = Decimal(str(exit_value)) * self.taker_fee
        
        # Add to cash (minus fees)
        self.cash += (exit_value - float(exit_fee))
        
        # Close trade and calculate P&L
        trade.close_trade(
            exit_time=timestamp,
            exit_price=Decimal(str(price)),
            exit_reason=reason
        )
        trade.exit_fee = exit_fee
        
        # Recalculate P&L with fees
        if trade.side == 'buy':
            trade.pnl = (trade.exit_price - trade.entry_price) * trade.quantity - trade.entry_fee - trade.exit_fee
        else:
            trade.pnl = (trade.entry_price - trade.exit_price) * trade.quantity - trade.entry_fee - trade.exit_fee
        
        if trade.position_size_quote > 0:
            trade.pnl_pct = (trade.pnl / trade.position_size_quote) * 100
        
        self.current_trade = None
        
        logger.info(f"Closed trade: P&L ${trade.pnl:.2f} ({trade.pnl_pct:.2f}%)")
    
    def _check_exit_conditions(self, timestamp: datetime, kline: pd.Series):
        """Check stop loss and take profit conditions."""
        if not self.current_trade:
            return
        
        trade = self.current_trade
        high = float(kline['high'])
        low = float(kline['low'])
        close = float(kline['close'])
        entry_price = float(trade.entry_price)
        
        # Calculate current P&L percentage
        if trade.side == 'buy':
            current_pnl_pct = ((close - entry_price) / entry_price) * 100
            
            # Stop loss
            if self.strategy.stop_loss_pct and low <= entry_price * (1 - float(self.strategy.stop_loss_pct) / 100):
                exit_price = entry_price * (1 - float(self.strategy.stop_loss_pct) / 100)
                self._close_trade(timestamp, exit_price, 'stop_loss')
                return
            
            # Take profit
            if self.strategy.take_profit_pct and high >= entry_price * (1 + float(self.strategy.take_profit_pct) / 100):
                exit_price = entry_price * (1 + float(self.strategy.take_profit_pct) / 100)
                self._close_trade(timestamp, exit_price, 'take_profit')
                return
        
        else:  # sell/short
            current_pnl_pct = ((entry_price - close) / entry_price) * 100
            
            # Stop loss
            if self.strategy.stop_loss_pct and high >= entry_price * (1 + float(self.strategy.stop_loss_pct) / 100):
                exit_price = entry_price * (1 + float(self.strategy.stop_loss_pct) / 100)
                self._close_trade(timestamp, exit_price, 'stop_loss')
                return
            
            # Take profit
            if self.strategy.take_profit_pct and low <= entry_price * (1 - float(self.strategy.take_profit_pct) / 100):
                exit_price = entry_price * (1 - float(self.strategy.take_profit_pct) / 100)
                self._close_trade(timestamp, exit_price, 'take_profit')
                return
    
    def _record_portfolio_state(self, timestamp: datetime, price: float):
        """Record current portfolio state."""
        # Calculate position value
        position_value = 0.0
        if self.current_trade:
            position_value = float(self.current_trade.quantity) * price
        
        total_value = self.cash + position_value
        
        # Add to equity curve
        self.equity_curve.append({
            'timestamp': timestamp.isoformat(),
            'value': round(total_value, 2)
        })
        
        # Create portfolio snapshot every N periods (e.g., daily)
        if len(self.equity_curve) % 24 == 0:  # Assuming 1h interval, snapshot daily
            snapshot = {
                'timestamp': timestamp,
                'cash': round(self.cash, 2),
                'position_value': round(position_value, 2),
                'total_value': round(total_value, 2)
            }
            self.portfolio_snapshots.append(snapshot)
    
    def _calculate_metrics(self):
        """Calculate backtest performance metrics."""
        if not self.trades:
            return
        
        # Convert trades to DataFrame for analysis
        trades_data = []
        for trade in self.trades:
            if not trade.is_open:
                trades_data.append({
                    'pnl': float(trade.pnl),
                    'pnl_pct': float(trade.pnl_pct),
                    'entry_time': trade.entry_time,
                    'exit_time': trade.exit_time
                })
        
        if not trades_data:
            return
        
        df_trades = pd.DataFrame(trades_data)
        
        # Calculate metrics
        winning_trades = df_trades[df_trades['pnl'] > 0]
        losing_trades = df_trades[df_trades['pnl'] < 0]
        
        total_trades = len(df_trades)
        wins = len(winning_trades)
        losses = len(losing_trades)
        
        # Store in backtest_run
        self.backtest_run.total_trades = total_trades
        self.backtest_run.winning_trades = wins
        self.backtest_run.losing_trades = losses
        
        if total_trades > 0:
            self.backtest_run.win_rate = Decimal(wins) / Decimal(total_trades) * 100
        
        if len(winning_trades) > 0:
            self.backtest_run.avg_win = Decimal(str(winning_trades['pnl'].mean()))
        
        if len(losing_trades) > 0:
            self.backtest_run.avg_loss = Decimal(str(abs(losing_trades['pnl'].mean())))
        
        # Profit factor
        if (self.backtest_run.avg_win and self.backtest_run.avg_loss and 
            self.backtest_run.avg_loss > 0):
            self.backtest_run.profit_factor = self.backtest_run.avg_win / self.backtest_run.avg_loss
        
        # Calculate max drawdown from equity curve
        equity_values = [point['value'] for point in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        self.backtest_run.max_drawdown = Decimal(str(max_dd))
        
        # Sharpe ratio (simplified)
        if len(df_trades) > 1:
            returns = df_trades['pnl_pct'].values
            if returns.std() > 0:
                sharpe = (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized
                self.backtest_run.sharpe_ratio = Decimal(str(sharpe))
    
    def _save_results(self):
        """Save backtest results to database."""
        with transaction.atomic():
            # Save trades
            for trade in self.trades:
                trade.save()
            
            # Save portfolio snapshots
            for snapshot in self.portfolio_snapshots:
                Portfolio.objects.create(
                    backtest_run=self.backtest_run,
                    timestamp=snapshot['timestamp'],
                    cash=Decimal(str(snapshot['cash'])),
                    position_value=Decimal(str(snapshot['position_value'])),
                    total_value=Decimal(str(snapshot['total_value']))
                )
            
            # Save equity curve
            self.backtest_run.equity_curve = self.equity_curve
            self.backtest_run.save()
