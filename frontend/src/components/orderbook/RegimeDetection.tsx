import { useState } from 'react';
import { api } from '../../services/api';
import type { Symbol, RegimeDetection as RegimeDetectionType } from '../../types';

interface Props {
  symbol: Symbol;
}

export default function RegimeDetection({ symbol }: Props) {
  const [lookbackDays, setLookbackDays] = useState(30);
  const [nRegimes, setNRegimes] = useState(4);
  const [isDetecting, setIsDetecting] = useState(false);
  const [detection, setDetection] = useState<RegimeDetectionType | null>(null);

  const detectRegime = async () => {
    setIsDetecting(true);
    try {
      const result = await api.detectRegime({
        symbol_id: symbol.id,
        lookback_days: lookbackDays,
        n_regimes: nRegimes,
      });
      
      setDetection(result);
    } catch (error) {
      console.error('Failed to detect regime:', error);
    } finally {
      setIsDetecting(false);
    }
  };

  const getRegimeColor = (regime: number) => {
    const colors = [
      'bg-green-500',
      'bg-blue-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-purple-500',
    ];
    return colors[regime % colors.length];
  };

  const getRegimeName = (regime: number) => {
    const names = [
      'Trending Up',
      'Trending Down',
      'Ranging',
      'High Volatility',
      'Consolidation',
    ];
    return names[regime % names.length];
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Lookback Period (days)
            </label>
            <input
              type="number"
              min="7"
              max="365"
              step="1"
              value={lookbackDays}
              onChange={(e) => setLookbackDays(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Number of Regimes
            </label>
            <input
              type="number"
              min="2"
              max="5"
              step="1"
              value={nRegimes}
              onChange={(e) => setNRegimes(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={detectRegime}
              disabled={isDetecting}
              className="w-full px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
            >
              {isDetecting ? 'Detecting...' : 'Detect Regime'}
            </button>
          </div>
        </div>
      </div>

      {detection ? (
        <>
          {/* Current Regime */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Current Market Regime
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-2">
                <div className={`${getRegimeColor(detection.current_regime)} rounded-lg p-6 text-white`}>
                  <div className="text-sm opacity-90">Active Regime</div>
                  <div className="text-4xl font-bold mt-2">{detection.regime_name}</div>
                  <div className="text-sm opacity-90 mt-2">
                    Regime {detection.current_regime + 1} of {nRegimes}
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
                <div className="text-sm text-gray-600 dark:text-gray-400">Confidence</div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white mt-2">
                  {(detection.regime_probability * 100).toFixed(1)}%
                </div>
                <div className="mt-4">
                  <div className="h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getRegimeColor(detection.current_regime)}`}
                      style={{ width: `${detection.regime_probability * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 text-sm text-gray-500 dark:text-gray-400">
              Detected at: {new Date(detection.timestamp).toLocaleString()}
            </div>
          </div>

          {/* Regime Characteristics */}
          {detection.regime_characteristics && Object.keys(detection.regime_characteristics).length > 0 && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Regime Characteristics
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(detection.regime_characteristics).map(([key, value]) => (
                  <div key={key} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {key.replace(/_/g, ' ')}
                    </div>
                    <div className="text-xl font-bold text-gray-900 dark:text-white mt-1">
                      {typeof value === 'number' ? value.toFixed(4) : String(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Transition Matrix */}
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Regime Transition Matrix
            </h3>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr>
                    <th className="p-2 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                      From \ To
                    </th>
                    {detection.transition_matrix.map((_, idx) => (
                      <th key={idx} className="p-2 text-center text-sm font-medium text-gray-700 dark:text-gray-300">
                        {getRegimeName(idx)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {detection.transition_matrix.map((row, rowIdx) => (
                    <tr key={rowIdx}>
                      <td className="p-2 text-sm font-medium text-gray-700 dark:text-gray-300">
                        {getRegimeName(rowIdx)}
                      </td>
                      {row.map((prob, colIdx) => (
                        <td key={colIdx} className="p-2">
                          <div
                            className={`rounded text-center py-2 text-sm font-semibold ${
                              prob > 0.5
                                ? 'bg-green-500 text-white'
                                : prob > 0.2
                                ? 'bg-yellow-500 text-white'
                                : 'bg-gray-300 text-gray-700'
                            }`}
                            title={`P(${getRegimeName(rowIdx)} → ${getRegimeName(colIdx)}): ${(prob * 100).toFixed(1)}%`}
                          >
                            {(prob * 100).toFixed(0)}%
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
              The transition matrix shows the probability of moving from one regime to another.
              Diagonal values indicate regime persistence.
            </p>
          </div>

          {/* Interpretation */}
          <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-4 rounded-r-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-blue-800 dark:text-blue-300">
                  Regime Analysis Interpretation
                </h4>
                <div className="mt-2 text-sm text-blue-700 dark:text-blue-400">
                  <p>
                    The market is currently in a <strong>{detection.regime_name}</strong> regime with{' '}
                    {(detection.regime_probability * 100).toFixed(1)}% confidence. This was detected using 
                    Hidden Markov Model (HMM) analysis over the last {lookbackDays} days.
                  </p>
                  <p className="mt-2">
                    Use this information to:
                  </p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li>Adjust trading strategies based on current market conditions</li>
                    <li>Anticipate regime changes using transition probabilities</li>
                    <li>Optimize position sizing for the current volatility regime</li>
                  </ul>
                </div>
              </div>
            </div>
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
            No regime analysis yet
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Click "Detect Regime" to analyze market conditions for {symbol.name}
          </p>
        </div>
      )}
    </div>
  );
}
