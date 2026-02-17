import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import api from '../services/api';
import { formatPrice, formatPercent, formatNumber, formatDateTime, getColorForChange, intervals } from '../utils/formatters';
import type { Symbol, Strategy, BacktestRun, Trade } from '../types';

const Backtest = () => {
  const [view, setView] = useState<'list' | 'create' | 'results'>('list');
  const [selectedBacktest, setSelectedBacktest] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    strategy_id: '',
    symbol_id: '',
    interval: '1h',
    start_date: '',
    end_date: '',
  });

  // Fetch strategies
  const { data: strategiesData } = useQuery({
    queryKey: ['strategies'],
    queryFn: () => api.getStrategies({ limit: 100 }),
  });

  // Fetch symbols
  const { data: symbolsData } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => api.getSymbols({ is_tracked: true, limit: 100 }),
  });

  // Fetch backtest runs
  const { data: backtestsData, refetch: refetchBacktests } = useQuery({
    queryKey: ['backtests'],
    queryFn: () => api.getBacktestRuns({ limit: 50 }),
  });

  // Fetch selected backtest details
  const { data: backtestDetails } = useQuery({
    queryKey: ['backtest', selectedBacktest],
    queryFn: () => api.getBacktestRun(selectedBacktest!),
    enabled: !!selectedBacktest,
  });

  // Fetch trades for selected backtest
  const { data: tradesData } = useQuery({
    queryKey: ['trades', selectedBacktest],
    queryFn: () => api.getBacktestTrades(selectedBacktest!, { limit: 100 }),
    enabled: !!selectedBacktest,
  });

  // Run backtest mutation
  const runBacktestMutation = useMutation({
    mutationFn: api.runBacktest,
    onSuccess: () => {
      setTimeout(() => {
        refetchBacktests();
      }, 2000);
      setView('list');
      alert('Backtest started! Check the list for results.');
    },
  });

  const strategies = strategiesData?.results || [];
  const symbols = symbolsData?.results || [];
  const backtests = backtestsData?.results || [];
  const trades = tradesData?.results || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    runBacktestMutation.mutate({
      strategy_id: parseInt(formData.strategy_id),
      symbol_id: parseInt(formData.symbol_id),
      interval: formData.interval,
      start_date: formData.start_date,
      end_date: formData.end_date,
    });
  };

  const viewResults = (backtestId: number) => {
    setSelectedBacktest(backtestId);
    setView('results');
  };

  // Prepare equity curve data
  const equityCurveData = backtestDetails?.equity_curve?.map(point => ({
    date: formatDateTime(point.timestamp),
    value: point.value,
  })) || [];

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Backtest Lab</h1>
          <p className="text-gray-600 mt-2">Test trading strategies with historical data</p>
        </div>
        <div className="space-x-2">
          <button
            onClick={() => setView('list')}
            className={`px-4 py-2 rounded font-medium transition ${
              view === 'list'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Backtest List
          </button>
          <button
            onClick={() => setView('create')}
            className={`px-4 py-2 rounded font-medium transition ${
              view === 'create'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            New Backtest
          </button>
        </div>
      </div>

      {/* Backtest List View */}
      {view === 'list' && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Backtest Runs</h2>
          </div>
          {backtests.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500 text-lg">No backtests yet</p>
              <button
                onClick={() => setView('create')}
                className="mt-4 px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Create Your First Backtest
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Strategy
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Period
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Return
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Trades
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      Win Rate
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {backtests.map((backtest: BacktestRun) => (
                    <tr key={backtest.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {backtest.strategy_data?.name || `Strategy #${backtest.strategy}`}
                        </div>
                        <div className="text-xs text-gray-500">
                          {backtest.interval}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {backtest.symbol_name || `Symbol #${backtest.symbol}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-600">
                        {backtest.start_date} to {backtest.end_date}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-semibold ${
                            backtest.status === 'completed'
                              ? 'bg-green-100 text-green-800'
                              : backtest.status === 'failed'
                              ? 'bg-red-100 text-red-800'
                              : backtest.status === 'running'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {backtest.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {backtest.total_return ? (
                          <span className={`text-sm font-semibold ${getColorForChange(backtest.total_return)}`}>
                            {formatPercent(backtest.total_return)}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                        {backtest.total_trades}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {backtest.win_rate ? (
                          <span className="text-sm text-gray-900">
                            {formatNumber(backtest.win_rate, 1)}%
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <button
                          onClick={() => viewResults(backtest.id)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Create Backtest View */}
      {view === 'create' && (
        <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Backtest</h2>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Strategy
              </label>
              <select
                value={formData.strategy_id}
                onChange={(e) => setFormData({ ...formData, strategy_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select a strategy</option>
                {strategies.map((strategy: Strategy) => (
                  <option key={strategy.id} value={strategy.id}>
                    {strategy.name} ({strategy.strategy_type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Symbol
              </label>
              <select
                value={formData.symbol_id}
                onChange={(e) => setFormData({ ...formData, symbol_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select a symbol</option>
                {symbols.map((symbol: Symbol) => (
                  <option key={symbol.id} value={symbol.id}>
                    {symbol.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Interval
              </label>
              <select
                value={formData.interval}
                onChange={(e) => setFormData({ ...formData, interval: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {intervals.map(({ label, value }) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date
                </label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  End Date
                </label>
                <input
                  type="date"
                  value={formData.end_date}
                  onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            </div>

            <div className="flex space-x-3">
              <button
                type="submit"
                disabled={runBacktestMutation.isPending}
                className="flex-1 px-6 py-3 bg-blue-500 text-white rounded font-medium hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {runBacktestMutation.isPending ? 'Running...' : 'Run Backtest'}
              </button>
              <button
                type="button"
                onClick={() => setView('list')}
                className="px-6 py-3 bg-gray-200 text-gray-700 rounded font-medium hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Results View */}
      {view === 'results' && backtestDetails && (
        <div className="space-y-6">
          {/* Header */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {backtestDetails.strategy_data?.name}
                </h2>
                <p className="text-gray-600">
                  {backtestDetails.symbol_name} • {backtestDetails.interval} • {backtestDetails.start_date} to {backtestDetails.end_date}
                </p>
              </div>
              <button
                onClick={() => setView('list')}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                ← Back to List
              </button>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600">Total Return</div>
                <div className={`text-2xl font-bold ${backtestDetails.total_return ? getColorForChange(backtestDetails.total_return) : ''}`}>
                  {backtestDetails.total_return ? formatPercent(backtestDetails.total_return) : '-'}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600">Win Rate</div>
                <div className="text-2xl font-bold text-gray-900">
                  {backtestDetails.win_rate ? formatNumber(backtestDetails.win_rate, 1) + '%' : '-'}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600">Total Trades</div>
                <div className="text-2xl font-bold text-gray-900">{backtestDetails.total_trades}</div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600">Sharpe Ratio</div>
                <div className="text-2xl font-bold text-gray-900">
                  {backtestDetails.sharpe_ratio ? formatNumber(backtestDetails.sharpe_ratio, 2) : '-'}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600">Profit Factor</div>
                <div className="text-2xl font-bold text-gray-900">
                  {backtestDetails.profit_factor ? formatNumber(backtestDetails.profit_factor, 2) : '-'}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600">Max Drawdown</div>
                <div className="text-2xl font-bold text-red-600">
                  {backtestDetails.max_drawdown ? formatPercent(backtestDetails.max_drawdown) : '-'}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600">Avg Win</div>
                <div className="text-2xl font-bold text-green-600">
                  {backtestDetails.avg_win ? formatPrice(backtestDetails.avg_win) : '-'}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded">
                <div className="text-sm text-gray-600">Avg Loss</div>
                <div className="text-2xl font-bold text-red-600">
                  {backtestDetails.avg_loss ? formatPrice(backtestDetails.avg_loss) : '-'}
                </div>
              </div>
            </div>
          </div>

          {/* Equity Curve */}
          {equityCurveData.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity Curve</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={equityCurveData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#3b82f6"
                    name="Portfolio Value"
                    dot={false}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Trade Log */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Trade Log</h3>
            </div>
            {trades.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No trades executed</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Side
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Entry
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Exit
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        P&L
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        Return %
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {trades.map((trade: Trade) => (
                      <tr key={trade.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              trade.side === 'buy'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}
                          >
                            {trade.side.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {formatPrice(trade.entry_price)}
                          </div>
                          <div className="text-xs text-gray-500">
                            {formatDateTime(trade.entry_time)}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {trade.exit_price ? (
                            <>
                              <div className="text-sm text-gray-900">
                                {formatPrice(trade.exit_price)}
                              </div>
                              <div className="text-xs text-gray-500">
                                {trade.exit_time && formatDateTime(trade.exit_time)}
                              </div>
                            </>
                          ) : (
                            <span className="text-sm text-gray-400">Open</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                          {formatNumber(trade.quantity, 6)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          {trade.pnl ? (
                            <span className={`text-sm font-semibold ${getColorForChange(trade.pnl)}`}>
                              {formatPrice(trade.pnl)}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          {trade.pnl_pct ? (
                            <span className={`text-sm font-semibold ${getColorForChange(trade.pnl_pct)}`}>
                              {formatPercent(trade.pnl_pct)}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-400">-</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Backtest;
