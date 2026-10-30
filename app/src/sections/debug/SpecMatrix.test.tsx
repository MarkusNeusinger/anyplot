import { useMemo, useState } from 'react';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { LIBRARIES } from 'src/constants';
import { countImpls } from 'src/sections/debug/debugFormat';
import { HeaderCell } from 'src/sections/debug/HeaderCell';
import { SortableHeader, type SortDir } from 'src/sections/debug/SortableHeader';
import { SpecMatrix, type SpecStatus } from 'src/sections/debug/SpecMatrix';
import { render, screen, userEvent } from 'src/test-utils';

function makeSpec(overrides: Partial<SpecStatus> & { id: string; title: string }): SpecStatus {
  return {
    updated: '2026-01-15T12:00:00Z',
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
    updated: '2026-01-15T12:00:00Z',
    avg_score: 95.0,
    ...ALL_LIBRARIES_FULL,
  }),
  makeSpec({
    id: 'bar-grouped',
    title: 'Grouped Bar Chart',
    updated: '2026-02-20T12:00:00Z',
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

type SortCol = keyof SpecStatus | 'coverage';

function StatefulSpecMatrix({ specs = SAMPLE_SPECS }: { specs?: SpecStatus[] }) {
  const [searchText, setSearchText] = useState('');
  const [showIncomplete, setShowIncomplete] = useState(false);
  const [showLowScores, setShowLowScores] = useState(false);
  const [missingLibrary, setMissingLibrary] = useState('');
  const [sortCol, setSortCol] = useState<SortCol>('updated');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  const filteredSpecs = useMemo(() => {
    let list = [...specs];
    if (searchText) {
      const q = searchText.toLowerCase();
      list = list.filter(s => s.id.toLowerCase().includes(q) || s.title.toLowerCase().includes(q));
    }
    if (showIncomplete) {
      list = list.filter(s => countImpls(s) < LIBRARIES.length);
    }
    if (showLowScores) {
      list = list.filter(s =>
        LIBRARIES.some(lib => {
          const score = s[lib as keyof SpecStatus] as number | null;
          return score !== null && score < 90;
        })
      );
    }
    if (missingLibrary) {
      list = list.filter(s => s[missingLibrary as keyof SpecStatus] === null);
    }
    list.sort((a, b) => {
      let cmp = 0;
      switch (sortCol) {
        case 'updated':
          cmp = (a.updated || '').localeCompare(b.updated || '');
          break;
        case 'id':
          cmp = a.id.localeCompare(b.id);
          break;
        case 'title':
          cmp = a.title.localeCompare(b.title);
          break;
        case 'avg_score':
          cmp = (a.avg_score ?? 0) - (b.avg_score ?? 0);
          break;
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });
    return list;
  }, [specs, searchText, showIncomplete, showLowScores, missingLibrary, sortCol, sortDir]);

  const handleSort = (col: SortCol) => {
    if (sortCol === col) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortCol(col);
      setSortDir(col === 'updated' || col === 'avg_score' ? 'desc' : 'asc');
    }
  };

  return (
    <SpecMatrix
      searchText={searchText}
      setSearchText={setSearchText}
      showIncomplete={showIncomplete}
      setShowIncomplete={setShowIncomplete}
      showLowScores={showLowScores}
      setShowLowScores={setShowLowScores}
      missingLibrary={missingLibrary}
      setMissingLibrary={setMissingLibrary}
      filteredSpecs={filteredSpecs}
      totalSpecs={specs.length}
      sortCol={sortCol}
      sortDir={sortDir}
      handleSort={handleSort}
    />
  );
}

/** Returns the spec IDs in the order they appear in the desktop table links. */
function renderedSpecOrder(): string[] {
  const knownIds = new Set(SAMPLE_SPECS.map(s => s.id));
  return screen
    .getAllByRole('link')
    .map(link => link.textContent ?? '')
    .filter(text => knownIds.has(text));
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
    render(<StatefulSpecMatrix />);

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

  it('sorts specs by each sortable column and toggles direction', async () => {
    const user = userEvent.setup();
    render(<StatefulSpecMatrix />);

    // Initial sort is updated desc: bar-grouped (Feb 20), scatter-basic (Jan 15), heatmap-annotated (null)
    expect(renderedSpecOrder()).toEqual(['bar-grouped', 'scatter-basic', 'heatmap-annotated']);

    // Toggle updated to asc
    await user.click(screen.getByRole('button', { name: /updated/ }));
    expect(renderedSpecOrder()).toEqual(['heatmap-annotated', 'scatter-basic', 'bar-grouped']);

    // Sort by spec id (defaults to asc, then toggle to desc)
    await user.click(screen.getByRole('button', { name: /spec id/ }));
    expect(renderedSpecOrder()).toEqual(['bar-grouped', 'heatmap-annotated', 'scatter-basic']);

    await user.click(screen.getByRole('button', { name: /spec id/ }));
    expect(renderedSpecOrder()).toEqual(['scatter-basic', 'heatmap-annotated', 'bar-grouped']);

    // Sort by title (defaults to asc, then toggle to desc)
    await user.click(screen.getByRole('button', { name: /title/ }));
    expect(renderedSpecOrder()).toEqual(['heatmap-annotated', 'scatter-basic', 'bar-grouped']);

    await user.click(screen.getByRole('button', { name: /title/ }));
    expect(renderedSpecOrder()).toEqual(['bar-grouped', 'scatter-basic', 'heatmap-annotated']);

    // Sort by avg (defaults to desc, then toggle to asc)
    await user.click(screen.getByRole('button', { name: /avg/ }));
    expect(renderedSpecOrder()).toEqual(['scatter-basic', 'bar-grouped', 'heatmap-annotated']);

    await user.click(screen.getByRole('button', { name: /avg/ }));
    expect(renderedSpecOrder()).toEqual(['heatmap-annotated', 'bar-grouped', 'scatter-basic']);
  });

  it('filters specs by search text, incomplete coverage, low scores, and missing library', async () => {
    const user = userEvent.setup();
    render(<StatefulSpecMatrix />);

    // Incomplete filter (< 15 libraries): excludes scatter-basic (15/15)
    const incompleteBtn = screen.getByRole('button', {
      name: new RegExp(`incomplete <${LIBRARIES.length}`, 'i'),
    });
    await user.click(incompleteBtn);
    expect(screen.getByText('2 / 3')).toBeInTheDocument();
    expect(renderedSpecOrder()).toEqual(['bar-grouped', 'heatmap-annotated']);

    // Toggle incomplete off
    await user.click(incompleteBtn);
    expect(screen.getByText('3 / 3')).toBeInTheDocument();

    // Low scores filter (< 90): keeps only bar-grouped (seaborn = 78)
    const lowScoresBtn = screen.getByRole('button', { name: /low scores <90/i });
    await user.click(lowScoresBtn);
    expect(screen.getByText('1 / 3')).toBeInTheDocument();
    expect(renderedSpecOrder()).toEqual(['bar-grouped']);

    // Toggle low scores off
    await user.click(lowScoresBtn);
    expect(screen.getByText('3 / 3')).toBeInTheDocument();

    // Missing library filter: matplotlib is present on scatter-basic and bar-grouped, missing on heatmap-annotated
    const missingSelect = screen.getByRole('combobox');
    await user.selectOptions(missingSelect, 'matplotlib');
    expect(screen.getByText('1 / 3')).toBeInTheDocument();
    expect(renderedSpecOrder()).toEqual(['heatmap-annotated']);

    // Reset missing library filter
    await user.selectOptions(missingSelect, '');
    expect(screen.getByText('3 / 3')).toBeInTheDocument();

    // Search input filter by title or id
    const searchInput = screen.getByPlaceholderText('search spec id or title...');
    await user.type(searchInput, 'Grouped');
    expect(screen.getByText('1 / 3')).toBeInTheDocument();
    expect(renderedSpecOrder()).toEqual(['bar-grouped']);
  });
});
