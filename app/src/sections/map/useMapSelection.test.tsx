import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { CLUSTER_COLORS, type MapGraphData, NODE_SIZE } from 'src/hooks/useForceGraphSimulation';
import { fitToBox, type MapNode, nodeAspectRatio } from 'src/pages/MapPage.helpers';
import { colors } from 'src/theme';

import { useMapSelection } from './useMapSelection';

function node(overrides: Partial<MapNode> & { id: string }): MapNode {
  return {
    title: overrides.id,
    tags: [],
    thumbUrl: null,
    imgs: new Map(),
    pendingTiers: new Set(),
    colorBucket: null,
    ...overrides,
  };
}

function graph(overrides: Partial<MapGraphData> = {}): MapGraphData {
  return {
    nodes: [],
    links: [],
    topTypes: [],
    typeCounts: new Map(),
    idf: new Map(),
    ...overrides,
  };
}

function setup(nodes: MapNode[] = [], graphData: MapGraphData = graph(), fg: object | null = null) {
  const nodeById = new Map(nodes.map(n => [n.id, n]));
  return renderHook(() => useMapSelection({ graphData, nodeById, fgRef: { current: fg } }));
}

describe('useMapSelection', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('starts with nothing hovered, pinned, or shown', () => {
    const { result } = setup();

    expect(result.current.hoverId).toBeNull();
    expect(result.current.pinnedId).toBeNull();
    expect(result.current.pinScreen).toBeNull();
    expect(result.current.hoverType).toBeNull();
    expect(result.current.panelNodeId).toBeNull();
    expect(result.current.panelData).toBeNull();
    expect(result.current.pinColor).toBe(colors.primary);
  });

  it('debounces a node hover by 100 ms and clears it at once on leave', () => {
    vi.useFakeTimers();
    const a = node({ id: 'a' });
    const { result } = setup([a]);

    act(() => result.current.handleNodeHover(a));
    act(() => vi.advanceTimersByTime(99));
    expect(result.current.hoverId).toBeNull();
    act(() => vi.advanceTimersByTime(1));
    expect(result.current.hoverId).toBe('a');

    act(() => result.current.handleNodeHover(null));
    expect(result.current.hoverId).toBeNull();
  });

  it('a newer hover cancels the pending one', () => {
    vi.useFakeTimers();
    const a = node({ id: 'a' });
    const b = node({ id: 'b' });
    const { result } = setup([a, b]);

    act(() => result.current.handleNodeHover(a));
    act(() => vi.advanceTimersByTime(50));
    act(() => result.current.handleNodeHover(b));
    act(() => vi.advanceTimersByTime(100));
    expect(result.current.hoverId).toBe('b');
  });

  it('clears a pending hover timer on unmount', () => {
    vi.useFakeTimers();
    const clear = vi.spyOn(window, 'clearTimeout');
    const a = node({ id: 'a' });
    const { result, unmount } = setup([a]);

    act(() => result.current.handleNodeHover(a));
    clear.mockClear();
    unmount();
    expect(clear).toHaveBeenCalledTimes(1);
    expect(vi.getTimerCount()).toBe(0);
    clear.mockRestore();
  });

  it('derives the panel from the hovered node: plot type, top tags by IDF, preview tier', () => {
    const a = node({
      id: 'a',
      title: 'Basic Scatter',
      thumbUrl: 'https://cdn.example/plot-light.png',
      tags: ['plot_type:scatter', 'domain:finance', 'feature:hover', 'style:dark', 'rare', 'zero'],
    });
    const idf = new Map([
      ['domain:finance', 0.5],
      ['feature:hover', 0.9],
      ['style:dark', 0.2],
      ['rare', 1.5],
      ['zero', 0],
    ]);
    const { result } = setup([a], graph({ idf, topTypes: ['scatter'] }));

    act(() => result.current.setHoverId('a'));

    expect(result.current.panelNodeId).toBe('a');
    expect(result.current.panelData).toEqual({
      title: 'Basic Scatter',
      plotType: 'scatter',
      chipColor: expect.any(String),
      tags: ['rare', 'feature:hover', 'domain:finance', 'style:dark'],
      previewUrl: 'https://cdn.example/plot-light_800.webp',
    });
  });

  it('keeps showing the last node after the hover ends, and prefers the pin', () => {
    const a = node({ id: 'a' });
    const b = node({ id: 'b' });
    const { result } = setup([a, b]);

    act(() => result.current.setHoverId('a'));
    act(() => result.current.setHoverId(null));
    expect(result.current.panelNodeId).toBe('a');

    act(() => result.current.setPinnedId('b'));
    expect(result.current.panelNodeId).toBe('b');
  });

  it('colours the pin by its cluster, with the primary colour as fallback', () => {
    // Slot 1, because slot 0 of CLUSTER_COLORS is the brand green itself.
    const inCluster = node({ id: 'a', colorBucket: 'bar' });
    const outside = node({ id: 'b', colorBucket: null });
    const { result } = setup([inCluster, outside], graph({ topTypes: ['scatter', 'bar'] }));

    act(() => result.current.setPinnedId('a'));
    expect(result.current.pinColor).toBe(CLUSTER_COLORS[1]);

    act(() => result.current.setPinnedId('b'));
    expect(result.current.pinColor).toBe(colors.primary);
  });

  it('tracks the pinned node on screen each frame and stops when the pin goes', () => {
    const frames: FrameRequestCallback[] = [];
    vi.stubGlobal('requestAnimationFrame', (cb: FrameRequestCallback) => frames.push(cb));
    const cancel = vi.fn();
    vi.stubGlobal('cancelAnimationFrame', cancel);
    const a = Object.assign(node({ id: 'a' }), { x: 100, y: 50 });
    const screenPos = { x: 400, y: 300 };
    const fg = { graph2ScreenCoords: vi.fn(() => screenPos), zoom: vi.fn(() => 2) };
    const { result } = setup([a], graph(), fg);

    act(() => result.current.setPinnedId('a'));
    act(() => frames[frames.length - 1](0));

    const { w, h } = fitToBox(NODE_SIZE, nodeAspectRatio(a));
    expect(fg.graph2ScreenCoords).toHaveBeenCalledWith(100, 50);
    expect(result.current.pinScreen).toEqual({ x: 400 - w, y: 300 - h, w: 2 * w, h: 2 * h });

    // An unchanged position keeps the same object, so nothing re-renders.
    const first = result.current.pinScreen;
    act(() => frames[frames.length - 1](16));
    expect(result.current.pinScreen).toBe(first);

    screenPos.x = 420;
    act(() => frames[frames.length - 1](32));
    expect(result.current.pinScreen?.x).toBe(420 - w);

    act(() => result.current.setPinnedId(null));
    expect(cancel).toHaveBeenCalled();
  });
});
