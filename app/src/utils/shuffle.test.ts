/**
 * Tests for the shuffleArray utility (Fisher-Yates).
 *
 * Used by useFilterFetch and useFeaturedSpecs as the replacement for the
 * biased `[...arr].sort(() => Math.random() - 0.5)` idiom.
 */

import { describe, it, expect, vi } from 'vitest';
import { shuffleArray } from './shuffle';

describe('shuffleArray', () => {
  it('returns an array of the same length', () => {
    expect(shuffleArray([1, 2, 3, 4, 5])).toHaveLength(5);
  });

  it('contains exactly the same elements (set-equal)', () => {
    const input = [1, 2, 3, 4, 5];
    const out = shuffleArray(input);
    expect([...out].sort()).toEqual([1, 2, 3, 4, 5]);
  });

  it('does not mutate the input array', () => {
    const input = [1, 2, 3, 4, 5];
    shuffleArray(input);
    expect(input).toEqual([1, 2, 3, 4, 5]);
  });

  it('handles empty arrays', () => {
    expect(shuffleArray([])).toEqual([]);
  });

  it('handles single-element arrays', () => {
    expect(shuffleArray(['only'])).toEqual(['only']);
  });

  it('produces a deterministic order when Math.random is mocked', () => {
    // With Math.random always returning 0, Fisher-Yates always swaps with
    // index 0 — yields a fully-reversed array for ascending input.
    const spy = vi.spyOn(Math, 'random').mockReturnValue(0);
    try {
      expect(shuffleArray([1, 2, 3, 4])).toEqual([2, 3, 4, 1]);
    } finally {
      spy.mockRestore();
    }
  });

  it('accepts readonly arrays (TS contract)', () => {
    // Compile-time check disguised as a runtime test — readonly accepted.
    const input: readonly string[] = ['a', 'b', 'c'];
    const out = shuffleArray(input);
    expect(out).toHaveLength(3);
  });
});
