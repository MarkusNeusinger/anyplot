import { useEffect, useState } from 'react';

const API_URL = 'https://api.github.com/repos/MarkusNeusinger/anyplot/releases/latest';
const CACHE_KEY = 'anyplot:latest-release';
const TTL_MS = 60 * 60 * 1000;

type Cached = { tag: string; ts: number };

function readCache(): Cached | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const parsed: Cached = JSON.parse(raw);
    if (parsed?.tag && typeof parsed.ts === 'number') return parsed;
  } catch {
    /* ignore */
  }
  return null;
}

function isFresh(entry: Cached | null): boolean {
  return !!entry && Date.now() - entry.ts < TTL_MS;
}

export function useLatestRelease(): string | null {
  const [tag, setTag] = useState<string | null>(() => readCache()?.tag ?? null);

  useEffect(() => {
    let cancelled = false;

    const refresh = () => {
      if (isFresh(readCache())) return;
      fetch(API_URL)
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (cancelled) return;
          const name: string | undefined = data?.tag_name;
          if (!name) return;
          setTag(name);
          try {
            localStorage.setItem(CACHE_KEY, JSON.stringify({ tag: name, ts: Date.now() } satisfies Cached));
          } catch {
            /* ignore */
          }
        })
        .catch(() => {
          /* offline / rate-limited — fallback stays */
        });
    };

    refresh();
    const interval = window.setInterval(refresh, TTL_MS);
    const onVisible = () => {
      if (document.visibilityState === 'visible') refresh();
    };
    document.addEventListener('visibilitychange', onVisible);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, []);

  return tag;
}
