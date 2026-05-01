import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { render, screen, waitFor } from '../test-utils';
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
// branches (e.g. tap-to-pin) need a per-test override.
vi.mock('@mui/material/useMediaQuery', () => ({
  default: () => true,
}));

// Capture the props passed to ForceGraph2D so individual callbacks can be exercised
// from outside React. A live canvas can't run in jsdom, but the callbacks (drawNode,
// onNodeClick, linkColor, …) are pure-ish JS and worth testing in isolation.
type FgProps = Record<string, unknown>;
const lastFgProps: { current: FgProps | null } = { current: null };

vi.mock('react-force-graph-2d', () => ({
  default: (props: FgProps) => {
    lastFgProps.current = props;
    const data = props.graphData as { nodes: unknown[]; links: unknown[] };
    return (
      <div
        data-testid="force-graph-2d"
        data-node-count={data.nodes.length}
        data-link-count={data.links.length}
      />
    );
  },
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
});
