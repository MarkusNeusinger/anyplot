import { useEffect, useRef, useState } from 'react';

import type { useAnalytics } from 'src/hooks';
import { type ForceGraphHandle, type MapNode, type SpecMapItem } from 'src/pages/MapPage.helpers';

export function useMapSearch({
  nodeById,
  fgRef,
  setHoverId,
  setPinnedId,
  setSearchQuery,
  trackEvent,
}: {
  nodeById: Map<string, MapNode>;
  fgRef: React.RefObject<ForceGraphHandle>;
  setHoverId: (id: string | null) => void;
  setPinnedId: (id: string | null) => void;
  setSearchQuery: (q: string) => void;
  trackEvent: ReturnType<typeof useAnalytics>['trackEvent'];
}) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchIdx, setSearchIdx] = useState(0);
  const searchInputRef = useRef<HTMLInputElement | null>(null);

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

  return {
    searchOpen,
    setSearchOpen,
    searchIdx,
    setSearchIdx,
    searchInputRef,
    flyTo,
    selectMatch,
  };
}
