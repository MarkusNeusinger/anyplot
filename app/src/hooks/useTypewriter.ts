import { useEffect, useState } from 'react';

interface UseTypewriterOptions {
  /** Milliseconds between characters. */
  charDelay?: number;
  /** Extra pause after each completed line. */
  linePause?: number;
  /** Delay before the first character starts typing. */
  startDelay?: number;
}

interface UseTypewriterResult {
  /** Partial lines reflecting typing progress. `lines.length` equals input length; each string grows over time. */
  rendered: string[];
  /** Index of the line currently being typed; -1 once all lines are complete. */
  activeLine: number;
  done: boolean;
}

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
}

export function useTypewriter(
  lines: string[],
  { charDelay = 45, linePause = 250, startDelay = 200 }: UseTypewriterOptions = {},
): UseTypewriterResult {
  const reduced = prefersReducedMotion();
  const [rendered, setRendered] = useState<string[]>(() =>
    reduced ? [...lines] : lines.map(() => ''),
  );
  const [activeLine, setActiveLine] = useState<number>(reduced ? -1 : 0);

  useEffect(() => {
    if (reduced) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    const typeLine = (lineIdx: number, charIdx: number) => {
      if (cancelled) return;
      if (lineIdx >= lines.length) {
        setActiveLine(-1);
        return;
      }
      const line = lines[lineIdx];
      if (charIdx > line.length) {
        timer = setTimeout(() => typeLine(lineIdx + 1, 0), linePause);
        return;
      }
      setRendered(prev => {
        const next = [...prev];
        next[lineIdx] = line.slice(0, charIdx);
        return next;
      });
      setActiveLine(lineIdx);
      timer = setTimeout(() => typeLine(lineIdx, charIdx + 1), charDelay);
    };

    timer = setTimeout(() => typeLine(0, 0), startDelay);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [lines, charDelay, linePause, startDelay, reduced]);

  return { rendered, activeLine, done: activeLine === -1 };
}
