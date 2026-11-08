import { useState } from 'react';

import { fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { FilterSearch } from 'src/sections/plots-gallery/FilterBar/FilterSearch';
import { render, screen, waitFor } from 'src/test-utils';
import type { ActiveFilters, FilterCounts } from 'src/types';

// Uses the real src/utils (fuse.js included) so keyboard navigation walks real results.
const filterCounts: FilterCounts = {
  lang: { python: 180 },
  lib: { matplotlib: 100, seaborn: 80 },
  spec: {},
  plot: { scatter: 10, bar: 5 },
  data: {},
  dom: {},
  feat: {},
  dep: {},
  tech: {},
  pat: {},
  prep: {},
  style: {},
};

const defaultProps = {
  activeFilters: [],
  filterCounts,
  globalCounts: filterCounts,
  specTitles: {},
  onAddFilter: vi.fn(),
  onClearFilters: vi.fn(),
  onTrackEvent: vi.fn(),
};

// With the chip lib:seaborn only seaborn plots remain, and none is a bar plot
const seabornFilters = [{ category: 'lib' as const, values: ['seaborn'] }];
const seabornCounts: FilterCounts = {
  ...filterCounts,
  lib: { seaborn: 80 },
  plot: { scatter: 10 },
};

function getSearchInput() {
  return screen.getByLabelText('Search filters');
}

/**
 * The page around the search: it owns the chips, and its contextual counts
 * stay those of the filtered response until a refetch, as on /plots.
 */
function SearchWithChips({ onAddFilter }: { onAddFilter: (c: string, v: string) => void }) {
  const [activeFilters, setActiveFilters] = useState<ActiveFilters>(seabornFilters);
  return (
    <FilterSearch
      {...defaultProps}
      activeFilters={activeFilters}
      filterCounts={seabornCounts}
      onAddFilter={onAddFilter}
      onClearFilters={() => setActiveFilters([])}
    />
  );
}

describe('FilterSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('opens the category dropdown on focus', async () => {
    render(<FilterSearch {...defaultProps} />);
    fireEvent.focus(getSearchInput());
    // Categories with available values: lang, lib, plot
    expect(await screen.findByText('language')).toBeInTheDocument();
    expect(screen.getByText('library')).toBeInTheDocument();
    expect(screen.getByText('type')).toBeInTheDocument();
  });

  it('drills into a category with ArrowDown + Enter', async () => {
    render(<FilterSearch {...defaultProps} />);
    const input = getSearchInput();
    fireEvent.focus(input);
    await screen.findByText('language');

    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });

    // First category (lang) is selected: back item + its values appear
    expect(await screen.findByText('← language')).toBeInTheDocument();
    expect(screen.getByText('python')).toBeInTheDocument();
    expect(defaultProps.onAddFilter).not.toHaveBeenCalled();
  });

  it('selects the first search result on Enter without highlight', async () => {
    render(<FilterSearch {...defaultProps} />);
    const input = getSearchInput();
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'scatter' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(defaultProps.onAddFilter).toHaveBeenCalledWith('plot', 'scatter');
    expect(defaultProps.onTrackEvent).toHaveBeenCalledWith('search', {
      query: 'scatter',
      category: 'plot',
    });
  });

  it('closes the dropdown on Escape', async () => {
    render(<FilterSearch {...defaultProps} />);
    const input = getSearchInput();
    fireEvent.focus(input);
    expect(await screen.findByText('library')).toBeInTheDocument();

    fireEvent.keyDown(input, { key: 'Escape' });
    await waitFor(() => {
      expect(screen.queryByText('library')).not.toBeInTheDocument();
    });
  });

  it('adds a filter when a value is clicked, without a search track event', async () => {
    render(<FilterSearch {...defaultProps} />);
    fireEvent.focus(getSearchInput());
    fireEvent.click(await screen.findByText('library'));
    fireEvent.click(await screen.findByText('matplotlib'));

    expect(defaultProps.onAddFilter).toHaveBeenCalledWith('lib', 'matplotlib');
    expect(defaultProps.onTrackEvent).not.toHaveBeenCalledWith('search', expect.anything());
  });

  it('collapses to an icon button when filters are active', () => {
    render(
      <FilterSearch
        {...defaultProps}
        activeFilters={[{ category: 'lib', values: ['matplotlib'] }]}
      />
    );
    expect(screen.getByRole('button', { name: 'Open filter search' })).toBeInTheDocument();
  });

  it('expands the collapsed search via keyboard', async () => {
    render(
      <FilterSearch
        {...defaultProps}
        activeFilters={[{ category: 'lib', values: ['matplotlib'] }]}
      />
    );
    const button = screen.getByRole('button', { name: 'Open filter search' });
    fireEvent.keyDown(button, { key: 'Enter' });

    expect(await screen.findByText('library')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Open filter search' })).not.toBeInTheDocument();
  });

  it('hides the search input entirely when 5 filter groups are active', () => {
    const five = ['matplotlib', 'seaborn', 'plotly', 'bokeh', 'altair'].map(value => ({
      category: 'lib' as const,
      values: [value],
    }));
    render(<FilterSearch {...defaultProps} activeFilters={five} />);
    expect(screen.queryByLabelText('Search filters')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Open filter search' })).not.toBeInTheDocument();
  });

  it('finds a value from a query with a generic noun and an umlaut', async () => {
    render(<FilterSearch {...defaultProps} />);
    const input = getSearchInput();
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'Scätter Diagramm' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(defaultProps.onAddFilter).toHaveBeenCalledWith('plot', 'scatter');
  });

  it('offers .search_all() when the chips hide every match', async () => {
    render(
      <FilterSearch {...defaultProps} activeFilters={seabornFilters} filterCounts={seabornCounts} />
    );
    fireEvent.keyDown(screen.getByRole('button', { name: 'Open filter search' }), {
      key: 'Enter',
    });
    const input = getSearchInput();
    fireEvent.change(input, { target: { value: 'bar' } });

    expect(await screen.findByText('1 match without the filters')).toBeInTheDocument();

    // A bare Enter never removes the filters
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(defaultProps.onClearFilters).not.toHaveBeenCalled();

    // An explicit pick does, and keeps the query
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(defaultProps.onClearFilters).toHaveBeenCalledTimes(1);
    expect(input).toHaveValue('bar');
  });

  it('offers no .search_all() when all plots have no match either', async () => {
    render(
      <FilterSearch {...defaultProps} activeFilters={seabornFilters} filterCounts={seabornCounts} />
    );
    fireEvent.keyDown(screen.getByRole('button', { name: 'Open filter search' }), {
      key: 'Enter',
    });
    fireEvent.change(getSearchInput(), { target: { value: 'zzzzzz' } });

    expect(await screen.findByLabelText('No matches')).toBeInTheDocument();
    expect(screen.queryByText('.search_all()')).not.toBeInTheDocument();
  });

  it('shows the hits in all plots after a click on .search_all()', async () => {
    const onAddFilter = vi.fn();
    render(<SearchWithChips onAddFilter={onAddFilter} />);
    fireEvent.keyDown(screen.getByRole('button', { name: 'Open filter search' }), {
      key: 'Enter',
    });
    fireEvent.change(getSearchInput(), { target: { value: 'bar' } });

    fireEvent.click(
      await screen.findByRole('menuitem', {
        name: 'Search all plots: 1 match without the filters',
      })
    );

    // The chip is gone, the query stays, and the dropdown lists the global hit
    const hit = await screen.findByText('bar');
    expect(getSearchInput()).toHaveValue('bar');
    expect(screen.queryByLabelText('No matches')).not.toBeInTheDocument();
    fireEvent.click(hit);
    expect(onAddFilter).toHaveBeenCalledWith('plot', 'bar');
  });

  it('searches the global counts as soon as no filter is left', async () => {
    // The contextual counts still hold the last filtered response
    render(<FilterSearch {...defaultProps} filterCounts={seabornCounts} />);
    const input = getSearchInput();
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'bar' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(defaultProps.onAddFilter).toHaveBeenCalledWith('plot', 'bar');
  });

  it('tracks search_no_results for queries without matches (debounced)', async () => {
    render(<FilterSearch {...defaultProps} />);
    const input = getSearchInput();
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: 'zzzzzz' } });

    await waitFor(() => {
      expect(defaultProps.onTrackEvent).toHaveBeenCalledWith('search_no_results', {
        query: 'zzzzzz',
      });
    });
  });
});
