import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Symbol, OrderbookAnalysis, ImbalanceAlert } from '../types';

// Components
import OrderbookDepth from '../components/orderbook/OrderbookDepth';
import RiskMetrics from '../components/orderbook/RiskMetrics';
import CorrelationMatrix from '../components/orderbook/CorrelationMatrix';
import RegimeDetection from '../components/orderbook/RegimeDetection';
import ImbalanceAlerts from '../components/orderbook/ImbalanceAlerts';

export default function OrderbookAnalytics() {
  const [selectedSymbol, setSelectedSymbol] = useState<Symbol | null>(null);
  const [activeTab, setActiveTab] = useState<'depth' | 'risk' | 'correlation' | 'regime' | 'alerts'>('depth');
  const [timeRange, setTimeRange] = useState('24h');

  // Fetch symbols
  const { data: symbolsData } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => api.getSymbols({ is_tracked: true, limit: 100 }),
  });

  // Fetch orderbook analyses for selected symbol
  const { data: analysesData, isLoading: isLoadingAnalyses } = useQuery({
    queryKey: ['orderbook-analyses', selectedSymbol?.id, timeRange],
    queryFn: () => {
      if (!selectedSymbol) return null;
      const endTime = new Date();
      const startTime = new Date();
      
      switch (timeRange) {
        case '1h':
          startTime.setHours(startTime.getHours() - 1);
          break;
        case '24h':
          startTime.setHours(startTime.getHours() - 24);
          break;
        case '7d':
          startTime.setDate(startTime.getDate() - 7);
          break;
        case '30d':
          startTime.setDate(startTime.getDate() - 30);
          break;
      }

      return api.getOrderbookAnalyses({
        symbol: selectedSymbol.id,
        start_time: startTime.toISOString(),
        end_time: endTime.toISOString(),
        limit: 1000,
      });
    },
    enabled: !!selectedSymbol,
  });

  // Fetch imbalance alerts
  const { data: alertsData } = useQuery({
    queryKey: ['imbalance-alerts', selectedSymbol?.id],
    queryFn: () => {
      if (!selectedSymbol) return null;
      return api.getImbalanceAlerts({
        symbol: selectedSymbol.id,
        is_resolved: false,
        limit: 50,
      });
    },
    enabled: !!selectedSymbol,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const handleAnalyzeNow = async () => {
    if (!selectedSymbol) return;
    try {
      await api.analyzeOrderbook(selectedSymbol.id);
      // Trigger refetch of analyses
      window.location.reload();
    } catch (error) {
      console.error('Failed to analyze orderbook:', error);
    }
  };

  const symbols = symbolsData?.results || [];
  const analyses = analysesData?.results || [];
  const alerts = alertsData?.results || [];
  const latestAnalysis = analyses.length > 0 ? analyses[0] : null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Orderbook Analytics
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Deep liquidity analysis and market microstructure insights
              </p>
            </div>
            {selectedSymbol && (
              <button
                onClick={handleAnalyzeNow}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Analyze Now
              </button>
            )}
          </div>

          {/* Symbol Selection */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Symbol
              </label>
              <select
                value={selectedSymbol?.id || ''}
                onChange={(e) => {
                  const symbol = symbols.find((s) => s.id === Number(e.target.value));
                  setSelectedSymbol(symbol || null);
                }}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Choose a symbol...</option>
                {symbols.map((symbol) => (
                  <option key={symbol.id} value={symbol.id}>
                    {symbol.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Time Range
              </label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
              >
                <option value="1h">Last Hour</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
              </select>
            </div>

            {/* Quick Stats */}
            {latestAnalysis && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Latest Metrics
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Spread (bps)</div>
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {parseFloat(latestAnalysis.spread_bps).toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-gray-500 dark:text-gray-400">Liquidity Score</div>
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {parseFloat(latestAnalysis.liquidity_score).toFixed(2)}/100
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Alerts Banner */}
        {alerts.length > 0 && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-400 p-4 rounded-r-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700 dark:text-yellow-300">
                  <span className="font-medium">{alerts.length} Active Alert{alerts.length > 1 ? 's' : ''}</span>
                  {' - Orderbook imbalances detected'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        {selectedSymbol && (
          <>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="flex -mb-px">
                  <button
                    onClick={() => setActiveTab('depth')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'depth'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                    }`}
                  >
                    Orderbook Depth
                  </button>
                  <button
                    onClick={() => setActiveTab('risk')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'risk'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                    }`}
                  >
                    Risk Metrics
                  </button>
                  <button
                    onClick={() => setActiveTab('correlation')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'correlation'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                    }`}
                  >
                    Correlation Matrix
                  </button>
                  <button
                    onClick={() => setActiveTab('regime')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === 'regime'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                    }`}
                  >
                    Market Regime
                  </button>
                  <button
                    onClick={() => setActiveTab('alerts')}
                    className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors relative ${
                      activeTab === 'alerts'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300'
                    }`}
                  >
                    Alerts
                    {alerts.length > 0 && (
                      <span className="ml-2 px-2 py-1 text-xs bg-red-500 text-white rounded-full">
                        {alerts.length}
                      </span>
                    )}
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {activeTab === 'depth' && (
                  <OrderbookDepth
                    symbol={selectedSymbol}
                    analyses={analyses}
                    isLoading={isLoadingAnalyses}
                  />
                )}
                {activeTab === 'risk' && (
                  <RiskMetrics symbol={selectedSymbol} timeRange={timeRange} />
                )}
                {activeTab === 'correlation' && (
                  <CorrelationMatrix symbols={symbols} timeRange={timeRange} />
                )}
                {activeTab === 'regime' && (
                  <RegimeDetection symbol={selectedSymbol} />
                )}
                {activeTab === 'alerts' && (
                  <ImbalanceAlerts symbol={selectedSymbol} alerts={alerts} />
                )}
              </div>
            </div>
          </>
        )}

        {/* Empty State */}
        {!selectedSymbol && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-12 text-center">
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
              No symbol selected
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Select a symbol from the dropdown above to view orderbook analytics
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
