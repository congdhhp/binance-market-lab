import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { formatNumber, formatPrice, formatPercent, formatVolume, getColorForChange } from '../utils/formatters';
import type { Symbol, Ticker24h } from '../types';

const Dashboard = () => {
  const [stats, setStats] = useState<any>(null);

  // Fetch tracked symbols
  const { data: symbolsData, isLoading: symbolsLoading } = useQuery({
    queryKey: ['symbols', 'tracked'],
    queryFn: () => api.getSymbols({ is_tracked: true, limit: 20 }),
  });

  // Fetch latest tickers
  const { data: tickersData, isLoading: tickersLoading } = useQuery({
    queryKey: ['tickers'],
    queryFn: () => api.getTickers({ limit: 20 }),
    refetchInterval: 30000, // Refresh every 30s
  });

  // Fetch market stats
  const { data: statsData } = useQuery({
    queryKey: ['market-stats'],
    queryFn: () => api.getMarketStats(),
    refetchInterval: 60000,
  });

  useEffect(() => {
    if (statsData) {
      setStats(statsData);
    }
  }, [statsData]);

  if (symbolsLoading || tickersLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading market data...</p>
        </div>
      </div>
    );
  }

  const symbols = symbolsData?.results || [];
  const tickers = tickersData?.results || [];

  // Create ticker map for quick lookup
  const tickerMap = new Map(tickers.map(t => [t.symbol, t]));

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Market Dashboard</h1>
        <p className="text-gray-600 mt-2">Real-time cryptocurrency market overview</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Total Symbols</div>
          <div className="text-2xl font-bold text-gray-900">{symbolsData?.count || 0}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Tracked Symbols</div>
          <div className="text-2xl font-bold text-blue-600">{symbols.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">24h Volume</div>
          <div className="text-2xl font-bold text-gray-900">
            {stats?.total_volume ? formatVolume(stats.total_volume) : '-'}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-sm text-gray-600 mb-1">Avg Change 24h</div>
          <div className={`text-2xl font-bold ${stats?.avg_change ? getColorForChange(stats.avg_change) : ''}`}>
            {stats?.avg_change ? formatPercent(stats.avg_change) : '-'}
          </div>
        </div>
      </div>

      {/* Top Movers Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Top Movers</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Price
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  24h Change
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  24h Volume
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  High / Low
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {symbols.map((symbol: Symbol) => {
                const ticker = tickerMap.get(symbol.id);
                if (!ticker) return null;

                return (
                  <tr key={symbol.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{symbol.name}</div>
                          <div className="text-xs text-gray-500">
                            {symbol.base_asset}/{symbol.quote_asset}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {formatPrice(ticker.last_price)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className={`text-sm font-semibold ${getColorForChange(ticker.price_change_pct)}`}>
                        {formatPercent(ticker.price_change_pct)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="text-sm text-gray-900">
                        {formatVolume(ticker.volume)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="text-xs text-gray-600">
                        {formatPrice(ticker.high_price)} / {formatPrice(ticker.low_price)}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Phase Info */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-2">✅ Phase 1: Data Ingestion</h3>
          <ul className="text-sm text-green-700 space-y-1">
            <li>• Klines, Tickers, Orderbook</li>
            <li>• Real-time data ingestion</li>
            <li>• TimescaleDB optimization</li>
          </ul>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-2">✅ Phase 2: Technical Analysis</h3>
          <ul className="text-sm text-green-700 space-y-1">
            <li>• 39 Technical Indicators</li>
            <li>• Signal Generation</li>
            <li>• Indicator Caching</li>
          </ul>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-2">✅ Phase 3: Backtest Engine</h3>
          <ul className="text-sm text-green-700 space-y-1">
            <li>• Strategy Framework</li>
            <li>• Performance Metrics</li>
            <li>• Trade Simulation</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
