import { useState } from 'react';
import { api } from '../../services/api';
import type { Symbol, RiskMetrics as RiskMetricsType } from '../../types';

interface Props {
  symbol: Symbol;
  timeRange: string;
}

export default function RiskMetrics({ symbol, timeRange }: Props) {
  const [confidenceLevel, setConfidenceLevel] = useState(95);
  const [isCalculating, setIsCalculating] = useState(false);
  const [metrics, setMetrics] = useState<RiskMetricsType | null>(null);

  const calculateMetrics = async () => {
    setIsCalculating(true);
    try {
      const endDate = new Date();
      const startDate = new Date();
      
      switch (timeRange) {
        case '1h':
          startDate.setHours(startDate.getHours() - 1);
          break;
        case '24h':
          startDate.setHours(startDate.getHours() - 24);
          break;
        case '7d':
          startDate.setDate(startDate.getDate() - 7);
          break;
        case '30d':
          startDate.setDate(startDate.getDate() - 30);
          break;
      }

      const result = await api.getRiskMetrics({
        symbol_id: symbol.id,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        confidence_level: confidenceLevel / 100,
      });
      
      setMetrics(result);
    } catch (error) {
      console.error('Failed to calculate risk metrics:', error);
    } finally {
      setIsCalculating(false);
    }
  };

  const formatPercentage = (value: number | null | undefined) => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatNumber = (value: number | null | undefined, decimals = 2) => {
    if (value === null || value === undefined) return 'N/A';
    return value.toFixed(decimals);
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Confidence Level (%)
            </label>
            <input
              type="number"
              min="90"
              max="99"
              step="1"
              value={confidenceLevel}
              onChange={(e) => setConfidenceLevel(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={calculateMetrics}
              disabled={isCalculating}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              {isCalculating ? 'Calculating...' : 'Calculate Metrics'}
            </button>
          </div>
        </div>
      </div>

      {metrics ? (
        <>
          {/* Value at Risk (VaR) */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Value at Risk (VaR)
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">VaR 95%</div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
                  {formatPercentage(metrics.var_95)}
                </div>
              </div>
              <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">VaR 99%</div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
                  {formatPercentage(metrics.var_99)}
                </div>
              </div>
              <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">CVaR 95%</div>
                <div className="text-2xl font-bold text-red-700 dark:text-red-500 mt-1">
                  {formatPercentage(metrics.cvar_95)}
                </div>
              </div>
              <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">CVaR 99%</div>
                <div className="text-2xl font-bold text-red-700 dark:text-red-500 mt-1">
                  {formatPercentage(metrics.cvar_99)}
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
              There is a {confidenceLevel}% probability that losses will not exceed the VaR amount in a single day.
              CVaR represents the expected loss given that the VaR threshold is exceeded.
            </p>
          </div>

          {/* Risk-Adjusted Returns */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Risk-Adjusted Return Ratios
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Sharpe Ratio</div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                  {formatNumber(metrics.sharpe_ratio, 3)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {metrics.sharpe_ratio && metrics.sharpe_ratio > 1 ? 'Good' : 
                   metrics.sharpe_ratio && metrics.sharpe_ratio > 0 ? 'Fair' : 'Poor'}
                </div>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Sortino Ratio</div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                  {formatNumber(metrics.sortino_ratio, 3)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Downside risk only
                </div>
              </div>
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Calmar Ratio</div>
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                  {formatNumber(metrics.calmar_ratio, 3)}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Return/Max DD
                </div>
              </div>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
              Higher ratios indicate better risk-adjusted returns. Sharpe {'>'} 1 is considered good, {'>'} 2 is excellent.
            </p>
          </div>

          {/* Drawdown & Volatility */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Drawdown & Volatility Analysis
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Max Drawdown</div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">
                  {formatPercentage(metrics.max_drawdown)}
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">DD Duration</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {metrics.max_drawdown_duration_days || 'N/A'}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">days</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Volatility</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {formatPercentage(metrics.volatility)}
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Downside Dev</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                  {formatPercentage(metrics.downside_deviation)}
                </div>
              </div>
            </div>
          </div>

          {/* Market Correlation */}
          {(metrics.beta !== null || metrics.alpha !== null) && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Market Correlation
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Beta (β)</div>
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">
                    {formatNumber(metrics.beta, 3)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Market sensitivity
                  </div>
                </div>
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400">Alpha (α)</div>
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mt-1">
                    {formatPercentage(metrics.alpha)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Excess return
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Period Info */}
          <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
            Analysis period: {new Date(metrics.start_date).toLocaleDateString()} - {new Date(metrics.end_date).toLocaleDateString()}
          </div>
        </>
      ) : (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
            No metrics calculated yet
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Click "Calculate Metrics" to analyze risk for {symbol.name}
          </p>
        </div>
      )}
    </div>
  );
}
