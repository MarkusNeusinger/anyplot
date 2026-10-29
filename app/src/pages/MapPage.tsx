import { useEffect, useMemo, useRef, useState } from 'react';

import { Link, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useAnalytics } from 'src/hooks';
import {
  CLUSTER_COLORS,
  colorFor,
  NODE_SIZE,
  useForceGraphSimulation,
} from 'src/hooks/useForceGraphSimulation';
import { useTheme } from 'src/hooks/useLayoutContext';
import {
  buildVariantUrl,
  fitToBox,
  type MapNode,
  nodeAspectRatio,
  type SpecMapItem,
} from 'src/pages/MapPage.helpers';
import { specPath } from 'src/routes/paths';
import type { ForceGraphInstance } from 'src/sections/map/MapForceGraph';
import { MapForceGraph } from 'src/sections/map/MapForceGraph';
import { MapHoverPanel } from 'src/sections/map/MapHoverPanel';
import { MapLegend } from 'src/sections/map/MapLegend';
import { visuallyHiddenSx } from 'src/sections/map/MapPage.utils';
import { MapPinMarker } from 'src/sections/map/MapPinMarker';
import { MapSearchPill } from 'src/sections/map/MapSearchPill';
import { MapSettlingGate } from 'src/sections/map/MapSettlingGate';
import { MapWeightsPanel } from 'src/sections/map/MapWeightsPanel';
import { colors, fontSize, typography } from 'src/theme';

export function MapPage() {
  const { trackPageview, trackEvent } = useAnalytics();
  const { isDark } = useTheme();
  const navigate = useNavigate();

  // refs
  // ForceGraph2D's TypeScript surface for the imperative ref is non-trivial; the
  // generated types live in dist and aren't worth re-typing here. Treat as opaque.
  const fgRef = useRef<ForceGraphInstance>(null);
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

  // Clean up unknown pending hover-debounce timer on unmount.
  useEffect(() => {
    // capture the ref for cleanup
    const timerRef = hoverTimerRef;
    return () => {
      if (timerRef.current != null) {
        window.clearTimeout(timerRef.current);
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

  // Cmd/Ctrl+K focuses the search pill from unknownwhere on the page. Always
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
      <>
        <title>map() — unknownplot</title>
        <meta
          name="description"
          content="Interactive map of all unknownplot specifications, clustered by tag similarity."
        />
      </>
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
        aria-label="Force-directed map of unknownplot specifications, clustered by tag similarity"
      >
        {/* Header overlay with tiny meta. On phones the search pill takes
            the top row so the meta drops to a second row. left values
            mirror RootLayout's container px in raw pixels (sx `left` is
            NOT spacing-aware, unlike `px`/`mx`) so the text aligns with
            the unknownplot logo / nav links. */}
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

        <MapSearchPill
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          searchOpen={searchOpen}
          setSearchOpen={setSearchOpen}
          searchIdx={searchIdx}
          setSearchIdx={setSearchIdx}
          searchMatches={searchMatches}
          searchInputRef={searchInputRef}
          selectMatch={selectMatch}
        />

        <MapLegend
          graphData={graphData}
          legendOpen={legendOpen}
          setLegendOpen={setLegendOpen}
          activeCategory={activeCategory}
          hoverType={hoverType}
          setHoverType={setHoverType}
        />
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

        <MapWeightsPanel
          weights={weights}
          setWeights={setWeights}
          minSim={minSim}
          setMinSim={setMinSim}
          resetWeights={resetWeights}
          weightsOpen={weightsOpen}
          setWeightsOpen={setWeightsOpen}
        />

        <MapPinMarker pinnedId={pinnedId} pinScreen={pinScreen} pinColor={pinColor} />

        {/* Hover panel: fixed bottom-right, fades in/out on hover. Lives in
            the DOM so its size is independent of zoom level and never clips
            at the viewport edge. Pointer-transparent so it never steals
            hover detection from canvas nodes underneath. */}
        <MapHoverPanel
          hoverId={hoverId}
          pinnedId={pinnedId}
          panelData={panelData}
          isDark={isDark}
        />

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
          <MapForceGraph
            fgRef={fgRef}
            graphData={graphData}
            size={size}
            forceConfig={forceConfig}
            hoverId={hoverId}
            hoverType={hoverType}
            neighbors={neighbors}
            nodeById={nodeById}
            isDark={isDark}
            onNodeClick={onNodeClick}
            setPinnedId={setPinnedId}
            setHoverId={setHoverId}
            hoverTimerRef={hoverTimerRef}
            markSettled={markSettled}
            handleEngineTick={handleEngineTick}
          />
        )}

        <MapSettlingGate
          ready={ready}
          settled={settled}
          isDark={isDark}
          tickProgress={tickProgress}
        />

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
