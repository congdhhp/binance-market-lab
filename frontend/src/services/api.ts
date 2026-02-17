/**
 * API Service Layer
 * Centralized API calls to Django backend
 */

import axios, { AxiosInstance } from 'axios';
import type {
  Symbol,
  Kline,
  Ticker24h,
  OrderbookSnapshot,
  IndicatorCache,
  SignalRule,
  Signal,
  Strategy,
  BacktestRun,
  Trade,
  BacktestMetrics,
  PaginatedResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // ============= Market Data API (Phase 1) =============

  async getSymbols(params?: {
    is_tracked?: boolean;
    is_spot?: boolean;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<Symbol>> {
    const { data } = await this.client.get('/api/v1/market-data/symbols/', { params });
    return data;
  }

  async getSymbol(id: number): Promise<Symbol> {
    const { data } = await this.client.get(`/api/v1/market-data/symbols/${id}/`);
    return data;
  }

  async getKlines(params: {
    symbol?: number;
    symbol_name?: string;
    interval?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<Kline>> {
    const { data } = await this.client.get('/api/v1/market-data/klines/', { params });
    return data;
  }

  async getTickers(params?: {
    symbol?: number;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<Ticker24h>> {
    const { data } = await this.client.get('/api/v1/market-data/tickers/', { params });
    return data;
  }

  async getLatestTicker(symbolId: number): Promise<Ticker24h> {
    const { data } = await this.client.get(`/api/v1/market-data/symbols/${symbolId}/ticker/`);
    return data;
  }

  async getOrderbook(params: {
    symbol?: number;
    limit?: number;
  }): Promise<PaginatedResponse<OrderbookSnapshot>> {
    const { data } = await this.client.get('/api/v1/market-data/orderbook/', { params });
    return data;
  }

  async getMarketStats(): Promise<any> {
    const { data } = await this.client.get('/api/v1/market-data/stats/');
    return data;
  }

  // ============= Technical Analysis API (Phase 2) =============

  async getIndicators(params: {
    symbol?: number;
    interval?: string;
    start_time?: string;
    end_time?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<IndicatorCache>> {
    const { data } = await this.client.get('/api/v1/analysis/indicators/', { params });
    return data;
  }

  async getSignalRules(params?: {
    signal_type?: string;
    is_active?: boolean;
    limit?: number;
  }): Promise<PaginatedResponse<SignalRule>> {
    const { data } = await this.client.get('/api/v1/analysis/signal-rules/', { params });
    return data;
  }

  async createSignalRule(ruleData: Partial<SignalRule>): Promise<SignalRule> {
    const { data } = await this.client.post('/api/v1/analysis/signal-rules/', ruleData);
    return data;
  }

  async getSignals(params?: {
    symbol?: number;
    interval?: string;
    signal_type?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<PaginatedResponse<Signal>> {
    const { data } = await this.client.get('/api/v1/analysis/signals/', { params });
    return data;
  }

  async computeIndicators(symbolId: number, interval: string): Promise<any> {
    const { data } = await this.client.post('/api/v1/analysis/compute/', {
      symbol_id: symbolId,
      interval,
    });
    return data;
  }

  // ============= Backtest API (Phase 3) =============

  async getStrategies(params?: {
    strategy_type?: string;
    is_active?: boolean;
    limit?: number;
  }): Promise<PaginatedResponse<Strategy>> {
    const { data } = await this.client.get('/api/v1/backtest/strategies/', { params });
    return data;
  }

  async getStrategy(id: number): Promise<Strategy> {
    const { data } = await this.client.get(`/api/v1/backtest/strategies/${id}/`);
    return data;
  }

  async createStrategy(strategyData: Partial<Strategy>): Promise<Strategy> {
    const { data } = await this.client.post('/api/v1/backtest/strategies/', strategyData);
    return data;
  }

  async updateStrategy(id: number, strategyData: Partial<Strategy>): Promise<Strategy> {
    const { data } = await this.client.put(`/api/v1/backtest/strategies/${id}/`, strategyData);
    return data;
  }

  async deleteStrategy(id: number): Promise<void> {
    await this.client.delete(`/api/v1/backtest/strategies/${id}/`);
  }

  async getBacktestRuns(params?: {
    strategy?: number;
    symbol?: number;
    status?: string;
    limit?: number;
  }): Promise<PaginatedResponse<BacktestRun>> {
    const { data } = await this.client.get('/api/v1/backtest/runs/', { params });
    return data;
  }

  async getBacktestRun(id: number): Promise<BacktestRun> {
    const { data } = await this.client.get(`/api/v1/backtest/runs/${id}/`);
    return data;
  }

  async runBacktest(params: {
    strategy_id: number;
    symbol_id: number;
    interval: string;
    start_date: string;
    end_date: string;
  }): Promise<{
    status: string;
    task_id: string;
    backtest_run_id: number;
    backtest_run_name: string;
  }> {
    const { data } = await this.client.post('/api/v1/backtest/run/', params);
    return data;
  }

  async getBacktestTrades(backtestRunId: number, params?: {
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<Trade>> {
    const { data } = await this.client.get(`/api/v1/backtest/runs/${backtestRunId}/trades/`, { params });
    return data;
  }

  async getBacktestMetrics(backtestRunId: number): Promise<BacktestMetrics> {
    const { data } = await this.client.get(`/api/v1/backtest/runs/${backtestRunId}/metrics/`);
    return data;
  }

  async getEquityCurve(backtestRunId: number): Promise<Array<{ timestamp: string; value: number }>> {
    const { data } = await this.client.get(`/api/v1/backtest/runs/${backtestRunId}/equity_curve/`);
    return data;
  }

  async getBacktestStats(params?: {
    strategy_id?: number;
    symbol_id?: number;
    interval?: string;
  }): Promise<any> {
    const { data } = await this.client.get('/api/v1/backtest/stats/', { params });
    return data;
  }

  // ============= Health Check =============

  async healthCheck(): Promise<any> {
    const { data } = await this.client.get('/api/health/');
    return data;
  }
}

export const api = new ApiService();
export default api;
