import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  outlierSquashForce,
  type SimNode,
  useForceGraphSimulation,
} from 'src/hooks/useForceGraphSimulation';
import {
  DEFAULT_CATEGORY_WEIGHT,
  type MapNode,
  TAG_CATEGORIES,
  type TagCategory,
} from 'src/pages/MapPage.helpers';

vi.mock('src/hooks/useLayoutContext', () => ({
  useTheme: () => ({ isDark: false }),
}));

const mockSpecs = [
  {
    id: 'scatter-basic',
    title: 'Basic Scatter Plot',
    preview_url_light: 'https://example.com/scatter-basic-light.png',
    preview_url_dark: 'https://example.com/scatter-basic-dark.png',
    quality_score: 90,
    tags: { plot_type: ['scatter'], data_type: ['numeric'], features: ['basic'] },
    impl_tags: { dependencies: ['scipy'] },
  },
  {
    id: 'scatter-color-mapped',
    title: 'Scatter with Color Mapping',
    preview_url_light: 'https://example.com/scatter-color-light.png',
    preview_url_dark: 'https://example.com/scatter-color-dark.png',
    quality_score: 88,
    tags: { plot_type: ['scatter'], data_type: ['numeric'], features: ['color-mapped'] },
    impl_tags: { dependencies: ['scipy'] },
  },
  {
    id: 'line-basic',
    title: 'Basic Line Chart',
    preview_url_light: 'https://example.com/line-basic-light.png',
    preview_url_dark: 'https://example.com/line-basic-dark.png',
    quality_score: 92,
    tags: { plot_type: ['line'], data_type: ['numeric'], features: ['basic'] },
    impl_tags: null,
  },
];

function mockFetchSuccess() {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSpecs),
    })
  );
}

// Seeded simulation coordinates live on the node objects but are not part of
// the public MapNode surface (FG2D owns them at runtime).
type SeededNode = MapNode & { x?: number; y?: number };

async function renderLoadedHook() {
  const view = renderHook(() => useForceGraphSimulation());
  await waitFor(() => expect(view.result.current.specs).not.toBeNull());
  return view;
}

describe('useForceGraphSimulation', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // Restore stubbed globals (fetch, …) after every test so they don't leak
  // into subsequent suites.
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe('graph data derivation', () => {
    it('derives nodes, KNN links and legend buckets from the fetched specs', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();

      const { graphData } = result.current;
      expect(graphData.nodes.map(n => n.id).sort()).toEqual([
        'line-basic',
        'scatter-basic',
        'scatter-color-mapped',
      ]);
      // Only the two scatters share enough weighted-IDF tag mass to clear the
      // default similarity threshold — exactly one deduplicated KNN edge.
      expect(graphData.links).toHaveLength(1);
      expect([graphData.links[0].source, graphData.links[0].target].sort()).toEqual([
        'scatter-basic',
        'scatter-color-mapped',
      ]);
      expect(graphData.links[0].weight).toBeGreaterThan(0);
      // Legend buckets: scatter is the biggest cluster, line the runner-up.
      expect(graphData.topTypes[0]).toBe('scatter');
      expect(graphData.typeCounts.get('scatter')).toBe(2);
      expect(graphData.typeCounts.get('line')).toBe(1);
      // nodeById covers every node for O(1) paint-callback lookups.
      expect(result.current.nodeById.get('scatter-basic')?.title).toBe('Basic Scatter Plot');
      // neighbors is symmetric for the single link.
      expect(result.current.neighbors.get('scatter-basic')?.has('scatter-color-mapped')).toBe(true);
      expect(result.current.neighbors.get('scatter-color-mapped')?.has('scatter-basic')).toBe(true);
    });

    it('seeds initial node positions per cluster (warm start for the simulation)', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();

      const nodes = result.current.graphData.nodes as SeededNode[];
      // Every node should have a numeric seed position before FG2D ever ticks the simulation —
      // without seeding, FG2D's random initialiser would leave x/y undefined here.
      for (const n of nodes) {
        expect(typeof n.x).toBe('number');
        expect(typeof n.y).toBe('number');
        expect(Number.isFinite(n.x as number)).toBe(true);
        expect(Number.isFinite(n.y as number)).toBe(true);
      }
      // Same plot_type (= colorBucket) should land near the same centroid; nodes from
      // different buckets should land further apart on average. Take the two scatters
      // (bucketed together) vs. line-basic and compare distances.
      const scatterA = nodes.find(n => n.id === 'scatter-basic')!;
      const scatterB = nodes.find(n => n.id === 'scatter-color-mapped')!;
      const line = nodes.find(n => n.id === 'line-basic')!;
      const dist = (a: typeof scatterA, b: typeof scatterA) =>
        Math.hypot((a.x ?? 0) - (b.x ?? 0), (a.y ?? 0) - (b.y ?? 0));
      expect(dist(scatterA, scatterB)).toBeLessThan(dist(scatterA, line));
    });

    it('surfaces an HTTP error and keeps the graph empty', async () => {
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }));
      const { result } = renderHook(() => useForceGraphSimulation());

      await waitFor(() => expect(result.current.error).toBe('HTTP 500'));
      expect(result.current.specs).toBeNull();
      expect(result.current.graphData.nodes).toHaveLength(0);
      expect(result.current.graphData.links).toHaveLength(0);
    });
  });

  describe('similarity weight handling', () => {
    it('activeCategory follows the highest weight and falls back to plot_type', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();

      // Defaults privilege plot_type (2.0).
      expect(result.current.activeCategory).toBe('plot_type');

      // Bump features above plot_type — legend buckets switch category.
      act(() => {
        result.current.setWeights(w => ({ ...w, features: 3 }));
      });
      expect(result.current.activeCategory).toBe('features');
      expect(result.current.graphData.topTypes).toContain('basic');

      // All-zero weights fall back to plot_type.
      const zeroWeights = Object.fromEntries(TAG_CATEGORIES.map(c => [c, 0])) as Record<
        TagCategory,
        number
      >;
      act(() => {
        result.current.setWeights(zeroWeights);
      });
      expect(result.current.activeCategory).toBe('plot_type');
    });

    it('drops KNN edges when minSim rises above the pair similarity', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();

      expect(result.current.graphData.links).toHaveLength(1);
      act(() => {
        result.current.setMinSim(0.6);
      });
      expect(result.current.graphData.links).toHaveLength(0);
    });

    it('preserves node positions and image caches across weight changes', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();

      // Simulate FG2D having ticked the layout (position mutation) and a
      // thumbnail having loaded into the per-node image cache.
      const before = result.current.graphData.nodes.find(
        n => n.id === 'scatter-basic'
      )! as SeededNode;
      before.x = 1234;
      const fakeImg = { src: 'x' } as unknown as HTMLImageElement;
      before.imgs.set(400, fakeImg);

      act(() => {
        result.current.setWeights(w => ({ ...w, techniques: 1 }));
      });

      const after = result.current.graphData.nodes.find(
        n => n.id === 'scatter-basic'
      )! as SeededNode;
      // Fresh node object per derivation, but warm-started from the cache:
      // last position and the loaded HTMLImageElements survive the re-derive
      // (otherwise every slider tick would flicker all thumbnails).
      expect(after).not.toBe(before);
      expect(after.x).toBe(1234);
      expect(after.imgs).toBe(before.imgs);
      expect(after.imgs.get(400)).toBe(fakeImg);
    });

    it('resetWeights restores the default weights and edge threshold', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();
      const initialMinSim = result.current.minSim;

      act(() => {
        result.current.setWeights(w => ({ ...w, domain: 4 }));
        result.current.setMinSim(0.4);
      });
      expect(result.current.weights.domain).toBe(4);
      expect(result.current.minSim).toBe(0.4);

      act(() => {
        result.current.resetWeights();
      });
      expect(result.current.weights).toEqual(DEFAULT_CATEGORY_WEIGHT);
      expect(result.current.minSim).toBe(initialMinSim);
    });
  });

  describe('settling gate', () => {
    it('settles via markSettled and re-arms when the graph re-derives', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();

      // Still cooling after the initial derive.
      expect(result.current.settled).toBe(false);

      act(() => {
        result.current.markSettled();
      });
      expect(result.current.settled).toBe(true);

      // A weight change re-derives graphData → the gate must re-arm and the
      // progress bar must restart from zero for the new cooling phase.
      act(() => {
        for (let i = 0; i < 6; i++) result.current.handleEngineTick();
      });
      expect(result.current.tickProgress).toBeGreaterThan(0);
      act(() => {
        result.current.setWeights(w => ({ ...w, features: 2 }));
      });
      expect(result.current.settled).toBe(false);
      expect(result.current.tickProgress).toBe(0);
    });

    it('throttles tick progress to every 6th engine tick', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();

      act(() => {
        for (let i = 0; i < 5; i++) result.current.handleEngineTick();
      });
      // No flush before the batch boundary — the page must not re-render at 60 Hz.
      expect(result.current.tickProgress).toBe(0);

      act(() => {
        result.current.handleEngineTick();
      });
      // 6 of 300 cooldown ticks → 2 %.
      expect(result.current.tickProgress).toBeCloseTo(0.02, 5);
    });
  });

  describe('search matching', () => {
    it('matches every token against title, id and tags, best score first', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();

      expect(result.current.searchMatches).toEqual([]);

      act(() => {
        result.current.setSearchQuery('scatter');
      });
      // Both scatters title-match (score ties) → alphabetical title order.
      expect(result.current.searchMatches.map(s => s.id)).toEqual([
        'scatter-basic',
        'scatter-color-mapped',
      ]);

      // Multi-token queries require every token to match somewhere.
      act(() => {
        result.current.setSearchQuery('scatter color');
      });
      expect(result.current.searchMatches.map(s => s.id)).toEqual(['scatter-color-mapped']);

      // Tag-only hits still match (dependencies:scipy comes from impl_tags).
      act(() => {
        result.current.setSearchQuery('scipy');
      });
      expect(result.current.searchMatches.map(s => s.id).sort()).toEqual([
        'scatter-basic',
        'scatter-color-mapped',
      ]);
    });
  });

  describe('force configuration', () => {
    it('scales link distance/strength with similarity and caps the pull', async () => {
      mockFetchSuccess();
      const { result } = await renderLoadedHook();
      const { forceConfig } = result.current;

      // Higher similarity → shorter link (tighter cluster).
      expect(forceConfig.linkDistance({ source: 'a', target: 'b', weight: 1 })).toBeLessThan(
        forceConfig.linkDistance({ source: 'a', target: 'b', weight: 0.1 })
      );
      // Strength is capped at 0.4 and floored at 0.02.
      expect(forceConfig.linkStrength({ source: 'a', target: 'b', weight: 5 })).toBe(0.4);
      expect(forceConfig.linkStrength({ source: 'a', target: 'b', weight: 0 })).toBe(0.02);
      // Engine props are wired through as positive tuned values.
      expect(forceConfig.cooldownTicks).toBeGreaterThan(0);
      expect(forceConfig.alphaDecay).toBeGreaterThan(0);
      expect(forceConfig.alphaMin).toBeGreaterThan(0);
      expect(forceConfig.velocityDecay).toBeGreaterThan(0);
    });
  });

  describe('outlierSquashForce', () => {
    // Pure unit tests that exercise the force math directly. We bypass the
    // d3-force harness because the force's contract is "modify vx/vy of
    // outlier nodes in place"; the harness adds nothing beyond invoking
    // force(alpha) and force.initialize(nodes).
    type Sim = SimNode & { x: number; y: number; vx: number; vy: number };
    const makeNode = (x: number, y: number): Sim => ({ x, y, vx: 0, vy: 0 });

    it('is a no-op when there are no nodes', () => {
      const force = outlierSquashForce(0.95, 200, 0.18);
      // initialize with empty array; force(alpha) must not throw.
      (force as unknown as { initialize: (n: SimNode[]) => void }).initialize([]);
      expect(() => force(1)).not.toThrow();
    });

    it('is a no-op for graphs of fewer than 2 nodes', () => {
      const force = outlierSquashForce(0.95, 200, 0.18);
      const nodes: Sim[] = [makeNode(1000, 0)];
      (force as unknown as { initialize: (n: SimNode[]) => void }).initialize(nodes);
      force(1);
      expect(nodes[0].vx).toBe(0);
      expect(nodes[0].vy).toBe(0);
    });

    it('leaves nodes inside the threshold untouched (inner geometry preserved)', () => {
      // 99 inner nodes co-located at the origin + 1 far outlier. All inner
      // distances to the centroid are exactly equal, so the percentile
      // cutoff R lands exactly at the inner radius and the early
      // `r <= R → continue` short-circuit fires for every inner node.
      // The outlier is the only node above R.
      const force = outlierSquashForce(0.95, 200, 0.18);
      const inner: Sim[] = Array.from({ length: 99 }, () => makeNode(0, 0));
      const outlier = makeNode(5000, 0);
      const nodes: Sim[] = [...inner, outlier];
      (force as unknown as { initialize: (n: SimNode[]) => void }).initialize(nodes);
      force(1);
      for (const n of inner) {
        expect(n.vx).toBe(0);
        expect(n.vy).toBe(0);
      }
      // Outlier was pulled inward — vx is opposite-sign to its position.
      expect(outlier.vx).toBeLessThan(0);
      expect(outlier.vy).toBe(0);
    });

    it('still squashes outliers in small graphs (off-by-one regression guard)', () => {
      // Naive `floor(length * p)` would pick index 19 (the max) on n = 20
      // and never trigger the squash. The (n - 1) * p indexing must keep
      // at least the most-outlying node above R.
      const force = outlierSquashForce(0.95, 200, 0.18);
      const nodes: Sim[] = Array.from({ length: 20 }, (_, i) => makeNode(i, 0));
      // Push the last node much further so it's the unambiguous outlier.
      nodes[19] = makeNode(10_000, 0);
      (force as unknown as { initialize: (n: SimNode[]) => void }).initialize(nodes);
      force(1);
      // The outlier must have a non-zero inward correction.
      expect(nodes[19].vx).not.toBe(0);
      expect(nodes[19].vx).toBeLessThan(0);
    });

    it('keeps the velocity correction finite even for distant outliers', () => {
      // The compression map r' = R + (r - R)/(1 + (r - R)/k) has an
      // asymptote at R + k, so even a node at distance 1e6 produces a
      // bounded velocity correction. This is the property that prevents
      // a single rogue node from blowing up the simulation.
      const force = outlierSquashForce(0.95, 200, 0.18);
      const inner: Sim[] = Array.from({ length: 99 }, () => makeNode(0, 0));
      const far = makeNode(1_000_000, 0);
      const nodes: Sim[] = [...inner, far];
      (force as unknown as { initialize: (n: SimNode[]) => void }).initialize(nodes);
      force(1);
      expect(far.vx).toBeLessThan(0);
      expect(Number.isFinite(far.vx)).toBe(true);
      // |vx| upper bound: |position - 0| * strength * alpha = 1e6 * 0.18.
      // The actual value is much smaller because (targetR - r) / r is
      // close to -1 once r >> R, so the correction approaches -position.
      expect(Math.abs(far.vx)).toBeLessThan(1_000_000);
    });

    it('scales the velocity correction with alpha', () => {
      const force = outlierSquashForce(0.95, 200, 0.18);
      const inner: Sim[] = Array.from({ length: 99 }, () => makeNode(0, 0));
      const hot = makeNode(5_000, 0);
      const cool = makeNode(5_000, 0);
      // First simulation — alpha = 1 (hot).
      (force as unknown as { initialize: (n: SimNode[]) => void }).initialize([...inner, hot]);
      force(1);
      // Second simulation — alpha = 0.1 (cooling).
      const force2 = outlierSquashForce(0.95, 200, 0.18);
      const inner2: Sim[] = Array.from({ length: 99 }, () => makeNode(0, 0));
      (force2 as unknown as { initialize: (n: SimNode[]) => void }).initialize([...inner2, cool]);
      force2(0.1);
      // Cooler alpha → ~10× smaller velocity correction.
      expect(Math.abs(hot.vx)).toBeGreaterThan(Math.abs(cool.vx) * 5);
    });
  });
});
