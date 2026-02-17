import { useState } from 'react';
import { api } from '../../services/api';
import type { Symbol, CorrelationMatrix as CorrelationMatrixType } from '../../types';

interface Props {
  symbols: Symbol[];
  timeRange: string;
}

export default function CorrelationMatrix({ symbols, timeRange }: Props) {
  const [selectedSymbols, setSelectedSymbols] = useState<number[]>([]);
  const [method, setMethod] = useState<'pearson' | 'spearman' | 'kendall'>('pearson');
  const [includePCA, setIncludePCA] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [matrix, setMatrix] = useState<CorrelationMatrixType | null>(null);

  const calculateCorrelation = async () => {
    if (selectedSymbols.length < 2) {
      alert('Please select at least 2 symbols');
      return;
    }

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

      const result = await api.getCorrelationMatrix({
        symbol_ids: selectedSymbols,
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0],
        method,
        include_pca: includePCA,
      });
      
      setMatrix(result);
    } catch (error) {
      console.error('Failed to calculate correlation:', error);
    } finally {
      setIsCalculating(false);
    }
  };

  const toggleSymbol = (symbolId: number) => {
    setSelectedSymbols((prev) =>
      prev.includes(symbolId)
        ? prev.filter((id) => id !== symbolId)
        : [...prev, symbolId]
    );
  };

  const getCorrelationColor = (value: number) => {
    if (value >= 0.7) return 'bg-green-500';
    if (value >= 0.3) return 'bg-green-300';
    if (value >= -0.3) return 'bg-gray-300';
    if (value >= -0.7) return 'bg-red-300';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select Symbols (min 2)
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 max-h-40 overflow-y-auto">
              {symbols.map((symbol) => (
                <label
                  key={symbol.id}
                  className="flex items-center gap-2 p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedSymbols.includes(symbol.id)}
                    onChange={() => toggleSymbol(symbol.id)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-900 dark:text-white">{symbol.name}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Correlation Method
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value as any)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              >
                <option value="pearson">Pearson</option>
                <option value="spearman">Spearman</option>
                <option value="kendall">Kendall</option>
              </select>
            </div>

            <div className="flex items-center">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includePCA}
                  onChange={(e) => setIncludePCA(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">Include PCA Analysis</span>
              </label>
            </div>

            <div className="flex items-end">
              <button
                onClick={calculateCorrelation}
                disabled={isCalculating || selectedSymbols.length < 2}
                className="w-full px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
              >
                {isCalculating ? 'Calculating...' : 'Calculate Correlation'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {matrix ? (
        <>
          {/* Correlation Matrix */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Correlation Matrix ({method.charAt(0).toUpperCase() + method.slice(1)})
            </h3>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="p-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300"></th>
                    {matrix.symbol_names.map((name) => (
                      <th key={name} className="p-2 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrix.symbol_names.map((rowName) => (
                    <tr key={rowName}>
                      <td className="p-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                        {rowName}
                      </td>
                      {matrix.symbol_names.map((colName) => {
                        const value = matrix.correlation_matrix[rowName]?.[colName] || 0;
                        return (
                          <td key={colName} className="p-2">
                            <div
                              className={`${getCorrelationColor(value)} rounded text-center py-2 text-sm font-semibold text-white`}
                              title={`${rowName} vs ${colName}: ${value.toFixed(3)}`}
                            >
                              {value.toFixed(2)}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Legend */}
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-500 rounded"></div>
                  <span className="text-gray-600 dark:text-gray-400">Strong Positive (≥0.7)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-300 rounded"></div>
                  <span className="text-gray-600 dark:text-gray-400">Weak (-0.3 to 0.3)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                  <span className="text-gray-600 dark:text-gray-400">Strong Negative (≤-0.7)</span>
                </div>
              </div>
            </div>
          </div>

          {/* PCA Results */}
          {includePCA && matrix.pca_variance_explained && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Principal Component Analysis (PCA)
              </h3>
              
              <div className="space-y-4">
                {/* Variance Explained */}
                <div>
                  <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Variance Explained by Components
                  </div>
                  <div className="space-y-2">
                    {matrix.pca_variance_explained.slice(0, 5).map((variance, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400 w-16">
                          PC{idx + 1}
                        </span>
                        <div className="flex-1 h-8 bg-gray-200 dark:bg-gray-600 rounded overflow-hidden">
                          <div
                            className="h-full bg-blue-500"
                            style={{ width: `${variance * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600 dark:text-gray-400 w-16 text-right">
                          {(variance * 100).toFixed(2)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Cumulative Variance */}
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Cumulative Variance (First 5 Components)
                  </div>
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
                    {(matrix.pca_variance_explained.slice(0, 5).reduce((a, b) => a + b, 0) * 100).toFixed(2)}%
                  </div>
                </div>
              </div>

              <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
                PCA transforms correlated variables into uncorrelated principal components.
                Higher variance explained indicates that fewer components capture most of the data variation.
              </p>
            </div>
          )}

          {/* Period Info */}
          <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
            Analysis period: {new Date(matrix.start_date).toLocaleDateString()} - {new Date(matrix.end_date).toLocaleDateString()}
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
            No correlation analysis yet
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Select at least 2 symbols and click "Calculate Correlation"
          </p>
        </div>
      )}
    </div>
  );
}
