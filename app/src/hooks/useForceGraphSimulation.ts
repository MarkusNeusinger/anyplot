/**
 * useForceGraphSimulation — data + simulation-state orchestration for the
 * /map page's force-directed graph: spec loading, per-category similarity
 * weights, the KNN graph derivation (nodes / links / legend buckets), the
 * settling gate that swallows pointer input while the layout cools, search
 * matching over the loaded specs, and the tuned d3-force configuration.
 *
 * Deliberately NOT coupled to ForceGraph2D's imperative ref API: the view
 * (MapPage) keeps the canvas element, the paint callbacks, and every
 * handler that needs the graph ref (camera fit, force wiring, refresh).
 * The hook returns plain state + setters/handlers for the view to wire up;
 * the one inversion of control is `onRepaint`, a callback fired whenever a
 * thumbnail finishes loading so the view can trigger a canvas repaint.
 */

import { type Dispatch, type SetStateAction, useEffect, useMemo, useRef, useState } from 'react';

import { type Force, forceCollide } from 'd3-force-3d';

import { useTheme } from 'src/hooks/useLayoutContext';
import { ApiError, apiGet, endpoints } from 'src/lib/api';
import {
  buildKNNLinks,
  categoryValueCounts,
  computeIDF,
  DEFAULT_CATEGORY_WEIGHT,
  flattenTags,
  type MapLink,
  type MapNode,
  preloadImages,
  primaryCategoryValue,
  selectMapThumbUrl,
  type SpecMapItem,
  TAG_CATEGORIES,
  type TagCategory,
  topCategoryValues,
} from 'src/pages/MapPage.helpers';

export const NODE_SIZE = 60; // graph-space size of a node — large enough to read the thumbnail without hovering
const COOLDOWN_TICKS = 300; // simulation lifetime in ticks; the engine cap and alpha-decay below both derive from this so they stop together
// Stop the engine while motion is still perceptible. With d3-force's default
// alphaMin (0.001), alpha keeps decaying for ~150 more ticks after movement
// drops below the visible threshold (alpha ≈ 0.01) — that tail is dead time
// for the user. We bump alphaMin to 0.01 so engine-stop coincides with where
// the layout already looks frozen.
const COOLDOWN_ALPHA_MIN = 0.01;
// Couple alpha decay to COOLDOWN_TICKS so the engine stops exactly when the
// progress bar (denominated in COOLDOWN_TICKS) reaches 100%. Without this,
// alpha hits alphaMin before the bar is full and the "map.simulate()"
// overlay fades out with the bar still partway across.
//   alpha(n) = (1 - decay)^n  →  solve (1 - decay)^COOLDOWN_TICKS = alphaMin.
const COOLDOWN_ALPHA_DECAY = 1 - Math.pow(COOLDOWN_ALPHA_MIN, 1 / COOLDOWN_TICKS);
const CLUSTER_SEED_RADIUS = 600; // distance from origin where each colorBucket cluster's centroid is initially placed
const CLUSTER_SEED_JITTER = 150; // per-node random offset around the cluster centroid — small enough to keep clusters identifiable, large enough that collision can settle them
const KNN_K = 8; // edges per node in the sparse KNN graph
// Default threshold tuned for the plot_type-dominant default. Bumped up
// from 0.05 because once secondary categories (features, techniques, …)
// have non-zero weight, common tags like `features:basic` create weak
// cross-cluster bridges in the 0.05–0.12 range that collapse the graph
// into one blob. At 0.15 those bridges drop out and clusters stay distinct.
// Exposed as a live slider in the weights panel for power users.
const DEFAULT_MIN_SIM = 0.15;
export const MIN_SIM_BOUNDS = { min: 0.05, max: 0.4, step: 0.01 } as const;
// Forces: tuned so KNN edges + collision shape the layout while many-body
// repulsion stays GENTLE — collision already enforces minimum spacing, and
// strong repulsion would just blow the graph wide enough that zoomToFit
// zooms out too far for thumbnails to be readable. Goal: graph extent stays
// small enough that zoomToFit displays nodes at a generous CSS-pixel size.
const REPULSION = -50; // forceManyBody strength
const LINK_DISTANCE_MIN = NODE_SIZE * 1.1; // shortest link (highest sim)
const LINK_DISTANCE_MAX = NODE_SIZE * 3.5; // longest link (lowest sim above threshold)
const LINK_STRENGTH_CAP = 0.4; // max pull from a single link
const COLLIDE_PADDING = 6; // px padding on top of the bounding-box radius — visible breathing room between thumbnails
const CENTER_GRAVITY = 0.04; // gentle pull toward the viewport center; ~25× weaker than d3-force-3d's default to corral outliers without flattening clusters
// Outlier-squash: a custom radial force that activates only beyond a
// distance percentile of the centroid. Inside the threshold, geometry
// is untouched — the inner cluster keeps its exact shape. Outside, each
// outlier's distance is compressed via a sigmoid-like map
//     r' = R + (r - R) / (1 + (r - R) / k)
// so far-flung points stay visibly *separate* (their order is preserved)
// but bounded — the asymptote is R + k. This corrects the "everything
// collapses to a dot because of one runaway outlier" zoomToFit problem
// without needing stronger global gravity (which would crush clusters).
const OUTLIER_THRESHOLD_PERCENTILE = 0.95; // distance percentile beyond which compression starts
const OUTLIER_SQUASH_K = 120; // graph-units of extra room outliers can use beyond R; smaller = harder squash
const OUTLIER_SQUASH_STRENGTH = 0.18; // velocity-correction factor; tuned so outliers settle within COOLDOWN_TICKS

// Top-N most frequent plot_types each get a distinct imprint border color
// so the catalog's biggest categories (line, scatter, bar, …) stand out at
// a glance. Specs that don't fall into the top-N keep a neutral border.
// 8 categorical hues in imprint's hybrid-v3 sort order.
export const CLUSTER_COLORS = [
  '#009E73', // slot 0 — brand green
  '#C475FD', // slot 1 — lavender
  '#4467A3', // slot 2 — blue
  '#BD8233', // slot 3 — ochre
  '#AE3030', // slot 4 — matte red
  '#2ABCCD', // slot 5 — cyan
  '#954477', // slot 6 — rose
  '#99B314', // slot 7 — lime
] as const;

export function colorFor(bucket: string | null, topTypes: string[]): string | null {
  if (!bucket) return null;
  const idx = topTypes.indexOf(bucket);
  if (idx < 0) return null;
  return CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
}

// Custom d3-force that compresses extreme outliers radially toward the
// cluster centroid while leaving inner geometry untouched. See the block
// comment on OUTLIER_THRESHOLD_PERCENTILE for the math; this is the
// implementation. The simulation calls force(alpha) every tick, alpha
// decays from 1 → 0, so the velocity correction tapers off as the layout
// cools — the force is *active* during the same window the gate covers,
// then becomes a no-op once outliers are at their compressed targets.
// Exported for unit tests — the simulation only ever calls this through
// d3-force's `force(alpha)` interface, so the public surface is internal.
export type SimNode = { x?: number; y?: number; vx?: number; vy?: number };
export function outlierSquashForce(percentile: number, k: number, strength: number) {
  let nodes: SimNode[] = [];
  function force(alpha: number) {
    if (nodes.length === 0) return;
    let cx = 0,
      cy = 0,
      n = 0;
    for (const node of nodes) {
      if (node.x == null || node.y == null) continue;
      cx += node.x;
      cy += node.y;
      n++;
    }
    if (n === 0) return;
    cx /= n;
    cy /= n;
    // One pass to compute distances; second pass to apply velocity
    // adjustment to outliers. Allocating a fresh array per tick is fine
    // at ~300 nodes (~3 µs); we'd only avoid it at 10k+.
    const dists: number[] = new Array(nodes.length);
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      if (node.x == null || node.y == null) {
        dists[i] = 0;
        continue;
      }
      dists[i] = Math.hypot(node.x - cx, node.y - cy);
    }
    const sorted = dists.slice().sort((a, b) => a - b);
    // Use the (length - 1) * p index (numpy "linear" / "lower" interpolation
    // for a discrete percentile). The naive `length * p` rounds up to
    // `length - 1` for any n ≤ 1/(1-p) — i.e. with p = 0.95 and n ≤ 20 the
    // cutoff would be the *max* distance and the squash force would silently
    // disable itself. Filtered subsets of the catalog can easily land in
    // that range, so we never want the cutoff to coincide with the maximum.
    if (sorted.length < 2) return;
    const idx = Math.floor((sorted.length - 1) * percentile);
    const R = sorted[idx];
    if (!(R > 0)) return;
    for (let i = 0; i < nodes.length; i++) {
      const r = dists[i];
      if (r <= R) continue;
      const node = nodes[i];
      if (node.x == null || node.y == null) continue;
      const excess = r - R;
      const compressed = excess / (1 + excess / k);
      const targetR = R + compressed;
      const factor = (targetR - r) / r; // negative — pulls toward the centroid
      const dx = node.x - cx;
      const dy = node.y - cy;
      node.vx = (node.vx ?? 0) + dx * factor * strength * alpha;
      node.vy = (node.vy ?? 0) + dy * factor * strength * alpha;
    }
  }
  force.initialize = (n: SimNode[]) => {
    nodes = n;
  };
  return force;
}

/** Everything the graph derivation produces in one pass. */
export interface MapGraphData {
  nodes: MapNode[];
  links: MapLink[];
  topTypes: string[];
  typeCounts: Map<string, number>;
  idf: Map<string, number>;
}

/**
 * The tuned force-simulation parameters MapPage forwards to ForceGraph2D
 * (engine props + the d3 forces it wires up in onRenderFramePre). Plain
 * values and factories — nothing here touches the imperative graph ref.
 */
export interface MapForceConfig {
  cooldownTicks: number;
  alphaDecay: number;
  alphaMin: number;
  velocityDecay: number;
  chargeStrength: number;
  linkDistance: (l: MapLink) => number;
  linkStrength: (l: MapLink) => number;
  centerGravity: number;
  createCollideForce: () => Force<MapNode>;
  createOutlierSquashForce: () => ReturnType<typeof outlierSquashForce>;
}

// Static by construction — a single frozen object keeps the identity stable
// across renders so consumers can safely list it in dependency arrays.
const FORCE_CONFIG: MapForceConfig = {
  cooldownTicks: COOLDOWN_TICKS,
  alphaDecay: COOLDOWN_ALPHA_DECAY,
  alphaMin: COOLDOWN_ALPHA_MIN,
  velocityDecay: 0.35,
  // Stronger many-body repulsion than the default ~-30.
  chargeStrength: REPULSION,
  // Link distance/strength scale with weighted-Jaccard similarity:
  // tighter clusters for highly related specs, looser otherwise.
  linkDistance: (l: MapLink) => {
    const w = l.weight ?? 0.3;
    return LINK_DISTANCE_MIN + (1 - Math.min(1, w)) * (LINK_DISTANCE_MAX - LINK_DISTANCE_MIN);
  },
  linkStrength: (l: MapLink) =>
    Math.max(0.02, Math.min(LINK_STRENGTH_CAP, (l.weight ?? 0.3) * 0.4)),
  // Mild centering force so disconnected outliers (no KNN edges because all
  // sims < threshold) drift back toward the cluster mass instead of
  // vanishing to the corners. Strength is well below the default 1.0 so
  // cluster shapes stay intact.
  centerGravity: CENTER_GRAVITY,
  // Per-node collision: prevents thumbnail overlap. Radius = half the longer
  // side of the bounding box plus a small padding.
  createCollideForce: () =>
    forceCollide<MapNode>(() => NODE_SIZE / 2 + COLLIDE_PADDING).iterations(2),
  createOutlierSquashForce: () =>
    outlierSquashForce(OUTLIER_THRESHOLD_PERCENTILE, OUTLIER_SQUASH_K, OUTLIER_SQUASH_STRENGTH),
};

export interface UseForceGraphSimulationOptions {
  /**
   * Fired whenever a node thumbnail finishes loading so the view can repaint
   * the canvas (MapPage passes `() => fgRef.current?.refresh?.()`). Held in a
   * ref internally, so an inline arrow is fine — it never re-runs effects.
   */
  onRepaint?: () => void;
}

export interface ForceGraphSimulation {
  specs: SpecMapItem[] | null;
  error: string | null;
  weights: Record<TagCategory, number>;
  setWeights: Dispatch<SetStateAction<Record<TagCategory, number>>>;
  minSim: number;
  setMinSim: Dispatch<SetStateAction<number>>;
  /** Reset weights + edge threshold back to the tuned defaults. */
  resetWeights: () => void;
  activeCategory: TagCategory;
  graphData: MapGraphData;
  nodeById: Map<string, MapNode>;
  neighbors: Map<string, Set<string>>;
  settled: boolean;
  /** Flip the settling gate once the engine reports it stopped. */
  markSettled: () => void;
  tickProgress: number;
  /** Forward ForceGraph2D's onEngineTick here to drive the progress bar. */
  handleEngineTick: () => void;
  searchQuery: string;
  setSearchQuery: Dispatch<SetStateAction<string>>;
  searchMatches: SpecMapItem[];
  forceConfig: MapForceConfig;
}

export function useForceGraphSimulation({
  onRepaint,
}: UseForceGraphSimulationOptions = {}): ForceGraphSimulation {
  const { isDark } = useTheme();

  // data state
  const [specs, setSpecs] = useState<SpecMapItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Per-category weight overrides for the similarity calculation. Bound to
  // the weights panel sliders. Live-updates KNN edges + simulation on change.
  const [weights, setWeights] = useState<Record<TagCategory, number>>(DEFAULT_CATEGORY_WEIGHT);
  const [minSim, setMinSim] = useState<number>(DEFAULT_MIN_SIM);
  // settled = true once the force simulation has finished cooling. Until
  // then, the canvas is overlaid by a subtle gate that swallows pointer
  // input — a click on a still-moving node would otherwise pin the wrong
  // spec by the time the simulation settles around it. Resets to false
  // whenever graphData re-derives (filter / weight / category change), so
  // the gate also covers subsequent re-layouts.
  const [settled, setSettled] = useState(false);
  // Throttled tick counter for the "computing" overlay's progress bar.
  // We update React state at most every PROGRESS_TICK_BATCH simulation
  // ticks to avoid re-rendering the page at ~60 Hz while the layout cools.
  // tickCountRef holds the un-throttled count so we know when to flush.
  const tickCountRef = useRef(0);
  const [tickProgress, setTickProgress] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  // Keep the latest onRepaint without making it an effect dependency — the
  // preload effect must re-run on graphData changes only, and callers pass
  // inline arrows. Render-time ref writes are permitted by the project's
  // eslint config (`react-hooks/refs: off`): idempotent, pre-commit.
  const onRepaintRef = useRef(onRepaint);
  onRepaintRef.current = onRepaint;

  // 1. fetch the map payload once on mount
  useEffect(() => {
    const ctrl = new AbortController();
    apiGet<SpecMapItem[]>(endpoints.specsMap, { signal: ctrl.signal })
      .then(setSpecs)
      .catch((err: unknown) => {
        if (err instanceof Error && err.name === 'AbortError') return;
        // Keep the pre-migration user-visible message ("HTTP <status>") rather
        // than surfacing the longer ApiError format in the error banner.
        if (err instanceof ApiError) setError(`HTTP ${err.status}`);
        else setError(err instanceof Error ? err.message : 'Failed to load map data');
      });
    return () => ctrl.abort();
  }, []);

  // The category that drives the legend + node border colors: whichever
  // currently has the highest weight (plot_type wins on ties because it's
  // the first entry of TAG_CATEGORIES and we use strictly-greater compare).
  // Falls back to plot_type when all weights are 0.
  const activeCategory: TagCategory = useMemo(() => {
    let maxWeight = -Infinity;
    let active: TagCategory = 'plot_type';
    for (const c of TAG_CATEGORIES) {
      if (weights[c] > maxWeight) {
        maxWeight = weights[c];
        active = c;
      }
    }
    return maxWeight > 0 ? active : 'plot_type';
  }, [weights]);

  // graphData rebuilds whenever weights/minSim/activeCategory change
  // (because links + colorBucket depend on them). Without this cache, every
  // slider-drag tick would recreate every MapNode with empty imgs/pendingTiers
  // Maps, dropping the loaded HTMLImageElements — the canvas would then paint
  // fallback rects until each <img> re-fires onload, producing a visible
  // flicker across all 327 thumbnails on every onChange tick. We keep a
  // stable id → MapNode cache here and reuse imgs/pendingTiers as long as
  // thumbUrl is unchanged (theme toggle invalidates).
  const nodeCacheRef = useRef<Map<string, MapNode>>(new Map());

  // 2. derive graph data from specs/theme (pure — no setState in effect)
  const graphData = useMemo<MapGraphData>(() => {
    if (!specs) {
      return { nodes: [], links: [], topTypes: [], typeCounts: new Map(), idf: new Map() };
    }
    const idf = computeIDF(specs);
    const topTypes = topCategoryValues(specs, activeCategory, CLUSTER_COLORS.length);
    const typeCounts = categoryValueCounts(specs, activeCategory);
    const cache = nodeCacheRef.current;
    const nextCache = new Map<string, MapNode>();
    // Pre-compute one centroid per colorBucket on a circle around the origin.
    // Seeding each node near its cluster centroid (instead of the FG2D
    // default of random positions everywhere) gives the simulation a warm
    // start: clusters don't have to first separate from a uniform soup, and
    // the same number of cooldown ticks now produces visibly cleaner
    // separation. Null-bucket nodes sit at the origin and let the link force
    // pull them toward whatever clusters they connect to.
    const clusterCentroids = new Map<string, { x: number; y: number }>();
    topTypes.forEach((t, i) => {
      const angle = (i / topTypes.length) * Math.PI * 2;
      clusterCentroids.set(t, {
        x: Math.cos(angle) * CLUSTER_SEED_RADIUS,
        y: Math.sin(angle) * CLUSTER_SEED_RADIUS,
      });
    });
    // Hash-based jitter so seed positions are stable across re-renders for
    // the same spec id — avoids reshuffling on filter changes.
    const jitter = (id: string, salt: number) => {
      let h = salt;
      for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) | 0;
      return ((h & 0xffff) / 0xffff - 0.5) * 2 * CLUSTER_SEED_JITTER;
    };
    const nodes: (MapNode & { x?: number; y?: number; vx?: number; vy?: number })[] = specs.map(
      s => {
        const v = primaryCategoryValue(s, activeCategory);
        const colorBucket = topTypes.includes(v) ? v : null;
        const thumbUrl = selectMapThumbUrl(s, isDark);
        const cached = cache.get(s.id) as
          | (MapNode & { x?: number; y?: number; vx?: number; vy?: number })
          | undefined;
        const reuse = cached && cached.thumbUrl === thumbUrl;
        // Warm-start preference: keep the simulation's last x/y if we have it
        // (filter / weight tweaks reuse positions and refine in place). Cold
        // start: seed from the cluster centroid + stable per-id jitter.
        const seedCenter = colorBucket ? clusterCentroids.get(colorBucket) : null;
        const x = cached?.x ?? (seedCenter ? seedCenter.x + jitter(s.id, 1) : jitter(s.id, 3));
        const y = cached?.y ?? (seedCenter ? seedCenter.y + jitter(s.id, 2) : jitter(s.id, 5));
        const node: MapNode & { x: number; y: number; vx: number; vy: number } = {
          id: s.id,
          title: s.title,
          tags: flattenTags(s),
          colorBucket,
          thumbUrl,
          imgs: reuse ? cached!.imgs : new Map(),
          pendingTiers: reuse ? cached!.pendingTiers : new Set(),
          x,
          y,
          vx: cached?.vx ?? 0,
          vy: cached?.vy ?? 0,
        };
        nextCache.set(s.id, node);
        return node;
      }
    );
    nodeCacheRef.current = nextCache;
    const links = buildKNNLinks(specs, idf, KNN_K, minSim, weights);
    return { nodes, links, topTypes, typeCounts, idf };
  }, [specs, isDark, weights, minSim, activeCategory]);

  // Re-arm the settling gate whenever graphData re-derives — FG2D reheats
  // the simulation in response, and we want the gate to cover the new
  // cooling phase the same way it covers the initial one. No-op on the
  // very first render (settled is already false) and while specs are
  // still loading.
  //
  // Implemented via the "store previous prop in state" pattern (see
  // https://react.dev/reference/react/useState#storing-information-from-previous-renders)
  // instead of useEffect: React supports calling setState during render of
  // the *same* component, batches the updates, and re-renders once before
  // commit — no infinite loop, and the rule that bans setState in effects
  // doesn't apply to setState during render.
  const [prevGraphData, setPrevGraphData] = useState(graphData);
  if (graphData !== prevGraphData) {
    setPrevGraphData(graphData);
    if (graphData.nodes.length > 0) {
      setSettled(false);
      setTickProgress(0);
      tickCountRef.current = 0;
    }
  }

  // Eager-load the 400-tier thumbnails so something paints fast. Higher tiers
  // are fetched lazily from nodeCanvasObject when the user zooms in.
  useEffect(() => {
    if (graphData.nodes.length === 0) return;
    const nodeById = new Map(graphData.nodes.map(n => [n.id, n]));
    let cancelled = false;
    preloadImages(
      graphData.nodes.map(n => ({ id: n.id, thumbUrl: n.thumbUrl })),
      (id, tier, img) => {
        if (cancelled) return;
        const n = nodeById.get(id);
        if (n) n.imgs.set(tier, img);
        onRepaintRef.current?.();
      }
    );
    return () => {
      cancelled = true;
    };
  }, [graphData]);

  // 3. neighbor lookup for hover highlight (built once per links change)
  // Precomputed id → node lookup. linkColor/linkWidth fire once per link
  // per frame (~1k links), and a graphData.nodes.find() inside each call
  // would be O(N²) total per frame; the Map keeps it O(1).
  const nodeById = useMemo(() => {
    const map = new Map<string, MapNode>();
    for (const n of graphData.nodes) map.set(n.id, n);
    return map;
  }, [graphData.nodes]);

  const neighbors = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const l of graphData.links) {
      if (!map.has(l.source)) map.set(l.source, new Set());
      if (!map.has(l.target)) map.set(l.target, new Set());
      map.get(l.source)!.add(l.target);
      map.get(l.target)!.add(l.source);
    }
    return map;
  }, [graphData.links]);

  // 4. Precompute lowercased searchable fields per spec so each keystroke
  //    only does .includes() checks, not a fresh tag-flatten + lowercase.
  const searchHaystacks = useMemo(() => {
    if (!specs) return [];
    return specs.map(s => ({
      spec: s,
      titleL: s.title.toLowerCase(),
      idL: s.id.toLowerCase(),
      tagsL: flattenTags(s).map(t => t.toLowerCase()),
    }));
  }, [specs]);

  // 5. Match the search query: every whitespace-separated token must appear
  //    somewhere (title / id / tag), score weighted by where it hit. Top 8.
  const searchMatches = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    const tokens = q.split(/\s+/).filter(Boolean);
    const scored: { spec: SpecMapItem; score: number }[] = [];
    for (const h of searchHaystacks) {
      let score = 0;
      let allMatch = true;
      for (const tok of tokens) {
        const inTitle = h.titleL.includes(tok);
        const inId = h.idL.includes(tok);
        const inTags = h.tagsL.some(t => t.includes(tok));
        if (!(inTitle || inId || inTags)) {
          allMatch = false;
          break;
        }
        score += inTitle ? 3 : inId ? 2 : 1;
      }
      if (allMatch) scored.push({ spec: h.spec, score });
    }
    scored.sort((a, b) => b.score - a.score || a.spec.title.localeCompare(b.spec.title));
    return scored.slice(0, 8).map(x => x.spec);
  }, [searchQuery, searchHaystacks]);

  const markSettled = () => setSettled(true);

  // Drive the loading-overlay progress bar. Each simulation tick bumps the
  // un-throttled ref; we flush to React state every PROGRESS_TICK_BATCH
  // ticks (~5×/s at 60 Hz) so the bar advances smoothly without
  // re-rendering the page on every tick.
  const handleEngineTick = () => {
    tickCountRef.current += 1;
    const PROGRESS_TICK_BATCH = 6;
    if (tickCountRef.current % PROGRESS_TICK_BATCH === 0) {
      setTickProgress(Math.min(1, tickCountRef.current / COOLDOWN_TICKS));
    }
  };

  const resetWeights = () => {
    setWeights(DEFAULT_CATEGORY_WEIGHT);
    setMinSim(DEFAULT_MIN_SIM);
  };

  return {
    specs,
    error,
    weights,
    setWeights,
    minSim,
    setMinSim,
    resetWeights,
    activeCategory,
    graphData,
    nodeById,
    neighbors,
    settled,
    markSettled,
    tickProgress,
    handleEngineTick,
    searchQuery,
    setSearchQuery,
    searchMatches,
    forceConfig: FORCE_CONFIG,
  };
}
