import { useEffect, useRef } from 'react';

import { Link, useNavigate } from 'react-router-dom';

import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';

import { useAnalytics } from 'src/hooks';
import { useForceGraphSimulation } from 'src/hooks/useForceGraphSimulation';
import { type MapNode } from 'src/pages/MapPage.helpers';
import { specPath } from 'src/routes/paths';
import {
  MapCanvas,
  MapHoverPanel,
  MapLegend,
  MapSearchPill,
  MapWeights,
  useMapResize,
  useMapSearch,
  useMapSelection,
} from 'src/sections/map';
import { fontSize, typography } from 'src/theme';

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

export function MapPage() {
  const { trackPageview, trackEvent } = useAnalytics();
  const navigate = useNavigate();

  // refs
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null);

  // 1. page view
  useEffect(() => {
    trackPageview('/map');
  }, [trackPageview]);

  const { containerRef, size } = useMapResize();

  // Simulation/data orchestration: spec loading, weights, the KNN graph
  // derivation, settling gate, search matching, and force tuning all live
  // in the hook.
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

  const {
    hoverId,
    setHoverId,
    pinnedId,
    setPinnedId,
    pinScreen,
    hoverType,
    setHoverType,
    hoverTimerRef,
    panelData,
    pinColor,
  } = useMapSelection({
    graphData,
    nodeById,
    fgRef,
  });

  const { searchOpen, setSearchOpen, searchIdx, setSearchIdx, searchInputRef, selectMatch } =
    useMapSearch({
      nodeById,
      fgRef,
      setHoverId,
      setPinnedId,
      setSearchQuery,
      trackEvent,
    });

  const hasHover = useMediaQuery('(hover: hover)', { noSsr: true });

  const onNodeClick = (node: MapNode) => {
    if (!hasHover && pinnedId !== node.id) {
      setPinnedId(node.id);
      setHoverId(node.id);
      trackEvent('map_node_pin', { spec: node.id });
      return;
    }
    trackEvent('map_node_click', { spec: node.id });
    navigate(specPath(node.id));
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
        sx={{
          mx: { xs: -2, sm: -4, md: -8, lg: -12 },
          height: { xs: 'calc(100svh - 140px)', sm: 'calc(100svh - 180px)' },
          minHeight: 320,
          position: 'relative',
          bgcolor: 'var(--bg-page)',
          overflow: 'hidden',
        }}
        role="region"
        aria-label="Force-directed map of anyplot specifications, clustered by tag similarity"
      >
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
          searchInputRef={searchInputRef}
          searchMatches={searchMatches}
          selectMatch={selectMatch}
        />

        <MapLegend
          graphData={graphData}
          activeCategory={activeCategory}
          hoverType={hoverType}
          setHoverType={setHoverType}
        />

        <MapWeights
          weights={weights}
          setWeights={setWeights}
          minSim={minSim}
          setMinSim={setMinSim}
          resetWeights={resetWeights}
        />

        {pinScreen && pinnedId && (
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

        <MapHoverPanel hoverId={hoverId} pinnedId={pinnedId} panelData={panelData} />

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

        <MapCanvas
          ready={ready}
          fgRef={fgRef}
          graphData={graphData}
          size={size}
          forceConfig={forceConfig}
          hoverId={hoverId}
          hoverType={hoverType}
          nodeById={nodeById}
          neighbors={neighbors}
          onNodeClick={onNodeClick}
          setPinnedId={setPinnedId}
          setHoverId={setHoverId}
          hoverTimerRef={hoverTimerRef}
          markSettled={markSettled}
          handleEngineTick={handleEngineTick}
          settled={settled}
          tickProgress={tickProgress}
        />

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
