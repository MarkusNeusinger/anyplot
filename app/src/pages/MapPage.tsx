import { useEffect, useMemo, useRef, useState } from 'react';

import { useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useAnalytics } from 'src/hooks';
import { colorFor, useForceGraphSimulation } from 'src/hooks/useForceGraphSimulation';
import { useTheme } from 'src/hooks/useLayoutContext';
import { specPath } from 'src/routes/paths';
import {
  buildVariantUrl,
  MapA11yFallback,
  MapCanvas,
  MapHeader,
  MapHoverPanel,
  MapLegend,
  MapLoadingError,
  type MapNode,
  MapPinMarker,
  MapSearch,
  MapSettlingGate,
  MapWeights,
} from 'src/sections/map';
import { colors } from 'src/theme';

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
    forceConfig,
    searchQuery,
    setSearchQuery,
    searchMatches,
    tickProgress,
    handleEngineTick,
  } = useForceGraphSimulation();

  // UI state
  const [size, setSize] = useState({ w: 0, h: 0 });
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [hoverType, setHoverType] = useState<string | null>(null);
  const [pinnedId, setPinnedId] = useState<string | null>(null);
  const [pinScreen, setPinScreen] = useState<{ x: number; y: number; w: number; h: number } | null>(
    null
  );
  const [weightsOpen, setWeightsOpen] = useState(false);
  const [legendOpen, setLegendOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchIdx, setSearchIdx] = useState(0);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const lastPanelNodeIdRef = useRef<string | null>(null);
  const hoverTimerRef = useRef<number | null>(null);

  // 1. mount effects
  useEffect(() => {
    trackPageview('/map');
  }, [trackPageview]);

  // Read raw container dims via ResizeObserver instead of window events
  // so we correctly handle layout shifts (e.g. scrollbars appearing) and
  // don't assume the canvas is perfectly full-bleed.
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
    const timer = hoverTimerRef.current;
    return () => {
      if (timer != null) {
        window.clearTimeout(timer);
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
      if (pinnedId && fgRef.current) {
        const n = nodeById.get(pinnedId) as MapNode & { x?: number; y?: number };
        if (n?.x != null && n?.y != null) {
          try {
            const sc = fgRef.current.graph2ScreenCoords(n.x, n.y);
            const zoom = fgRef.current.zoom();
            // Match the bounding-box logic in nodeCanvasObject so the pulse
            // frame exactly hugs the rendered thumbnail.
            const size = 18 * zoom;
            const w = size;
            const h = (size * 9) / 16;
            setPinScreen(prev => {
              if (
                !prev ||
                Math.abs(prev.x - (sc.x - w / 2)) > 0.5 ||
                Math.abs(prev.y - (sc.y - h / 2)) > 0.5 ||
                Math.abs(prev.w - w) > 0.5
              ) {
                return { x: sc.x - w / 2, y: sc.y - h / 2, w, h };
              }
              return prev;
            });
          } catch {
            // graph2ScreenCoords throws if the canvas isn't fully initialized
            // (e.g. during a rapid mount/unmount cycle). We can safely ignore
            // it — the loop will catch up on the next tick.
          }
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
  // active (unbound in useEffect teardown).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setSearchOpen(true);
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
      // which is redundant.
      setHoverId(null);
      setPinnedId(node.id);
      trackEvent('map_node_pin', { spec: node.id });
      return;
    }
    // Desktop (where hover already showed the preview) OR touch device
    // tapping an already-pinned node: navigate to the spec detail.
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

  const selectMatch = (spec: { id: string }) => {
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
        <title>map() — anyplot</title>
        <meta
          name="description"
          content="Interactive map of all anyplot specifications, clustered by tag similarity."
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
        aria-label="Force-directed map of anyplot specifications, clustered by tag similarity"
      >
        <MapHeader specsCount={specs?.length} edgesCount={graphData.links.length} />

        <MapSearch
          searchInputRef={searchInputRef}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          searchIdx={searchIdx}
          setSearchIdx={setSearchIdx}
          searchOpen={searchOpen}
          setSearchOpen={setSearchOpen}
          searchMatches={searchMatches}
          selectMatch={selectMatch}
        />

        <MapLegend
          topTypes={graphData.topTypes}
          typeCounts={graphData.typeCounts}
          legendOpen={legendOpen}
          setLegendOpen={setLegendOpen}
          activeCategory={activeCategory}
          hoverType={hoverType}
          setHoverType={setHoverType}
        />

        <MapWeights
          weightsOpen={weightsOpen}
          setWeightsOpen={setWeightsOpen}
          weights={weights}
          setWeights={setWeights}
          minSim={minSim}
          setMinSim={setMinSim}
          resetWeights={resetWeights}
        />

        <MapPinMarker pinnedId={pinnedId} pinScreen={pinScreen} pinColor={pinColor} />

        <MapHoverPanel
          hoverId={hoverId}
          pinnedId={pinnedId}
          panelData={panelData}
          isDark={isDark}
        />

        <MapLoadingError specs={specs} error={error} />

        <MapCanvas
          ready={ready}
          fgRef={fgRef}
          graphData={graphData}
          size={size}
          forceConfig={forceConfig}
          hoverId={hoverId}
          setHoverId={setHoverId}
          hoverType={hoverType}
          neighbors={neighbors}
          isDark={isDark}
          nodeById={nodeById}
          onNodeClick={onNodeClick}
          setPinnedId={setPinnedId}
          hoverTimerRef={hoverTimerRef}
          markSettled={markSettled}
          handleEngineTick={handleEngineTick}
        />

        <MapSettlingGate
          ready={ready}
          settled={settled}
          isDark={isDark}
          tickProgress={tickProgress}
        />

        <MapA11yFallback specs={specs} />
      </Box>
    </>
  );
}
