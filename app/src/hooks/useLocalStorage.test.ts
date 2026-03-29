import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from './useLocalStorage';

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('returns default value when key does not exist', () => {
    const { result } = renderHook(() => useLocalStorage('theme', 'light'));
    expect(result.current[0]).toBe('light');
  });

  it('returns stored value when key exists', () => {
    localStorage.setItem('theme', JSON.stringify('dark'));
    const { result } = renderHook(() => useLocalStorage('theme', 'light'));
    expect(result.current[0]).toBe('dark');
  });

  it('updates localStorage when value changes', () => {
    const { result } = renderHook(() => useLocalStorage('count', 0));
    act(() => {
      result.current[1](42);
    });
    expect(result.current[0]).toBe(42);
    expect(JSON.parse(localStorage.getItem('count')!)).toBe(42);
  });

  it('supports functional updates', () => {
    const { result } = renderHook(() => useLocalStorage('count', 10));
    act(() => {
      result.current[1]((prev) => prev + 5);
    });
    expect(result.current[0]).toBe(15);
  });

  it('handles object values', () => {
    const defaultVal = { a: 1, b: 'hello' };
    const { result } = renderHook(() => useLocalStorage('obj', defaultVal));
    expect(result.current[0]).toEqual(defaultVal);

    act(() => {
      result.current[1]({ a: 2, b: 'world' });
    });
    expect(result.current[0]).toEqual({ a: 2, b: 'world' });
    expect(JSON.parse(localStorage.getItem('obj')!)).toEqual({ a: 2, b: 'world' });
  });

  it('stores strings without double-encoding', () => {
    const { result } = renderHook(() => useLocalStorage('name', 'alice'));
    act(() => {
      result.current[1]('bob');
    });
    // Strings should be stored as-is, not JSON-encoded
    expect(localStorage.getItem('name')).toBe('bob');
  });

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem('bad', '{invalid json');
    // Should fall back to the raw string rather than crashing
    const { result } = renderHook(() => useLocalStorage('bad', 'fallback'));
    expect(result.current[0]).toBe('{invalid json');
  });
});
