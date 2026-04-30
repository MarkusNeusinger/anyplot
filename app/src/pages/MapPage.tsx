import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
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
  computeIDF,
  DEFAULT_CATEGORY_WEIGHT,
  ensureNodeTier,
  fitToBox,
  flattenTags,
  nodeAspectRatio,
  pickBestLoadedTier,
  pickTier,
  plotTypeCounts,
  preloadImages,
  primaryPlotType,
  selectMapThumbUrl,
  TAG_CATEGORIES,
  topPlotTypes,
  type MapLink,
  type MapNode,
  type ResolutionTier,
  type SpecMapItem,
  type TagCategory,
} from './MapPage.helpers';


const NODE_SIZE = 60;            // graph-space size of a node — large enough to read the thumbnail without hovering
const HOVER_PREVIEW_SIZE = NODE_SIZE * 5;     // graph-space size of the hover preview overlay
const MIN_ZOOM = 0.5;             // floor for zoomToFit so outliers can't shrink the dense cluster into pixels
const COOLDOWN_TICKS = 400;       // longer settling for cleaner final positions
const KNN_K = 5;                  // edges per node in the sparse KNN graph
const KNN_MIN_SIM = 0.05;         // drop near-zero noise links
// Forces: tuned so KNN edges + collision shape the layout while many-body
// repulsion stays GENTLE — collision already enforces minimum spacing, and
// strong repulsion would just blow the graph wide enough that zoomToFit
// zooms out too far for thumbnails to be readable. Goal: graph extent stays
// small enough that zoomToFit displays nodes at a generous CSS-pixel size.
const REPULSION = -50;            // forceManyBody strength
const LINK_DISTANCE_MIN = NODE_SIZE * 1.1;   // shortest link (highest sim)
const LINK_DISTANCE_MAX = NODE_SIZE * 3.5;   // longest link (lowest sim above threshold)
const LINK_STRENGTH_CAP = 0.4;    // max pull from a single link
const COLLIDE_PADDING = 3;        // px padding on top of the bounding-box radius

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

// Hairline border around a thumbnail node, theme-aware. Top-N plot types
// paint with a brand color; the rest fall back to a neutral hairline.
function strokeFor(isDark: boolean, isHover: boolean, color: string | null): string {
  if (isHover) return colors.primary;
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
  // hoverType = a plot_type the user is hovering in the legend; everything
  // not in that cluster dims so the cluster shape is obvious.
  const [hoverType, setHoverType] = useState<string | null>(null);
  // Per-category weight overrides for the similarity calculation. Bound to
  // the weights panel sliders. Live-updates KNN edges + simulation on change.
  const [weights, setWeights] = useState<Record<TagCategory, number>>(DEFAULT_CATEGORY_WEIGHT);
  const [weightsOpen, setWeightsOpen] = useState(false);

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

  // 3. derive graph data from specs/theme (pure — no setState in effect)
  const graphData = useMemo<{
    nodes: MapNode[];
    links: MapLink[];
    topTypes: string[];
    typeCounts: Map<string, number>;
  }>(() => {
    if (!specs) return { nodes: [], links: [], topTypes: [], typeCounts: new Map() };
    const idf = computeIDF(specs);
    const topTypes = topPlotTypes(specs, CLUSTER_COLORS.length);
    const typeCounts = plotTypeCounts(specs);
    const nodes: MapNode[] = specs.map(s => {
      const pt = primaryPlotType(s);
      return {
        id: s.id,
        title: s.title,
        tags: flattenTags(s),
        colorBucket: topTypes.includes(pt) ? pt : null,
        thumbUrl: selectMapThumbUrl(s, isDark),
        imgs: new Map(),
        pendingTiers: new Set(),
      };
    });
    const links = buildKNNLinks(specs, idf, KNN_K, KNN_MIN_SIM, weights);
    return { nodes, links, topTypes, typeCounts };
  }, [specs, isDark, weights]);

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


  // 5. ForceGraph2D callbacks. Types for ctx come from the wrapper's prop signature
  // when these are passed inline below — extracting them out would force us to spell
  // CanvasRenderingContext2D explicitly, which our eslint config doesn't recognize.
  type WithCoords = MapNode & { x?: number; y?: number };

  const onNodeClick = (node: MapNode) => {
    trackEvent('map_node_click', { spec_id: node.id });
    navigate(specPath(node.id));
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
          height: { xs: 'calc(100svh - 200px)', sm: 'calc(100svh - 180px)' },
          minHeight: 480,
          position: 'relative',
          bgcolor: 'var(--bg-page)',
          overflow: 'hidden',
        }}
        role="region"
        aria-label="Force-directed map of anyplot specifications, clustered by tag similarity"
      >
        {/* Header overlay with tiny meta. left values mirror RootLayout's
            container px in raw pixels (sx `left` is NOT spacing-aware, unlike
            `px`/`mx`) so the text aligns with the anyplot logo / nav links. */}
        <Box sx={{
          position: 'absolute',
          top: { xs: 8, sm: 16 },
          left: { xs: 16, sm: 32, md: 64, lg: 96 },
          zIndex: 2,
          fontFamily: typography.mono,
          fontSize: fontSize.xs,
          color: 'var(--ink-soft)',
          pointerEvents: 'none',
        }}>
          {specs ? `${specs.length} specs · ${graphData.links.length} edges` : ' '}
          {hoverId && (
            <Box component="span" sx={{ ml: 1.5, color: 'var(--ink)', pointerEvents: 'auto' }}>
              ❯ {graphData.nodes.find(n => n.id === hoverId)?.title}
            </Box>
          )}
        </Box>

        {/* Legend: one row per top-N plot type with its cluster color and
            spec count. Hovering a row highlights that cluster on the canvas
            (matching nodes stay opaque, others dim) so the spatial shape of
            the cluster pops out even when nodes are scattered. */}
        {graphData.topTypes.length > 0 && (
          <Box
            sx={{
              position: 'absolute',
              top: { xs: 8, sm: 16 },
              right: { xs: 16, sm: 32, md: 64, lg: 96 },
              zIndex: 2,
              display: 'flex',
              flexDirection: 'column',
              gap: 0.5,
              fontFamily: typography.mono,
              fontSize: fontSize.xs,
              color: 'var(--ink-soft)',
            }}
          >
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
            similarity weights. Live-updates KNN + simulation on every drag. */}
        <Box sx={{
          position: 'absolute',
          bottom: { xs: 8, sm: 16 },
          left: { xs: 16, sm: 32, md: 64, lg: 96 },
          zIndex: 2,
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
              mt: 1,
              p: 2,
              minWidth: 280,
              border: '1px solid var(--rule)',
              borderRadius: '4px',
              bgcolor: 'var(--bg-surface)',
              display: 'flex',
              flexDirection: 'column',
              gap: 1.25,
            }}>
              {TAG_CATEGORIES.map(cat => (
                <Box key={cat} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <Box component="span" sx={{ minWidth: 100, fontFamily: typography.mono, fontSize: fontSize.xs }}>
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
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 0.5 }}>
                <Box
                  component="button"
                  onClick={() => setWeights(DEFAULT_CATEGORY_WEIGHT)}
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
            d3AlphaDecay={0.0228}
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
              // The hovered node itself doesn't grow here — the much larger
              // preview is drawn on top by onRenderFramePost. We DO bump
              // direct neighbors slightly so the relationship is legible.
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
            // dominate. Hovered-node connections light up bright green; when
            // a legend entry is hovered, links between same-cluster nodes
            // stay visible while everything else fades.
            linkColor={(l: MapLink) => {
              const involved = hoverId && (l.source === hoverId || l.target === hoverId);
              if (involved) return colors.primary;
              if (hoverType) {
                const sId = typeof l.source === 'string' ? l.source : (l.source as { id?: string })?.id;
                const tId = typeof l.target === 'string' ? l.target : (l.target as { id?: string })?.id;
                const sBucket = graphData.nodes.find(n => n.id === sId)?.colorBucket;
                const tBucket = graphData.nodes.find(n => n.id === tId)?.colorBucket;
                const intra = sBucket === hoverType && tBucket === hoverType;
                if (intra) return isDark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.22)';
                return isDark ? 'rgba(255,255,255,0.012)' : 'rgba(0,0,0,0.015)';
              }
              if (hoverId) return isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.025)';
              return isDark ? 'rgba(255,255,255,0.10)' : 'rgba(0,0,0,0.13)';
            }}
            linkWidth={(l: MapLink) => {
              const involved = hoverId && (l.source === hoverId || l.target === hoverId);
              if (involved) return Math.max(1, (l.weight ?? 0.3) * 2.5);
              return Math.max(0.4, (l.weight ?? 0.3) * 1.5);
            }}
            onNodeClick={onNodeClick}
            onNodeHover={(n: MapNode | null) => setHoverId(n?.id ?? null)}
            cooldownTicks={COOLDOWN_TICKS}
            // Fit the whole graph into the viewport once the engine settles,
            // but enforce a minimum zoom afterwards — without the floor, a
            // few far-flung outliers force zoomToFit to shrink the dense
            // central cluster down to illegible pixels.
            onEngineStop={() => {
              const fg = fgRef.current;
              if (!fg) return;
              fg.zoomToFit?.(600, 80);
              setTimeout(() => {
                if (typeof fg.zoom === 'function' && fg.zoom() < MIN_ZOOM) {
                  fg.zoom(MIN_ZOOM, 400);
                }
              }, 700);
            }}
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
              fg.__forcesWired = true;
              fg.d3ReheatSimulation?.();
            }}
            // Hover preview: paint a much larger version of the hovered node
            // AFTER all the regular nodes have been drawn, so it always sits
            // on top regardless of the node-paint order. Uses the same canvas
            // transform (graph coords) so positioning is just (n.x, n.y).
            onRenderFramePost={(ctx) => {
              if (!hoverId) return;
              const n = graphData.nodes.find(x => x.id === hoverId) as
                | (MapNode & { x?: number; y?: number })
                | undefined;
              if (!n || n.x == null || n.y == null) return;

              // Upgrade to the highest tier we'd want for a preview this large.
              const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
              const desiredTier = pickTier(HOVER_PREVIEW_SIZE * dpr);
              if (n.imgs && !n.imgs.has(desiredTier) && !n.pendingTiers?.has(desiredTier)) {
                ensureNodeTier(n, desiredTier, () => fgRef.current?.refresh?.());
              }
              const img = n.imgs ? pickBestLoadedTier(n.imgs, desiredTier) : null;

              const { w, h } = fitToBox(HOVER_PREVIEW_SIZE, nodeAspectRatio(n));
              const x = n.x - w / 2;
              const y = n.y - h / 2;

              ctx.save();
              // Soft drop-shadow halo to lift the preview off the canvas.
              ctx.shadowColor = colors.primary;
              ctx.shadowBlur = 16;
              ctx.fillStyle = isDark ? '#0a0a08' : '#FFFDF6';
              ctx.fillRect(x, y, w, h);
              ctx.shadowBlur = 0;
              if (img) ctx.drawImage(img, x, y, w, h);
              ctx.lineWidth = 1.5;
              ctx.strokeStyle = colors.primary;
              ctx.strokeRect(x, y, w, h);
              ctx.restore();
            }}
          />
        )}

        {/* a11y fallback: visually-hidden list so screen readers + keyboard users
            can still reach every spec from this page. */}
        <Box component="ul" sx={visuallyHiddenSx}>
          {(specs ?? []).map(s => (
            <li key={s.id}>
              <a href={specPath(s.id)}>{s.title}</a>
            </li>
          ))}
        </Box>
      </Box>
    </>
  );
}
