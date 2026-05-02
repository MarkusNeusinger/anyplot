import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import useMediaQuery from '@mui/material/useMediaQuery';
import Slider from '@mui/material/Slider';
import Typography from '@mui/material/Typography';
import ForceGraph2D from 'react-force-graph-2d';
import { forceCollide } from 'd3-force-3d';

import { API_URL } from '../constants';
import { useAnalytics } from '../hooks';
import { useTheme } from '../hooks/useLayoutContext';
import { specPath } from '../utils/paths';
import { colors, fontSize, typography } from '../theme';
import {
  buildKNNLinks,
  buildVariantUrl,
  categoryValueCounts,
  computeIDF,
  DEFAULT_CATEGORY_WEIGHT,
  ensureNodeTier,
  fitToBox,
  flattenTags,
  nodeAspectRatio,
  pickBestLoadedTier,
  pickTier,
  preloadImages,
  primaryCategoryValue,
  selectMapThumbUrl,
  TAG_CATEGORIES,
  topCategoryValues,
  type MapLink,
  type MapNode,
  type ResolutionTier,
  type SpecMapItem,
  type TagCategory,
} from './MapPage.helpers';


const NODE_SIZE = 60;            // graph-space size of a node — large enough to read the thumbnail without hovering
const COOLDOWN_TICKS = 450;       // a touch over the original 400 — just enough to let the slower alpha decay finish its work before the cap kicks in
const CLUSTER_SEED_RADIUS = 600;  // distance from origin where each colorBucket cluster's centroid is initially placed
const CLUSTER_SEED_JITTER = 150;  // per-node random offset around the cluster centroid — small enough to keep clusters identifiable, large enough that collision can settle them
const KNN_K = 8;                  // edges per node in the sparse KNN graph
// Default threshold tuned for the plot_type-dominant default. Bumped up
// from 0.05 because once secondary categories (features, techniques, …)
// have non-zero weight, common tags like `features:basic` create weak
// cross-cluster bridges in the 0.05–0.12 range that collapse the graph
// into one blob. At 0.15 those bridges drop out and clusters stay distinct.
// Exposed as a live slider in the weights panel for power users.
const DEFAULT_MIN_SIM = 0.15;
const MIN_SIM_BOUNDS = { min: 0.05, max: 0.4, step: 0.01 } as const;
// Forces: tuned so KNN edges + collision shape the layout while many-body
// repulsion stays GENTLE — collision already enforces minimum spacing, and
// strong repulsion would just blow the graph wide enough that zoomToFit
// zooms out too far for thumbnails to be readable. Goal: graph extent stays
// small enough that zoomToFit displays nodes at a generous CSS-pixel size.
const REPULSION = -50;            // forceManyBody strength
const LINK_DISTANCE_MIN = NODE_SIZE * 1.1;   // shortest link (highest sim)
const LINK_DISTANCE_MAX = NODE_SIZE * 3.5;   // longest link (lowest sim above threshold)
const LINK_STRENGTH_CAP = 0.4;    // max pull from a single link
const COLLIDE_PADDING = 6;        // px padding on top of the bounding-box radius — visible breathing room between thumbnails
const CENTER_GRAVITY = 0.04;      // gentle pull toward the viewport center; ~25× weaker than d3-force-3d's default to corral outliers without flattening clusters

// visually-hidden style — keeps the spec list readable for screen readers
// even though the canvas is the primary interface.
const visuallyHiddenSx = {
  position: 'absolute' as const,
  width: '1px',
  height: '1px',
  padding: 0,
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0, 0, 0, 0)',
  whiteSpace: 'nowrap' as const,
  border: 0,
};

// Top-N most frequent plot_types each get a distinct Okabe-Ito border color
// so the catalog's biggest categories (line, scatter, bar, …) stand out at
// a glance. Specs that don't fall into the top-N keep a neutral border.
// The palette has 7 categorical colors + an adaptive neutral as the 8th —
// here we use the 7 categorical ones; everything else stays uncolored.
const CLUSTER_COLORS = [
  '#009E73', // brand green
  '#D55E00', // vermillion
  '#0072B2', // blue
  '#CC79A7', // reddish purple
  '#E69F00', // orange
  '#56B4E9', // sky blue
  '#F0E442', // yellow
] as const;

function colorFor(bucket: string | null, topTypes: string[]): string | null {
  if (!bucket) return null;
  const idx = topTypes.indexOf(bucket);
  if (idx < 0) return null;
  return CLUSTER_COLORS[idx % CLUSTER_COLORS.length];
}

// Read a link endpoint's spec id regardless of whether ForceGraph2D has
// already mutated the field from a string into the resolved node object
// (it does so after the first simulation tick). All link-side comparisons
// must go through this helper or they silently break post-tick.
function linkEndId(end: MapLink['source']): string | undefined {
  if (typeof end === 'string') return end;
  return (end as { id?: string })?.id;
}

// Hairline border around a thumbnail node, theme-aware. Top-N plot types
// paint with a brand color; the rest fall back to a neutral hairline.
// On hover we keep the cluster color (or fall back to brand primary for
// non-bucketed nodes) so the frame doesn't suddenly turn green and clash
// with whatever color family the node belongs to.
function strokeFor(isDark: boolean, isHover: boolean, color: string | null): string {
  if (isHover) return color ?? colors.primary;
  if (color) return color;
  return isDark ? 'rgba(240,239,232,0.18)' : 'rgba(26,26,23,0.18)';
}


export function MapPage() {
  const { trackPageview, trackEvent } = useAnalytics();
  const { isDark } = useTheme();
  const navigate = useNavigate();

  // refs
  // ForceGraph2D's TypeScript surface for the imperative ref is non-trivial; the
  // generated types live in dist and aren't worth re-typing here. Treat as opaque.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // data state
  const [specs, setSpecs] = useState<SpecMapItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [size, setSize] = useState<{ w: number; h: number }>({ w: 0, h: 0 });
  const [hoverId, setHoverId] = useState<string | null>(null);
  // panelNodeId trails hoverId on mouse-out so the corner preview can fade
  // out while still showing the last node's content. It only updates to a
  // *new* node when hoverId becomes non-null.
  const [panelNodeId, setPanelNodeId] = useState<string | null>(null);
  // pinnedId persists a visual marker on the searched node so the user
  // doesn't lose track of it when the mouse drifts onto a different node
  // (which would otherwise overwrite hoverId and replace the panel content).
  // Cleared by clicking empty canvas or by triggering another search.
  const [pinnedId, setPinnedId] = useState<string | null>(null);
  // Screen-space rect of the pinned node, recomputed every frame while a
  // pin is active. Drives the DOM-overlay pulse marker — separate from the
  // canvas so a CSS @keyframes animation can drive the pulse independently
  // of FG2D's render loop (which pauses once the simulation cools down).
  const [pinScreen, setPinScreen] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  // ~100ms debounce so quick mouse-overs don't strobe the preview.
  const hoverTimerRef = useRef<number | null>(null);
  // hoverType = a plot_type the user is hovering in the legend; everything
  // not in that cluster dims so the cluster shape is obvious.
  const [hoverType, setHoverType] = useState<string | null>(null);
  // Per-category weight overrides for the similarity calculation. Bound to
  // the weights panel sliders. Live-updates KNN edges + simulation on change.
  const [weights, setWeights] = useState<Record<TagCategory, number>>(DEFAULT_CATEGORY_WEIGHT);
  const [minSim, setMinSim] = useState<number>(DEFAULT_MIN_SIM);
  const [weightsOpen, setWeightsOpen] = useState(false);
  // Mobile-only: legend collapses behind a `legend ▸` toggle to leave
  // canvas room. Tablet/desktop renders the legend list always-visible.
  const [legendOpen, setLegendOpen] = useState(false);
  // settled = true once the post-mount camera animation has finished. Until
  // then, the canvas is overlaid by a subtle gate that swallows pointer
  // input so a click during simulation/zoom can't be clobbered when the
  // camera then animates away from where the user tapped.
  const [settled, setSettled] = useState(false);

  // Search-pill state. searchOpen controls dropdown visibility (separate
  // from focus so we can keep showing matches briefly while a click is in
  // flight via the input's onBlur grace period).
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchIdx, setSearchIdx] = useState(0);
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  // 1. fetch + page view
  useEffect(() => {
    trackPageview('/map');
  }, [trackPageview]);

  useEffect(() => {
    const ctrl = new AbortController();
    fetch(`${API_URL}/specs/map`, { signal: ctrl.signal })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json() as Promise<SpecMapItem[]>;
      })
      .then(setSpecs)
      .catch(err => {
        if (err.name !== 'AbortError') setError(err.message ?? 'Failed to load map data');
      });
    return () => ctrl.abort();
  }, []);

  // 2. resize observer
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(entries => {
      const r = entries[0]?.contentRect;
      if (r) setSize({ w: r.width, h: r.height });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // Hover preview: when a new node becomes active, swap the panel content
  // immediately. When hover ends, fall back to the pinned spec (so the
  // searched node's details stay visible while the user looks around).
  // If neither hover nor pin is set, the previous content lingers in the
  // DOM but fades out via the opacity transition.
  useEffect(() => {
    if (hoverId) setPanelNodeId(hoverId);
    else if (pinnedId) setPanelNodeId(pinnedId);
  }, [hoverId, pinnedId]);

  // Clean up any pending hover-debounce timer on unmount.
  useEffect(() => {
    return () => {
      if (hoverTimerRef.current != null) {
        window.clearTimeout(hoverTimerRef.current);
      }
    };
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

  // 3. derive graph data from specs/theme (pure — no setState in effect)
  const graphData = useMemo<{
    nodes: MapNode[];
    links: MapLink[];
    topTypes: string[];
    typeCounts: Map<string, number>;
    idf: Map<string, number>;
  }>(() => {
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
    const nodes: (MapNode & { x?: number; y?: number; vx?: number; vy?: number })[] = specs.map(s => {
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
    });
    nodeCacheRef.current = nextCache;
    const links = buildKNNLinks(specs, idf, KNN_K, minSim, weights);
    return { nodes, links, topTypes, typeCounts, idf };
  }, [specs, isDark, weights, minSim, activeCategory]);

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
        fgRef.current?.refresh?.();
      }
    );
    return () => {
      cancelled = true;
    };
  }, [graphData]);

  // 4. neighbor lookup for hover highlight (built once per links change)
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

  // Track the pinned node's on-screen rect so the DOM-overlay pulse marker
  // stays glued to it while the user pans/zooms. Cheap (one RAF tick = a
  // graph→screen coord transform + a setState that no-ops on sub-pixel
  // diffs), no canvas repaint involved.
  useEffect(() => {
    if (!pinnedId) {
      setPinScreen(null);
      return;
    }
    let raf = 0;
    const tick = () => {
      const fg = fgRef.current;
      const node = nodeById.get(pinnedId) as
        | (MapNode & { x?: number; y?: number })
        | undefined;
      if (fg && node && node.x != null && node.y != null) {
        const sc = fg.graph2ScreenCoords?.(node.x, node.y);
        const z = typeof fg.zoom === 'function' ? fg.zoom() : 1;
        if (sc) {
          const { w: gw, h: gh } = fitToBox(NODE_SIZE, nodeAspectRatio(node));
          const w = gw * z;
          const h = gh * z;
          setPinScreen(prev => {
            const next = { x: sc.x - w / 2, y: sc.y - h / 2, w, h };
            if (
              prev &&
              Math.abs(prev.x - next.x) < 0.5 &&
              Math.abs(prev.y - next.y) < 0.5 &&
              Math.abs(prev.w - next.w) < 0.5 &&
              Math.abs(prev.h - next.h) < 0.5
            ) {
              return prev;
            }
            return next;
          });
        }
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [pinnedId, graphData]);

  // 5. derive everything the corner hover-panel needs from the (lagged)
  //    panelNodeId, so the panel can fade out without losing its content.
  const panelData = useMemo(() => {
    if (!panelNodeId) return null;
    const node = nodeById.get(panelNodeId);
    if (!node) return null;
    const ptTag = node.tags.find(t => t.startsWith('plot_type:'));
    const plotType = ptTag ? ptTag.slice('plot_type:'.length) : null;
    // Top 4 most distinctive tags by IDF, excluding plot_type (rendered as
    // chip) and zero-IDF noise (corpus-common tags zeroed out by computeIDF).
    const tags = node.tags
      .filter(t => !t.startsWith('plot_type:'))
      .map(t => ({ tag: t, w: graphData.idf.get(t) ?? 0 }))
      .filter(x => x.w > 0)
      .sort((a, b) => b.w - a.w)
      .slice(0, 4)
      .map(x => x.tag);
    return {
      title: node.title,
      plotType,
      chipColor: plotType ? colorFor(plotType, graphData.topTypes) : null,
      tags,
      // Prefer a higher-res variant for the panel — request 800-tier so the
      // preview looks crisp. The browser caches per-URL, so subsequent hovers
      // of the same node are instant.
      previewUrl: node.thumbUrl ? buildVariantUrl(node.thumbUrl, 800) : null,
    };
  }, [panelNodeId, graphData]);

  // Pulse colour: match the pinned node's natural cluster border so the
  // ring isn't a foreign green halo when the node itself is e.g. orange.
  // Top-N nodes (with a colorBucket) get their cluster color; specs that
  // fall outside the top-N (no colorBucket) fall back to the brand primary
  // for legibility against the neutral hairline border.
  const pinColor = useMemo(() => {
    if (!pinnedId) return colors.primary;
    const node = nodeById.get(pinnedId);
    if (!node) return colors.primary;
    return colorFor(node.colorBucket, graphData.topTypes) ?? colors.primary;
  }, [pinnedId, nodeById, graphData.topTypes]);

  // 6. Precompute lowercased searchable fields per spec so each keystroke
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

  // 7. Match the search query: every whitespace-separated token must appear
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

  // Reset the keyboard-cursor whenever the result list shrinks/reshuffles.
  useEffect(() => {
    setSearchIdx(0);
  }, [searchQuery]);

  // Cmd/Ctrl+K focuses the search pill from anywhere on the page. Always
  // preventDefault so the browser's own ⌘K (Chrome address bar) doesn't fire.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);


  // 5. ForceGraph2D callbacks. Types for ctx come from the wrapper's prop signature
  // when these are passed inline below — extracting them out would force us to spell
  // CanvasRenderingContext2D explicitly, which our eslint config doesn't recognize.
  type WithCoords = MapNode & { x?: number; y?: number };

  // Detect whether the device has a real hover-capable pointer (mouse,
  // trackpad). Touch-only devices never fire onNodeHover, so without this
  // check tapping a node would jump straight to the spec page — losing
  // the preview-panel + pin UX entirely. On touch, we delay navigation
  // until the *second* tap on the same node.
  const hasHover = useMediaQuery('(hover: hover)', { noSsr: true });

  const onNodeClick = (node: MapNode) => {
    // Belt-and-braces guard: the overlay already swallows pointer events
    // while the camera is animating, but ForceGraph2D may have buffered a
    // tap that landed just before the gate appeared.
    if (!settled) return;
    if (!hasHover && pinnedId !== node.id) {
      // Touch device, first tap on a fresh node: pin + open panel — same
      // semantics as desktop hover. We deliberately don't fly/zoom: the
      // user already sees where they tapped, and zooming in would make
      // the on-canvas thumbnail roughly the same size as the panel preview,
      // defeating the panel's purpose. Background tap clears the pin.
      setPinnedId(node.id);
      setHoverId(node.id);
      trackEvent('map_node_pin', { spec: node.id });
      return;
    }
    trackEvent('map_node_click', { spec: node.id });
    navigate(specPath(node.id));
  };

  // Fly the camera to a node and open its hover panel. Used by the search
  // dropdown when the user picks a result. Does nothing until the simulation
  // has placed the node (x/y populated) — by the time the user has typed a
  // query, the cooldown has long since finished.
  const flyTo = (id: string) => {
    if (!settled) return;
    const fg = fgRef.current;
    if (!fg) return;
    const node = nodeById.get(id) as
      | (MapNode & { x?: number; y?: number })
      | undefined;
    if (!node || node.x == null || node.y == null) return;
    fg.centerAt?.(node.x, node.y, 800);
    fg.zoom?.(2.0, 800);
    setHoverId(id);
  };

  const selectMatch = (spec: SpecMapItem) => {
    flyTo(spec.id);
    setPinnedId(spec.id);
    setSearchQuery('');
    setSearchOpen(false);
    searchInputRef.current?.blur();
    trackEvent('map_search_select', { spec: spec.id });
  };

  const ready = graphData.nodes.length > 0 && size.w > 0 && size.h > 0;

  return (
    <>
      <Helmet>
        <title>map() — anyplot</title>
        <meta name="description" content="Interactive map of all anyplot specifications, clustered by tag similarity." />
      </Helmet>
      <Box
        ref={containerRef}
        // Negative margins cancel RootLayout's container px so the canvas goes full-bleed.
        // TODO: replace with a router-level layout switch (analog to mastheadSticks) once we
        // have more full-bleed pages — see issue tracking the /map rollout.
        sx={{
          mx: { xs: -2, sm: -4, md: -8, lg: -12 },
          // Lower reserved chrome on phones so the canvas + bottom controls
          // (weights, hover panel) stay reachable in landscape orientation.
          // Universal minHeight of 320 only fires on very short viewports
          // (landscape phones) — desktop's computed height is always larger.
          height: { xs: 'calc(100svh - 140px)', sm: 'calc(100svh - 180px)' },
          minHeight: 320,
          position: 'relative',
          bgcolor: 'var(--bg-page)',
          overflow: 'hidden',
        }}
        role="region"
        aria-label="Force-directed map of anyplot specifications, clustered by tag similarity"
      >
        {/* Header overlay with tiny meta. On phones the search pill takes
            the top row so the meta drops to a second row. left values
            mirror RootLayout's container px in raw pixels (sx `left` is
            NOT spacing-aware, unlike `px`/`mx`) so the text aligns with
            the anyplot logo / nav links. */}
        <Box sx={{
          position: 'absolute',
          top: { xs: 50, sm: 16 },
          left: { xs: 16, sm: 32, md: 64, lg: 96 },
          zIndex: 2,
          fontFamily: typography.mono,
          fontSize: fontSize.xs,
          color: 'var(--ink-soft)',
          pointerEvents: 'none',
        }}>
          {specs ? `${specs.length} specs · ${graphData.links.length} edges` : ' '}
        </Box>

        {/* Search pill: top-center mono input with dropdown of top-8 matches.
            Cmd/Ctrl+K focuses from anywhere; ArrowUp/Down + Enter selects;
            Escape clears. Selecting a match flies the camera to the node and
            opens the hover panel. Higher z-index than the other overlays so
            the dropdown sits above legend + weights + hover panel. */}
        <Box sx={{
          position: 'absolute',
          top: { xs: 8, sm: 16 },
          // Phone: full-width pill spanning the canvas with 16 px gutters.
          // Tablet+: centered 280 px pill, capped against the meta line on
          // the left and the legend column on the right.
          left: { xs: 16, sm: '50%' },
          right: { xs: 16, sm: 'auto' },
          transform: { xs: 'none', sm: 'translateX(-50%)' },
          zIndex: 4,
          width: { xs: 'auto', sm: 280 },
          maxWidth: { xs: 'none', sm: 'calc(100vw - 320px)' },
          fontFamily: typography.mono,
        }}>
          <Box
            component="input"
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            placeholder="specs.search()"
            onChange={e => setSearchQuery((e.target as HTMLInputElement).value)}
            onFocus={() => setSearchOpen(true)}
            onBlur={() => window.setTimeout(() => setSearchOpen(false), 150)}
            onKeyDown={e => {
              if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSearchIdx(i => Math.min(i + 1, Math.max(0, searchMatches.length - 1)));
              } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSearchIdx(i => Math.max(i - 1, 0));
              } else if (e.key === 'Enter') {
                e.preventDefault();
                const pick = searchMatches[searchIdx];
                if (pick) selectMatch(pick);
              } else if (e.key === 'Escape') {
                setSearchQuery('');
                searchInputRef.current?.blur();
              }
            }}
            sx={{
              width: '100%',
              boxSizing: 'border-box',
              px: 1.25,
              py: 0.75,
              bgcolor: 'var(--bg-surface)',
              border: '1px solid var(--rule)',
              borderRadius: '4px',
              fontFamily: typography.mono,
              fontSize: fontSize.xs,
              color: 'var(--ink)',
              outline: 'none',
              '&::placeholder': { color: 'var(--ink-soft)', opacity: 0.65 },
              '&:focus': { borderColor: colors.primary },
            }}
          />
          {searchOpen && searchQuery.trim() && (
            <Box sx={{
              mt: 0.5,
              bgcolor: 'var(--bg-surface)',
              border: '1px solid var(--rule)',
              borderRadius: '4px',
              overflow: 'hidden',
              boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
            }}>
              {searchMatches.length === 0 ? (
                <Box sx={{
                  px: 1.25, py: 0.75,
                  fontSize: fontSize.xs,
                  color: 'var(--ink-soft)',
                  fontStyle: 'italic',
                }}>
                  no matches
                </Box>
              ) : (
                searchMatches.map((s, i) => (
                  <Box
                    key={s.id}
                    onMouseDown={e => {
                      e.preventDefault();
                      selectMatch(s);
                    }}
                    onMouseEnter={() => setSearchIdx(i)}
                    sx={{
                      px: 1.25, py: 0.75,
                      cursor: 'pointer',
                      fontSize: fontSize.xs,
                      color: 'var(--ink)',
                      bgcolor: i === searchIdx ? 'var(--bg-page)' : 'transparent',
                      borderBottom: i < searchMatches.length - 1 ? '1px solid var(--rule)' : 'none',
                      display: 'flex',
                      alignItems: 'baseline',
                      gap: 1,
                    }}
                  >
                    <Box sx={{
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}>
                      {s.title}
                    </Box>
                    <Box sx={{ color: 'var(--ink-soft)', opacity: 0.7, fontSize: '0.65rem' }}>
                      {s.id}
                    </Box>
                  </Box>
                ))
              )}
            </Box>
          )}
        </Box>

        {/* Legend: one row per top-N value of the highest-weighted tag
            category. Caption shows which category is active so it's obvious
            why the buckets just changed when a slider moves. Hovering a row
            highlights that cluster on the canvas (matching nodes stay opaque,
            others dim) so the spatial shape of the cluster pops out even
            when nodes are scattered. */}
        {/* Mobile-only legend toggle. Sits in the same row as the meta
            line (top: 50) so the top row stays clear for the search pill. */}
        {graphData.topTypes.length > 0 && (
          <Box
            component="button"
            onClick={() => setLegendOpen(o => !o)}
            sx={{
              all: 'unset',
              display: { xs: 'inline-block', sm: 'none' },
              position: 'absolute',
              top: 44,
              right: 10,
              zIndex: 2,
              cursor: 'pointer',
              // Bigger touch target since `all: 'unset'` strips the
              // default button padding.
              padding: '6px 6px',
              fontFamily: typography.mono,
              fontSize: fontSize.xs,
              color: legendOpen ? 'var(--ink)' : 'var(--ink-soft)',
              userSelect: 'none',
            }}
          >
            {legendOpen ? 'legend ▾' : 'legend ▸'}
          </Box>
        )}
        {graphData.topTypes.length > 0 && (
          <Box
            sx={{
              position: 'absolute',
              // Mobile: appears below the toggle when expanded; tablet+:
              // pinned to the top-right corner like before.
              top: { xs: 76, sm: 16 },
              right: { xs: 16, sm: 32, md: 64, lg: 96 },
              zIndex: 2,
              display: { xs: legendOpen ? 'flex' : 'none', sm: 'flex' },
              flexDirection: 'column',
              gap: 0.5,
              fontFamily: typography.mono,
              fontSize: fontSize.xs,
              color: 'var(--ink-soft)',
              // Subtle backdrop on mobile so the list reads against the canvas
              bgcolor: { xs: 'var(--bg-surface)', sm: 'transparent' },
              border: { xs: '1px solid var(--rule)', sm: 'none' },
              borderRadius: { xs: '4px', sm: 0 },
              p: { xs: 1, sm: 0 },
            }}
          >
            <Box sx={{ opacity: 0.6, mb: 0.25 }}>{activeCategory}</Box>
            {graphData.topTypes.map((t, i) => {
              const color = CLUSTER_COLORS[i % CLUSTER_COLORS.length];
              const count = graphData.typeCounts.get(t) ?? 0;
              const dimmed = hoverType != null && hoverType !== t;
              return (
                <Box
                  key={t}
                  onMouseEnter={() => setHoverType(t)}
                  onMouseLeave={() => setHoverType(null)}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    cursor: 'pointer',
                    opacity: dimmed ? 0.35 : 1,
                    transition: 'opacity 0.15s',
                    color: hoverType === t ? 'var(--ink)' : 'inherit',
                    userSelect: 'none',
                  }}
                >
                  <Box sx={{ width: 10, height: 10, bgcolor: color, borderRadius: '2px', flex: 'none' }} />
                  <Box component="span" sx={{ minWidth: 60 }}>{t}</Box>
                  <Box component="span" sx={{ opacity: 0.55, fontVariantNumeric: 'tabular-nums' }}>{count}</Box>
                </Box>
              );
            })}
          </Box>
        )}

        {/* Weights panel: collapsible bottom-left control for per-category
            similarity weights. Live-updates KNN + simulation on every drag.
            column-reverse keeps the toggle pinned at the bottom while the
            panel grows upward — without it, opening the panel pushes the
            toggle up by ~300 px on mobile, where it can land off-screen. */}
        <Box sx={{
          position: 'absolute',
          bottom: { xs: 8, sm: 16 },
          left: { xs: 16, sm: 32, md: 64, lg: 96 },
          zIndex: 2,
          display: 'flex',
          flexDirection: 'column-reverse',
          alignItems: 'flex-start',
          gap: 1,
          fontFamily: typography.mono,
          fontSize: fontSize.xs,
          color: 'var(--ink-soft)',
        }}>
          <Box
            component="button"
            onClick={() => setWeightsOpen(o => !o)}
            sx={{
              all: 'unset',
              cursor: 'pointer',
              // Bigger touch target on phones — `all: 'unset'` strips the
              // default button padding, so the bare text is only ~16 px
              // tall by default which is below the recommended 40 px.
              padding: { xs: '6px 4px', sm: '0' },
              fontFamily: typography.mono,
              fontSize: fontSize.xs,
              color: weightsOpen ? 'var(--ink)' : 'var(--ink-soft)',
              '&:hover': { color: colors.primary },
              userSelect: 'none',
            }}
          >
            {weightsOpen ? 'weights ▾' : 'weights ▸'}
          </Box>
          {weightsOpen && (
            <Box sx={{
              p: { xs: 1.25, sm: 2 },
              minWidth: { xs: 220, sm: 280 },
              border: '1px solid var(--rule)',
              borderRadius: '4px',
              bgcolor: 'var(--bg-surface)',
              display: 'flex',
              flexDirection: 'column',
              gap: { xs: 0.6, sm: 1.25 },
            }}>
              {TAG_CATEGORIES.map(cat => (
                <Box key={cat} sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: { xs: 1, sm: 1.5 },
                }}>
                  <Box component="span" sx={{
                    minWidth: { xs: 78, sm: 100 },
                    fontFamily: typography.mono,
                    fontSize: fontSize.xs,
                  }}>
                    {cat}
                  </Box>
                  <Slider
                    value={weights[cat]}
                    onChange={(_, v) => setWeights(w => ({ ...w, [cat]: v as number }))}
                    min={0}
                    max={5}
                    step={0.1}
                    size="small"
                    sx={{
                      flex: 1,
                      color: colors.primary,
                      // Compact knob & rail height so the rows can pack
                      // tighter on phones without the slider feeling cramped.
                      py: { xs: 0.25, sm: 0.5 },
                      '& .MuiSlider-rail': { opacity: 0.25 },
                    }}
                  />
                  <Box component="span" sx={{
                    minWidth: 28,
                    textAlign: 'right',
                    fontFamily: typography.mono,
                    fontSize: fontSize.xs,
                    fontVariantNumeric: 'tabular-nums',
                    color: 'var(--ink)',
                  }}>
                    {weights[cat].toFixed(1)}
                  </Box>
                </Box>
              ))}
              {/* Edge-threshold slider — controls KNN_MIN_SIM, the cutoff
                  below which a candidate KNN edge is dropped. Lower = denser
                  graph (more cross-cluster bridges); higher = sparser graph
                  (cleaner clusters but more isolated outliers). */}
              <Box sx={{
                display: 'flex',
                alignItems: 'center',
                gap: { xs: 1, sm: 1.5 },
                pt: { xs: 0.25, sm: 0.5 },
                borderTop: '1px dashed var(--rule)',
              }}>
                <Box component="span" sx={{
                  minWidth: { xs: 78, sm: 100 },
                  fontFamily: typography.mono,
                  fontSize: fontSize.xs,
                }}>
                  threshold
                </Box>
                <Slider
                  value={minSim}
                  onChange={(_, v) => setMinSim(v as number)}
                  min={MIN_SIM_BOUNDS.min}
                  max={MIN_SIM_BOUNDS.max}
                  step={MIN_SIM_BOUNDS.step}
                  size="small"
                  sx={{
                    flex: 1,
                    color: colors.primary,
                    py: { xs: 0.25, sm: 0.5 },
                    '& .MuiSlider-rail': { opacity: 0.25 },
                  }}
                />
                <Box component="span" sx={{
                  minWidth: 32,
                  textAlign: 'right',
                  fontFamily: typography.mono,
                  fontSize: fontSize.xs,
                  fontVariantNumeric: 'tabular-nums',
                  color: 'var(--ink)',
                }}>
                  {minSim.toFixed(2)}
                </Box>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: { xs: 0, sm: 0.5 } }}>
                <Box
                  component="button"
                  onClick={() => {
                    setWeights(DEFAULT_CATEGORY_WEIGHT);
                    setMinSim(DEFAULT_MIN_SIM);
                  }}
                  sx={{
                    all: 'unset',
                    cursor: 'pointer',
                    fontFamily: typography.mono,
                    fontSize: fontSize.xs,
                    color: 'var(--ink-soft)',
                    '&:hover': { color: colors.primary },
                  }}
                >
                  reset
                </Box>
              </Box>
            </Box>
          )}
        </Box>

        {/* Pin marker: a CSS-pulsing outline overlaid on the searched node.
            DOM-driven so the pulse animation runs independently of FG2D's
            render loop (which pauses once the simulation cools down). The
            position is recomputed every frame from graph2ScreenCoords so it
            tracks pan/zoom. pointerEvents:none keeps it from intercepting
            clicks/hovers on the node underneath. */}
        {pinScreen && (
          <Box
            sx={{
              position: 'absolute',
              left: pinScreen.x,
              top: pinScreen.y,
              width: pinScreen.w,
              height: pinScreen.h,
              pointerEvents: 'none',
              zIndex: 2,
              borderRadius: '2px',
              animation: 'mapPinPulse 1.4s ease-in-out infinite',
              '@keyframes mapPinPulse': {
                '0%, 100%': {
                  outline: `2px solid ${pinColor}`,
                  outlineOffset: '2px',
                  boxShadow: `0 0 8px ${pinColor}`,
                  opacity: 0.9,
                },
                '50%': {
                  outline: `4px solid ${pinColor}`,
                  outlineOffset: '5px',
                  boxShadow: `0 0 28px ${pinColor}, 0 0 6px ${pinColor}`,
                  opacity: 1,
                },
              },
            }}
          />
        )}

        {/* Hover panel: fixed bottom-right, fades in/out on hover. Lives in
            the DOM so its size is independent of zoom level and never clips
            at the viewport edge. Pointer-transparent so it never steals
            hover detection from canvas nodes underneath. */}
        <Box
          component="aside"
          aria-hidden={!(hoverId || pinnedId)}
          sx={{
            position: 'absolute',
            bottom: { xs: 8, sm: 16 },
            right: { xs: 16, sm: 32, md: 64, lg: 96 },
            zIndex: 3,
            // Phones: ~half the width, no tags. Otherwise the panel covers
            // the searched node + its connection lines after fly-to. Tablet+:
            // full 280 px panel as before.
            width: { xs: 160, sm: 280 },
            maxWidth: { xs: 'calc(60vw - 32px)', sm: 'calc(100vw - 64px)' },
            border: '1px solid var(--rule)',
            borderRadius: '4px',
            bgcolor: 'var(--bg-surface)',
            overflow: 'hidden',
            pointerEvents: 'none',
            opacity: (hoverId || pinnedId) && panelData ? 1 : 0,
            transform: (hoverId || pinnedId) && panelData ? 'translateY(0)' : 'translateY(4px)',
            transition: 'opacity 120ms ease, transform 120ms ease',
            fontFamily: typography.mono,
          }}
        >
          {panelData && (
            <>
              {panelData.previewUrl ? (
                <Box
                  component="img"
                  src={panelData.previewUrl}
                  alt=""
                  sx={{
                    display: 'block',
                    width: '100%',
                    height: 'auto',
                    maxHeight: { xs: 110, sm: 200 },
                    objectFit: 'contain',
                    bgcolor: isDark ? '#0a0a08' : '#FFFDF6',
                  }}
                />
              ) : (
                <Box sx={{ height: { xs: 90, sm: 158 }, bgcolor: isDark ? '#0a0a08' : '#FFFDF6' }} />
              )}
              <Box sx={{
                p: { xs: 0.75, sm: 1.25 },
                display: 'flex',
                flexDirection: 'column',
                gap: 0.5,
              }}>
                <Box
                  sx={{
                    fontSize: fontSize.sm,
                    color: 'var(--ink)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {panelData.title}
                </Box>
                {panelData.plotType && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '2px',
                        bgcolor: panelData.chipColor ?? 'var(--ink-soft)',
                        flex: 'none',
                      }}
                    />
                    <Box sx={{ fontSize: fontSize.xs, color: 'var(--ink-soft)' }}>
                      {panelData.plotType}
                    </Box>
                  </Box>
                )}
                {panelData.tags.length > 0 && (
                  <Box
                    sx={{
                      // Phones: hide tags, the smaller panel only shows
                      // image + title + plot_type chip so it doesn't cover
                      // the focused node and its KNN edges.
                      display: { xs: 'none', sm: 'flex' },
                      flexWrap: 'wrap',
                      gap: 0.75,
                      fontSize: fontSize.xs,
                      color: 'var(--ink-soft)',
                      opacity: 0.85,
                    }}
                  >
                    {panelData.tags.map(t => (
                      <Box key={t} component="span">
                        {t}
                      </Box>
                    ))}
                  </Box>
                )}
              </Box>
            </>
          )}
        </Box>

        {/* Loading / error states */}
        {!specs && !error && (
          <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CircularProgress size={28} />
          </Box>
        )}
        {error && (
          <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink-soft)', fontFamily: typography.mono }}>
            <Typography sx={{ fontFamily: typography.mono, fontSize: fontSize.sm }}>
              Failed to load map: {error}
            </Typography>
          </Box>
        )}

        {/* Canvas */}
        {ready && (
          <ForceGraph2D
            ref={fgRef}
            graphData={graphData}
            width={size.w}
            height={size.h}
            backgroundColor={'transparent'}
            nodeLabel={(n: MapNode) => n.title}
            // Boost global repulsion so nodes aren't crammed into a blob.
            d3VelocityDecay={0.35}
            d3AlphaDecay={0.018}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const n = node as WithCoords;
              if (n.x == null || n.y == null) return;
              const isHover = hoverId === n.id;
              const isNeighbor = !isHover && hoverId != null && neighbors.get(hoverId)?.has(n.id);
              // hoverType is set when the user hovers a legend entry — match
              // any node in that cluster, dim the rest.
              const matchesType = hoverType == null || n.colorBucket === hoverType;
              const dim =
                (hoverId != null && !isHover && !isNeighbor) ||
                (hoverType != null && !matchesType);
              // Hovered node itself doesn't grow — the rich preview lives in a
              // DOM corner panel. Direct neighbors get a small bump so the
              // relationship is still legible on the canvas.
              const baseSize = NODE_SIZE * (isNeighbor ? 1.2 : 1);

              // Pick the smallest variant whose source resolution comfortably
              // covers the on-screen size, then lazy-load it if not yet present.
              // force-graph only invokes nodeCanvasObject for visible nodes, so
              // off-screen specs never trigger a higher-tier fetch.
              const screenPx = baseSize * (globalScale ?? 1);
              const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
              const desired: ResolutionTier = pickTier(screenPx * dpr);
              if (n.imgs && !n.imgs.has(desired) && !n.pendingTiers?.has(desired)) {
                ensureNodeTier(n, desired, () => fgRef.current?.refresh?.());
              }
              const img = n.imgs ? pickBestLoadedTier(n.imgs, desired) : null;

              // Match draw size to the source aspect ratio (most plots are 16:9
              // from figsize=(16,9)) — keep the longer side at baseSize so nodes
              // share a consistent bounding-box scale.
              const { w, h } = fitToBox(baseSize, nodeAspectRatio(n));
              const x = n.x - w / 2;
              const y = n.y - h / 2;

              ctx.save();
              if (dim) ctx.globalAlpha = 0.18;
              if (img) {
                ctx.drawImage(img, x, y, w, h);
              } else {
                ctx.fillStyle = isDark ? '#242420' : '#FFFDF6';
                ctx.fillRect(x, y, w, h);
              }
              ctx.lineWidth = isHover ? 2 : n.colorBucket ? 1.5 : 1;
              ctx.strokeStyle = strokeFor(isDark, !!isHover, colorFor(n.colorBucket, graphData.topTypes));
              ctx.strokeRect(x, y, w, h);

              ctx.restore();
            }}
            nodePointerAreaPaint={(node, color, ctx) => {
              const n = node as WithCoords;
              if (n.x == null || n.y == null) return;
              const { w, h } = fitToBox(NODE_SIZE, nodeAspectRatio(n));
              ctx.fillStyle = color;
              ctx.fillRect(n.x - w / 2, n.y - h / 2, w, h);
            }}
            // Links are intentionally very subtle by default so the thumbnails
            // dominate. Hovered-node connections light up; when a legend
            // entry is hovered, links between same-cluster nodes stay
            // visible while everything else fades.
            //
            // NOTE: ForceGraph2D mutates link.source / link.target from
            // string IDs to actual node objects after the first simulation
            // tick. So `l.source === hoverId` would only ever match before
            // the first tick. linkEndId() reads through the object.
            linkColor={(l: MapLink) => {
              const sId = linkEndId(l.source);
              const tId = linkEndId(l.target);
              const involved = hoverId && (sId === hoverId || tId === hoverId);
              if (involved) {
                // Match the cluster color of the hovered node so the burst
                // of highlighted edges feels coherent with the frame.
                const hoverNode = nodeById.get(hoverId);
                return colorFor(hoverNode?.colorBucket ?? null, graphData.topTypes) ?? colors.primary;
              }
              if (hoverType) {
                const sBucket = sId ? nodeById.get(sId)?.colorBucket : undefined;
                const tBucket = tId ? nodeById.get(tId)?.colorBucket : undefined;
                const intra = sBucket === hoverType && tBucket === hoverType;
                if (intra) return isDark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.22)';
                return isDark ? 'rgba(255,255,255,0.012)' : 'rgba(0,0,0,0.015)';
              }
              // When a node is hovered, keep non-involved edges faintly
              // visible so the user can still read the surrounding cluster
              // structure — too much fade-out makes the map feel broken.
              if (hoverId) return isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.06)';
              return isDark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.13)';
            }}
            linkWidth={(l: MapLink) => {
              const sId = linkEndId(l.source);
              const tId = linkEndId(l.target);
              const involved = hoverId && (sId === hoverId || tId === hoverId);
              if (involved) return Math.max(1.5, (l.weight ?? 0.3) * 3);
              return Math.max(0.4, (l.weight ?? 0.3) * 1.5);
            }}
            onNodeClick={onNodeClick}
            // Background tap clears the pin AND closes the preview panel.
            // On desktop ForceGraph2D fires onNodeHover(null) when the
            // pointer leaves a node, but on touch there's no hover event,
            // so we need to clear hoverId explicitly here. Doing it on
            // both is a harmless no-op for the desktop path.
            onBackgroundClick={() => {
              setPinnedId(null);
              setHoverId(null);
            }}
            onNodeHover={(n: MapNode | null) => {
              if (hoverTimerRef.current != null) {
                window.clearTimeout(hoverTimerRef.current);
                hoverTimerRef.current = null;
              }
              if (n) {
                hoverTimerRef.current = window.setTimeout(() => {
                  setHoverId(n.id);
                  hoverTimerRef.current = null;
                }, 100);
              } else {
                setHoverId(null);
              }
            }}
            cooldownTicks={COOLDOWN_TICKS}
            // The simulation's centering force already lands the graph near
            // the viewport, so an explicit zoom-to-fit changes very little
            // and just adds a wait. Drop the gate as soon as the engine
            // stops — the user keeps whatever camera state the simulation
            // produced and can pan/zoom freely.
            onEngineStop={() => setSettled(true)}
            // Wire up the custom forces once the imperative ref is available.
            // onRenderFramePre fires every frame; the __forcesWired guard makes
            // it idempotent and the cost on subsequent frames is one property read.
            onRenderFramePre={() => {
              const fg = fgRef.current;
              if (!fg || fg.__forcesWired) return;
              // Stronger many-body repulsion than the default ~-30.
              fg.d3Force('charge')?.strength(REPULSION);
              // Link distance/strength scale with weighted-Jaccard similarity:
              // tighter clusters for highly related specs, looser otherwise.
              // The d3-force-3d ambient types are minimal; cast for the chained calls.
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const linkForce = fg.d3Force('link') as any;
              if (linkForce) {
                linkForce.distance((l: MapLink) => {
                  const w = l.weight ?? 0.3;
                  return LINK_DISTANCE_MIN + (1 - Math.min(1, w)) * (LINK_DISTANCE_MAX - LINK_DISTANCE_MIN);
                });
                linkForce.strength((l: MapLink) =>
                  Math.max(0.02, Math.min(LINK_STRENGTH_CAP, (l.weight ?? 0.3) * 0.4))
                );
              }
              // Per-node collision: prevents thumbnail overlap. Radius = half
              // the longer side of the bounding box plus a small padding.
              fg.d3Force(
                'collide',
                forceCollide<MapNode>(() => NODE_SIZE / 2 + COLLIDE_PADDING).iterations(2)
              );
              // Mild centering force so disconnected outliers (no KNN edges
              // because all sims < threshold) drift back toward the cluster
              // mass instead of vanishing to the corners. Strength is well
              // below the default 1.0 so cluster shapes stay intact.
              fg.d3Force('center')?.strength?.(CENTER_GRAVITY);
              fg.__forcesWired = true;
              fg.d3ReheatSimulation?.();
            }}
          />
        )}

        {/* Settling gate: visible while specs are loaded but the simulation
            hasn't finished cooling and the camera hasn't completed its initial
            fit-to-view. Sits on top of the canvas, swallows pointer events,
            and shows a small spinner in the corner so the user sees that the
            layout is still resolving. Drops as soon as `settled` flips. */}
        {ready && !settled && (
          <Box
            aria-hidden="true"
            sx={{
              position: 'absolute',
              inset: 0,
              pointerEvents: 'auto',
              cursor: 'wait',
              zIndex: 5,
            }}
          >
            <Box
              sx={{
                position: 'absolute',
                bottom: 12,
                right: 12,
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                px: 1.25,
                py: 0.5,
                borderRadius: 999,
                bgcolor: isDark ? 'rgba(36, 36, 32, 0.85)' : 'rgba(255, 253, 246, 0.85)',
                border: '1px solid var(--rule)',
                color: 'var(--ink-soft)',
                fontFamily: typography.mono,
                fontSize: fontSize.xs,
                backdropFilter: 'blur(4px)',
              }}
            >
              <CircularProgress size={12} thickness={5} />
              <span>arranging…</span>
            </Box>
          </Box>
        )}

        {/* a11y fallback: visually-hidden list so screen readers + keyboard users
            can still reach every spec from this page. */}
        <Box component="ul" sx={visuallyHiddenSx}>
          {(specs ?? []).map(s => (
            <li key={s.id}>
              <Link to={specPath(s.id)}>{s.title}</Link>
            </li>
          ))}
        </Box>
      </Box>
    </>
  );
}
