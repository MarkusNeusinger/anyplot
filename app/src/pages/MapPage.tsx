import { useEffect, useMemo, useRef, useState } from 'react';

import ForceGraph2D from 'react-force-graph-2d';
import { Helmet } from 'react-helmet-async';
import { Link, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Slider from '@mui/material/Slider';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useAnalytics } from 'src/hooks';
import {
  CLUSTER_COLORS,
  colorFor,
  MIN_SIM_BOUNDS,
  NODE_SIZE,
  useForceGraphSimulation,
} from 'src/hooks/useForceGraphSimulation';
import { useTheme } from 'src/hooks/useLayoutContext';
import {
  buildVariantUrl,
  ensureNodeTier,
  fitToBox,
  type MapLink,
  type MapNode,
  nodeAspectRatio,
  pickBestLoadedTier,
  pickTier,
  type ResolutionTier,
  type SpecMapItem,
  TAG_CATEGORIES,
} from 'src/pages/MapPage.helpers';
import { specPath } from 'src/routes/paths';
import { colors, fontSize, typography } from 'src/theme';

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

  // Simulation/data orchestration: spec loading, weights, the KNN graph
  // derivation, settling gate, search matching, and force tuning all live
  // in the hook. This component keeps the canvas, the paint callbacks, and
  // every handler that needs the imperative graph ref.
  const {
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
    forceConfig,
  } = useForceGraphSimulation({ onRepaint: () => fgRef.current?.refresh?.() });

  const [size, setSize] = useState<{ w: number; h: number }>({ w: 0, h: 0 });
  const [hoverId, setHoverId] = useState<string | null>(null);
  // panelNodeId trails hoverId on mouse-out so the corner preview can fade
  // out while still showing the last node's content. It only "advances" to
  // a *new* node when hoverId or pinnedId becomes non-null. Stored as a ref
  // + derived value (instead of useState + useEffect) to satisfy React's
  // set-state-in-effect rule: this is not external sync, it's pure
  // last-non-null memoization that belongs in render.
  const lastPanelNodeIdRef = useRef<string | null>(null);
  // pinnedId persists a visual marker on the searched node so the user
  // doesn't lose track of it when the mouse drifts onto a different node
  // (which would otherwise overwrite hoverId and replace the panel content).
  // Cleared by clicking empty canvas or by triggering another search.
  const [pinnedId, setPinnedId] = useState<string | null>(null);
  // Screen-space rect of the pinned node, recomputed every frame while a
  // pin is active. Drives the DOM-overlay pulse marker — separate from the
  // canvas so a CSS @keyframes animation can drive the pulse independently
  // of FG2D's render loop (which pauses once the simulation cools down).
  const [pinScreen, setPinScreen] = useState<{ x: number; y: number; w: number; h: number } | null>(
    null
  );
  // ~100ms debounce so quick mouse-overs don't strobe the preview.
  const hoverTimerRef = useRef<number | null>(null);
  // hoverType = a plot_type the user is hovering in the legend; everything
  // not in that cluster dims so the cluster shape is obvious.
  const [hoverType, setHoverType] = useState<string | null>(null);
  const [weightsOpen, setWeightsOpen] = useState(false);
  // Mobile-only: legend collapses behind a `legend ▸` toggle to leave
  // canvas room. Tablet/desktop renders the legend list always-visible.
  const [legendOpen, setLegendOpen] = useState(false);

  // Search-pill state. searchOpen controls dropdown visibility (separate
  // from focus so we can keep showing matches briefly while a click is in
  // flight via the input's onBlur grace period).
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchIdx, setSearchIdx] = useState(0);
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  // 1. page view
  useEffect(() => {
    trackPageview('/map');
  }, [trackPageview]);

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
  //
  // Derived during render rather than via a useState+useEffect pair: the
  // value is purely a function of (hoverId, pinnedId, last-non-null) and
  // never needs to react to external systems. The ref write below is
  // permitted by the project's eslint config (`react-hooks/refs: off`) —
  // it's idempotent (writes the same value on identical renders) and
  // happens *before* React commits, so subsequent reads see the update.
  const panelNodeId = hoverId ?? pinnedId ?? lastPanelNodeIdRef.current;
  if (panelNodeId !== null) lastPanelNodeIdRef.current = panelNodeId;

  // Clean up any pending hover-debounce timer on unmount.
  useEffect(() => {
    return () => {
      if (hoverTimerRef.current != null) {
        window.clearTimeout(hoverTimerRef.current);
      }
    };
  }, []);

  // Track the pinned node's on-screen rect so the DOM-overlay pulse marker
  // stays glued to it while the user pans/zooms. Cheap (one RAF tick = a
  // graph→screen coord transform + a setState that no-ops on sub-pixel
  // diffs), no canvas repaint involved.
  //
  // When pinnedId becomes null we just stop the RAF loop — the marker
  // visibility is gated on `pinnedId` at the JSX site, so there's no need
  // to setState(null) inside this effect (which would trip the
  // set-state-in-effect rule). pinScreen lingers at its last value but is
  // simply not rendered, then gets overwritten the next time a pin lands.
  useEffect(() => {
    if (!pinnedId) return;
    let raf = 0;
    const tick = () => {
      const fg = fgRef.current;
      const node = nodeById.get(pinnedId) as (MapNode & { x?: number; y?: number }) | undefined;
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
  }, [pinnedId, graphData, nodeById]);

  // 3. derive everything the corner hover-panel needs from the (lagged)
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
  }, [panelNodeId, graphData, nodeById]);

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

  // (searchIdx is reset inline in the input's onChange handler — moved out
  // of useEffect to avoid set-state-in-effect: it's a one-line followup
  // to a user event, not external sync.)

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

  // 4. ForceGraph2D callbacks. Types for ctx come from the wrapper's prop signature
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
    const fg = fgRef.current;
    if (!fg) return;
    const node = nodeById.get(id) as (MapNode & { x?: number; y?: number }) | undefined;
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
        <meta
          name="description"
          content="Interactive map of all anyplot specifications, clustered by tag similarity."
        />
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
        <Box
          sx={{
            position: 'absolute',
            top: { xs: 50, sm: 16 },
            left: { xs: 16, sm: 32, md: 64, lg: 96 },
            zIndex: 2,
            fontFamily: typography.mono,
            fontSize: fontSize.xs,
            color: 'var(--ink-soft)',
            pointerEvents: 'none',
          }}
        >
          {specs ? `${specs.length} specs · ${graphData.links.length} edges` : ' '}
        </Box>

        {/* Search pill: top-center mono input with dropdown of top-8 matches.
            Cmd/Ctrl+K focuses from anywhere; ArrowUp/Down + Enter selects;
            Escape clears. Selecting a match flies the camera to the node and
            opens the hover panel. Higher z-index than the other overlays so
            the dropdown sits above legend + weights + hover panel. */}
        <Box
          sx={{
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
          }}
        >
          <Box
            component="input"
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            placeholder="specs.search()"
            onChange={e => {
              setSearchQuery((e.target as HTMLInputElement).value);
              // Reset the keyboard-cursor inline: every keystroke produces
              // a fresh result ranking, so position 0 is the only sensible
              // default. Done here (rather than in a useEffect on
              // searchQuery) to satisfy set-state-in-effect.
              setSearchIdx(0);
            }}
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
            <Box
              sx={{
                mt: 0.5,
                bgcolor: 'var(--bg-surface)',
                border: '1px solid var(--rule)',
                borderRadius: '4px',
                overflow: 'hidden',
                boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
              }}
            >
              {searchMatches.length === 0 ? (
                <Box
                  aria-label="No matches"
                  sx={{
                    px: 1.25,
                    py: 0.75,
                    fontSize: fontSize.xs,
                    color: 'var(--ink-soft)',
                    fontFamily: typography.mono,
                    '& .subj': { opacity: 0.7 },
                  }}
                >
                  <span className="subj">results</span>.empty()
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
                      px: 1.25,
                      py: 0.75,
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
                    <Box
                      sx={{
                        flex: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
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
                  <Box
                    sx={{
                      width: 10,
                      height: 10,
                      bgcolor: color,
                      borderRadius: '2px',
                      flex: 'none',
                    }}
                  />
                  <Box component="span" sx={{ minWidth: 60 }}>
                    {t}
                  </Box>
                  <Box component="span" sx={{ opacity: 0.55, fontVariantNumeric: 'tabular-nums' }}>
                    {count}
                  </Box>
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
        <Box
          sx={{
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
          }}
        >
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
            <Box
              sx={{
                p: { xs: 1.25, sm: 2 },
                minWidth: { xs: 220, sm: 280 },
                border: '1px solid var(--rule)',
                borderRadius: '4px',
                bgcolor: 'var(--bg-surface)',
                display: 'flex',
                flexDirection: 'column',
                gap: { xs: 0.6, sm: 1.25 },
              }}
            >
              {TAG_CATEGORIES.map(cat => (
                <Box
                  key={cat}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: { xs: 1, sm: 1.5 },
                  }}
                >
                  <Box
                    component="span"
                    sx={{
                      minWidth: { xs: 78, sm: 100 },
                      fontFamily: typography.mono,
                      fontSize: fontSize.xs,
                    }}
                  >
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
                  <Box
                    component="span"
                    sx={{
                      minWidth: 28,
                      textAlign: 'right',
                      fontFamily: typography.mono,
                      fontSize: fontSize.xs,
                      fontVariantNumeric: 'tabular-nums',
                      color: 'var(--ink)',
                    }}
                  >
                    {weights[cat].toFixed(1)}
                  </Box>
                </Box>
              ))}
              {/* Edge-threshold slider — controls KNN_MIN_SIM, the cutoff
                  below which a candidate KNN edge is dropped. Lower = denser
                  graph (more cross-cluster bridges); higher = sparser graph
                  (cleaner clusters but more isolated outliers). */}
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: { xs: 1, sm: 1.5 },
                  pt: { xs: 0.25, sm: 0.5 },
                  borderTop: '1px dashed var(--rule)',
                }}
              >
                <Box
                  component="span"
                  sx={{
                    minWidth: { xs: 78, sm: 100 },
                    fontFamily: typography.mono,
                    fontSize: fontSize.xs,
                  }}
                >
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
                <Box
                  component="span"
                  sx={{
                    minWidth: 32,
                    textAlign: 'right',
                    fontFamily: typography.mono,
                    fontSize: fontSize.xs,
                    fontVariantNumeric: 'tabular-nums',
                    color: 'var(--ink)',
                  }}
                >
                  {minSim.toFixed(2)}
                </Box>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: { xs: 0, sm: 0.5 } }}>
                <Box
                  component="button"
                  onClick={resetWeights}
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
        {pinnedId && pinScreen && (
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
            // Phones + tablets: ~half the width, no tags. Otherwise the
            // panel covers the searched node + its connection lines after
            // fly-to. Desktop only: full 280 px panel with tag chips.
            width: { xs: 160, md: 280 },
            maxWidth: { xs: 'calc(60vw - 32px)', md: 'calc(100vw - 64px)' },
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
                    maxHeight: { xs: 110, md: 200 },
                    objectFit: 'contain',
                    bgcolor: isDark ? '#0a0a08' : '#FFFDF6',
                  }}
                />
              ) : (
                <Box
                  sx={{ height: { xs: 90, md: 158 }, bgcolor: isDark ? '#0a0a08' : '#FFFDF6' }}
                />
              )}
              <Box
                sx={{
                  p: { xs: 0.75, md: 1.25 },
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 0.5,
                }}
              >
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
                      // Phones + tablets: hide tags, the smaller panel
                      // only shows image + title + plot_type chip so it
                      // doesn't cover the focused node and its KNN edges.
                      display: { xs: 'none', md: 'flex' },
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
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <CircularProgress size={28} />
          </Box>
        )}
        {error && (
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--ink-soft)',
              fontFamily: typography.mono,
            }}
          >
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
            d3VelocityDecay={forceConfig.velocityDecay}
            d3AlphaDecay={forceConfig.alphaDecay}
            d3AlphaMin={forceConfig.alphaMin}
            nodeCanvasObject={(node, ctx, globalScale) => {
              const n = node as WithCoords;
              if (n.x == null || n.y == null) return;
              const isHover = hoverId === n.id;
              const isNeighbor = !isHover && hoverId != null && neighbors.get(hoverId)?.has(n.id);
              // hoverType is set when the user hovers a legend entry — match
              // any node in that cluster, dim the rest.
              const matchesType = hoverType == null || n.colorBucket === hoverType;
              const dim =
                (hoverId != null && !isHover && !isNeighbor) || (hoverType != null && !matchesType);
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
              ctx.strokeStyle = strokeFor(
                isDark,
                !!isHover,
                colorFor(n.colorBucket, graphData.topTypes)
              );
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
                return (
                  colorFor(hoverNode?.colorBucket ?? null, graphData.topTypes) ?? colors.primary
                );
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
            cooldownTicks={forceConfig.cooldownTicks}
            // Frame the dense cluster to ~80% of the viewport — instantly
            // (0 ms), so the camera move happens behind the still-active
            // gate overlay and the user just sees the final framing when
            // `settled` flips. The trick is bounding the *5th–95th
            // percentile* of node coordinates instead of the full bbox:
            // a couple of far-flung outliers (typically null-bucket specs
            // with no strong KNN edges) would otherwise dominate the bbox
            // and shrink the readable center to half its size. Outliers
            // remain reachable via pan.
            onEngineStop={() => {
              const fg = fgRef.current;
              if (fg) {
                const xs: number[] = [];
                const ys: number[] = [];
                for (const n of graphData.nodes as Array<MapNode & { x?: number; y?: number }>) {
                  if (n.x != null && n.y != null) {
                    xs.push(n.x);
                    ys.push(n.y);
                  }
                }
                if (xs.length > 0) {
                  xs.sort((a, b) => a - b);
                  ys.sort((a, b) => a - b);
                  const trim = 0.05;
                  const lo = Math.floor(xs.length * trim);
                  const hi = Math.floor(xs.length * (1 - trim));
                  const minX = xs[lo],
                    maxX = xs[hi],
                    minY = ys[lo],
                    maxY = ys[hi];
                  const cx = (minX + maxX) / 2;
                  const cy = (minY + maxY) / 2;
                  const bboxW = Math.max(1, maxX - minX);
                  const bboxH = Math.max(1, maxY - minY);
                  const padding = Math.round(Math.min(size.w, size.h) * 0.1);
                  const fitZoom = Math.min(
                    (size.w - 2 * padding) / bboxW,
                    (size.h - 2 * padding) / bboxH
                  );
                  fg.centerAt?.(cx, cy, 0);
                  fg.zoom?.(fitZoom, 0);
                }
              }
              markSettled();
            }}
            // Wire up the custom forces once the imperative ref is available.
            // The tuned values/factories come from the hook's forceConfig.
            // onRenderFramePre fires every frame; the __forcesWired guard makes
            // it idempotent and the cost on subsequent frames is one property read.
            onRenderFramePre={() => {
              const fg = fgRef.current;
              if (!fg || fg.__forcesWired) return;
              fg.d3Force('charge')?.strength(forceConfig.chargeStrength);
              // The d3-force-3d ambient types are minimal; cast for the chained calls.
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              const linkForce = fg.d3Force('link') as any;
              if (linkForce) {
                linkForce.distance(forceConfig.linkDistance);
                linkForce.strength(forceConfig.linkStrength);
              }
              fg.d3Force('collide', forceConfig.createCollideForce());
              fg.d3Force('center')?.strength?.(forceConfig.centerGravity);
              // Outlier-squash: register the custom radial-compression force
              // AFTER the standard ones so its velocity correction is the
              // last word per tick. Inner geometry is untouched (force is a
              // no-op below the percentile threshold), so this stacks on the
              // existing layout instead of fighting it.
              fg.d3Force('outlier-squash', forceConfig.createOutlierSquashForce());
              fg.__forcesWired = true;
              fg.d3ReheatSimulation?.();
            }}
            onEngineTick={handleEngineTick}
          />
        )}

        {/* Settling gate: visible while specs are loaded but the simulation
            hasn't finished cooling. Sits on top of the canvas, swallows
            pointer events, and shows a centered spinner + progress bar so
            non-technical users get an unmistakable signal that the map is
            *computing*, not broken. Renders as long as `ready` so the fade
            transition runs both ways — opacity drops to 0 after `settled`
            flips, then the next graphData re-derive fades it back in.
            pointerEvents flips to `none` once settled so canvas drags work
            even during the fade-out. */}
        {ready && (
          <Box
            aria-hidden={settled}
            sx={{
              position: 'absolute',
              inset: 0,
              pointerEvents: settled ? 'none' : 'auto',
              cursor: settled ? 'default' : 'wait',
              // Above the canvas (implicit 0), below all interactive
              // controls (search pill / legend / weights at z 2, corner
              // panel at 3, pin-marker at 4) so the gate only swallows
              // canvas pointer events — search, filters, etc. stay
              // usable while the simulation is still cooling.
              zIndex: 1,
              opacity: settled ? 0 : 1,
              transition: 'opacity 250ms ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              // Slight dim + blur so users register that the canvas is in
              // a transient state without losing the underlying preview of
              // where points are heading.
              bgcolor: isDark ? 'rgba(20, 20, 18, 0.55)' : 'rgba(252, 251, 243, 0.55)',
              backdropFilter: 'blur(2px)',
              WebkitBackdropFilter: 'blur(2px)',
            }}
          >
            <Box
              role="status"
              aria-live="polite"
              aria-label="Computing map layout"
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 1.25,
                px: 3,
                py: 2,
                fontFamily: typography.mono,
              }}
            >
              <CircularProgress size={48} thickness={4} />
              <Box
                sx={{
                  fontFamily: typography.mono,
                  fontSize: fontSize.sm,
                  color: 'var(--ink)',
                }}
              >
                map.simulate()
              </Box>
              {/* Hand-rolled thin progress bar — slimmer than MUI's
                  LinearProgress and avoids an extra import. Width
                  transitions on each batched tick-progress update so the
                  bar slides smoothly between throttle frames. */}
              <Box
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(tickProgress * 100)}
                aria-label="Layout computation progress"
                sx={{
                  width: 160,
                  height: 3,
                  borderRadius: 2,
                  bgcolor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
                  overflow: 'hidden',
                }}
              >
                <Box
                  sx={{
                    width: `${Math.round(tickProgress * 100)}%`,
                    height: '100%',
                    bgcolor: colors.primary,
                    transition: 'width 140ms linear',
                  }}
                />
              </Box>
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
