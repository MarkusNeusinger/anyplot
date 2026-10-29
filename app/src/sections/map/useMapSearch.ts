import { useEffect, useRef, useState } from 'react';

import { type MapNode, type SpecMapItem } from 'src/pages/MapPage.helpers';

export function useMapSearch({
  nodeById,
  fgRef,
  setHoverId,
  setPinnedId,
  setSearchQuery,
  trackEvent,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  nodeById: Map<string, any>;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  fgRef: React.RefObject<any>;
  setHoverId: (id: string | null) => void;
  setPinnedId: (id: string | null) => void;
  setSearchQuery: (q: string) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  trackEvent: (event: string, properties?: any) => void;
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
