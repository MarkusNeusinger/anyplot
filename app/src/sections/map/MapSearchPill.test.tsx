import { useRef, useState } from 'react';

import { afterEach, describe, expect, it, vi } from 'vitest';

import type { SpecMapItem } from 'src/pages/MapPage.helpers';
import { act, fireEvent, render, screen } from 'src/test-utils';

import { MapSearchPill } from './MapSearchPill';

const mockMatches: SpecMapItem[] = [
  {
    id: 'scatter-basic',
    title: 'Basic Scatter Plot',
    preview_url_light: null,
    preview_url_dark: null,
    quality_score: 90,
    tags: { plot_type: ['scatter'] },
    impl_tags: null,
  },
  {
    id: 'line-basic',
    title: 'Basic Line Chart',
    preview_url_light: null,
    preview_url_dark: null,
    quality_score: 92,
    tags: { plot_type: ['line'] },
    impl_tags: null,
  },
];

interface HarnessProps {
  initialQuery?: string;
  initialOpen?: boolean;
  initialIdx?: number;
  matches?: SpecMapItem[];
  onSelectMatch?: (spec: SpecMapItem) => void;
}

function SearchPillHarness({
  initialQuery = '',
  initialOpen = false,
  initialIdx = 0,
  matches = mockMatches,
  onSelectMatch = vi.fn(),
}: HarnessProps) {
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [searchOpen, setSearchOpen] = useState(initialOpen);
  const [searchIdx, setSearchIdx] = useState(initialIdx);
  const searchInputRef = useRef<HTMLInputElement | null>(null);

  return (
    <MapSearchPill
      searchQuery={searchQuery}
      setSearchQuery={setSearchQuery}
      searchOpen={searchOpen}
      setSearchOpen={setSearchOpen}
      searchIdx={searchIdx}
      setSearchIdx={setSearchIdx}
      searchInputRef={searchInputRef}
      searchMatches={matches}
      selectMatch={onSelectMatch}
    />
  );
}

describe('MapSearchPill', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('renders the search input and hides the dropdown when closed or when query is blank', () => {
    const { unmount } = render(<SearchPillHarness initialQuery="scatter" initialOpen={false} />);

    const input = screen.getByPlaceholderText('specs.search()');
    expect(input).toHaveValue('scatter');
    expect(screen.queryByText('Basic Scatter Plot')).not.toBeInTheDocument();
    unmount();

    render(<SearchPillHarness initialQuery="   " initialOpen={true} />);
    expect(screen.getByPlaceholderText('specs.search()')).toHaveValue('   ');
    expect(screen.queryByText('Basic Scatter Plot')).not.toBeInTheDocument();
  });

  it('opens on focus, shows matching results, and closes after blur timeout', () => {
    vi.useFakeTimers();
    render(<SearchPillHarness initialQuery="basic" initialOpen={false} />);

    const input = screen.getByPlaceholderText('specs.search()');
    fireEvent.focus(input);

    expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
    expect(screen.getByText('scatter-basic')).toBeInTheDocument();
    expect(screen.getByText('Basic Line Chart')).toBeInTheDocument();
    expect(screen.getByText('line-basic')).toBeInTheDocument();

    fireEvent.blur(input);
    act(() => {
      vi.advanceTimersByTime(150);
    });
    expect(screen.queryByText('Basic Scatter Plot')).not.toBeInTheDocument();
  });

  it('shows the empty state when searchOpen is true with a non-empty query and no matches', () => {
    render(<SearchPillHarness initialQuery="nonexistent" initialOpen={true} matches={[]} />);

    expect(screen.getByLabelText('No matches')).toHaveTextContent('results.empty()');
  });

  it('navigates results with ArrowDown/ArrowUp, selects with Enter, and clears with Escape', () => {
    vi.useFakeTimers();
    const selectMatch = vi.fn();
    render(
      <SearchPillHarness
        initialQuery="basic"
        initialOpen={true}
        initialIdx={0}
        onSelectMatch={selectMatch}
      />
    );

    const input = screen.getByPlaceholderText('specs.search()');
    input.focus();

    // Move down to index 1, clamp at the last item, then press Enter
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(selectMatch).toHaveBeenCalledTimes(1);
    expect(selectMatch).toHaveBeenLastCalledWith(mockMatches[1]);

    // Move back up to index 0, clamp at 0, then press Enter
    fireEvent.keyDown(input, { key: 'ArrowUp' });
    fireEvent.keyDown(input, { key: 'ArrowUp' });
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(selectMatch).toHaveBeenCalledTimes(2);
    expect(selectMatch).toHaveBeenLastCalledWith(mockMatches[0]);

    // Typing resets index to 0 and updates the query
    fireEvent.keyDown(input, { key: 'ArrowDown' });
    fireEvent.change(input, { target: { value: 'line' } });
    expect(input).toHaveValue('line');
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(selectMatch).toHaveBeenLastCalledWith(mockMatches[0]);

    // Escape clears the query and blurs the input
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(input).toHaveValue('');
    expect(document.activeElement).not.toBe(input);
    expect(screen.queryByText('Basic Scatter Plot')).not.toBeInTheDocument();
  });

  it('selects a result on mouseDown and updates active index on mouseEnter', () => {
    const selectMatch = vi.fn();
    render(
      <SearchPillHarness initialQuery="basic" initialOpen={true} onSelectMatch={selectMatch} />
    );

    const input = screen.getByPlaceholderText('specs.search()');
    const secondItem = screen.getByText('Basic Line Chart');

    fireEvent.mouseEnter(secondItem);
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(selectMatch).toHaveBeenCalledWith(mockMatches[1]);

    selectMatch.mockClear();
    fireEvent.mouseDown(screen.getByText('Basic Scatter Plot'));
    expect(selectMatch).toHaveBeenCalledWith(mockMatches[0]);
  });

  it('does not call selectMatch on Enter when there are no matches', () => {
    const selectMatch = vi.fn();
    render(
      <SearchPillHarness
        initialQuery="none"
        initialOpen={true}
        matches={[]}
        onSelectMatch={selectMatch}
      />
    );

    const input = screen.getByPlaceholderText('specs.search()');
    fireEvent.keyDown(input, { key: 'Enter' });
    expect(selectMatch).not.toHaveBeenCalled();
  });
});
