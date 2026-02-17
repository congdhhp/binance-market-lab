import { useMemo } from 'react';
import type { Symbol, OrderbookAnalysis } from '../../types';

interface Props {
  symbol: Symbol;
  analyses: OrderbookAnalysis[];
  isLoading: boolean;
}

export default function OrderbookDepth({ symbol, analyses, isLoading }: Props) {
  const latestAnalysis = analyses.length > 0 ? analyses[0] : null;

  // Calculate depth chart data
  const depthData = useMemo(() => {
    if (!latestAnalysis) return { bids: [], asks: [] };
    
    // Mock data - in real implementation, we'd fetch actual orderbook depth
    const bids = Array.from({ length: 20 }, (_, i) => ({
      price: parseFloat(latestAnalysis.vwap_bid) * (1 - (i * 0.001)),
      volume: Math.random() * 100 + 50,
      total: 0,
    }));

    const asks = Array.from({ length: 20 }, (_, i) => ({
      price: parseFloat(latestAnalysis.vwap_ask) * (1 + (i * 0.001)),
      volume: Math.random() * 100 + 50,
      total: 0,
    }));

    // Calculate cumulative volumes
    let bidTotal = 0;
    let askTotal = 0;
    bids.forEach((bid) => {
      bidTotal += bid.volume;
      bid.total = bidTotal;
    });
    asks.forEach((ask) => {
      askTotal += ask.volume;
      ask.total = askTotal;
    });

    return { bids: bids.reverse(), asks };
  }, [latestAnalysis]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!latestAnalysis) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">
          No orderbook data available for {symbol.name}
        </p>
      </div>
    );
  }

  const maxBidVolume = Math.max(...depthData.bids.map((b) => b.total));
  const maxAskVolume = Math.max(...depthData.asks.map((a) => a.total));
  const maxVolume = Math.max(maxBidVolume, maxAskVolume);

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Bid-Ask Spread</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {parseFloat(latestAnalysis.bid_ask_spread).toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {parseFloat(latestAnalysis.spread_bps).toFixed(2)} bps
          </div>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Orderbook Imbalance</div>
          <div className={`text-2xl font-bold mt-1 ${
            parseFloat(latestAnalysis.orderbook_imbalance) > 0
              ? 'text-green-600 dark:text-green-400'
              : 'text-red-600 dark:text-red-400'
          }`}>
            {(parseFloat(latestAnalysis.orderbook_imbalance) * 100).toFixed(2)}%
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {parseFloat(latestAnalysis.orderbook_imbalance) > 0 ? 'Bid Heavy' : 'Ask Heavy'}
          </div>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Total Depth (10 levels)</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            ${parseFloat(latestAnalysis.total_depth_10).toLocaleString()}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Bid: ${parseFloat(latestAnalysis.bid_depth_10).toLocaleString()}
          </div>
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <div className="text-sm text-gray-500 dark:text-gray-400">Liquidity Score</div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mt-1">
            {parseFloat(latestAnalysis.liquidity_score).toFixed(2)}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            / 100
          </div>
        </div>
      </div>

      {/* VWAP Metrics */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
          Volume-Weighted Average Price
        </h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">VWAP Bid</div>
            <div className="text-xl font-bold text-green-600 dark:text-green-400">
              ${parseFloat(latestAnalysis.vwap_bid).toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">VWAP Mid</div>
            <div className="text-xl font-bold text-gray-900 dark:text-white">
              ${parseFloat(latestAnalysis.vwap_mid).toFixed(2)}
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-500 dark:text-gray-400">VWAP Ask</div>
            <div className="text-xl font-bold text-red-600 dark:text-red-400">
              ${parseFloat(latestAnalysis.vwap_ask).toFixed(2)}
            </div>
          </div>
        </div>
      </div>

      {/* Depth Chart */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Order Book Depth
        </h3>
        
        <div className="space-y-4">
          {/* Bids */}
          <div>
            <div className="flex justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <span>Bids (Buy Orders)</span>
              <span className="text-green-600 dark:text-green-400">
                Total: ${maxBidVolume.toLocaleString()}
              </span>
            </div>
            <div className="space-y-1">
              {depthData.bids.slice(0, 10).map((bid, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className="text-sm text-gray-600 dark:text-gray-400 w-24">
                    ${bid.price.toFixed(2)}
                  </div>
                  <div className="flex-1 h-6 bg-gray-200 dark:bg-gray-600 rounded overflow-hidden">
                    <div
                      className="h-full bg-green-500 dark:bg-green-600"
                      style={{ width: `${(bid.total / maxVolume) * 100}%` }}
                    />
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 w-24 text-right">
                    {bid.volume.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Spread Indicator */}
          <div className="border-t border-b border-gray-300 dark:border-gray-600 py-2">
            <div className="text-center text-sm font-medium text-gray-700 dark:text-gray-300">
              Spread: {parseFloat(latestAnalysis.bid_ask_spread).toFixed(2)} ({parseFloat(latestAnalysis.spread_bps).toFixed(2)} bps)
            </div>
          </div>

          {/* Asks */}
          <div>
            <div className="flex justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              <span>Asks (Sell Orders)</span>
              <span className="text-red-600 dark:text-red-400">
                Total: ${maxAskVolume.toLocaleString()}
              </span>
            </div>
            <div className="space-y-1">
              {depthData.asks.slice(0, 10).map((ask, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className="text-sm text-gray-600 dark:text-gray-400 w-24">
                    ${ask.price.toFixed(2)}
                  </div>
                  <div className="flex-1 h-6 bg-gray-200 dark:bg-gray-600 rounded overflow-hidden">
                    <div
                      className="h-full bg-red-500 dark:bg-red-600"
                      style={{ width: `${(ask.total / maxVolume) * 100}%` }}
                    />
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 w-24 text-right">
                    {ask.volume.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Timestamp */}
      <div className="text-sm text-gray-500 dark:text-gray-400 text-center">
        Last updated: {new Date(latestAnalysis.timestamp).toLocaleString()}
      </div>
    </div>
  );
}
