import { useCallback, useEffect, useRef, useState } from 'react';

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
  // One timer for both states: a second click restarts it, so the latest state keeps its full
  // time, and none fires after `reset` or once the component is gone.
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clearTimer = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  }, []);
  useEffect(() => clearTimer, [clearTimer]);

  const copyToClipboard = useCallback(
    async (text: string) => {
      const settle = () => {
        clearTimer();
        timer.current = setTimeout(() => {
          setCopied(false);
          setFailed(false);
        }, timeout);
      };
      try {
        await navigator.clipboard.writeText(text);
        setFailed(false);
        setCopied(true);
        onCopy?.();
        settle();
      } catch (err) {
        console.error('Failed to copy text:', err);
        setCopied(false);
        setFailed(true);
        onError?.();
        settle();
      }
    },
    [onCopy, onError, timeout, clearTimer]
  );

  const reset = useCallback(() => {
    clearTimer();
    setCopied(false);
    setFailed(false);
  }, [clearTimer]);

  return { copied, failed, copyToClipboard, reset };
}
