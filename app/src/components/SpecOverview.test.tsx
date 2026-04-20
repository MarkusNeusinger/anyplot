import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '../test-utils';
import { SpecOverview } from './SpecOverview';
import type { Implementation } from '../types';

vi.mock('../utils/responsiveImage', () => ({
  buildSrcSet: (url: string, fmt: string) => `${url}-srcset-${fmt}`,
  OVERVIEW_SIZES: '33vw',
}));

const makeImpl = (overrides: Partial<Implementation> = {}): Implementation => ({
  library_id: 'matplotlib',
  library_name: 'Matplotlib',
  preview_url: 'https://example.com/plot.png',
  preview_html: undefined,
  quality_score: 85,
  code: 'print("hello")',
  ...overrides,
});

const implA = makeImpl({ library_id: 'altair', library_name: 'Altair', quality_score: 72 });
const implB = makeImpl({ library_id: 'matplotlib', library_name: 'Matplotlib', quality_score: 85 });
const implC = makeImpl({
  library_id: 'plotly',
  library_name: 'Plotly',
  quality_score: 90,
  preview_html: '<div>interactive</div>',
});

const defaultGetLibraryMeta = (id: string) => ({
  id,
  name: id,
  description: `${id} description`,
  documentation_url: `https://${id}.org`,
});

const defaultProps = {
  specId: 'scatter-basic',
  specTitle: 'Basic Scatter Plot',
  implementations: [implC, implA, implB],
  codeCopied: null,
  downloadDone: null,
  openTooltip: null,
  onImplClick: vi.fn(),
  onCopyCode: vi.fn(),
  onDownload: vi.fn(),
  onTooltipToggle: vi.fn(),
  getLibraryMeta: defaultGetLibraryMeta,
  onTrackEvent: vi.fn(),
};

describe('SpecOverview', () => {
  it('renders all implementation cards', () => {
    render(<SpecOverview {...defaultProps} />);
    const images = screen.getAllByRole('img');
    expect(images).toHaveLength(3);
  });

  it('cards are sorted alphabetically by library_id', () => {
    render(<SpecOverview {...defaultProps} />);
    const images = screen.getAllByRole('img');
    // Sorted: altair, matplotlib, plotly
    expect(images[0]).toHaveAttribute('alt', 'Basic Scatter Plot - altair');
    expect(images[1]).toHaveAttribute('alt', 'Basic Scatter Plot - matplotlib');
    expect(images[2]).toHaveAttribute('alt', 'Basic Scatter Plot - plotly');
  });

  it('shows quality score for each implementation', () => {
    render(<SpecOverview {...defaultProps} />);
    expect(screen.getByText('72')).toBeInTheDocument();
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('90')).toBeInTheDocument();
  });

  it('does not show quality score when null', () => {
    const implNoScore = makeImpl({ library_id: 'seaborn', quality_score: null });
    render(
      <SpecOverview
        {...defaultProps}
        implementations={[implNoScore]}
      />,
    );
    expect(screen.getByText('seaborn')).toBeInTheDocument();
    // No score rendered - only the library name text and no numeric text
    const allText = screen.getByText('seaborn').closest('[class]')?.parentElement?.textContent;
    expect(allText).not.toMatch(/\d+/);
  });

  it('shows library name below each card', () => {
    render(<SpecOverview {...defaultProps} />);
    expect(screen.getByText('altair')).toBeInTheDocument();
    expect(screen.getByText('matplotlib')).toBeInTheDocument();
    expect(screen.getByText('plotly')).toBeInTheDocument();
  });

  it('calls onImplClick when a card is clicked', async () => {
    const onImplClick = vi.fn();
    const user = userEvent.setup();

    render(<SpecOverview {...defaultProps} onImplClick={onImplClick} />);

    // Click on the first image (altair, sorted)
    const images = screen.getAllByRole('img');
    await user.click(images[0]);
    expect(onImplClick).toHaveBeenCalledWith('altair');
  });

  it('renders Copy Code button for each card that calls onCopyCode', async () => {
    const onCopyCode = vi.fn();
    const user = userEvent.setup();

    render(<SpecOverview {...defaultProps} onCopyCode={onCopyCode} />);

    const copyButtons = screen.getAllByRole('button', { name: /copy code/i });
    expect(copyButtons).toHaveLength(3);

    await user.click(copyButtons[0]);
    // First sorted impl is altair
    expect(onCopyCode).toHaveBeenCalledWith(implA);
  });

  it('renders Download PNG button for each card that calls onDownload', async () => {
    const onDownload = vi.fn();
    const user = userEvent.setup();

    render(<SpecOverview {...defaultProps} onDownload={onDownload} />);

    const downloadButtons = screen.getAllByRole('button', { name: /download png/i });
    expect(downloadButtons).toHaveLength(3);

    await user.click(downloadButtons[1]);
    // Second sorted impl is matplotlib
    expect(onDownload).toHaveBeenCalledWith(implB);
  });

  it('shows Open Interactive only for implementations with preview_html', () => {
    render(<SpecOverview {...defaultProps} />);
    // Only plotly has preview_html
    const interactiveLinks = screen.getAllByRole('link', { name: /open interactive/i });
    expect(interactiveLinks).toHaveLength(1);
  });

  it('shows skeleton when an implementation has no preview_url', () => {
    const implNoPreview = makeImpl({
      library_id: 'bokeh',
      library_name: 'Bokeh',
      preview_url: '' as unknown as string,
    });
    // SpecOverview checks `impl.preview_url` as truthy -> falsy string renders skeleton
    const { container } = render(
      <SpecOverview
        {...defaultProps}
        implementations={[makeImpl({ library_id: 'bokeh', preview_url: '' as unknown as string })]}
      />,
    );
    const skeleton = container.querySelector('.MuiSkeleton-root');
    expect(skeleton).toBeInTheDocument();
  });

  it('shows ">>> .copied" overlay when codeCopied matches a library_id', () => {
    render(
      <SpecOverview {...defaultProps} codeCopied="matplotlib" />,
    );
    expect(screen.getByText('>>> .copied')).toBeInTheDocument();
  });

  it('shows ">>> .downloaded" overlay when downloadDone matches a library_id', () => {
    render(
      <SpecOverview {...defaultProps} downloadDone="plotly" />,
    );
    expect(screen.getByText('>>> .downloaded')).toBeInTheDocument();
  });

  it('does not show overlay when codeCopied does not match any library_id', () => {
    render(
      <SpecOverview {...defaultProps} codeCopied="nonexistent" />,
    );
    expect(screen.queryByText('>>> .copied')).not.toBeInTheDocument();
    expect(screen.queryByText('>>> .downloaded')).not.toBeInTheDocument();
  });
});
