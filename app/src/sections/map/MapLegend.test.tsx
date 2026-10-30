import { afterEach, describe, expect, it, vi } from 'vitest';

import type { MapGraphData } from 'src/hooks/useForceGraphSimulation';
import { fireEvent, render, screen } from 'src/test-utils';

import { MapLegend } from './MapLegend';

function makeGraphData(overrides: Partial<MapGraphData> = {}): MapGraphData {
  return {
    nodes: [],
    links: [],
    topTypes: ['scatter', 'bar'],
    typeCounts: new Map([
      ['scatter', 14],
      ['bar', 7],
    ]),
    idf: new Map(),
    ...overrides,
  };
}

describe('MapLegend', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('renders nothing when topTypes is empty', () => {
    render(
      <MapLegend
        graphData={makeGraphData({ topTypes: [] })}
        activeCategory="plot_type"
        hoverType={null}
        setHoverType={vi.fn()}
      />
    );

    expect(screen.queryByRole('button', { name: /legend/i })).not.toBeInTheDocument();
    expect(screen.queryByText('plot_type')).not.toBeInTheDocument();
  });

  it('renders the active category and each top type with its count', () => {
    const graphData = makeGraphData({
      topTypes: ['scatter', 'bar', 'violin'],
      typeCounts: new Map([
        ['scatter', 14],
        ['bar', 7],
      ]),
    });

    render(
      <MapLegend
        graphData={graphData}
        activeCategory="plot_type"
        hoverType={null}
        setHoverType={vi.fn()}
      />
    );

    expect(screen.getByText('plot_type')).toBeInTheDocument();
    expect(screen.getByText('scatter')).toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();
    expect(screen.getByText('bar')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('violin')).toBeInTheDocument();
    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('toggles the mobile legend button between closed and open states', () => {
    render(
      <MapLegend
        graphData={makeGraphData()}
        activeCategory="plot_type"
        hoverType={null}
        setHoverType={vi.fn()}
      />
    );

    const toggle = screen.getByRole('button', { name: 'legend ▸' });
    fireEvent.click(toggle);
    expect(screen.getByRole('button', { name: 'legend ▾' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'legend ▾' }));
    expect(screen.getByRole('button', { name: 'legend ▸' })).toBeInTheDocument();
  });

  it('calls setHoverType on mouse enter and clears it on mouse leave', () => {
    const setHoverType = vi.fn();

    render(
      <MapLegend
        graphData={makeGraphData()}
        activeCategory="plot_type"
        hoverType="scatter"
        setHoverType={setHoverType}
      />
    );

    const barLabel = screen.getByText('bar');
    fireEvent.mouseEnter(barLabel);
    expect(setHoverType).toHaveBeenCalledWith('bar');

    fireEvent.mouseLeave(barLabel);
    expect(setHoverType).toHaveBeenCalledWith(null);
  });
});
