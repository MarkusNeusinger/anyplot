import { afterEach, describe, expect, it, vi } from 'vitest';

import { CommonWeaknesses } from 'src/sections/debug/CommonWeaknesses';
import { DailyActivityChart } from 'src/sections/debug/DailyActivityChart';
import { KPIGrid } from 'src/sections/debug/KPIGrid';
import { LibraryCoverage } from 'src/sections/debug/LibraryCoverage';
import { ProblemAreas } from 'src/sections/debug/ProblemAreas';
import { RecentActivity } from 'src/sections/debug/RecentActivity';
import { SystemHealthRow } from 'src/sections/debug/SystemHealthRow';
import { render, screen, userEvent, within } from 'src/test-utils';

describe('SystemHealthRow', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('shows initial system health before live pings arrive and updates with ping history', () => {
    const systemData = {
      database_connected: true,
      api_response_time_ms: 42,
      timestamp: '2026-05-20T12:00:00Z',
    };

    const { rerender } = render(
      <SystemHealthRow pings={[]} systemData={systemData} pingHistory={4} />
    );

    expect(screen.getByText('database connected')).toBeInTheDocument();
    expect(screen.getByText('42ms')).toBeInTheDocument();
    expect(screen.queryByText(/avg /i)).not.toBeInTheDocument();
    expect(screen.getByText(/updated /i)).toBeInTheDocument();

    // Rerender with mixed pings where the latest ping failed
    rerender(
      <SystemHealthRow
        pings={[
          { ms: 50, ok: true },
          { ms: 150, ok: true },
          { ms: 250, ok: false },
        ]}
        systemData={systemData}
        pingHistory={5}
      />
    );

    expect(screen.getByText('database down')).toBeInTheDocument();
    expect(screen.getByText('250ms')).toBeInTheDocument();
    expect(screen.getByText('avg 100')).toBeInTheDocument();

    // Rerender where latest ping is ok
    rerender(
      <SystemHealthRow
        pings={[
          { ms: 60, ok: true },
          { ms: 80, ok: true },
        ]}
        systemData={systemData}
        pingHistory={3}
      />
    );
    expect(screen.getByText('database connected')).toBeInTheDocument();
    expect(screen.getByText('80ms')).toBeInTheDocument();
    expect(screen.getByText('avg 70')).toBeInTheDocument();
  });
});

describe('KPIGrid', () => {
  it('renders formatted KPI values with suffixes and em-dash for null', () => {
    render(
      <KPIGrid
        kpis={[
          { label: 'specs', value: 120 },
          { label: 'impls', value: 1800 },
          { label: 'coverage', value: 92.4, suffix: '%' },
          { label: 'avg quality', value: null },
        ]}
      />
    );

    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('specs')).toBeInTheDocument();
    expect(screen.getByText('1.8K')).toBeInTheDocument();
    expect(screen.getByText('impls')).toBeInTheDocument();
    expect(screen.getByText('92.4%')).toBeInTheDocument();
    expect(screen.getByText('coverage')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();
    expect(screen.getByText('avg quality')).toBeInTheDocument();
  });
});

describe('DailyActivityChart', () => {
  it('renders activity header, date range endpoints, bar tooltip on hover, and handles empty data', async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <DailyActivityChart
        data={[
          { date: '2026-05-01', impls_updated: 0 },
          { date: '2026-05-02', impls_updated: 12 },
          { date: '2026-05-30', impls_updated: 4 },
        ]}
      />
    );

    expect(screen.getByText('daily activity')).toBeInTheDocument();
    expect(screen.getByText('implementation updates · last 30 days')).toBeInTheDocument();
    expect(screen.getByText('2026-05-01')).toBeInTheDocument();
    expect(screen.getByText('2026-05-30')).toBeInTheDocument();

    const bar = screen.getByLabelText('2026-05-02: 12 impls');
    await user.hover(bar);
    expect(await screen.findByRole('tooltip')).toHaveTextContent('2026-05-02: 12 impls');

    rerender(<DailyActivityChart data={[]} />);
    expect(screen.queryByLabelText(/impls$/)).not.toBeInTheDocument();
    expect(screen.queryByText('2026-05-01')).not.toBeInTheDocument();
    expect(screen.queryByText('2026-05-30')).not.toBeInTheDocument();
  });
});

describe('LibraryCoverage', () => {
  it('sorts libraries by implementation count descending and formats scores and null fallbacks', () => {
    render(
      <LibraryCoverage
        stats={[
          {
            id: 'seaborn',
            name: 'Seaborn',
            impl_count: 45,
            avg_score: 88.2,
            min_score: 72,
            max_score: 96,
          },
          {
            id: 'matplotlib',
            name: 'Matplotlib',
            impl_count: 90,
            avg_score: 93.4,
            min_score: 80,
            max_score: 99,
          },
          {
            id: 'pygal',
            name: 'Pygal',
            impl_count: 0,
            avg_score: null,
            min_score: null,
            max_score: null,
          },
        ]}
      />
    );

    expect(screen.getByText('libraries')).toBeInTheDocument();
    expect(screen.getByText('impl count · avg · min–max')).toBeInTheDocument();

    const names = screen.getAllByText(/Matplotlib|Seaborn|Pygal/).map(el => el.textContent);
    expect(names).toEqual(['Matplotlib', 'Seaborn', 'Pygal']);

    expect(screen.getByText('90')).toBeInTheDocument();
    expect(screen.getByText('93.4')).toBeInTheDocument();
    expect(screen.getByText('80–99')).toBeInTheDocument();
    expect(screen.getByText('72–96')).toBeInTheDocument();
    expect(screen.getByText('—–—')).toBeInTheDocument();
  });
});

describe('RecentActivity', () => {
  it('renders nothing when empty and lists recent implementation links when populated', () => {
    const { container, rerender } = render(<RecentActivity activity={[]} />);
    expect(container).toBeEmptyDOMElement();

    rerender(
      <RecentActivity
        activity={[
          {
            spec_id: 'scatter-basic',
            spec_title: 'Basic Scatter',
            library_id: 'matplotlib',
            language_id: 'python',
            quality_score: 94.6,
            generated_by: 'impl-generate',
            updated: '2026-05-20T10:00:00Z',
          },
          {
            spec_id: 'bar-grouped',
            spec_title: 'Grouped Bar',
            library_id: 'd3',
            language_id: 'javascript',
            quality_score: null,
            generated_by: null,
            updated: '2026-05-19T10:00:00Z',
          },
        ]}
      />
    );

    expect(screen.getByText('recent activity')).toBeInTheDocument();
    const links = screen.getAllByRole('link');
    expect(links[0]).toHaveAttribute('href', '/scatter-basic/python/matplotlib');
    expect(links[0]).toHaveTextContent('Basic Scatter');
    expect(links[0]).toHaveTextContent('95');
    expect(links[0]).toHaveTextContent('impl-generate');

    expect(links[1]).toHaveAttribute('href', '/bar-grouped/javascript/d3');
    expect(links[1]).toHaveTextContent('Grouped Bar');
  });
});

describe('CommonWeaknesses', () => {
  it('renders nothing when empty and displays weakness tags across frequency ratios', () => {
    const { container, rerender } = render(<CommonWeaknesses weaknesses={[]} />);
    expect(container).toBeEmptyDOMElement();

    rerender(
      <CommonWeaknesses
        weaknesses={[
          { text: 'overlapping labels', count: 20 },
          { text: 'missing units', count: 12 },
          { text: 'low contrast grid', count: 6 },
          { text: 'clipped title', count: 2 },
        ]}
      />
    );

    expect(screen.getByText('common weaknesses')).toBeInTheDocument();
    expect(screen.getByText('overlapping labels')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('missing units')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('low contrast grid')).toBeInTheDocument();
    expect(screen.getByText('6')).toBeInTheDocument();
    expect(screen.getByText('clipped title')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });
});

describe('ProblemAreas', () => {
  it('renders collapsible problem sections with counts and links to affected specs', () => {
    render(
      <ProblemAreas
        lowScoreThreshold={90}
        lowScoreSpecs={[
          { id: 'scatter-basic', title: 'Basic Scatter', issue: 'seaborn below 90', value: '78.0' },
          { id: 'bar-grouped', title: 'Grouped Bar', issue: 'bokeh below 90', value: null },
        ]}
        missingPreviewSpecs={[]}
        missingTagsSpecs={[
          {
            id: 'heatmap-annotated',
            title: 'Annotated Heatmap',
            issue: 'no domain tag',
            value: null,
          },
        ]}
        oldestSpecs={[]}
      />
    );

    expect(screen.getByText('problem areas')).toBeInTheDocument();
    const lowScoresSection = screen.getByText('low scores (avg < 90)').closest('summary');
    expect(lowScoresSection).not.toBeNull();
    expect(within(lowScoresSection as HTMLElement).getByText('2')).toBeInTheDocument();

    const missingPreviewsSection = screen.getByText('missing previews').closest('summary');
    expect(missingPreviewsSection).not.toBeNull();
    expect(within(missingPreviewsSection as HTMLElement).getByText('0')).toBeInTheDocument();

    const missingTagsSection = screen.getByText('missing tags').closest('summary');
    expect(missingTagsSection).not.toBeNull();
    expect(within(missingTagsSection as HTMLElement).getByText('1')).toBeInTheDocument();

    const oldestSpecsSection = screen.getByText('oldest specs').closest('summary');
    expect(oldestSpecsSection).not.toBeNull();
    expect(within(oldestSpecsSection as HTMLElement).getByText('0')).toBeInTheDocument();

    const scatterLink = screen.getByRole('link', { name: /scatter-basic/ });
    expect(scatterLink).toHaveAttribute('href', '/scatter-basic');
    expect(scatterLink).toHaveTextContent('seaborn below 90');
    expect(scatterLink).toHaveTextContent('78.0');

    const heatmapLink = screen.getByRole('link', { name: /heatmap-annotated/ });
    expect(heatmapLink).toHaveAttribute('href', '/heatmap-annotated');
    expect(heatmapLink).toHaveTextContent('no domain tag');
  });
});
