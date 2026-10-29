import type React from 'react';

import ForceGraph2D from 'react-force-graph-2d';

import { colorFor, NODE_SIZE } from 'src/hooks/useForceGraphSimulation';
import {
  ensureNodeTier,
  fitToBox,
  type MapLink,
  type MapNode,
  nodeAspectRatio,
  pickBestLoadedTier,
  pickTier,
  type ResolutionTier,
} from 'src/sections/map/MapPage.helpers';
import { colors } from 'src/theme';

type WithCoords = MapNode & { x?: number; y?: number };

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

export function MapCanvas({
  ready,
  fgRef,
  graphData,
  size,
  forceConfig,
  hoverId,
  setHoverId,
  hoverType,
  neighbors,
  isDark,
  nodeById,
  onNodeClick,
  setPinnedId,
  hoverTimerRef,
  markSettled,
  handleEngineTick,
}: {
  ready: boolean;
  fgRef: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  graphData: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  size: { w: number; h: number };
  forceConfig: any; // eslint-disable-line @typescript-eslint/no-explicit-any
  hoverId: string | null;
  setHoverId: (id: string | null) => void;
  hoverType: string | null;
  neighbors: Map<string, Set<string>>;
  isDark: boolean;
  nodeById: Map<string, MapNode>;
  onNodeClick: (node: MapNode) => void;
  setPinnedId: (id: string | null) => void;
  hoverTimerRef: React.MutableRefObject<number | null>;
  markSettled: () => void;
  handleEngineTick: () => void;
}) {
  if (!ready) return null;

  return (
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
        const matchesType = hoverType == null || n.colorBucket === hoverType;
        const dim =
          (hoverId != null && !isHover && !isNeighbor) || (hoverType != null && !matchesType);
        const baseSize = NODE_SIZE * (isNeighbor ? 1.2 : 1);

        const screenPx = baseSize * (globalScale ?? 1);
        const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
        const desired: ResolutionTier = pickTier(screenPx * dpr);
        if (n.imgs && !n.imgs.has(desired) && !n.pendingTiers?.has(desired)) {
          ensureNodeTier(n, desired, () => fgRef.current?.refresh?.());
        }
        const img = n.imgs ? pickBestLoadedTier(n.imgs, desired) : null;

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
      linkColor={(l: MapLink) => {
        const sId = linkEndId(l.source);
        const tId = linkEndId(l.target);
        const involved = hoverId && (sId === hoverId || tId === hoverId);
        if (involved) {
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
      onRenderFramePre={() => {
        const fg = fgRef.current;
        if (!fg || fg.__forcesWired) return;
        fg.d3Force('charge')?.strength(forceConfig.chargeStrength);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const linkForce = fg.d3Force('link') as any;
        if (linkForce) {
          linkForce.distance(forceConfig.linkDistance);
          linkForce.strength(forceConfig.linkStrength);
        }
        fg.d3Force('collide', forceConfig.createCollideForce());
        fg.d3Force('center')?.strength?.(forceConfig.centerGravity);
        fg.d3Force('outlier-squash', forceConfig.createOutlierSquashForce());
        fg.__forcesWired = true;
        fg.d3ReheatSimulation?.();
      }}
      onEngineTick={handleEngineTick}
    />
  );
}
