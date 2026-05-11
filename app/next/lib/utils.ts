/**
 * Utility functions for the InsightForge application
 */

export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat().format(num);
}

export function truncateString(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength) + '...';
}