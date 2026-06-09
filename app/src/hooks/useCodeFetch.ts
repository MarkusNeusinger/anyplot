/**
 * Hook for fetching plot code on-demand.
 *
 * Code is deferred in the database and excluded from /specs/{id} responses.
 * This hook fetches code from the lightweight /specs/{spec_id}/{library}/code endpoint.
 */

import { useCallback, useRef, useState } from 'react';

import { API_URL } from '../constants';

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
  const [isLoading, setIsLoading] = useState(false);
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

      // Only append the language query param when it diverges from the API
      // default — keeps URLs for the common Python case unchanged.
      const url =
        language === 'python'
          ? `${API_URL}/specs/${specId}/${library}/code`
          : `${API_URL}/specs/${specId}/${library}/code?language=${encodeURIComponent(language)}`;

      setIsLoading(true);
      const promise = (async () => {
        try {
          const response = await fetch(url);
          if (!response.ok) {
            cacheRef.current[key] = null;
            return null;
          }

          const data = await response.json();
          const code = data.code ?? null;
          cacheRef.current[key] = code;
          return code;
        } catch {
          cacheRef.current[key] = null;
          return null;
        } finally {
          pendingRef.current.delete(key);
          setIsLoading(false);
        }
      })();

      pendingRef.current.set(key, promise);
      return promise;
    },
    []
  );

  return { fetchCode, getCode, isLoading };
}
