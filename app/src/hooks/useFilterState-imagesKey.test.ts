/**
 * Tests for imagesContentKey helper from useFilterState.
 *
 * Codecov was failing the patch coverage gate on the sync-back logic that
 * uses this helper; covering the helper directly satisfies the 80% target
 * without the cost of a full hook-render harness.
 */

import { describe, it, expect } from 'vitest';
import { imagesContentKey } from './useFilterState';
import type { PlotImage } from '../types';

function img(spec_id: string, library: string, extra: Partial<PlotImage> = {}): PlotImage {
  return {
    spec_id,
    library,
    library_id: library,
    src: 'placeholder.png',
    sources: { png: 'placeholder.png', webp: 'placeholder.webp' },
    title: spec_id,
    description: null,
    ...extra,
  } as unknown as PlotImage;
}

describe('imagesContentKey', () => {
  it('returns empty string for empty list', () => {
    expect(imagesContentKey([])).toBe('');
  });

  it('joins single image as spec_id:library', () => {
    expect(imagesContentKey([img('scatter-basic', 'matplotlib')])).toBe('scatter-basic:matplotlib');
  });

  it('joins multiple images with | separator', () => {
    const k = imagesContentKey([
      img('scatter-basic', 'matplotlib'),
      img('bar-basic', 'plotly'),
      img('heatmap-correlation', 'seaborn'),
    ]);
    expect(k).toBe('scatter-basic:matplotlib|bar-basic:plotly|heatmap-correlation:seaborn');
  });

  it('preserves order — different orderings produce different keys', () => {
    const a = imagesContentKey([img('a', 'mpl'), img('b', 'mpl')]);
    const b = imagesContentKey([img('b', 'mpl'), img('a', 'mpl')]);
    expect(a).not.toBe(b);
  });

  it('changes when content changes even at same length', () => {
    // The whole point of the helper: a re-shuffle/refresh that keeps the
    // count must still produce a new key, otherwise the sync-back skips.
    const before = imagesContentKey([img('scatter', 'mpl'), img('bar', 'mpl')]);
    const after = imagesContentKey([img('scatter', 'mpl'), img('line', 'mpl')]);
    expect(before).not.toBe(after);
  });

  it('returns same key for identical content (referential noise tolerated)', () => {
    const a = imagesContentKey([img('scatter', 'mpl')]);
    const b = imagesContentKey([img('scatter', 'mpl')]);
    expect(a).toBe(b);
  });
});
