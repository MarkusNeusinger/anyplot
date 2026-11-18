import { useState } from 'react';

import { act, fireEvent } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { MISS_PAUSE_MS } from 'src/lib/searchMiss';
import { FilterSearch } from 'src/sections/plots-gallery/FilterBar/FilterSearch';
import { render, screen, waitFor } from 'src/test-utils';
import type { ActiveFilters, FilterCounts } from 'src/types';

// The one report of a miss, replaced: `reported` records the text it is handed, and the count at
// Plausible runs as the real one runs it, so a test sees both reports. The claim's own rule and
// once-per-page-load are `searchMiss.test.ts`'s. The pause stays the real one.
const { reported } = vi.hoisted(() => ({ reported: vi.fn() }));
vi.mock('src/lib/searchMiss', async importOriginal => ({
  ...(await importOriginal<typeof import('src/lib/searchMiss')>()),
  reportSearchMiss: (query: string, count: () => void) => {
    reported(query);
    count();
  },
}));

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
    // The category of the pick, never what was typed: the dashboard is public.
    expect(defaultProps.onTrackEvent).toHaveBeenCalledWith('search', { category: 'plot' });
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
});

describe('FilterSearch misses for the private list', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  function type(text: string) {
    fireEvent.change(getSearchInput(), { target: { value: text } });
  }

  function wait(ms: number) {
    act(() => {
      vi.advanceTimersByTime(ms);
    });
  }

  function openSearch() {
    fireEvent.focus(getSearchInput());
  }

  it('sends no fragment followed by more typing, and the finished text once after the pause', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();

    type('zzqq');
    wait(MISS_PAUSE_MS - 500);
    type('zzqqx');
    wait(MISS_PAUSE_MS - 500);
    type('zzqqxy');
    wait(MISS_PAUSE_MS - 1);
    expect(reported).not.toHaveBeenCalled();

    wait(1);
    expect(reported).toHaveBeenCalledTimes(1);
    expect(reported).toHaveBeenCalledWith('zzqqxy');
    wait(MISS_PAUSE_MS * 2);
    expect(reported).toHaveBeenCalledTimes(1);
  });

  it('sends the normalised text', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('  ZZQQ   Chart ');
    wait(MISS_PAUSE_MS);

    expect(reported).toHaveBeenCalledWith('zzqq chart');
  });

  it('sends a pending miss at once when the field loses focus, and not again after the pause', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqqxy');
    wait(300);
    fireEvent.blur(getSearchInput());

    expect(reported).toHaveBeenCalledTimes(1);
    expect(reported).toHaveBeenCalledWith('zzqqxy');
    wait(MISS_PAUSE_MS);
    expect(reported).toHaveBeenCalledTimes(1);
  });

  it('drops a pending miss when Escape throws the text away', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqqxy');
    fireEvent.keyDown(getSearchInput(), { key: 'Escape' });
    // Escape also blurs the field, which must not send what was thrown away.
    fireEvent.blur(getSearchInput());
    wait(MISS_PAUSE_MS);

    expect(reported).not.toHaveBeenCalled();
  });

  it('drops a pending miss when the clear cross throws the text away, and keeps the focus', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqqxy');
    const cross = screen.getByTestId('CloseIcon');
    // The press keeps the focus in the field (its default is prevented), so no blur sends the text
    // before the click drops it.
    expect(fireEvent.mouseDown(cross)).toBe(false);
    fireEvent.click(cross);
    wait(MISS_PAUSE_MS);

    expect(reported).not.toHaveBeenCalled();
    expect(getSearchInput()).toHaveValue('');
  });

  /**
   * The open menu's invisible backdrop covers the page, so in a browser a press on the cross
   * lands on the backdrop, not on the cross (checked with a real browser: the element at the
   * cross's centre is the backdrop). The cross's box is given here, since jsdom lays nothing out.
   */
  function backdropWithCrossAt(left: number, top: number) {
    const cross = screen.getByTestId('CloseIcon');
    vi.spyOn(cross, 'getBoundingClientRect').mockReturnValue(new DOMRect(left, top, 18, 18));
    const backdrop = document.querySelector('.MuiBackdrop-root');
    expect(backdrop).not.toBeNull();
    return backdrop as HTMLElement;
  }

  it('drops a pending miss when a press on the cross reaches the menu backdrop', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqqxy');
    const backdrop = backdropWithCrossAt(200, 10);
    // The backdrop keeps the focus in the field, so no blur sends the text first.
    expect(fireEvent.mouseDown(backdrop)).toBe(false);
    fireEvent.click(backdrop, { clientX: 209, clientY: 19 });
    wait(MISS_PAUSE_MS);

    expect(reported).not.toHaveBeenCalled();
    expect(getSearchInput()).toHaveValue('');
  });

  it('sends a pending miss when a press elsewhere closes the menu', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqqxy');
    const backdrop = backdropWithCrossAt(200, 10);
    fireEvent.mouseDown(backdrop);
    fireEvent.click(backdrop, { clientX: 600, clientY: 400 });

    expect(reported).toHaveBeenCalledTimes(1);
    expect(reported).toHaveBeenCalledWith('zzqqxy');
  });

  it('drops a pending miss when "← back" leaves the category, and keeps the focus', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    // The second category is the library.
    fireEvent.keyDown(getSearchInput(), { key: 'ArrowDown' });
    fireEvent.keyDown(getSearchInput(), { key: 'ArrowDown' });
    fireEvent.keyDown(getSearchInput(), { key: 'Enter' });
    fireEvent.change(screen.getByLabelText('Search library'), { target: { value: 'zzqqxy' } });
    const back = screen.getByRole('menuitem', { name: '← library' });
    expect(fireEvent.mouseDown(back)).toBe(false);
    fireEvent.click(back);
    wait(MISS_PAUSE_MS);

    expect(reported).not.toHaveBeenCalled();
  });

  it('asks the browser and password managers not to fill the field', () => {
    render(<FilterSearch {...defaultProps} />);
    expect(getSearchInput()).toHaveAttribute('autocomplete', 'off');
  });

  it('sends a pending miss when the gallery goes away', () => {
    const view = render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqqxy');
    view.unmount();

    expect(reported).toHaveBeenCalledWith('zzqqxy');
  });

  it('sends nothing for a text that finds plots outside the active filters', () => {
    render(
      <FilterSearch {...defaultProps} activeFilters={seabornFilters} filterCounts={seabornCounts} />
    );
    fireEvent.keyDown(screen.getByRole('button', { name: 'Open filter search' }), {
      key: 'Enter',
    });
    type('bar');
    wait(MISS_PAUSE_MS);
    fireEvent.blur(getSearchInput());

    expect(reported).not.toHaveBeenCalled();
  });

  it('sends nothing for a text another category knows', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    // The second category is the library: `python` finds no library, but it is a language.
    fireEvent.keyDown(getSearchInput(), { key: 'ArrowDown' });
    fireEvent.keyDown(getSearchInput(), { key: 'ArrowDown' });
    fireEvent.keyDown(getSearchInput(), { key: 'Enter' });
    expect(screen.getByLabelText('Search library')).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Search library'), { target: { value: 'python' } });
    expect(screen.getByLabelText('No matches')).toBeInTheDocument();
    wait(MISS_PAUSE_MS);
    fireEvent.blur(screen.getByLabelText('Search library'));

    expect(reported).not.toHaveBeenCalled();
  });

  it('sends nothing while the counts of all plots are unknown', () => {
    render(<FilterSearch {...defaultProps} globalCounts={null} />);
    openSearch();
    type('zzqqxy');
    wait(MISS_PAUSE_MS);
    fireEvent.blur(getSearchInput());

    expect(reported).not.toHaveBeenCalled();
  });

  it('sends nothing for a text whose folded form finds something', () => {
    // A fullwidth "scatter": the gallery's search does not fold it and finds nothing, but the
    // text that would be sent, folded, is "scatter", a word the catalogue has.
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type(String.fromCodePoint(0xff53, 0xff43, 0xff41, 0xff54, 0xff54, 0xff45, 0xff52));
    wait(MISS_PAUSE_MS);
    fireEvent.blur(getSearchInput());

    expect(reported).not.toHaveBeenCalled();
  });

  it('sends nothing for a text that finds something', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('scatter');
    wait(MISS_PAUSE_MS);
    fireEvent.blur(getSearchInput());

    expect(reported).not.toHaveBeenCalled();
  });

  /** How often the search was counted at Plausible as one that found nothing. */
  function countedWithoutHit() {
    return vi
      .mocked(defaultProps.onTrackEvent)
      .mock.calls.filter(([name]) => name === 'search_no_results').length;
  }

  it('counts a search without a hit at Plausible only when it is reported, after the pause', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqq');
    wait(300); // the old count came 200 ms after a keystroke, fragments included
    expect(countedWithoutHit()).toBe(0);
    type('zzqqxy');
    wait(MISS_PAUSE_MS - 1);
    expect(countedWithoutHit()).toBe(0);
    expect(reported).not.toHaveBeenCalled();

    wait(1);
    expect(countedWithoutHit()).toBe(1);
    expect(reported).toHaveBeenCalledTimes(1);
    wait(MISS_PAUSE_MS * 2);
    expect(countedWithoutHit()).toBe(1);
  });

  it('counts a search without a hit at Plausible when the field loses focus, with the report', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqqxy');
    wait(300);
    fireEvent.blur(getSearchInput());

    expect(countedWithoutHit()).toBe(1);
    expect(reported).toHaveBeenCalledWith('zzqqxy');
  });

  it.each(['Escape', 'the clear cross'])(
    'counts nothing at Plausible for a text thrown away with %s',
    way => {
      render(<FilterSearch {...defaultProps} />);
      openSearch();
      type('zzqqxy');
      if (way === 'Escape') {
        fireEvent.keyDown(getSearchInput(), { key: 'Escape' });
        fireEvent.blur(getSearchInput());
      } else {
        const cross = screen.getByTestId('CloseIcon');
        fireEvent.mouseDown(cross);
        fireEvent.click(cross);
      }
      wait(MISS_PAUSE_MS);

      expect(countedWithoutHit()).toBe(0);
      expect(reported).not.toHaveBeenCalled();
    }
  );

  it('counts nothing at Plausible for a text the plots outside the filters match', () => {
    render(
      <FilterSearch {...defaultProps} activeFilters={seabornFilters} filterCounts={seabornCounts} />
    );
    fireEvent.keyDown(screen.getByRole('button', { name: 'Open filter search' }), {
      key: 'Enter',
    });
    type('bar');
    wait(MISS_PAUSE_MS);
    fireEvent.blur(getSearchInput());

    expect(countedWithoutHit()).toBe(0);
  });

  it('gives the public events no word of what was typed', () => {
    render(<FilterSearch {...defaultProps} />);
    openSearch();
    type('zzqqxy');
    wait(MISS_PAUSE_MS);
    type('scatter');
    fireEvent.keyDown(getSearchInput(), { key: 'Enter' });

    const calls = vi.mocked(defaultProps.onTrackEvent).mock.calls;
    expect(calls).toContainEqual(['search_no_results']);
    expect(calls).toContainEqual(['search', { category: 'plot' }]);
    expect(JSON.stringify(calls)).not.toMatch(/zzqqxy|scatter/);
  });
});
