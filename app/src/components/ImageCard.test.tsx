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
  language: 'python',
  url: 'https://example.com/plot.png',
  spec_id: 'scatter-basic',
  title: 'Basic Scatter Plot',
};

const rImage: PlotImage = {
  library: 'ggplot2',
  language: 'r',
  url: 'https://example.com/biplot.png',
  spec_id: 'biplot-pca',
  title: 'PCA Biplot',
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

  describe('language token', () => {
    it('renders the language token in normal mode for python', () => {
      render(<ImageCard {...defaultProps} />);
      expect(screen.getByLabelText('Language: Python')).toHaveTextContent('Python');
    });

    it('renders the language token in normal mode for r', () => {
      render(<ImageCard {...defaultProps} image={rImage} />);
      expect(screen.getByLabelText('Language: R')).toHaveTextContent('R');
    });

    it('toggles the language tooltip on click', async () => {
      const { userEvent } = await import('../test-utils');
      const user = userEvent.setup();
      const onTooltipToggle = vi.fn();
      render(<ImageCard {...defaultProps} onTooltipToggle={onTooltipToggle} />);

      await user.click(screen.getByLabelText('Language: Python'));
      expect(onTooltipToggle).toHaveBeenCalledWith('lang-scatter-basic-matplotlib');
    });

    it('shows the language description + docs link when its tooltip is open', () => {
      render(
        <ImageCard
          {...defaultProps}
          languageDescription="High-level programming language."
          languageDocUrl="https://www.python.org"
          openTooltip="lang-scatter-basic-matplotlib"
        />
      );
      expect(screen.getByText('High-level programming language.')).toBeInTheDocument();
      const link = screen.getByRole('link', { name: /www\.python\.org/i });
      expect(link).toHaveAttribute('href', 'https://www.python.org');
      expect(link).toHaveAttribute('target', '_blank');
    });

    it('does not show the language token in compact mode', () => {
      render(<ImageCard {...defaultProps} imageSize="compact" />);
      expect(screen.queryByLabelText('Language: Python')).not.toBeInTheDocument();
    });

    it('embeds the language as a file-extension suffix on the library in compact mode (python)', () => {
      render(<ImageCard {...defaultProps} imageSize="compact" />);
      expect(screen.getByText('mpl.py')).toBeInTheDocument();
    });

    it('embeds the language as a file-extension suffix on the library in compact mode (r)', () => {
      render(<ImageCard {...defaultProps} image={rImage} imageSize="compact" />);
      expect(screen.getByText('ggplot2.r')).toBeInTheDocument();
    });
  });
});
