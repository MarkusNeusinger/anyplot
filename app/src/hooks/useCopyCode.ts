import { useCallback, useState } from 'react';

interface UseCopyCodeOptions {
  /** Callback when copy succeeds */
  onCopy?: () => void;
  /** Timeout for copied state reset (ms) */
  timeout?: number;
}

interface UseCopyCodeReturn {
  /** Whether text was recently copied */
  copied: boolean;
  /** Function to copy text to clipboard */
  copyToClipboard: (text: string) => Promise<void>;
  /** Function to reset copied state */
  reset: () => void;
}

/**
 * Hook for copying text to clipboard with visual feedback.
 *
 * @example
 * const { copied, copyToClipboard } = useCopyCode({
 *   onCopy: () => trackEvent('copy_code'),
 * });
 *
 * <button onClick={() => copyToClipboard(code)}>
 *   {copied ? 'Copied!' : 'Copy'}
 * </button>
 */
export function useCopyCode({
  onCopy,
  timeout = 2000,
}: UseCopyCodeOptions = {}): UseCopyCodeReturn {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        onCopy?.();
        setTimeout(() => setCopied(false), timeout);
      } catch (err) {
        console.error('Failed to copy text:', err);
      }
    },
    [onCopy, timeout]
  );

  const reset = useCallback(() => {
    setCopied(false);
  }, []);

  return { copied, copyToClipboard, reset };
}
