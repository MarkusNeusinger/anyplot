import type { ComponentProps } from 'react';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { LIBRARIES } from 'src/constants';
import { HeaderCell } from 'src/sections/debug/HeaderCell';
import { SortableHeader } from 'src/sections/debug/SortableHeader';
import { SpecMatrix, type SpecStatus } from 'src/sections/debug/SpecMatrix';
import { render, screen, userEvent } from 'src/test-utils';

function makeSpec(overrides: Partial<SpecStatus> & { id: string; title: string }): SpecStatus {
  return {
    updated: '2026-01-15T12:00:00',
    avg_score: null,
    altair: null,
    bokeh: null,
    chartjs: null,
    d3: null,
    echarts: null,
    ggplot2: null,
    highcharts: null,
    letsplot: null,
    makie: null,
    matplotlib: null,
    muix: null,
    plotly: null,
    plotnine: null,
    pygal: null,
    seaborn: null,
    ...overrides,
  };
}

const ALL_LIBRARIES_FULL = Object.fromEntries(
  LIBRARIES.map(lib => [lib, 95])
) as Partial<SpecStatus>;

const SAMPLE_SPECS: SpecStatus[] = [
  makeSpec({
    id: 'scatter-basic',
    title: 'Basic Scatter Plot',
    updated: '2026-01-15T12:00:00',
    avg_score: 95.0,
    ...ALL_LIBRARIES_FULL,
  }),
  makeSpec({
    id: 'bar-grouped',
    title: 'Grouped Bar Chart',
    updated: '2026-02-20T12:00:00',
    avg_score: 84.5,
    matplotlib: 91,
    seaborn: 78,
  }),
  makeSpec({
    id: 'heatmap-annotated',
    title: 'Annotated Heatmap',
    updated: null,
    avg_score: null,
  }),
];

function makeMatrixProps(
  overrides: Partial<ComponentProps<typeof SpecMatrix>> = {}
): ComponentProps<typeof SpecMatrix> {
  return {
    searchText: '',
    setSearchText: vi.fn(),
    showIncomplete: false,
    setShowIncomplete: vi.fn(),
    showLowScores: false,
    setShowLowScores: vi.fn(),
    missingLibrary: '',
    setMissingLibrary: vi.fn(),
    filteredSpecs: SAMPLE_SPECS,
    totalSpecs: SAMPLE_SPECS.length,
    sortCol: 'updated',
    sortDir: 'desc',
    handleSort: vi.fn(),
    ...overrides,
  };
}

describe('HeaderCell', () => {
  it('renders header text in both default and centered alignments', () => {
    const { rerender } = render(<HeaderCell>#</HeaderCell>);
    expect(screen.getByText('#')).toBeInTheDocument();

    rerender(<HeaderCell center>mpl</HeaderCell>);
    expect(screen.getByText('mpl')).toBeInTheDocument();
  });
});

describe('SortableHeader', () => {
  it('shows the direction indicator only when active and triggers onClick', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    const { rerender } = render(
      <SortableHeader label="spec id" active={false} dir="asc" onClick={onClick} />
    );

    const button = screen.getByRole('button', { name: 'spec id' });
    expect(button).not.toHaveTextContent('▲');
    expect(button).not.toHaveTextContent('▼');

    await user.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);

    rerender(<SortableHeader label="spec id" active dir="asc" onClick={onClick} center />);
    expect(screen.getByRole('button', { name: /spec id/ })).toHaveTextContent('▲');

    rerender(<SortableHeader label="spec id" active dir="desc" onClick={onClick} center />);
    expect(screen.getByRole('button', { name: /spec id/ })).toHaveTextContent('▼');
  });
});

describe('SpecMatrix', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('renders spec rows with implementation counts, scores, links, and fallback dashes', () => {
    render(<SpecMatrix {...makeMatrixProps()} />);

    expect(screen.getByText('3 / 3')).toBeInTheDocument();
    expect(screen.getByText(`${LIBRARIES.length}/${LIBRARIES.length}`)).toBeInTheDocument();
    expect(screen.getByText(`2/${LIBRARIES.length}`)).toBeInTheDocument();
    expect(screen.getByText(`0/${LIBRARIES.length}`)).toBeInTheDocument();

    // Average score formatting in desktop and mobile views
    expect(screen.getByText('95.0')).toBeInTheDocument();
    expect(screen.getByText('84.5')).toBeInTheDocument();
    expect(screen.getByText('avg 95')).toBeInTheDocument();
    expect(screen.getByText('avg 85')).toBeInTheDocument();
    expect(screen.getByText('avg —')).toBeInTheDocument();

    // Updated date formatting and missing activity fallback
    expect(screen.getByText('Jan 15')).toBeInTheDocument();
    expect(screen.getByText('Feb 20')).toBeInTheDocument();
    expect(screen.getByText('no activity')).toBeInTheDocument();

    // Links to spec pages and implementation pages
    const specLinks = screen.getAllByRole('link', { name: 'scatter-basic' });
    expect(specLinks[0]).toHaveAttribute('href', '/scatter-basic');

    const implLinks = screen.getAllByRole('link', { name: '78' });
    expect(implLinks[0]).toHaveAttribute('href', '/bar-grouped/python/seaborn');
  });

  it('shows the direction arrow only on the active sortable header and calls handleSort for each column', async () => {
    const user = userEvent.setup();
    const handleSort = vi.fn();

    const { rerender } = render(
      <SpecMatrix {...makeMatrixProps({ sortCol: 'id', sortDir: 'asc', handleSort })} />
    );

    const getHeaders = () => ({
      id: screen.getByRole('button', { name: /^spec id/ }),
      title: screen.getByRole('button', { name: /^title/ }),
      avg_score: screen.getByRole('button', { name: /^avg/ }),
      updated: screen.getByRole('button', { name: /^updated/ }),
    });

    let headers = getHeaders();
    expect(headers.id).toHaveTextContent('▲');
    expect(headers.title).not.toHaveTextContent(/[▲▼]/);
    expect(headers.avg_score).not.toHaveTextContent(/[▲▼]/);
    expect(headers.updated).not.toHaveTextContent(/[▲▼]/);

    rerender(
      <SpecMatrix {...makeMatrixProps({ sortCol: 'title', sortDir: 'desc', handleSort })} />
    );
    headers = getHeaders();
    expect(headers.title).toHaveTextContent('▼');
    expect(headers.id).not.toHaveTextContent(/[▲▼]/);
    expect(headers.avg_score).not.toHaveTextContent(/[▲▼]/);
    expect(headers.updated).not.toHaveTextContent(/[▲▼]/);

    rerender(
      <SpecMatrix {...makeMatrixProps({ sortCol: 'avg_score', sortDir: 'asc', handleSort })} />
    );
    headers = getHeaders();
    expect(headers.avg_score).toHaveTextContent('▲');
    expect(headers.id).not.toHaveTextContent(/[▲▼]/);
    expect(headers.title).not.toHaveTextContent(/[▲▼]/);
    expect(headers.updated).not.toHaveTextContent(/[▲▼]/);

    rerender(
      <SpecMatrix {...makeMatrixProps({ sortCol: 'updated', sortDir: 'desc', handleSort })} />
    );
    headers = getHeaders();
    expect(headers.updated).toHaveTextContent('▼');
    expect(headers.id).not.toHaveTextContent(/[▲▼]/);
    expect(headers.title).not.toHaveTextContent(/[▲▼]/);
    expect(headers.avg_score).not.toHaveTextContent(/[▲▼]/);

    await user.click(headers.id);
    expect(handleSort).toHaveBeenLastCalledWith('id');

    await user.click(headers.title);
    expect(handleSort).toHaveBeenLastCalledWith('title');

    await user.click(headers.avg_score);
    expect(handleSort).toHaveBeenLastCalledWith('avg_score');

    await user.click(headers.updated);
    expect(handleSort).toHaveBeenLastCalledWith('updated');
    expect(handleSort).toHaveBeenCalledTimes(4);
  });

  it('calls filter setters when controls are used', async () => {
    const user = userEvent.setup();
    const setSearchText = vi.fn();
    const setShowIncomplete = vi.fn();
    const setShowLowScores = vi.fn();
    const setMissingLibrary = vi.fn();

    const { rerender } = render(
      <SpecMatrix
        {...makeMatrixProps({
          setSearchText,
          setShowIncomplete,
          setShowLowScores,
          setMissingLibrary,
        })}
      />
    );

    const incompleteBtn = screen.getByRole('button', {
      name: new RegExp(`incomplete <${LIBRARIES.length}`, 'i'),
    });
    await user.click(incompleteBtn);
    expect(setShowIncomplete).toHaveBeenCalledTimes(1);
    const incompleteUpdater = setShowIncomplete.mock.calls[0][0] as (prev: boolean) => boolean;
    expect(incompleteUpdater(false)).toBe(true);
    expect(incompleteUpdater(true)).toBe(false);

    const lowScoresBtn = screen.getByRole('button', { name: /low scores <90/i });
    await user.click(lowScoresBtn);
    expect(setShowLowScores).toHaveBeenCalledTimes(1);
    const lowScoresUpdater = setShowLowScores.mock.calls[0][0] as (prev: boolean) => boolean;
    expect(lowScoresUpdater(false)).toBe(true);
    expect(lowScoresUpdater(true)).toBe(false);

    const missingSelect = screen.getByRole('combobox');
    await user.selectOptions(missingSelect, 'matplotlib');
    expect(setMissingLibrary).toHaveBeenCalledWith('matplotlib');

    const searchInput = screen.getByPlaceholderText('search spec id or title...');
    await user.type(searchInput, 'scatter');
    expect(setSearchText).toHaveBeenCalledWith('s');

    // Render with active filter flags
    rerender(
      <SpecMatrix
        {...makeMatrixProps({
          showIncomplete: true,
          showLowScores: true,
          missingLibrary: 'matplotlib',
          searchText: 'scatter',
        })}
      />
    );
    expect(screen.getByDisplayValue('scatter')).toBeInTheDocument();
    expect(screen.getByRole('combobox')).toHaveValue('matplotlib');
  });
});
