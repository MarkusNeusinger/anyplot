import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { MapPanelData } from 'src/sections/map/useMapSelection';
import { render, screen } from 'src/test-utils';

import { MapHoverPanel } from './MapHoverPanel';

const mockIsDark = { current: false };

vi.mock('src/hooks/useLayoutContext', () => ({
  useTheme: () => ({ isDark: mockIsDark.current }),
}));

function makePanelData(overrides: Partial<MapPanelData> = {}): MapPanelData {
  return {
    title: 'Basic Scatter Plot',
    plotType: 'scatter',
    chipColor: '#009E73',
    tags: ['domain:finance', 'feature:annotated'],
    previewUrl: 'https://example.com/scatter_800.webp',
    ...overrides,
  };
}

describe('MapHoverPanel', () => {
  beforeEach(() => {
    mockIsDark.current = false;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('stays aria-hidden and empty when nothing is hovered or pinned', () => {
    render(<MapHoverPanel hoverId={null} pinnedId={null} panelData={null} />);

    expect(screen.queryByRole('complementary')).not.toBeInTheDocument();
    const hiddenAside = screen.getByRole('complementary', { hidden: true });
    expect(hiddenAside).toHaveAttribute('aria-hidden', 'true');
    expect(hiddenAside).toBeEmptyDOMElement();
  });

  it('reveals the panel with preview image, title, plot type, and tags when a node is hovered', () => {
    const panelData = makePanelData();

    render(<MapHoverPanel hoverId="scatter-basic" pinnedId={null} panelData={panelData} />);

    const aside = screen.getByRole('complementary');
    expect(aside).toHaveAttribute('aria-hidden', 'false');
    expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
    expect(screen.getByText('scatter')).toBeInTheDocument();
    expect(screen.getByText('domain:finance')).toBeInTheDocument();
    expect(screen.getByText('feature:annotated')).toBeInTheDocument();

    const img = aside.querySelector('img');
    expect(img).not.toBeNull();
    expect(img).toHaveAttribute('src', 'https://example.com/scatter_800.webp');
    expect(img).toHaveAttribute('alt', '');
  });

  it('reveals the panel without an img element when a node is pinned and has no previewUrl', () => {
    mockIsDark.current = true;
    const panelData = makePanelData({
      title: 'Pinned Line Plot',
      plotType: 'line',
      chipColor: null,
      tags: [],
      previewUrl: null,
    });

    render(<MapHoverPanel hoverId={null} pinnedId="line-basic" panelData={panelData} />);

    const aside = screen.getByRole('complementary');
    expect(aside).toHaveAttribute('aria-hidden', 'false');
    expect(screen.getByText('Pinned Line Plot')).toBeInTheDocument();
    expect(screen.getByText('line')).toBeInTheDocument();
    expect(aside.querySelector('img')).toBeNull();
  });

  it('omits the plot type row when plotType is null', () => {
    mockIsDark.current = true;
    const panelData = makePanelData({
      title: 'Custom Chart',
      plotType: null,
      tags: [],
    });

    render(<MapHoverPanel hoverId="custom-chart" pinnedId={null} panelData={panelData} />);

    expect(screen.getByRole('complementary')).toHaveAttribute('aria-hidden', 'false');
    expect(screen.getByText('Custom Chart')).toBeInTheDocument();
    expect(screen.queryByText('scatter')).not.toBeInTheDocument();
  });
});
