import { useEffect, useMemo, useRef, useState } from 'react';

import { colorFor, NODE_SIZE } from 'src/hooks/useForceGraphSimulation';
import {
  buildVariantUrl,
  fitToBox,
  type MapNode,
  nodeAspectRatio,
} from 'src/pages/MapPage.helpers';
import { colors } from 'src/theme';

export function useMapSelection({
  graphData,
  nodeById,
  fgRef,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  graphData: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  nodeById: Map<string, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fgRef: React.RefObject<any>;
}) {
  const [hoverId, setHoverId] = useState<string | null>(null);
  const lastPanelNodeIdRef = useRef<string | null>(null);
  const [pinnedId, setPinnedId] = useState<string | null>(null);
  const [pinScreen, setPinScreen] = useState<{ x: number; y: number; w: number; h: number } | null>(
    null
  );
  const hoverTimerRef = useRef<number | null>(null);
  const [hoverType, setHoverType] = useState<string | null>(null);

  const panelNodeId = hoverId ?? pinnedId ?? lastPanelNodeIdRef.current;
  if (panelNodeId !== null) lastPanelNodeIdRef.current = panelNodeId;

  useEffect(() => {
    const timer = hoverTimerRef.current;
    return () => {
      if (timer != null) {
        window.clearTimeout(timer);
      }
    };
  }, []);

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
  }, [pinnedId, graphData, nodeById, fgRef]);

  const panelData = useMemo(() => {
    if (!panelNodeId) return null;
    const node = nodeById.get(panelNodeId);
    if (!node) return null;
    const ptTag = node.tags.find((t: string) => t.startsWith('plot_type:'));
    const plotType = ptTag ? ptTag.slice('plot_type:'.length) : null;
    const tags = node.tags
      .filter((t: string) => !t.startsWith('plot_type:'))
      .map((t: string) => ({ tag: t, w: graphData.idf.get(t) ?? 0 }))
      .filter((x: { w: number }) => x.w > 0)
      .sort((a: { w: number }, b: { w: number }) => b.w - a.w)
      .slice(0, 4)
      .map((x: { tag: string }) => x.tag);
    return {
      title: node.title,
      plotType,
      chipColor: plotType ? colorFor(plotType, graphData.topTypes) : null,
      tags,
      previewUrl: node.thumbUrl ? buildVariantUrl(node.thumbUrl, 800) : null,
    };
  }, [panelNodeId, graphData, nodeById]);

  const pinColor = useMemo(() => {
    if (!pinnedId) return colors.primary;
    const node = nodeById.get(pinnedId);
    if (!node) return colors.primary;
    return colorFor(node.colorBucket, graphData.topTypes) ?? colors.primary;
  }, [pinnedId, nodeById, graphData.topTypes]);

  return {
    hoverId,
    setHoverId,
    pinnedId,
    setPinnedId,
    pinScreen,
    hoverType,
    setHoverType,
    hoverTimerRef,
    panelNodeId,
    panelData,
    pinColor,
  };
}
