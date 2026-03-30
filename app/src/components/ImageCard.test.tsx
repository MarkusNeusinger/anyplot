import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../test-utils';
import { ImageCard } from './ImageCard';
import type { PlotImage } from '../types';

// Mock useCodeFetch to avoid actual API calls
vi.mock('../hooks/useCodeFetch', () => ({
  useCodeFetch: () => ({ fetchCode: vi.fn().mockResolvedValue('print("hello")'), cache: new Map() }),
}));

const baseImage: PlotImage = {
  library: 'matplotlib',
  url: 'https://example.com/plot.png',
  spec_id: 'scatter-basic',
  title: 'Basic Scatter Plot',
};

const defaultProps = {
  image: baseImage,
  index: 0,
  viewMode: 'library' as const,
  selectedSpec: '',
  openTooltip: null,
  imageSize: 'normal' as const,
  onTooltipToggle: vi.fn(),
  onClick: vi.fn(),
};

describe('ImageCard', () => {
  it('renders the card with spec_id label', () => {
    render(<ImageCard {...defaultProps} />);
    expect(screen.getByText('scatter-basic')).toBeInTheDocument();
  });

  it('renders library name in normal mode', () => {
    render(<ImageCard {...defaultProps} />);
    expect(screen.getByText('matplotlib')).toBeInTheDocument();
  });

  it('renders the plot image with responsive fallback src', () => {
    render(<ImageCard {...defaultProps} />);
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', 'https://example.com/plot_800.png');
  });

  it('calls onClick when card is clicked', async () => {
    const { userEvent } = await import('../test-utils');
    const user = userEvent.setup();
    const onClick = vi.fn();

    render(<ImageCard {...defaultProps} onClick={onClick} />);
    await user.click(screen.getByRole('button', { name: /view scatter-basic plot/i }));
    expect(onClick).toHaveBeenCalledWith(baseImage);
  });

  it('has correct aria-label for library view mode', () => {
    render(<ImageCard {...defaultProps} viewMode="library" />);
    expect(screen.getByRole('button', { name: /view scatter-basic plot/i })).toHaveAttribute(
      'aria-label',
      'View scatter-basic plot in fullscreen'
    );
  });

  it('toggles spec tooltip on spec_id click', async () => {
    const { userEvent } = await import('../test-utils');
    const user = userEvent.setup();
    const onTooltipToggle = vi.fn();

    render(<ImageCard {...defaultProps} onTooltipToggle={onTooltipToggle} />);

    // Click on the spec_id text
    await user.click(screen.getByText('scatter-basic'));
    expect(onTooltipToggle).toHaveBeenCalledWith('spec-scatter-basic-matplotlib');
  });

  it('shows spec description when tooltip is open', () => {
    render(
      <ImageCard
        {...defaultProps}
        specDescription="A basic scatter plot example"
        openTooltip="spec-scatter-basic-matplotlib"
      />
    );
    expect(screen.getByText('A basic scatter plot example')).toBeInTheDocument();
  });
});
