import { describe, it, expect } from 'vitest';

import {
  flattenTags,
  computeIDF,
  weightedJaccard,
  buildKNNLinks,
  selectMapThumbUrl,
  buildVariantUrl,
  pickTier,
  pickBestLoadedTier,
  fitToBox,
  primaryPlotType,
  topPlotTypes,
  type SpecMapItem,
} from './MapPage.helpers';


function spec(id: string, tags: SpecMapItem['tags'], implTags: SpecMapItem['impl_tags'] = null): SpecMapItem {
  return {
    id,
    title: id,
    preview_url_light: `https://example.com/${id}-light.png`,
    preview_url_dark: `https://example.com/${id}-dark.png`,
    quality_score: 90,
    tags,
    impl_tags: implTags,
  };
}


describe('flattenTags', () => {
  it('prefixes values with their category', () => {
    const s = spec('a', { plot_type: ['scatter'], features: ['basic', '2d'] });
    expect(flattenTags(s).sort()).toEqual(['features:2d', 'features:basic', 'plot_type:scatter']);
  });

  it('merges spec.tags with impl_tags by default', () => {
    const s = spec('a', { plot_type: ['scatter'] }, { dependencies: ['scipy'] });
    expect(flattenTags(s).sort()).toEqual(['dependencies:scipy', 'plot_type:scatter']);
  });

  it('skips impl_tags when includeImpl=false', () => {
    const s = spec('a', { plot_type: ['scatter'] }, { dependencies: ['scipy'] });
    expect(flattenTags(s, false)).toEqual(['plot_type:scatter']);
  });

  it('handles missing dicts and empty arrays', () => {
    expect(flattenTags(spec('a', null, null))).toEqual([]);
    expect(flattenTags(spec('a', { plot_type: [] }, null))).toEqual([]);
  });

  it('deduplicates identical category:value pairs', () => {
    const s = spec('a', { plot_type: ['scatter', 'scatter'] }, { plot_type: ['scatter'] });
    expect(flattenTags(s)).toEqual(['plot_type:scatter']);
  });
});


describe('computeIDF', () => {
  it('assigns log(N / df) to every tag', () => {
    const specs = [
      spec('a', { plot_type: ['scatter'] }),
      spec('b', { plot_type: ['scatter'] }),
      spec('c', { plot_type: ['line'] }),
    ];
    const idf = computeIDF(specs);
    expect(idf.get('plot_type:scatter')).toBeCloseTo(Math.log(3 / 2));
    expect(idf.get('plot_type:line')).toBeCloseTo(Math.log(3 / 1));
  });

  it('gives ubiquitous tags weight ~0', () => {
    const specs = [
      spec('a', { data_type: ['numeric'] }),
      spec('b', { data_type: ['numeric'] }),
    ];
    expect(computeIDF(specs).get('data_type:numeric')).toBe(0);
  });

  it('survives empty input without dividing by zero', () => {
    expect(computeIDF([]).size).toBe(0);
  });

  it('zeroes out tags above the maxDfRatio cutoff (default 0.67)', () => {
    // 4 specs, "dependencies:selenium" appears in 3 (75%) → above default 0.67 cutoff
    const specs = [
      spec('a', { plot_type: ['scatter'] }, { dependencies: ['selenium'] }),
      spec('b', { plot_type: ['scatter'] }, { dependencies: ['selenium'] }),
      spec('c', { plot_type: ['line'] }, { dependencies: ['selenium'] }),
      spec('d', { plot_type: ['bar'] }, { dependencies: ['matplotlib'] }),
    ];
    const idf = computeIDF(specs);
    expect(idf.get('dependencies:selenium')).toBe(0);
    // The rare one stays meaningful
    expect(idf.get('dependencies:matplotlib')).toBeGreaterThan(0);
  });

  it('honors a custom maxDfRatio', () => {
    const specs = [
      spec('a', { features: ['basic'] }),
      spec('b', { features: ['basic'] }),
      spec('c', { features: ['rare'] }),
    ];
    // basic in 2/3 = 67 % — below default 0.67 cutoff, kept
    expect(computeIDF(specs).get('features:basic')).toBeGreaterThan(0);
    // tighten cutoff to 0.5 → basic now noise
    expect(computeIDF(specs, 0.5).get('features:basic')).toBe(0);
  });
});


describe('weightedJaccard', () => {
  const idf = new Map([
    ['plot_type:scatter', 1.0],
    ['plot_type:line', 1.0],
    ['features:basic', 0.5],
  ]);

  it('returns 1 when sets are identical', () => {
    expect(weightedJaccard(['plot_type:scatter'], ['plot_type:scatter'], idf)).toBeCloseTo(1);
  });

  it('returns 0 when sets are disjoint', () => {
    expect(weightedJaccard(['plot_type:scatter'], ['plot_type:line'], idf)).toBe(0);
  });

  it('weights overlap by IDF (rare overlap > common overlap)', () => {
    const rareIdf = new Map([['plot_type:scatter', 2], ['features:basic', 0.1]]);
    const sharedRare = weightedJaccard(['plot_type:scatter'], ['plot_type:scatter', 'features:basic'], rareIdf);
    const sharedCommon = weightedJaccard(['features:basic'], ['features:basic', 'plot_type:scatter'], rareIdf);
    expect(sharedRare).toBeGreaterThan(sharedCommon);
  });

  it('returns 0 when either set is empty', () => {
    expect(weightedJaccard([], ['plot_type:scatter'], idf)).toBe(0);
    expect(weightedJaccard(['plot_type:scatter'], [], idf)).toBe(0);
  });
});


describe('buildKNNLinks', () => {
  it('keeps top-K neighbors above the similarity threshold', () => {
    const specs = [
      spec('scatter1', { plot_type: ['scatter'], features: ['basic'] }),
      spec('scatter2', { plot_type: ['scatter'], features: ['basic'] }),
      spec('line1', { plot_type: ['line'], features: ['basic'] }),
      spec('bar1', { plot_type: ['bar'] }),
    ];
    const idf = computeIDF(specs);
    const links = buildKNNLinks(specs, idf, 2, 0.0);
    // scatter1 ↔ scatter2 should be linked (most similar pair)
    const ids = links.map(l => `${l.source}-${l.target}`).sort();
    expect(ids).toContain('scatter1-scatter2');
  });

  it('produces undirected links (no A→B and B→A duplicate)', () => {
    // Need a 3-spec corpus so IDF gives non-zero weight to scatter (otherwise
    // a universal tag has weight 0 and no link is emitted — correct behavior).
    const specs = [
      spec('a', { plot_type: ['scatter'] }),
      spec('b', { plot_type: ['scatter'] }),
      spec('c', { plot_type: ['line'] }),
    ];
    const links = buildKNNLinks(specs, computeIDF(specs), 5, 0.0);
    const keys = links.map(l => `${l.source}|${l.target}`);
    // a-b should appear exactly once, not twice
    expect(keys.filter(k => k === 'a|b' || k === 'b|a').length).toBe(1);
  });

  it('drops links below minSim', () => {
    const specs = [
      spec('a', { plot_type: ['scatter'] }),
      spec('b', { plot_type: ['line'] }),
    ];
    const links = buildKNNLinks(specs, computeIDF(specs), 5, 0.5);
    expect(links).toHaveLength(0);
  });

  it('every link weight is in (0, 1]', () => {
    const specs = [
      spec('a', { plot_type: ['scatter'], features: ['basic'] }),
      spec('b', { plot_type: ['scatter'], features: ['regression'] }),
      spec('c', { plot_type: ['line'], features: ['basic'] }),
    ];
    const links = buildKNNLinks(specs, computeIDF(specs), 3, 0.0);
    for (const l of links) {
      expect(l.weight).toBeGreaterThan(0);
      expect(l.weight).toBeLessThanOrEqual(1);
    }
  });
});


describe('selectMapThumbUrl', () => {
  it('returns the dark URL in dark mode and light URL in light mode', () => {
    const s = spec('a', null);
    expect(selectMapThumbUrl(s, true)).toBe('https://example.com/a-dark.png');
    expect(selectMapThumbUrl(s, false)).toBe('https://example.com/a-light.png');
  });

  it('falls back to the other theme when the preferred URL is missing', () => {
    const s: SpecMapItem = { ...spec('a', null), preview_url_dark: null };
    expect(selectMapThumbUrl(s, true)).toBe('https://example.com/a-light.png');
  });

  it('returns null when no preview URLs at all', () => {
    const s: SpecMapItem = { ...spec('a', null), preview_url_light: null, preview_url_dark: null };
    expect(selectMapThumbUrl(s, false)).toBeNull();
  });
});


describe('buildVariantUrl', () => {
  it('rewrites .png to _{tier}.webp', () => {
    expect(buildVariantUrl('https://example.com/plot.png', 400)).toBe('https://example.com/plot_400.webp');
    expect(buildVariantUrl('https://example.com/plot-light.png', 800)).toBe('https://example.com/plot-light_800.webp');
    expect(buildVariantUrl('https://example.com/plot-dark.png', 1200)).toBe('https://example.com/plot-dark_1200.webp');
  });

  it('passes through URLs that do not end in .png', () => {
    expect(buildVariantUrl('https://example.com/plot.svg', 400)).toBe('https://example.com/plot.svg');
  });
});


describe('pickTier', () => {
  it('returns 400 when device pixel size fits in 400 with headroom', () => {
    expect(pickTier(100)).toBe(400);
    expect(pickTier(300)).toBe(400);
  });

  it('returns 800 when 400 would require upscaling', () => {
    expect(pickTier(500)).toBe(800);
    expect(pickTier(600)).toBe(800);
  });

  it('returns 1200 for very large device sizes', () => {
    expect(pickTier(1000)).toBe(1200);
    expect(pickTier(2000)).toBe(1200);
  });
});


describe('primaryPlotType', () => {
  it('returns the first plot_type entry', () => {
    expect(primaryPlotType(spec('a', { plot_type: ['scatter', 'point'] }))).toBe('scatter');
  });

  it('returns "other" when plot_type is missing', () => {
    expect(primaryPlotType(spec('a', null))).toBe('other');
    expect(primaryPlotType(spec('a', { domain: ['statistics'] }))).toBe('other');
  });
});


describe('topPlotTypes', () => {
  it('returns the N most frequent primary types in descending order', () => {
    const specs = [
      spec('s1', { plot_type: ['line'] }),
      spec('s2', { plot_type: ['line'] }),
      spec('s3', { plot_type: ['line'] }),
      spec('s4', { plot_type: ['scatter'] }),
      spec('s5', { plot_type: ['scatter'] }),
      spec('s6', { plot_type: ['bar'] }),
    ];
    expect(topPlotTypes(specs, 3)).toEqual(['line', 'scatter', 'bar']);
  });

  it('truncates to the requested length', () => {
    const specs = [
      spec('s1', { plot_type: ['a'] }),
      spec('s2', { plot_type: ['b'] }),
      spec('s3', { plot_type: ['c'] }),
    ];
    expect(topPlotTypes(specs, 2)).toHaveLength(2);
  });

  it('breaks ties alphabetically for determinism', () => {
    const specs = [
      spec('s1', { plot_type: ['zebra'] }),
      spec('s2', { plot_type: ['apple'] }),
      spec('s3', { plot_type: ['mango'] }),
    ];
    // All have count=1, alphabetic order: apple, mango, zebra
    expect(topPlotTypes(specs, 3)).toEqual(['apple', 'mango', 'zebra']);
  });

  it('excludes the synthetic "other" bucket so it does not waste a color slot', () => {
    const specs = [
      spec('s1', null),  // no plot_type → primaryPlotType returns 'other'
      spec('s2', { plot_type: ['line'] }),
    ];
    expect(topPlotTypes(specs, 5)).toEqual(['line']);
  });
});


describe('fitToBox', () => {
  it('returns a square for 1:1 aspect ratio', () => {
    expect(fitToBox(22, 1)).toEqual({ w: 22, h: 22 });
  });

  it('keeps width = box and shrinks height for 16:9', () => {
    const r = fitToBox(22, 16 / 9);
    expect(r.w).toBe(22);
    expect(r.h).toBeCloseTo(22 * 9 / 16);
  });

  it('keeps height = box and shrinks width for portrait (9:16)', () => {
    const r = fitToBox(22, 9 / 16);
    expect(r.h).toBe(22);
    expect(r.w).toBeCloseTo(22 * 9 / 16);
  });

  it('falls back to a square for invalid aspect ratios', () => {
    expect(fitToBox(22, 0)).toEqual({ w: 22, h: 22 });
    expect(fitToBox(22, NaN)).toEqual({ w: 22, h: 22 });
    expect(fitToBox(22, Infinity)).toEqual({ w: 22, h: 22 });
  });
});


describe('pickBestLoadedTier', () => {
  function img(): HTMLImageElement {
    return document.createElement('img');
  }

  it('returns the desired tier when loaded', () => {
    const a = img();
    const imgs = new Map([[400 as const, a]]);
    expect(pickBestLoadedTier(imgs, 400)).toBe(a);
  });

  it('returns a higher-resolution variant when desired is not loaded', () => {
    const a = img();
    const imgs = new Map([[800 as const, a]]);
    expect(pickBestLoadedTier(imgs, 400)).toBe(a);
  });

  it('falls back to a smaller tier when nothing larger is loaded', () => {
    const a = img();
    const imgs = new Map([[400 as const, a]]);
    expect(pickBestLoadedTier(imgs, 800)).toBe(a);
  });

  it('returns null when nothing is loaded', () => {
    expect(pickBestLoadedTier(new Map(), 400)).toBeNull();
  });
});
