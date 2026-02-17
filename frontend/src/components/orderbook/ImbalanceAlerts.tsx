import type { Symbol, ImbalanceAlert } from '../../types';

interface Props {
  symbol: Symbol;
  alerts: ImbalanceAlert[];
}

export default function ImbalanceAlerts({ symbol, alerts }: Props) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 dark:bg-red-900/30 border-red-500 text-red-800 dark:text-red-300';
      case 'high':
        return 'bg-orange-100 dark:bg-orange-900/30 border-orange-500 text-orange-800 dark:text-orange-300';
      case 'medium':
        return 'bg-yellow-100 dark:bg-yellow-900/30 border-yellow-500 text-yellow-800 dark:text-yellow-300';
      case 'low':
        return 'bg-blue-100 dark:bg-blue-900/30 border-blue-500 text-blue-800 dark:text-blue-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 border-gray-500 text-gray-800 dark:text-gray-300';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return (
          <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'high':
      case 'medium':
        return (
          <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      default:
        return (
          <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  const getAlertTypeLabel = (type: string) => {
    switch (type) {
      case 'bid_heavy':
        return 'Bid Heavy';
      case 'ask_heavy':
        return 'Ask Heavy';
      case 'balanced':
        return 'Balanced';
      case 'critical':
        return 'Critical Imbalance';
      default:
        return type;
    }
  };

  const getAlertTypeColor = (type: string) => {
    switch (type) {
      case 'bid_heavy':
        return 'text-green-600 dark:text-green-400';
      case 'ask_heavy':
        return 'text-red-600 dark:text-red-400';
      case 'balanced':
        return 'text-blue-600 dark:text-blue-400';
      case 'critical':
        return 'text-purple-600 dark:text-purple-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (alerts.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-green-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
          No active alerts
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          The orderbook for {symbol.name} is currently balanced
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 border-l-4 border-red-500">
          <div className="text-sm text-gray-600 dark:text-gray-400">Critical</div>
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">
            {alerts.filter((a) => a.severity === 'critical').length}
          </div>
        </div>
        <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border-l-4 border-orange-500">
          <div className="text-sm text-gray-600 dark:text-gray-400">High</div>
          <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
            {alerts.filter((a) => a.severity === 'high').length}
          </div>
        </div>
        <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 border-l-4 border-yellow-500">
          <div className="text-sm text-gray-600 dark:text-gray-400">Medium</div>
          <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
            {alerts.filter((a) => a.severity === 'medium').length}
          </div>
        </div>
        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border-l-4 border-blue-500">
          <div className="text-sm text-gray-600 dark:text-gray-400">Low</div>
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {alerts.filter((a) => a.severity === 'low').length}
          </div>
        </div>
      </div>

      {/* Alert List */}
      <div className="space-y-3">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`rounded-lg border-l-4 p-4 ${getSeverityColor(alert.severity)}`}
          >
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 mt-0.5">
                {getSeverityIcon(alert.severity)}
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`text-lg font-semibold ${getAlertTypeColor(alert.alert_type)}`}>
                      {getAlertTypeLabel(alert.alert_type)}
                    </span>
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-white dark:bg-gray-800">
                      {alert.severity.toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="text-sm opacity-75">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </div>
                </div>

                <p className="mt-2 text-sm">
                  {alert.description}
                </p>

                <div className="mt-3 flex items-center gap-4 text-sm">
                  <div>
                    <span className="opacity-75">Imbalance Ratio:</span>{' '}
                    <span className="font-semibold">
                      {(parseFloat(alert.imbalance_ratio) * 100).toFixed(2)}%
                    </span>
                  </div>
                  
                  <div>
                    <span className="opacity-75">Symbol:</span>{' '}
                    <span className="font-semibold">
                      {alert.symbol_name || `ID: ${alert.symbol}`}
                    </span>
                  </div>

                  {alert.is_resolved && (
                    <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
                      <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span>Resolved</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Info Box */}
      <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
          Understanding Orderbook Imbalance Alerts
        </h4>
        <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <li>
            <strong>Bid Heavy:</strong> More buy orders than sell orders - potential upward pressure
          </li>
          <li>
            <strong>Ask Heavy:</strong> More sell orders than buy orders - potential downward pressure
          </li>
          <li>
            <strong>Critical:</strong> Extreme imbalance detected - significant price movement may occur
          </li>
          <li>
            <strong>Balanced:</strong> Orderbook is relatively balanced - stable market conditions
          </li>
        </ul>
      </div>
    </div>
  );
}
