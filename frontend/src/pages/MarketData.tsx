import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import api from '../services/api';
import { formatPrice, formatPercent, formatVolume, formatDateTime, getColorForChange, intervals } from '../utils/formatters';
import type { Symbol, Kline } from '../types';

const MarketData = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<number | null>(null);
  const [selectedInterval, setSelectedInterval] = useState('1h');


  // Fetch symbols
  const { data: symbolsData } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => api.getSymbols({ is_tracked: true, limit: 100 }),
  });

  // Fetch klines for selected symbol
  const { data: klinesData, isLoading: klinesLoading } = useQuery({
    queryKey: ['klines', selectedSymbol, selectedInterval],
    queryFn: () => api.getKlines({
      symbol: selectedSymbol!,
      interval: selectedInterval,
      limit: 100,
    }),
    enabled: !!selectedSymbol,
  });

  // Fetch ticker for selected symbol
  const { data: ticker } = useQuery({
    queryKey: ['ticker', selectedSymbol],
    queryFn: () => api.getLatestTicker(selectedSymbol!),
    enabled: !!selectedSymbol,
    refetchInterval: 30000,
  });

  const symbols = symbolsData?.results || [];
  const klines = klinesData?.results || [];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Market Data Explorer</h1>
        <p className="text-gray-600 mt-2">Browse symbols and view historical price data</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Symbol List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-4 py-3 border-b border-gray-200">
            <h2 className="font-semibold text-gray-900">Symbols</h2>
          </div>
          <div className="overflow-y-auto max-h-[600px]">
            {symbols.map((symbol: Symbol) => (
              <div
                key={symbol.id}
                onClick={() => setSelectedSymbol(symbol.id)}
                className={`px-4 py-3 cursor-pointer border-b border-gray-100 hover:bg-blue-50 transition ${
                  selectedSymbol === symbol.id ? 'bg-blue-100' : ''
                }`}
              >
                <div className="font-medium text-gray-900">{symbol.name}</div>
                <div className="text-xs text-gray-500">
                  {symbol.base_asset}/{symbol.quote_asset}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          {!selectedSymbol ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <p className="text-gray-500 text-lg">← Select a symbol to view data</p>
            </div>
          ) : (
            <>
              {/* Ticker Info */}
              {ticker && (
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-2xl font-bold text-gray-900">
                      {symbols.find((s: Symbol) => s.id === selectedSymbol)?.name}
                    </h2>
                    <div className="text-right">
                      <div className="text-3xl font-bold text-gray-900">
                        {formatPrice(ticker.last_price)}
                      </div>
                      <div className={`text-lg font-semibold ${getColorForChange(ticker.price_change_pct)}`}>
                        {formatPercent(ticker.price_change_pct)} (24h)
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">24h High</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {formatPrice(ticker.high_price)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">24h Low</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {formatPrice(ticker.low_price)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">24h Volume</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {formatVolume(ticker.volume)}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Trades</div>
                      <div className="text-lg font-semibold text-gray-900">
                        {ticker.trades_count.toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Interval Selector */}
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-700">Interval:</span>
                  {intervals.map(({ label, value }) => (
                    <button
                      key={value}
                      onClick={() => setSelectedInterval(value)}
                      className={`px-3 py-1 rounded text-sm font-medium transition ${
                        selectedInterval === value
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Klines Table */}
              <div className="bg-white rounded-lg shadow overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Price History</h3>
                </div>
                {klinesLoading ? (
                  <div className="p-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
                  </div>
                ) : (
                  <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            Time
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Open
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            High
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Low
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Close
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                            Volume
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {klines.map((kline: Kline) => (
                          <tr key={kline.id} className="hover:bg-gray-50">
                            <td className="px-6 py-3 whitespace-nowrap text-sm text-gray-900">
                              {formatDateTime(kline.open_time)}
                            </td>
                            <td className="px-6 py-3 whitespace-nowrap text-sm text-right text-gray-900">
                              {formatPrice(kline.open)}
                            </td>
                            <td className="px-6 py-3 whitespace-nowrap text-sm text-right text-green-600 font-medium">
                              {formatPrice(kline.high)}
                            </td>
                            <td className="px-6 py-3 whitespace-nowrap text-sm text-right text-red-600 font-medium">
                              {formatPrice(kline.low)}
                            </td>
                            <td className="px-6 py-3 whitespace-nowrap text-sm text-right text-gray-900 font-medium">
                              {formatPrice(kline.close)}
                            </td>
                            <td className="px-6 py-3 whitespace-nowrap text-sm text-right text-gray-600">
                              {formatVolume(kline.volume)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default MarketData;
