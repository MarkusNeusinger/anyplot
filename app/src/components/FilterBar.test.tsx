import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '../test-utils';

// Mock the utils module
vi.mock('../utils', () => ({
  getAvailableValues: vi.fn(() => [['scatter', 10], ['bar', 5]]),
  getAvailableValuesForGroup: vi.fn(() => [['scatter', 15]]),
  getSearchResults: vi.fn(() => []),
}));

import { FilterBar } from './FilterBar';

// ResizeObserver polyfill
class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

const defaultProps = {
  activeFilters: [] as { category: 'lib'; values: string[] }[],
  filterCounts: {
    lib: { matplotlib: 100, seaborn: 80 },
    spec: {}, plot: {}, data: {}, dom: {}, feat: {},
    dep: {}, tech: {}, pat: {}, prep: {}, style: {},
  },
  orCounts: [] as Record<string, number>[],
  specTitles: {},
  currentTotal: 100,
  displayedCount: 20,
  randomAnimation: null,
  imageSize: 'normal' as const,
  onImageSizeChange: vi.fn(),
  onAddFilter: vi.fn(),
  onAddValueToGroup: vi.fn(),
  onRemoveFilter: vi.fn(),
  onRemoveGroup: vi.fn(),
  onTrackEvent: vi.fn(),
};

describe('FilterBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal('ResizeObserver', MockResizeObserver);
  });

  it('renders without crashing', () => {
    render(<FilterBar {...defaultProps} />);
    // Component should mount and have an input
    expect(document.querySelector('input')).toBeTruthy();
  });

  it('renders active filter chip with category:value format', () => {
    const filters = [
      { category: 'lib' as const, values: ['matplotlib'] },
    ];
    render(<FilterBar {...defaultProps} activeFilters={filters} />);
    // Chip label is "category:value" format
    expect(screen.getByText('lib:matplotlib')).toBeInTheDocument();
  });

  it('shows counter text with total', () => {
    render(<FilterBar {...defaultProps} currentTotal={42} displayedCount={20} />);
    expect(screen.getByText(/42/)).toBeInTheDocument();
  });

  it('renders chip for each filter group', () => {
    const filters = [
      { category: 'lib' as const, values: ['matplotlib'] },
      { category: 'plot' as const, values: ['scatter'] },
    ];
    render(<FilterBar {...defaultProps} activeFilters={filters} />);
    const chips = document.querySelectorAll('.MuiChip-root');
    expect(chips.length).toBeGreaterThanOrEqual(2);
  });

  it('renders comma-separated values in chip', () => {
    const filters = [
      { category: 'lib' as const, values: ['matplotlib', 'seaborn'] },
    ];
    render(<FilterBar {...defaultProps} activeFilters={filters} />);
    expect(screen.getByText('lib:matplotlib,seaborn')).toBeInTheDocument();
  });
});
