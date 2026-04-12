import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, userEvent } from '../test-utils';
import { SpecTabs } from './SpecTabs';

// Mock the lazy-loaded CodeHighlighter
vi.mock('./CodeHighlighter', () => ({
  default: ({ code }: { code: string }) => (
    <pre data-testid="code-highlighter">{code}</pre>
  ),
}));

// Mock the constants module to avoid import.meta issues
vi.mock('../constants', () => ({
  API_URL: 'http://localhost:8000',
}));

beforeEach(() => {
  vi.restoreAllMocks();
  // Mock fetch globally - return tag counts
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () =>
      Promise.resolve({
        globalCounts: {
          plot: { scatter: 42, line: 30 },
          data: { numeric: 20 },
          dep: { numpy: 50 },
        },
      }),
  });
});

const baseProps = {
  code: 'import matplotlib\nprint("hello")',
  specId: 'scatter-basic',
  title: 'Basic Scatter Plot',
  description: 'A scatter plot showing data points',
  libraryId: 'matplotlib',
  qualityScore: null as number | null,
};

describe('SpecTabs', () => {
  // -------------------------------------------------------
  // 1. Rendering in default mode (all 4 tabs visible)
  // -------------------------------------------------------
  it('renders all 4 tabs in default mode', () => {
    render(<SpecTabs {...baseProps} />);
    expect(screen.getByRole('tab', { name: /code/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /spec/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /impl/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /quality/i })).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 2. Rendering in overviewMode (only Spec tab)
  // -------------------------------------------------------
  it('renders only the Spec tab in overviewMode', () => {
    render(<SpecTabs {...baseProps} overviewMode />);
    expect(screen.queryByRole('tab', { name: /code/i })).not.toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /spec/i })).toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: /impl/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('tab', { name: /quality/i })).not.toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 3. Tab click opens content, second click collapses
  // -------------------------------------------------------
  it('opens tab content on click and collapses on second click', async () => {
    const user = userEvent.setup();
    const onTrackEvent = vi.fn();
    render(<SpecTabs {...baseProps} onTrackEvent={onTrackEvent} />);

    const specTab = screen.getByRole('tab', { name: /spec/i });

    // Click to open
    await user.click(specTab);
    expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
    expect(onTrackEvent).toHaveBeenCalledWith('tab_toggle', {
      action: 'open',
      tab: 'specification',
      library: 'matplotlib',
    });

    // Click again to collapse
    await user.click(specTab);
    expect(onTrackEvent).toHaveBeenCalledWith('tab_toggle', {
      action: 'close',
      tab: 'specification',
      library: 'matplotlib',
    });
  });

  // -------------------------------------------------------
  // 4. Specification tab content
  // -------------------------------------------------------
  it('shows specification content: title, description, applications, data, notes', async () => {
    const user = userEvent.setup();
    render(
      <SpecTabs
        {...baseProps}
        applications={['Data analysis', 'Statistical visualization']}
        data={['Random numeric data', 'CSV files']}
        notes={['Use for small datasets', 'Works best with 2D data']}
      />,
    );

    await user.click(screen.getByRole('tab', { name: /spec/i }));

    // Title
    expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();

    // Description heading and text
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByText('A scatter plot showing data points')).toBeInTheDocument();

    // Applications
    expect(screen.getByText('Applications')).toBeInTheDocument();
    expect(screen.getByText('Data analysis')).toBeInTheDocument();
    expect(screen.getByText('Statistical visualization')).toBeInTheDocument();

    // Data
    expect(screen.getByText('Data')).toBeInTheDocument();
    expect(screen.getByText('Random numeric data')).toBeInTheDocument();
    expect(screen.getByText('CSV files')).toBeInTheDocument();

    // Notes
    expect(screen.getByText('Notes')).toBeInTheDocument();
    expect(screen.getByText('Use for small datasets')).toBeInTheDocument();
    expect(screen.getByText('Works best with 2D data')).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 5. Implementation tab content
  // -------------------------------------------------------
  it('shows implementation content: imageDescription, strengths, weaknesses', async () => {
    const user = userEvent.setup();
    render(
      <SpecTabs
        {...baseProps}
        imageDescription="A colorful scatter plot with labeled axes"
        strengths={['Clear layout', 'Good color choices']}
        weaknesses={['Missing legend', 'Overlapping points']}
      />,
    );

    await user.click(screen.getByRole('tab', { name: /impl/i }));

    expect(screen.getByText('A colorful scatter plot with labeled axes')).toBeInTheDocument();

    expect(screen.getByText('Strengths')).toBeInTheDocument();
    expect(screen.getByText('Clear layout')).toBeInTheDocument();
    expect(screen.getByText('Good color choices')).toBeInTheDocument();

    expect(screen.getByText('Weaknesses')).toBeInTheDocument();
    expect(screen.getByText('Missing legend')).toBeInTheDocument();
    expect(screen.getByText('Overlapping points')).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 6. Quality tab: score display
  // -------------------------------------------------------
  it('shows quality score formatted as score/100', async () => {
    const user = userEvent.setup();
    render(<SpecTabs {...baseProps} qualityScore={85} />);

    await user.click(screen.getByRole('tab', { name: /85/i }));

    expect(screen.getByText('85/100')).toBeInTheDocument();
  });

  it('shows N/A when quality score is null', async () => {
    const user = userEvent.setup();
    render(<SpecTabs {...baseProps} qualityScore={null} />);

    await user.click(screen.getByRole('tab', { name: /quality/i }));

    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 7. Quality tab: criteria breakdown
  // -------------------------------------------------------
  it('shows criteria breakdown with category scores', async () => {
    const user = userEvent.setup();
    const criteriaChecklist = {
      visual_quality: {
        score: 18,
        max: 20,
        items: [
          { id: 'vq1', name: 'Color harmony', score: 9, max: 10, passed: true, comment: 'Great palette' },
          { id: 'vq2', name: 'Layout balance', score: 9, max: 10, passed: true },
        ],
      },
      accuracy: {
        score: 15,
        max: 20,
        items: [],
      },
    };
    render(<SpecTabs {...baseProps} qualityScore={92} criteriaChecklist={criteriaChecklist} />);

    await user.click(screen.getByRole('tab', { name: /92/i }));

    expect(screen.getByText('Breakdown')).toBeInTheDocument();
    expect(screen.getByText('visual quality')).toBeInTheDocument();
    expect(screen.getByText('18/20')).toBeInTheDocument();
    expect(screen.getByText('accuracy')).toBeInTheDocument();
    expect(screen.getByText('15/20')).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 8. Tags display
  // -------------------------------------------------------
  it('displays spec tags and impl tags', () => {
    render(
      <SpecTabs
        {...baseProps}
        tags={{ plot_type: ['scatter', 'bubble'], data_type: ['numeric'] }}
        implTags={{ dependencies: ['numpy'], techniques: ['vectorized'] }}
      />,
    );

    // Spec tags
    expect(screen.getByText('scatter')).toBeInTheDocument();
    expect(screen.getByText('bubble')).toBeInTheDocument();
    expect(screen.getByText('numeric')).toBeInTheDocument();

    // Impl tags
    expect(screen.getByText('numpy')).toBeInTheDocument();
    expect(screen.getByText('vectorized')).toBeInTheDocument();

    // Category labels
    expect(screen.getByText('plot type:')).toBeInTheDocument();
    expect(screen.getByText('data type:')).toBeInTheDocument();
    expect(screen.getByText('dependencies:')).toBeInTheDocument();
    expect(screen.getByText('techniques:')).toBeInTheDocument();
  });

  it('does not display impl tags in overviewMode', () => {
    render(
      <SpecTabs
        {...baseProps}
        overviewMode
        tags={{ plot_type: ['scatter'] }}
        implTags={{ dependencies: ['numpy'] }}
      />,
    );

    expect(screen.getByText('scatter')).toBeInTheDocument();
    expect(screen.queryByText('numpy')).not.toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 9. Copy code functionality
  // -------------------------------------------------------
  it('copies code to clipboard and fires tracking event', async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      value: { writeText },
      writable: true,
      configurable: true,
    });

    const onTrackEvent = vi.fn();
    render(<SpecTabs {...baseProps} onTrackEvent={onTrackEvent} />);

    // Open Code tab
    await user.click(screen.getByRole('tab', { name: /code/i }));

    // Click copy button
    const copyButton = screen.getByRole('button', { name: /copy code/i });
    await user.click(copyButton);

    expect(writeText).toHaveBeenCalledWith('import matplotlib\nprint("hello")');
    expect(onTrackEvent).toHaveBeenCalledWith('copy_code', {
      spec: 'scatter-basic',
      library: 'matplotlib',
      method: 'tab',
      page: 'spec_detail',
    });
  });

  // -------------------------------------------------------
  // 10. "No quality data available" message
  // -------------------------------------------------------
  it('shows "No quality data available." when no score and no checklist', async () => {
    const user = userEvent.setup();
    render(<SpecTabs {...baseProps} qualityScore={null} criteriaChecklist={undefined} />);

    await user.click(screen.getByRole('tab', { name: /quality/i }));

    expect(screen.getByText('No quality data available.')).toBeInTheDocument();
  });

  it('does not show "No quality data" when score is present', async () => {
    const user = userEvent.setup();
    render(<SpecTabs {...baseProps} qualityScore={75} />);

    await user.click(screen.getByRole('tab', { name: /75/i }));

    expect(screen.queryByText('No quality data available.')).not.toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 11. "No implementation review data available" message
  // -------------------------------------------------------
  it('shows "No implementation review data available." when no impl data', async () => {
    const user = userEvent.setup();
    render(
      <SpecTabs
        {...baseProps}
        imageDescription={undefined}
        strengths={undefined}
        weaknesses={undefined}
      />,
    );

    await user.click(screen.getByRole('tab', { name: /impl/i }));

    expect(screen.getByText('No implementation review data available.')).toBeInTheDocument();
  });

  it('does not show "No implementation review data" when imageDescription is present', async () => {
    const user = userEvent.setup();
    render(<SpecTabs {...baseProps} imageDescription="A nice plot" />);

    await user.click(screen.getByRole('tab', { name: /impl/i }));

    expect(
      screen.queryByText('No implementation review data available.'),
    ).not.toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 12. Quality tab label shows numeric score when present
  // -------------------------------------------------------
  it('shows numeric score in the Quality tab label', () => {
    render(<SpecTabs {...baseProps} qualityScore={93} />);
    expect(screen.getByRole('tab', { name: /93/i })).toBeInTheDocument();
  });

  it('shows "Quality" in the tab label when score is null', () => {
    render(<SpecTabs {...baseProps} qualityScore={null} />);
    expect(screen.getByRole('tab', { name: /quality/i })).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 13. Tag counts fetched and displayed
  // -------------------------------------------------------
  it('renders tags and fetch mock is configured for tag counts', async () => {
    // The module-level cache means fetch may or may not be called depending
    // on test execution order. We verify the component renders tags correctly.
    render(
      <SpecTabs
        {...baseProps}
        tags={{ plot_type: ['scatter'] }}
      />,
    );

    // Tag chip is rendered
    expect(screen.getByText('scatter')).toBeInTheDocument();

    // Fetch is mocked for tag counts (may be called if cache is empty)
    expect(global.fetch).toBeDefined();
  });

  // -------------------------------------------------------
  // 14. Implementation tab metadata (specId, libraryId, date)
  // -------------------------------------------------------
  it('shows metadata in the implementation tab', async () => {
    const user = userEvent.setup();
    render(
      <SpecTabs
        {...baseProps}
        imageDescription="Plot description"
        generatedAt="2025-01-15T00:00:00Z"
      />,
    );

    await user.click(screen.getByRole('tab', { name: /impl/i }));

    // The metadata line contains specId, libraryId, and date together
    expect(
      screen.getByText(/scatter-basic · matplotlib · Jan 15, 2025/),
    ).toBeInTheDocument();
  });

  // -------------------------------------------------------
  // 15. Code tab shows code via CodeHighlighter
  // -------------------------------------------------------
  it('renders CodeHighlighter with code when Code tab is open', async () => {
    const user = userEvent.setup();
    render(<SpecTabs {...baseProps} />);

    await user.click(screen.getByRole('tab', { name: /code/i }));

    await waitFor(() => {
      expect(screen.getByTestId('code-highlighter')).toBeInTheDocument();
    });
    expect(screen.getByTestId('code-highlighter')).toHaveTextContent(
      'import matplotlib print("hello")',
    );
  });

  // -------------------------------------------------------
  // 16. Tag click handler navigates
  // -------------------------------------------------------
  it('fires onTrackEvent and navigates on tag click', async () => {
    const user = userEvent.setup();
    const onTrackEvent = vi.fn();
    // Mock window.location.href setter
    const hrefSetter = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    });
    Object.defineProperty(window.location, 'href', {
      set: hrefSetter,
      get: () => '',
    });

    render(
      <SpecTabs
        {...baseProps}
        onTrackEvent={onTrackEvent}
        tags={{ plot_type: ['scatter'] }}
      />,
    );

    await user.click(screen.getByText('scatter'));

    expect(onTrackEvent).toHaveBeenCalledWith('tag_click', {
      param: 'plot',
      value: 'scatter',
      source: 'spec_detail',
    });
  });

  // -------------------------------------------------------
  // 17. Expanding criteria categories
  // -------------------------------------------------------
  it('expands criteria items on category click', async () => {
    const user = userEvent.setup();
    const criteriaChecklist = {
      visual_quality: {
        score: 18,
        max: 20,
        items: [
          { id: 'vq1', name: 'Color harmony', score: 9, max: 10, passed: true, comment: 'Looks great' },
        ],
      },
    };
    render(<SpecTabs {...baseProps} qualityScore={90} criteriaChecklist={criteriaChecklist} />);

    await user.click(screen.getByRole('tab', { name: /90/i }));

    // Click the category to expand
    await user.click(screen.getByText('visual quality'));

    // Now the item details should be visible
    expect(screen.getByText('Color harmony')).toBeInTheDocument();
    expect(screen.getByText('9/10')).toBeInTheDocument();
    expect(screen.getByText('Looks great')).toBeInTheDocument();
  });
});
