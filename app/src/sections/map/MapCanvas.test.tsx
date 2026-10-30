import { createRef, forwardRef, useImperativeHandle } from 'react';

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { MapForceConfig, MapGraphData } from 'src/hooks/useForceGraphSimulation';
import type { MapLink, MapNode } from 'src/pages/MapPage.helpers';
import { render, screen } from 'src/test-utils';

import { MapCanvas } from './MapCanvas';

const mockIsDark = { current: false };

vi.mock('src/hooks/useLayoutContext', () => ({
  useTheme: () => ({ isDark: mockIsDark.current }),
}));

type FgProps = Record<string, unknown>;
const lastFgProps: { current: FgProps | null } = { current: null };

interface FgInstance {
  centerAt: ReturnType<typeof vi.fn>;
  zoom: ReturnType<typeof vi.fn>;
  d3Force: ReturnType<typeof vi.fn>;
  d3ReheatSimulation: ReturnType<typeof vi.fn>;
  refresh: ReturnType<typeof vi.fn>;
  __forcesWired?: boolean;
}

const fgInstance: FgInstance = {
  centerAt: vi.fn(),
  zoom: vi.fn(),
  d3Force: vi.fn(),
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

function makeNode(
  overrides: Partial<MapNode> & { id: string; x?: number; y?: number }
): MapNode & { x?: number; y?: number } {
  return {
    title: overrides.id,
    tags: [],
    thumbUrl: null,
    imgs: new Map(),
    pendingTiers: new Set(),
    colorBucket: 'scatter',
    ...overrides,
  };
}

const collideForceSentinel: ReturnType<MapForceConfig['createCollideForce']> = {
  initialize: () => {},
  radius: () => collideForceSentinel,
  iterations: () => collideForceSentinel,
  strength: () => collideForceSentinel,
  distance: () => collideForceSentinel,
};
const outlierSquashSentinel = Object.assign(() => {}, { initialize: () => {} });

function makeForceConfig(): MapForceConfig {
  return {
    cooldownTicks: 300,
    alphaDecay: 0.015,
    alphaMin: 0.01,
    velocityDecay: 0.35,
    chargeStrength: -50,
    linkDistance: () => 80,
    linkStrength: () => 0.2,
    centerGravity: 0.04,
    createCollideForce: vi.fn(() => collideForceSentinel),
    createOutlierSquashForce: vi.fn(() => outlierSquashSentinel),
  };
}

function makeProps(overrides: Partial<Parameters<typeof MapCanvas>[0]> = {}) {
  const n1 = makeNode({ id: 'scatter-basic', title: 'Basic Scatter Plot', x: 10, y: 20 });
  const n2 = makeNode({
    id: 'line-basic',
    title: 'Basic Line Chart',
    colorBucket: 'line',
    x: 110,
    y: 120,
  });
  const nodes = [n1, n2];
  const links: MapLink[] = [{ source: 'scatter-basic', target: 'line-basic', weight: 0.6 }];
  const graphData: MapGraphData = {
    nodes,
    links,
    topTypes: ['scatter', 'line'],
    typeCounts: new Map([
      ['scatter', 1],
      ['line', 1],
    ]),
    idf: new Map(),
  };
  const fgRef = createRef<FgInstance>();

  return {
    ready: true,
    fgRef,
    graphData,
    size: { w: 800, h: 600 },
    forceConfig: makeForceConfig(),
    hoverId: null,
    hoverType: null,
    nodeById: new Map(nodes.map(n => [n.id, n])),
    neighbors: new Map([
      ['scatter-basic', new Set(['line-basic'])],
      ['line-basic', new Set(['scatter-basic'])],
    ]),
    onNodeClick: vi.fn(),
    setPinnedId: vi.fn(),
    setHoverId: vi.fn(),
    onNodeHover: vi.fn(),
    markSettled: vi.fn(),
    handleEngineTick: vi.fn(),
    settled: false,
    tickProgress: 0,
    ...overrides,
  };
}

describe('MapCanvas', () => {
  beforeEach(() => {
    mockIsDark.current = false;
    lastFgProps.current = null;
    fgInstance.centerAt.mockReset();
    fgInstance.zoom.mockReset();
    fgInstance.d3Force
      .mockReset()
      .mockReturnValue({ strength: vi.fn().mockReturnThis(), distance: vi.fn().mockReturnThis() });
    fgInstance.d3ReheatSimulation.mockReset();
    fgInstance.refresh.mockReset();
    fgInstance.__forcesWired = undefined;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('renders nothing before ready is true', () => {
    render(<MapCanvas {...makeProps({ ready: false })} />);

    expect(screen.queryByTestId('force-graph-2d')).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('shows the settling overlay with progress while cooling and hides it from assistive tech once settled', () => {
    const { rerender } = render(
      <MapCanvas {...makeProps({ ready: true, settled: false, tickProgress: 0.45 })} />
    );

    const status = screen.getByRole('status', { name: 'Computing map layout' });
    expect(status).toHaveTextContent('map.simulate()');

    const progressBar = screen.getByRole('progressbar', { name: 'Layout computation progress' });
    expect(progressBar).toHaveAttribute('aria-valuenow', '45');

    mockIsDark.current = true;
    rerender(<MapCanvas {...makeProps({ ready: true, settled: true, tickProgress: 1 })} />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('passes graphData, dimensions, and click/hover/tick handlers to ForceGraph2D', () => {
    const props = makeProps();
    render(<MapCanvas {...props} />);

    const fg = screen.getByTestId('force-graph-2d');
    expect(fg).toHaveAttribute('data-node-count', '2');
    expect(fg).toHaveAttribute('data-link-count', '1');

    const captured = lastFgProps.current!;
    expect(captured.graphData).toBe(props.graphData);
    expect(captured.width).toBe(800);
    expect(captured.height).toBe(600);

    const firstNode = props.graphData.nodes[0];
    const onNodeHover = captured.onNodeHover as (n: MapNode | null) => void;
    onNodeHover(firstNode);
    expect(props.onNodeHover).toHaveBeenCalledWith(firstNode);
    onNodeHover(null);
    expect(props.onNodeHover).toHaveBeenCalledWith(null);

    const onNodeClick = captured.onNodeClick as (n: MapNode) => void;
    onNodeClick(firstNode);
    expect(props.onNodeClick).toHaveBeenCalledWith(firstNode);

    const onEngineTick = captured.onEngineTick as () => void;
    onEngineTick();
    expect(props.handleEngineTick).toHaveBeenCalledTimes(1);

    const nodeLabel = captured.nodeLabel as (n: MapNode) => string;
    expect(nodeLabel(firstNode)).toBe('Basic Scatter Plot');

    const onBackgroundClick = captured.onBackgroundClick as () => void;
    onBackgroundClick();
    expect(props.setPinnedId).toHaveBeenCalledWith(null);
    expect(props.setHoverId).toHaveBeenCalledWith(null);
  });

  it('frames the cluster on engine stop and wires d3 forces once in onRenderFramePre', () => {
    const props = makeProps();
    render(<MapCanvas {...props} />);

    const captured = lastFgProps.current!;
    const onEngineStop = captured.onEngineStop as () => void;
    onEngineStop();

    expect(fgInstance.centerAt).toHaveBeenCalledWith(60, 70, 0);
    expect(fgInstance.zoom).toHaveBeenCalledWith(4.8, 0);
    expect(props.markSettled).toHaveBeenCalledTimes(1);

    const onRenderFramePre = captured.onRenderFramePre as () => void;
    onRenderFramePre();
    expect(fgInstance.d3Force).toHaveBeenCalledWith('charge');
    expect(fgInstance.d3Force).toHaveBeenCalledWith('link');
    expect(fgInstance.d3Force).toHaveBeenCalledWith('collide', collideForceSentinel);
    expect(fgInstance.d3Force).toHaveBeenCalledWith('center');
    expect(fgInstance.d3Force).toHaveBeenCalledWith('outlier-squash', outlierSquashSentinel);
    expect(fgInstance.d3ReheatSimulation).toHaveBeenCalledTimes(1);

    // Second frame is a no-op because __forcesWired is now true
    onRenderFramePre();
    expect(fgInstance.d3ReheatSimulation).toHaveBeenCalledTimes(1);
  });

  it('computes linkColor and linkWidth across hoverId and hoverType states', () => {
    const props = makeProps({ hoverId: 'scatter-basic', hoverType: 'scatter' });
    const { rerender } = render(<MapCanvas {...props} />);

    const linkColor = lastFgProps.current!.linkColor as (l: unknown) => string;
    const linkWidth = lastFgProps.current!.linkWidth as (l: unknown) => number;

    const involvedColor = linkColor({
      source: 'scatter-basic',
      target: { id: 'line-basic' },
      weight: 0.6,
    });
    expect(involvedColor).toMatch(/^#/);
    expect(
      linkWidth({ source: 'scatter-basic', target: 'line-basic', weight: 0.6 })
    ).toBeGreaterThan(linkWidth({ source: 'other-a', target: 'other-b', weight: 0.6 }));

    // Uninvolved link while hoverId is active (hoverType null)
    rerender(<MapCanvas {...makeProps({ hoverId: 'scatter-basic', hoverType: null })} />);
    const uninvolvedHoverColor = (lastFgProps.current!.linkColor as (l: unknown) => string)({
      source: 'line-basic',
      target: 'other',
      weight: 0.5,
    });
    expect(uninvolvedHoverColor).toContain('rgba');

    // hoverType active without hoverId
    rerender(<MapCanvas {...makeProps({ hoverId: null, hoverType: 'scatter' })} />);
    const hoverTypeLinkColor = lastFgProps.current!.linkColor as (l: unknown) => string;
    const intraColor = hoverTypeLinkColor({
      source: 'scatter-basic',
      target: 'scatter-basic',
      weight: 0.5,
    });
    const interColor = hoverTypeLinkColor({
      source: 'scatter-basic',
      target: 'line-basic',
      weight: 0.5,
    });
    expect(intraColor).not.toBe(interColor);
  });
});
