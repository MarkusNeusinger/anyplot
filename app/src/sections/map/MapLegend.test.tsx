import { afterEach, describe, expect, it, vi } from 'vitest';

import type { MapGraphData } from 'src/hooks/useForceGraphSimulation';
import { fireEvent, render, screen, styleAt } from 'src/test-utils';

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

    // The toggle shows on a phone only. jsdom applies `@media` at its fixed 1024 px window, where
    // the toggle is hidden and so has no accessible name: the test finds the button by its text,
    // which names it on a phone, and checks the widths on the style sheet.
    const toggle = screen.getByText('legend ▸');
    expect(toggle.tagName).toBe('BUTTON');
    expect(styleAt(toggle, 390).display).toBe('inline-block');
    expect(styleAt(toggle, 1024).display).toBe('none');
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    fireEvent.click(toggle);
    expect(screen.getByText('legend ▾')).toHaveAttribute('aria-expanded', 'true');

    fireEvent.click(screen.getByText('legend ▾'));
    expect(screen.getByText('legend ▸')).toHaveAttribute('aria-expanded', 'false');
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
