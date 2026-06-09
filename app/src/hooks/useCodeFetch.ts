/**
 * Hook for fetching plot code on-demand.
 *
 * Code is deferred in the database and excluded from /specs/{id} responses.
 * This hook fetches code from the lightweight /specs/{spec_id}/{library}/code endpoint.
 */

import { useCallback, useRef, useState } from 'react';

import { apiGet, endpoints } from 'src/lib/api';

interface CodeCache {
  [key: string]: string | null; // key: `${spec_id}:${language}:${library}`
}

interface UseCodeFetchReturn {
  fetchCode: (specId: string, library: string, language?: string) => Promise<string | null>;
  getCode: (specId: string, library: string, language?: string) => string | null;
  isLoading: boolean;
}

// Default language matches the API's own default so old call sites — and the
// majority of (Python) impls — keep producing the same URL and cache key.
const cacheKey = (specId: string, library: string, language: string) =>
  `${specId}:${language}:${library}`;

export function useCodeFetch(): UseCodeFetchReturn {
  // Count in-flight requests instead of a boolean: with overlapping fetches
  // (different cache keys) the first completion must not clear the loading
  // state while the second request is still pending.
  const [pendingCount, setPendingCount] = useState(0);
  const cacheRef = useRef<CodeCache>({});
  const pendingRef = useRef<Map<string, Promise<string | null>>>(new Map());

  const getCode = useCallback(
    (specId: string, library: string, language: string = 'python'): string | null => {
      return cacheRef.current[cacheKey(specId, library, language)] ?? null;
    },
    []
  );

  const fetchCode = useCallback(
    async (
      specId: string,
      library: string,
      language: string = 'python'
    ): Promise<string | null> => {
      const key = cacheKey(specId, library, language);

      // Check cache first
      if (key in cacheRef.current) {
        return cacheRef.current[key];
      }

      // Check if already fetching
      const pending = pendingRef.current.get(key);
      if (pending) {
        return pending;
      }

      setPendingCount(count => count + 1);
      const promise = (async () => {
        try {
          const data = await apiGet<{ code?: string | null }>(
            endpoints.code(specId, library, language)
          );
          const code = data.code ?? null;
          cacheRef.current[key] = code;
          return code;
        } catch {
          cacheRef.current[key] = null;
          return null;
        } finally {
          pendingRef.current.delete(key);
          setPendingCount(count => count - 1);
        }
      })();

      pendingRef.current.set(key, promise);
      return promise;
    },
    []
  );

  return { fetchCode, getCode, isLoading: pendingCount > 0 };
}
