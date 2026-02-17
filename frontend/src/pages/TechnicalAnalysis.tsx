import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../services/api';
import { formatPrice, formatDateTime, intervals } from '../utils/formatters';
import type { Symbol, IndicatorCache, Signal } from '../types';

const TechnicalAnalysis = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<number | null>(null);
  const [selectedInterval, setSelectedInterval] = useState('1h');
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>(['rsi', 'macd']);

  // Fetch symbols
  const { data: symbolsData } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => api.getSymbols({ is_tracked: true, limit: 100 }),
  });

  // Fetch indicators
  const { data: indicatorsData, isLoading: indicatorsLoading } = useQuery({
    queryKey: ['indicators', selectedSymbol, selectedInterval],
    queryFn: () => api.getIndicators({
      symbol: selectedSymbol!,
      interval: selectedInterval,
      limit: 100,
    }),
    enabled: !!selectedSymbol,
  });

  // Fetch signals
  const { data: signalsData } = useQuery({
    queryKey: ['signals', selectedSymbol, selectedInterval],
    queryFn: () => api.getSignals({
      symbol: selectedSymbol!,
      interval: selectedInterval,
      limit: 20,
    }),
    enabled: !!selectedSymbol,
  });

  const symbols = symbolsData?.results || [];
  const indicators = indicatorsData?.results || [];
  const signals = signalsData?.results || [];

  // Prepare chart data
  const chartData = indicators.map((ind: IndicatorCache) => ({
    timestamp: new Date(ind.timestamp).getTime(),
    date: formatDateTime(ind.timestamp),
    rsi: ind.rsi,
    macd: ind.macd,
    macd_signal: ind.macd_signal,
    adx: ind.adx,
    bb_high: ind.bb_high,
    bb_mid: ind.bb_mid,
    bb_low: ind.bb_low,
    ema_21: ind.ema_21,
    sma_50: ind.sma_50,
  })).reverse();

  const availableIndicators = [
    { value: 'rsi', label: 'RSI', color: '#8884d8' },
    { value: 'macd', label: 'MACD', color: '#82ca9d' },
    { value: 'adx', label: 'ADX', color: '#ffc658' },
    { value: 'ema_21', label: 'EMA 21', color: '#ff7c7c' },
    { value: 'sma_50', label: 'SMA 50', color: '#a78bfa' },
  ];

  const toggleIndicator = (indicator: string) => {
    setSelectedIndicators(prev =>
      prev.includes(indicator)
        ? prev.filter(i => i !== indicator)
        : [...prev, indicator]
    );
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Technical Analysis</h1>
        <p className="text-gray-600 mt-2">View indicators and trading signals</p>
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
              <p className="text-gray-500 text-lg">← Select a symbol to view analysis</p>
            </div>
          ) : (
            <>
              {/* Controls */}
              <div className="bg-white rounded-lg shadow p-4 space-y-4">
                {/* Interval Selector */}
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

                {/* Indicator Selector */}
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">Indicators:</div>
                  <div className="flex flex-wrap gap-2">
                    {availableIndicators.map(({ value, label, color }) => (
                      <button
                        key={value}
                        onClick={() => toggleIndicator(value)}
                        className={`px-3 py-1 rounded text-sm font-medium transition ${
                          selectedIndicators.includes(value)
                            ? 'text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                        style={{
                          backgroundColor: selectedIndicators.includes(value) ? color : undefined,
                        }}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Chart */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Indicator Chart</h3>
                {indicatorsLoading ? (
                  <div className="h-[400px] flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  </div>
                ) : chartData.length === 0 ? (
                  <div className="h-[400px] flex items-center justify-center">
                    <p className="text-gray-500">No indicator data available</p>
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        interval="preserveStartEnd"
                      />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Legend />
                      {selectedIndicators.map(indicator => {
                        const config = availableIndicators.find(i => i.value === indicator);
                        return (
                          <Line
                            key={indicator}
                            type="monotone"
                            dataKey={indicator}
                            stroke={config?.color}
                            name={config?.label}
                            dot={false}
                            strokeWidth={2}
                          />
                        );
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>

              {/* Signals */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">Recent Signals</h3>
                </div>
                {signals.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    No signals generated yet
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {signals.map((signal: Signal) => (
                      <div key={signal.id} className="px-6 py-4 hover:bg-gray-50">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span
                              className={`px-3 py-1 rounded-full text-sm font-semibold ${
                                signal.signal_type === 'buy'
                                  ? 'bg-green-100 text-green-800'
                                  : signal.signal_type === 'sell'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {signal.signal_type.toUpperCase()}
                            </span>
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                Strength: {signal.strength}%
                              </div>
                              <div className="text-xs text-gray-500">
                                {formatDateTime(signal.timestamp)}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-900">
                              {formatPrice(signal.price)}
                            </div>
                            <div className="text-xs text-gray-500">
                              Rule #{signal.rule}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
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

export default TechnicalAnalysis;
