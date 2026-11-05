import { useCallback, useState } from 'react';

interface UseCopyCodeOptions {
  /** Callback when copy succeeds */
  onCopy?: () => void;
  /** Callback when the browser refused the copy */
  onError?: () => void;
  /** Timeout for the copied and failed states' reset (ms) */
  timeout?: number;
}

interface UseCopyCodeReturn {
  /** Whether text was recently copied */
  copied: boolean;
  /**
   * Whether the browser recently refused the copy (no clipboard permission, a document without
   * focus): a refused copy changes nothing on the page otherwise, and reads as a dead button.
   */
  failed: boolean;
  /** Function to copy text to clipboard */
  copyToClipboard: (text: string) => Promise<void>;
  /** Function to reset the copied and failed states */
  reset: () => void;
}

/**
 * Hook for copying text to clipboard with visual feedback.
 *
 * @example
 * const { copied, failed, copyToClipboard } = useCopyCode({
 *   onCopy: () => trackEvent('copy_code'),
 * });
 *
 * <button onClick={() => copyToClipboard(code)}>
 *   {copied ? 'Copied!' : failed ? 'Copy failed' : 'Copy'}
 * </button>
 */
export function useCopyCode({
  onCopy,
  onError,
  timeout = 2000,
}: UseCopyCodeOptions = {}): UseCopyCodeReturn {
  const [copied, setCopied] = useState(false);
  const [failed, setFailed] = useState(false);

  const copyToClipboard = useCallback(
    async (text: string) => {
      try {
        await navigator.clipboard.writeText(text);
        setFailed(false);
        setCopied(true);
        onCopy?.();
        setTimeout(() => setCopied(false), timeout);
      } catch (err) {
        console.error('Failed to copy text:', err);
        setCopied(false);
        setFailed(true);
        onError?.();
        setTimeout(() => setFailed(false), timeout);
      }
    },
    [onCopy, onError, timeout]
  );

  const reset = useCallback(() => {
    setCopied(false);
    setFailed(false);
  }, []);

  return { copied, failed, copyToClipboard, reset };
}
