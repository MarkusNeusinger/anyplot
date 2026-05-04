import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { forwardRef, useImperativeHandle } from 'react';

import { act, render, screen, waitFor } from '../test-utils';
import { MapPage } from './MapPage';


vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockNavigate = vi.fn();
const mockTrackEvent = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('../hooks', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: mockTrackEvent,
  }),
}));

vi.mock('../hooks/useLayoutContext', () => ({
  useTheme: () => ({ isDark: false }),
}));

// Default to "(hover: hover)" matching → desktop behaviour. Touch-specific
// branches (e.g. tap-to-pin) need a per-test override via mockHasHover.
const mockHasHover = { current: true };
vi.mock('@mui/material/useMediaQuery', () => ({
  default: () => mockHasHover.current,
}));

// Capture the props passed to ForceGraph2D so individual callbacks can be exercised
// from outside React. A live canvas can't run in jsdom, but the callbacks (drawNode,
// onNodeClick, linkColor, …) are pure-ish JS and worth testing in isolation.
type FgProps = Record<string, unknown>;
const lastFgProps: { current: FgProps | null } = { current: null };

// Mock instance returned via ref. The page calls imperative methods like
// `fgRef.current?.centerAt(...)` from `onEngineStop`; without forwardRef the
// ref would be null and those branches would silently early-return.
type FgInstance = {
  centerAt: ReturnType<typeof vi.fn>;
  zoom: ReturnType<typeof vi.fn>;
  zoomToFit: ReturnType<typeof vi.fn>;
  d3Force: ReturnType<typeof vi.fn>;
  d3ReheatSimulation: ReturnType<typeof vi.fn>;
  refresh: ReturnType<typeof vi.fn>;
  __forcesWired?: boolean;
};
const fgInstance: FgInstance = {
  centerAt: vi.fn(),
  zoom: vi.fn().mockReturnValue(1),
  zoomToFit: vi.fn(),
  d3Force: vi.fn().mockReturnValue({ strength: vi.fn().mockReturnThis(), distance: vi.fn().mockReturnThis() }),
  d3ReheatSimulation: vi.fn(),
  refresh: vi.fn(),
};

vi.mock('react-force-graph-2d', () => ({
  default: forwardRef<FgInstance, FgProps>((props, ref) => {
    lastFgProps.current = props;
    useImperativeHandle(ref, () => fgInstance, []);
    const data = props.graphData as { nodes: unknown[]; links: unknown[] };
    return (
      <div
        data-testid="force-graph-2d"
        data-node-count={data.nodes.length}
        data-link-count={data.links.length}
      />
    );
  }),
}));


function makeCtxStub() {
  // Minimal mock of CanvasRenderingContext2D — just enough surface for drawNode/paintHitbox.
  return {
    save: vi.fn(),
    restore: vi.fn(),
    drawImage: vi.fn(),
    fillRect: vi.fn(),
    strokeRect: vi.fn(),
    fillStyle: '',
    strokeStyle: '',
    lineWidth: 0,
    globalAlpha: 1,
  };
}


const mockSpecs = [
  {
    id: 'scatter-basic',
    title: 'Basic Scatter Plot',
    preview_url_light: 'https://example.com/scatter-basic-light.png',
    preview_url_dark: 'https://example.com/scatter-basic-dark.png',
    quality_score: 90,
    tags: { plot_type: ['scatter'], data_type: ['numeric'], features: ['basic'] },
    impl_tags: { dependencies: ['scipy'] },
  },
  {
    id: 'scatter-color-mapped',
    title: 'Scatter with Color Mapping',
    preview_url_light: 'https://example.com/scatter-color-light.png',
    preview_url_dark: 'https://example.com/scatter-color-dark.png',
    quality_score: 88,
    tags: { plot_type: ['scatter'], data_type: ['numeric'], features: ['color-mapped'] },
    impl_tags: { dependencies: ['scipy'] },
  },
  {
    id: 'line-basic',
    title: 'Basic Line Chart',
    preview_url_light: 'https://example.com/line-basic-light.png',
    preview_url_dark: 'https://example.com/line-basic-dark.png',
    quality_score: 92,
    tags: { plot_type: ['line'], data_type: ['numeric'], features: ['basic'] },
    impl_tags: null,
  },
];


function mockFetchSuccess() {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockSpecs),
    }),
  );
}


// jsdom doesn't ship ResizeObserver; stub it so the page's useEffect doesn't crash
// AND fire the callback once with non-zero dimensions so the `size.w > 0` gate that
// guards <ForceGraph2D> mounting is satisfied.
type ResizeCb = (entries: { contentRect: { width: number; height: number } }[]) => void;
class MockResizeObserver {
  cb: ResizeCb;
  constructor(cb: ResizeCb) {
    this.cb = cb;
  }
  observe(_target: Element) {
    setTimeout(() => {
      this.cb([{ contentRect: { width: 800, height: 600 } }]);
    }, 0);
  }
  unobserve() {}
  disconnect() {}
}


describe('MapPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockNavigate.mockReset();
    mockTrackEvent.mockReset();
    lastFgProps.current = null;
    mockHasHover.current = true;
    fgInstance.centerAt.mockReset();
    fgInstance.zoom.mockReset().mockReturnValue(1);
    fgInstance.zoomToFit.mockReset();
    fgInstance.d3Force.mockReset().mockReturnValue({ strength: vi.fn().mockReturnThis(), distance: vi.fn().mockReturnThis() });
    fgInstance.d3ReheatSimulation.mockReset();
    fgInstance.refresh.mockReset();
    fgInstance.__forcesWired = undefined;
    vi.stubGlobal('ResizeObserver', MockResizeObserver);
  });

  // Restore stubbed globals (fetch, ResizeObserver, …) after every test so
  // they don't leak into subsequent suites — other frontend tests rely on a
  // clean global surface and silently break otherwise.
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('renders the spec/edge count meta after fetch', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => {
      expect(screen.getByText(/3 specs/)).toBeInTheDocument();
    });
  });

  it('renders an a11y fallback list of every spec as anchor links', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Basic Scatter Plot' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Basic Line Chart' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Scatter with Color Mapping' })).toBeInTheDocument();
    });
  });

  it('shows an error message when the fetch fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 500 }));
    render(<MapPage />);
    await waitFor(() => {
      expect(screen.getByText(/Failed to load map/)).toBeInTheDocument();
    });
  });

  it('passes graph data with the expected node count to ForceGraph2D', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => {
      expect(screen.getByTestId('force-graph-2d')).toBeInTheDocument();
    });
    expect(screen.getByTestId('force-graph-2d').getAttribute('data-node-count')).toBe('3');
  });

  it('navigates to the spec page and emits an analytics event on node click', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    const onNodeClick = lastFgProps.current!.onNodeClick as (n: { id: string }) => void;
    onNodeClick({ id: 'scatter-basic' });

    expect(mockNavigate).toHaveBeenCalledWith('/scatter-basic');
    expect(mockTrackEvent).toHaveBeenCalledWith('map_node_click', { spec: 'scatter-basic' });
  });

  it('drawNode paints a fallback rect when a node has no preloaded image', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    const drawNode = lastFgProps.current!.nodeCanvasObject as (n: unknown, c: unknown, gs?: number) => void;
    const ctx = makeCtxStub();
    drawNode({ id: 'scatter-basic', x: 100, y: 100, imgs: new Map(), pendingTiers: new Set(), colorBucket: null }, ctx, 1);

    // Without an attached image, the fallback rect path runs.
    expect(ctx.fillRect).toHaveBeenCalled();
    expect(ctx.strokeRect).toHaveBeenCalled();
    expect(ctx.drawImage).not.toHaveBeenCalled();
  });

  it('drawNode paints the thumbnail when a node has a preloaded image', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    const drawNode = lastFgProps.current!.nodeCanvasObject as (n: unknown, c: unknown, gs?: number) => void;
    const ctx = makeCtxStub();
    const fakeImg = { src: 'x' } as unknown as HTMLImageElement;
    drawNode(
      { id: 'scatter-basic', x: 50, y: 50, imgs: new Map([[400, fakeImg]]), pendingTiers: new Set(), colorBucket: null },
      ctx,
      1,
    );

    expect(ctx.drawImage).toHaveBeenCalledWith(fakeImg, expect.any(Number), expect.any(Number), expect.any(Number), expect.any(Number));
    expect(ctx.strokeRect).toHaveBeenCalled();
  });

  it('paintHitbox draws a sprite-sized hit rectangle', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    const paintHitbox = lastFgProps.current!.nodePointerAreaPaint as (n: unknown, c: string, ctx: unknown) => void;
    const ctx = makeCtxStub();
    paintHitbox({ id: 'scatter-basic', x: 80, y: 60, imgs: new Map(), pendingTiers: new Set(), colorBucket: null }, '#ff00ff', ctx);

    expect(ctx.fillStyle).toBe('#ff00ff');
    expect(ctx.fillRect).toHaveBeenCalled();
  });

  it('linkColor returns the brand green for links touching the hovered node', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    // Hover a node, then ask the link-color callback for its incident link.
    const onNodeHover = lastFgProps.current!.onNodeHover as (n: { id: string } | null) => void;
    onNodeHover({ id: 'scatter-basic' });
    await waitFor(() => {
      const linkColor = lastFgProps.current!.linkColor as (l: unknown) => string;
      const colorInvolved = linkColor({ source: 'scatter-basic', target: 'line-basic', weight: 0.5 });
      const colorOther = linkColor({ source: 'line-basic', target: 'scatter-color-mapped', weight: 0.5 });
      expect(colorInvolved).toMatch(/^#/); // brand color (hex)
      expect(colorInvolved).not.toBe(colorOther);
    });
  });

  it('linkWidth scales with link weight', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    const linkWidth = lastFgProps.current!.linkWidth as (l: unknown) => number;
    const small = linkWidth({ weight: 0.1 });
    const large = linkWidth({ weight: 0.9 });
    expect(large).toBeGreaterThan(small);
    expect(small).toBeGreaterThan(0);
  });

  it('seeds initial node positions per cluster (warm start for the simulation)', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    const nodes = (lastFgProps.current!.graphData as { nodes: Array<{ id: string; x?: number; y?: number; vx?: number; vy?: number }> }).nodes;
    // Every node should have a numeric seed position before FG2D ever ticks the simulation —
    // without seeding, FG2D's random initialiser would leave x/y undefined here.
    for (const n of nodes) {
      expect(typeof n.x).toBe('number');
      expect(typeof n.y).toBe('number');
      expect(Number.isFinite(n.x as number)).toBe(true);
      expect(Number.isFinite(n.y as number)).toBe(true);
    }
    // Same plot_type (= colorBucket) should land near the same centroid; nodes from
    // different buckets should land further apart on average. Take the two scatters
    // (bucketed together) vs. line-basic and compare distances.
    const scatterA = nodes.find(n => n.id === 'scatter-basic')!;
    const scatterB = nodes.find(n => n.id === 'scatter-color-mapped')!;
    const line = nodes.find(n => n.id === 'line-basic')!;
    const dist = (a: typeof scatterA, b: typeof scatterA) =>
      Math.hypot((a.x ?? 0) - (b.x ?? 0), (a.y ?? 0) - (b.y ?? 0));
    expect(dist(scatterA, scatterB)).toBeLessThan(dist(scatterA, line));
  });

  it('shows the settling overlay until the simulation cools, then hides it', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(screen.getByTestId('force-graph-2d')).toBeInTheDocument());

    // Gate is visible (role="status" is reachable) while the engine is still cooling.
    expect(screen.getByRole('status')).toHaveTextContent(/arranging/i);

    // Engine stops → settled flips → overlay sets aria-hidden=true and fades.
    // We keep the node in the DOM for the fade transition, so query-by-role
    // (which filters aria-hidden by default) is the right invariant: it
    // becomes unreachable to assistive tech the moment the gate is settled.
    const onEngineStop = lastFgProps.current!.onEngineStop as () => void;
    act(() => onEngineStop());
    await waitFor(() => expect(screen.queryByRole('status')).not.toBeInTheDocument());
  });

  it('frames the bbox via centerAt + zoom on engine stop', async () => {
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    // The percentile-trimmed fit reads node x/y; seed positions guarantee these are set.
    const onEngineStop = lastFgProps.current!.onEngineStop as () => void;
    act(() => onEngineStop());

    expect(fgInstance.centerAt).toHaveBeenCalledTimes(1);
    expect(fgInstance.zoom).toHaveBeenCalled();
    // Animation duration is 0 → instant, hidden behind the gate.
    const centerCall = fgInstance.centerAt.mock.calls[0];
    expect(centerCall[2]).toBe(0);
  });

  it('first tap pins on touch devices, second tap navigates', async () => {
    mockHasHover.current = false;
    mockFetchSuccess();
    render(<MapPage />);
    await waitFor(() => expect(lastFgProps.current).not.toBeNull());

    // First tap: pin (no navigation, analytics fires map_node_pin).
    act(() => {
      const onNodeClick = lastFgProps.current!.onNodeClick as (n: { id: string }) => void;
      onNodeClick({ id: 'scatter-basic' });
    });
    expect(mockNavigate).not.toHaveBeenCalled();
    expect(mockTrackEvent).toHaveBeenCalledWith('map_node_pin', { spec: 'scatter-basic' });

    // Second tap on the same node: navigate. After the first tap React
    // re-rendered MapPage with the new pinnedId, so lastFgProps.current
    // now holds a fresh onNodeClick closure that reads the updated state.
    act(() => {
      const onNodeClick = lastFgProps.current!.onNodeClick as (n: { id: string }) => void;
      onNodeClick({ id: 'scatter-basic' });
    });
    expect(mockNavigate).toHaveBeenCalledWith('/scatter-basic');
    expect(mockTrackEvent).toHaveBeenCalledWith('map_node_click', { spec: 'scatter-basic' });
  });
});
