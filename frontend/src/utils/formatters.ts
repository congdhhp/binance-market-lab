/**
 * Utility functions for formatting data
 */

export const formatNumber = (value: number | string, decimals: number = 2): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '0';
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

export const formatPrice = (value: number | string, decimals: number = 2): string => {
  return '$' + formatNumber(value, decimals);
};

export const formatPercent = (value: number | string, decimals: number = 2): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  const sign = num >= 0 ? '+' : '';
  return sign + formatNumber(num, decimals) + '%';
};

export const formatVolume = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (num >= 1e9) return formatNumber(num / 1e9, 2) + 'B';
  if (num >= 1e6) return formatNumber(num / 1e6, 2) + 'M';
  if (num >= 1e3) return formatNumber(num / 1e3, 2) + 'K';
  return formatNumber(num, 0);
};

export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const formatTimeAgo = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
};

export const getColorForChange = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (num > 0) return 'text-green-500';
  if (num < 0) return 'text-red-500';
  return 'text-gray-500';
};

export const getBackgroundColorForChange = (value: number | string): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (num > 0) return 'bg-green-100 text-green-800';
  if (num < 0) return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-800';
};

export const intervals = [
  { label: '1m', value: '1m' },
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1h', value: '1h' },
  { label: '4h', value: '4h' },
  { label: '1d', value: '1d' },
];

export const getIntervalLabel = (interval: string): string => {
  const found = intervals.find(i => i.value === interval);
  return found ? found.label : interval;
};
