import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { MapNode, SpecMapItem } from 'src/pages/MapPage.helpers';

import { useMapSearch } from './useMapSearch';

function node(id: string, x?: number, y?: number): MapNode & { x?: number; y?: number } {
  return {
    id,
    title: id,
    tags: [],
    thumbUrl: null,
    imgs: new Map(),
    pendingTiers: new Set(),
    colorBucket: null,
    x,
    y,
  };
}

function setup(nodes: MapNode[] = [], fg: object | null = { centerAt: vi.fn(), zoom: vi.fn() }) {
  const deps = {
    nodeById: new Map(nodes.map(n => [n.id, n])),
    fgRef: { current: fg },
    setHoverId: vi.fn(),
    setPinnedId: vi.fn(),
    setSearchQuery: vi.fn(),
    trackEvent: vi.fn(),
  };
  const hook = renderHook(() => useMapSearch(deps));
  return { ...hook, deps, fg };
}

describe('useMapSearch', () => {
  it('starts closed, on the first match, with no input attached', () => {
    const { result } = setup();

    expect(result.current.searchOpen).toBe(false);
    expect(result.current.searchIdx).toBe(0);
    expect(result.current.searchInputRef.current).toBeNull();
  });

  it('focuses and selects the search input on Cmd+K and Ctrl+K', () => {
    const { result } = setup();
    const input = document.createElement('input');
    const select = vi.spyOn(input, 'select');
    document.body.appendChild(input);
    result.current.searchInputRef.current = input;

    for (const mod of [{ metaKey: true }, { ctrlKey: true }]) {
      input.blur();
      const event = new KeyboardEvent('keydown', { key: 'K', cancelable: true, ...mod });
      window.dispatchEvent(event);
      expect(document.activeElement).toBe(input);
      expect(event.defaultPrevented).toBe(true);
    }
    expect(select).toHaveBeenCalledTimes(2);

    // A plain K is typing, not the shortcut.
    input.blur();
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k' }));
    expect(document.activeElement).not.toBe(input);
    input.remove();
  });

  it('stops listening for the shortcut on unmount', () => {
    const remove = vi.spyOn(window, 'removeEventListener');
    const { unmount } = setup();

    unmount();
    expect(remove).toHaveBeenCalledWith('keydown', expect.any(Function));
    remove.mockRestore();
  });

  it('selectMatch flies to the node, pins it, clears the query, closes the popup, and tracks it', () => {
    const { result, deps, fg } = setup([node('scatter-basic', 10, 20)]);
    act(() => result.current.setSearchOpen(true));

    act(() => result.current.selectMatch({ id: 'scatter-basic' } as SpecMapItem));

    const graph = fg as { centerAt: ReturnType<typeof vi.fn>; zoom: ReturnType<typeof vi.fn> };
    expect(graph.centerAt).toHaveBeenCalledWith(10, 20, 800);
    expect(graph.zoom).toHaveBeenCalledWith(2.0, 800);
    expect(deps.setHoverId).toHaveBeenCalledWith('scatter-basic');
    expect(deps.setPinnedId).toHaveBeenCalledWith('scatter-basic');
    expect(deps.setSearchQuery).toHaveBeenCalledWith('');
    expect(result.current.searchOpen).toBe(false);
    expect(deps.trackEvent).toHaveBeenCalledWith('map_search_select', { spec: 'scatter-basic' });
  });

  it('flyTo does nothing before the graph or the node position exists', () => {
    const noGraph = setup([node('a', 1, 2)], null);
    noGraph.result.current.flyTo('a');
    expect(noGraph.deps.setHoverId).not.toHaveBeenCalled();

    const unplaced = setup([node('b')]);
    unplaced.result.current.flyTo('b');
    const graph = unplaced.fg as { centerAt: ReturnType<typeof vi.fn> };
    expect(graph.centerAt).not.toHaveBeenCalled();
    expect(unplaced.deps.setHoverId).not.toHaveBeenCalled();
  });
});
