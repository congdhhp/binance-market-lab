/**
 * Type definitions for Binance Market Lab Frontend
 */

// ============= Market Data Types (Phase 1) =============

export interface Symbol {
  id: number;
  name: string;
  base_asset: string;
  quote_asset: string;
  status: string;
  is_spot: boolean;
  is_futures: boolean;
  is_tracked: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface Kline {
  id: number;
  symbol: number;
  symbol_name?: string;
  interval: string;
  open_time: string;
  close_time: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
  quote_volume: string;
  trades_count: number;
  taker_buy_volume: string;
  taker_buy_quote_volume: string;
}

export interface Ticker24h {
  id: number;
  symbol: number;
  symbol_name?: string;
  price_change: string;
  price_change_pct: string;
  weighted_avg_price: string;
  prev_close: string;
  last_price: string;
  bid_price: string;
  ask_price: string;
  open_price: string;
  high_price: string;
  low_price: string;
  volume: string;
  quote_volume: string;
  open_time: string;
  close_time: string;
  trades_count: number;
  timestamp: string;
}

export interface OrderbookSnapshot {
  id: number;
  symbol: number;
  symbol_name?: string;
  timestamp: string;
  bids: Array<[string, string]>;
  asks: Array<[string, string]>;
  last_update_id: number;
}

// ============= Technical Analysis Types (Phase 2) =============

export interface IndicatorCache {
  id: number;
  symbol: number;
  symbol_name?: string;
  interval: string;
  timestamp: string;
  // Moving Averages
  ema_9?: number;
  ema_21?: number;
  ema_50?: number;
  ema_100?: number;
  ema_200?: number;
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  hull_ma?: number;
  // Momentum
  rsi?: number;
  macd?: number;
  macd_signal?: number;
  macd_diff?: number;
  stoch_k?: number;
  stoch_d?: number;
  williams_r?: number;
  // Trend
  adx?: number;
  adx_pos?: number;
  adx_neg?: number;
  supertrend?: number;
  supertrend_direction?: number;
  // Volatility
  bb_high?: number;
  bb_mid?: number;
  bb_low?: number;
  bb_width?: number;
  atr?: number;
  // Volume
  obv?: number;
  vwap?: number;
}

export interface SignalRule {
  id: number;
  name: string;
  description: string;
  signal_type: 'buy' | 'sell' | 'neutral';
  strength: number;
  intervals: string[];
  symbols: number[];
  symbols_data?: Symbol[];
  conditions: Record<string, any>;
  is_active: boolean;
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface Signal {
  id: number;
  rule: number;
  rule_data?: SignalRule;
  symbol: number;
  symbol_name?: string;
  interval: string;
  timestamp: string;
  signal_type: 'buy' | 'sell' | 'neutral';
  strength: number;
  price: string;
  metadata: Record<string, any>;
  created_at: string;
}

// ============= Backtest Types (Phase 3) =============

export interface Strategy {
  id: number;
  name: string;
  description: string;
  strategy_type: 'signal_based' | 'indicator' | 'ml_model' | 'custom';
  signal_rules: number[];
  signal_rules_data?: SignalRule[];
  parameters: Record<string, any>;
  initial_capital: string;
  position_size: string;
  stop_loss_pct: string;
  take_profit_pct: string;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface BacktestRun {
  id: number;
  strategy: number;
  strategy_data?: Strategy;
  symbol: number;
  symbol_name?: string;
  interval: string;
  start_date: string;
  end_date: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  initial_capital: string;
  final_capital: string;
  total_return: string | null;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: string | null;
  profit_factor: string | null;
  sharpe_ratio: string | null;
  max_drawdown: string | null;
  avg_win: string | null;
  avg_loss: string | null;
  equity_curve: Array<{ timestamp: string; value: number }>;
  error_message: string;
  created_at: string;
  started_at: string;
  completed_at: string;
}

export interface Trade {
  id: number;
  backtest_run: number;
  side: 'buy' | 'sell';
  entry_time: string;
  entry_price: string;
  exit_time: string | null;
  exit_price: string | null;
  quantity: string;
  pnl: string | null;
  pnl_pct: string | null;
  fees: string;
  is_open: boolean;
  metadata: Record<string, any>;
}

export interface BacktestMetrics {
  id: number;
  backtest_run: number;
  annual_return: string;
  volatility: string;
  sharpe_ratio: string;
  sortino_ratio: string;
  calmar_ratio: string;
  max_consecutive_wins: number;
  max_consecutive_losses: number;
  avg_trade_duration: string;
  profit_factor: string;
  recovery_factor: string;
}

// ============= Orderbook Analytics Types (Phase 4) =============

export interface OrderbookAnalysis {
  id: number;
  symbol: number;
  symbol_name?: string;
  timestamp: string;
  bid_ask_spread: string;
  spread_bps: string;
  bid_depth_10: string;
  ask_depth_10: string;
  total_depth_10: string;
  bid_depth_100: string;
  ask_depth_100: string;
  total_depth_100: string;
  orderbook_imbalance: string;
  vwap_bid: string;
  vwap_ask: string;
  vwap_mid: string;
  liquidity_score: string;
  created_at: string;
}

export interface ImbalanceAlert {
  id: number;
  symbol: number;
  symbol_name?: string;
  timestamp: string;
  alert_type: 'bid_heavy' | 'ask_heavy' | 'balanced' | 'critical';
  imbalance_ratio: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  is_resolved: boolean;
  resolved_at: string | null;
  created_at: string;
}

export interface RiskMetrics {
  symbol_id: number;
  symbol_name?: string;
  start_date: string;
  end_date: string;
  var_95: number | null;
  var_99: number | null;
  cvar_95: number | null;
  cvar_99: number | null;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  calmar_ratio: number | null;
  max_drawdown: number | null;
  max_drawdown_duration_days: number | null;
  volatility: number | null;
  downside_deviation: number | null;
  beta: number | null;
  alpha: number | null;
}

export interface CorrelationMatrix {
  start_date: string;
  end_date: string;
  correlation_matrix: { [key: string]: { [key: string]: number } };
  symbol_names: string[];
  pca_variance_explained?: number[];
  pca_components?: number[][];
}

export interface RegimeDetection {
  symbol_id: number;
  symbol_name?: string;
  lookback_days: number;
  current_regime: number;
  regime_name: string;
  regime_probability: number;
  transition_matrix: number[][];
  regime_characteristics: { [key: string]: any };
  timestamp: string;
}

// ============= API Response Types =============

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  [key: string]: any;
}

// ============= UI State Types =============

export interface ChartConfig {
  symbol: string;
  interval: string;
  indicators: string[];
  showVolume: boolean;
}

export interface AppState {
  selectedSymbol: Symbol | null;
  selectedInterval: string;
  theme: 'light' | 'dark';
}
