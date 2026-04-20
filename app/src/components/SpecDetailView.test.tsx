import { describe, it, expect, vi } from 'vitest';
import { render, screen, userEvent } from '../test-utils';
import { SpecDetailView } from './SpecDetailView';
import type { Implementation } from '../types';

vi.mock('../utils/responsiveImage', () => ({
  buildDetailSrcSet: (url: string, fmt: string) => `${url}-srcset-${fmt}`,
  DETAIL_SIZES: '100vw',
}));

const makeImpl = (overrides: Partial<Implementation> = {}): Implementation => ({
  library_id: 'matplotlib',
  library_name: 'Matplotlib',
  language: 'python',
  preview_url: 'https://example.com/plot.png',
  preview_html: null,
  quality_score: 85,
  code: 'import matplotlib\nprint("hello")',
  ...overrides,
});

const implA = makeImpl({ library_id: 'altair', library_name: 'Altair' });
const implB = makeImpl({ library_id: 'matplotlib', library_name: 'Matplotlib' });
const implC = makeImpl({ library_id: 'plotly', library_name: 'Plotly', preview_html: '<div>interactive</div>' });

const defaultProps = {
  specTitle: 'Basic Scatter Plot',
  selectedLibrary: 'matplotlib',
  currentImpl: implB,
  implementations: [implB, implA, implC],
  imageLoaded: true,
  codeCopied: null,
  downloadDone: null,
  viewMode: 'preview' as const,
  onImageLoad: vi.fn(),
  onCopyCode: vi.fn(),
  onDownload: vi.fn(),
  onViewModeChange: vi.fn(),
  onTrackEvent: vi.fn(),
};

describe('SpecDetailView', () => {
  it('renders image with correct alt text', () => {
    render(<SpecDetailView {...defaultProps} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('alt', 'Basic Scatter Plot - matplotlib');
  });

  it('shows skeleton when image is not loaded', () => {
    const { container } = render(
      <SpecDetailView {...defaultProps} imageLoaded={false} />,
    );
    // MUI Skeleton renders a span with class containing MuiSkeleton
    const skeleton = container.querySelector('.MuiSkeleton-root');
    expect(skeleton).toBeInTheDocument();
  });

  it('does not show skeleton when image is loaded', () => {
    const { container } = render(
      <SpecDetailView {...defaultProps} imageLoaded={true} />,
    );
    const skeleton = container.querySelector('.MuiSkeleton-root');
    expect(skeleton).not.toBeInTheDocument();
  });

  it('renders Copy Code button that calls onCopyCode', async () => {
    const onCopyCode = vi.fn();
    const user = userEvent.setup();

    render(<SpecDetailView {...defaultProps} onCopyCode={onCopyCode} />);

    const btn = screen.getByRole('button', { name: /copy code/i });
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(onCopyCode).toHaveBeenCalledWith(implB);
  });

  it('renders Download PNG button that calls onDownload', async () => {
    const onDownload = vi.fn();
    const user = userEvent.setup();

    render(<SpecDetailView {...defaultProps} onDownload={onDownload} />);

    const btn = screen.getByRole('button', { name: /download png/i });
    expect(btn).toBeInTheDocument();
    await user.click(btn);
    expect(onDownload).toHaveBeenCalledWith(implB);
  });

  it('shows Show Interactive button only when preview_html exists', () => {
    // No preview_html on current impl
    const { rerender } = render(<SpecDetailView {...defaultProps} />);
    expect(screen.queryByRole('button', { name: /show interactive/i })).not.toBeInTheDocument();

    // With preview_html — renders an in-page toggle button (no longer a link)
    rerender(
      <SpecDetailView
        {...defaultProps}
        currentImpl={implC}
        selectedLibrary="plotly"
      />,
    );
    expect(screen.getByRole('button', { name: /show interactive/i })).toBeInTheDocument();
  });

  it('shows implementation counter with current/total', () => {
    render(<SpecDetailView {...defaultProps} />);
    // Sorted alphabetically: altair(1), matplotlib(2), plotly(3) -> matplotlib = 2/3
    expect(screen.getByText('2/3')).toBeInTheDocument();
  });

  it('does not show implementation counter when only one implementation', () => {
    render(
      <SpecDetailView
        {...defaultProps}
        implementations={[implB]}
      />,
    );
    expect(screen.queryByText('1/1')).not.toBeInTheDocument();
  });

  it('shows ">>> copied" overlay when codeCopied matches current library', () => {
    render(
      <SpecDetailView {...defaultProps} codeCopied="matplotlib" />,
    );
    expect(screen.getByText('>>> copied')).toBeInTheDocument();
  });

  it('shows ">>> downloaded" overlay when downloadDone matches current library', () => {
    render(
      <SpecDetailView {...defaultProps} downloadDone="matplotlib" />,
    );
    expect(screen.getByText('>>> downloaded')).toBeInTheDocument();
  });

  it('does not show overlay when codeCopied does not match current library', () => {
    render(
      <SpecDetailView {...defaultProps} codeCopied="plotly" />,
    );
    expect(screen.queryByText('>>> copied')).not.toBeInTheDocument();
    expect(screen.queryByText('>>> downloaded')).not.toBeInTheDocument();
  });

  it('toggles zoom on click via aria-label change', async () => {
    const user = userEvent.setup();
    render(<SpecDetailView {...defaultProps} />);

    const zoomContainer = screen.getByRole('button', { name: 'Zoom in' });
    expect(zoomContainer).toBeInTheDocument();

    await user.click(zoomContainer);
    expect(screen.getByRole('button', { name: 'Zoom out' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Zoom out' }));
    expect(screen.getByRole('button', { name: 'Zoom in' })).toBeInTheDocument();
  });

  it('renders nothing special when currentImpl is null', () => {
    render(
      <SpecDetailView {...defaultProps} currentImpl={null} />,
    );
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /copy code/i })).not.toBeInTheDocument();
  });
});
