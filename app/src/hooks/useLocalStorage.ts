import { useCallback, useEffect, useState } from 'react';

/**
 * Hook for syncing state with localStorage.
 *
 * @param key - localStorage key
 * @param defaultValue - Default value if key doesn't exist
 * @returns Tuple of [value, setValue] like useState
 *
 * @example
 * const [theme, setTheme] = useLocalStorage('theme', 'light');
 */
export function useLocalStorage<T>(
  key: string,
  defaultValue: T
): [T, (value: T | ((prev: T) => T)) => void] {
  // Initialize state from localStorage or default
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = localStorage.getItem(key);
      if (stored !== null) {
        // Try to parse as JSON, fallback to raw string
        try {
          return JSON.parse(stored) as T;
        } catch {
          return stored as unknown as T;
        }
      }
    } catch {
      // localStorage might not be available (SSR, private mode)
    }
    return defaultValue;
  });

  // Sync to localStorage when value changes
  useEffect(() => {
    try {
      const serialized = typeof value === 'string' ? value : JSON.stringify(value);
      localStorage.setItem(key, serialized);
    } catch {
      // localStorage might not be available
    }
  }, [key, value]);

  // Wrapper to support functional updates
  const setValueWrapped = useCallback((newValue: T | ((prev: T) => T)) => {
    setValue(prev =>
      typeof newValue === 'function' ? (newValue as (prev: T) => T)(prev) : newValue
    );
  }, []);

  return [value, setValueWrapped];
}
