import ForceGraph2D from 'react-force-graph-2d';

import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';

import { colorFor, NODE_SIZE } from 'src/hooks/useForceGraphSimulation';
import { useTheme } from 'src/hooks/useLayoutContext';
import {
  ensureNodeTier,
  fitToBox,
  type MapLink,
  type MapNode,
  nodeAspectRatio,
  pickBestLoadedTier,
  pickTier,
  type ResolutionTier,
} from 'src/pages/MapPage.helpers';
import { colors, fontSize, typography } from 'src/theme';

interface MapCanvasProps {
  ready: boolean;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fgRef: React.RefObject<any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  graphData: any;
  size: { w: number; h: number };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  forceConfig: any;
  hoverId: string | null;
  hoverType: string | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  nodeById: Map<string, any>;
  neighbors: Map<string, Set<string>>;
  onNodeClick: (node: MapNode) => void;
  setPinnedId: (id: string | null) => void;
  setHoverId: (id: string | null) => void;
  hoverTimerRef: React.MutableRefObject<number | null>;
  markSettled: () => void;
  handleEngineTick: () => void;
  settled: boolean;
  tickProgress: number;
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

type WithCoords = MapNode & { x?: number; y?: number };

export function MapCanvas({
  ready,
  fgRef,
  graphData,
  size,
  forceConfig,
  hoverId,
  hoverType,
  nodeById,
  neighbors,
  onNodeClick,
  setPinnedId,
  setHoverId,
  hoverTimerRef,
  markSettled,
  handleEngineTick,
  settled,
  tickProgress,
}: MapCanvasProps) {
  const { isDark } = useTheme();

  return (
    <>
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
    </>
  );
}
