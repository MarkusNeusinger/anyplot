import { fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  type DropdownItem,
  FilterMenu,
  type FilterMenuProps,
} from 'src/sections/plots-gallery/FilterBar/FilterMenu';
import { render, screen } from 'src/test-utils';
import type { FilterCounts } from 'src/types';
import type { SearchResult } from 'src/utils';

const filterCounts: FilterCounts = {
  lang: { python: 180 },
  lib: { matplotlib: 100, seaborn: 80 },
  spec: {},
  plot: { scatter: 10 },
  data: {},
  dom: {},
  feat: {},
  dep: {},
  tech: {},
  pat: {},
  prep: {},
  style: {},
};

const categoryItems: DropdownItem[] = [
  { type: 'category', category: 'lang' },
  { type: 'category', category: 'lib' },
  { type: 'category', category: 'plot' },
];

const callbacks = {
  onClose: vi.fn(),
  onCategorySelect: vi.fn(),
  onValueSelect: vi.fn(),
  onBack: vi.fn(),
};

function renderMenu(overrides: Partial<FilterMenuProps> = {}) {
  const anchor = document.createElement('div');
  document.body.appendChild(anchor);
  return render(
    <FilterMenu
      anchorEl={anchor}
      open
      filterCounts={filterCounts}
      activeFilters={[]}
      specTitles={{}}
      selectedCategory={null}
      hasQuery={false}
      searchResults={[]}
      dropdownItems={categoryItems}
      highlightedIndex={-1}
      {...callbacks}
      {...overrides}
    />
  );
}

describe('FilterMenu', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('lists available categories with option counts', () => {
    renderMenu();
    expect(screen.getByText('language')).toBeInTheDocument();
    expect(screen.getByText('library')).toBeInTheDocument();
    expect(screen.getByText('type')).toBeInTheDocument();
    expect(screen.getByText('2 options')).toBeInTheDocument(); // lib has 2 values
    // Categories without values are skipped
    expect(screen.queryByText('field')).not.toBeInTheDocument();
  });

  it('calls onCategorySelect when a category is clicked', () => {
    renderMenu();
    fireEvent.click(screen.getByText('library'));
    expect(callbacks.onCategorySelect).toHaveBeenCalledWith('lib');
  });

  it('marks the highlighted item as selected', () => {
    renderMenu({ highlightedIndex: 1 });
    expect(screen.getByText('library').closest('li')).toHaveClass('Mui-selected');
    expect(screen.getByText('language').closest('li')).not.toHaveClass('Mui-selected');
  });

  it('shows category values with a back item when a category is selected', () => {
    renderMenu({ selectedCategory: 'lib' });
    expect(screen.getByText('← library')).toBeInTheDocument();
    expect(screen.getByText('matplotlib')).toBeInTheDocument();
    expect(screen.getByText('(100)')).toBeInTheDocument();

    fireEvent.click(screen.getByText('matplotlib'));
    expect(callbacks.onValueSelect).toHaveBeenCalledWith('lib', 'matplotlib');

    fireEvent.click(screen.getByText('← library'));
    expect(callbacks.onBack).toHaveBeenCalled();
  });

  it('splits search results into exact and fuzzy sections', () => {
    const searchResults: SearchResult[] = [
      { category: 'plot', value: 'scatter', count: 10, matchType: 'exact' },
      { category: 'lib', value: 'seaborn', count: 80, matchType: 'fuzzy' },
    ];
    const dropdownItems: DropdownItem[] = searchResults.map(r => ({ type: 'value', ...r }));
    renderMenu({ hasQuery: true, searchResults, dropdownItems });

    expect(screen.getByText('scatter')).toBeInTheDocument();
    expect(screen.getByText('seaborn')).toBeInTheDocument();
    expect(screen.getByText('fuzzy')).toBeInTheDocument(); // divider label

    fireEvent.click(screen.getByText('seaborn'));
    expect(callbacks.onValueSelect).toHaveBeenCalledWith('lib', 'seaborn');
  });

  it('shows the empty state when a query has no results', () => {
    renderMenu({ hasQuery: true, searchResults: [], dropdownItems: [] });
    expect(screen.getByLabelText('No matches')).toBeInTheDocument();
  });
});
