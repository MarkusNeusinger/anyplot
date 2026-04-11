import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../test-utils';
import { ImagesGrid } from './ImagesGrid';
import type { PlotImage, LibraryInfo, SpecInfo } from '../types';
import type { ImageSize } from '../constants';
import { createRef } from 'react';

// Mock child components to isolate ImagesGrid
vi.mock('./ImageCard', () => ({
  ImageCard: ({ image, index }: { image: PlotImage; index: number }) => (
    <div data-testid={`image-card-${index}`}>{image.library}</div>
  ),
}));

vi.mock('./LoaderSpinner', () => ({
  LoaderSpinner: ({ size }: { size: string }) => (
    <div data-testid="loader-spinner">{size}</div>
  ),
}));

const mockLibraries: LibraryInfo[] = [
  { id: 'matplotlib', name: 'Matplotlib', description: 'Matplotlib desc', documentation_url: 'https://matplotlib.org' },
];

const mockSpecs: SpecInfo[] = [
  { id: 'scatter-basic', title: 'Basic Scatter Plot', description: 'A scatter plot' },
];

function makeImages(n: number): PlotImage[] {
  return Array.from({ length: n }, (_, i) => ({
    library: 'matplotlib',
    url: `https://example.com/img${i}.png`,
    spec_id: `scatter-${i}`,
  }));
}

interface DefaultProps {
  images: PlotImage[];
  viewMode: 'spec' | 'library';
  selectedSpec: string;
  selectedLibrary: string;
  loading: boolean;
  hasMore: boolean;
  isLoadingMore: boolean;
  isTransitioning: boolean;
  librariesData: LibraryInfo[];
  specsData: SpecInfo[];
  openTooltip: string | null;
  loadMoreRef: React.RefObject<HTMLDivElement | null>;
  imageSize: ImageSize;
  onTooltipToggle: ReturnType<typeof vi.fn>;
  onCardClick: ReturnType<typeof vi.fn>;
}

function getDefaultProps(overrides: Partial<DefaultProps> = {}): DefaultProps {
  return {
    images: [],
    viewMode: 'library',
    selectedSpec: '',
    selectedLibrary: '',
    loading: false,
    hasMore: false,
    isLoadingMore: false,
    isTransitioning: false,
    librariesData: mockLibraries,
    specsData: mockSpecs,
    openTooltip: null,
    loadMoreRef: createRef<HTMLDivElement>(),
    imageSize: 'normal',
    onTooltipToggle: vi.fn(),
    onCardClick: vi.fn(),
    ...overrides,
  };
}

describe('ImagesGrid', () => {
  it('shows loading spinner when loading with no images', () => {
    render(<ImagesGrid {...getDefaultProps({ loading: true })} />);
    expect(screen.getByTestId('loader-spinner')).toBeInTheDocument();
    expect(screen.getByTestId('loader-spinner')).toHaveTextContent('large');
  });

  it('shows "No images found" alert when images are empty and not loading', () => {
    render(<ImagesGrid {...getDefaultProps({ loading: false, images: [] })} />);
    expect(screen.getByText('No images found for this spec.')).toBeInTheDocument();
  });

  it('renders an ImageCard for each image', () => {
    const images = makeImages(3);
    render(<ImagesGrid {...getDefaultProps({ images })} />);

    expect(screen.getByTestId('image-card-0')).toBeInTheDocument();
    expect(screen.getByTestId('image-card-1')).toBeInTheDocument();
    expect(screen.getByTestId('image-card-2')).toBeInTheDocument();
  });

  it('renders correctly with compact image size', () => {
    const images = makeImages(2);
    render(<ImagesGrid {...getDefaultProps({ images, imageSize: 'compact' })} />);

    expect(screen.getByTestId('image-card-0')).toBeInTheDocument();
    expect(screen.getByTestId('image-card-1')).toBeInTheDocument();
  });

  it('renders bottom loading indicator when isLoadingMore and hasMore', () => {
    const images = makeImages(3);
    render(
      <ImagesGrid {...getDefaultProps({ images, hasMore: true, isLoadingMore: true })} />,
    );
    // There should be two loader spinners: one is the bottom small spinner
    const spinners = screen.getAllByTestId('loader-spinner');
    expect(spinners.some((s) => s.textContent === 'small')).toBe(true);
  });

  it('does not show loading spinner when loading but isTransitioning is true', () => {
    render(
      <ImagesGrid {...getDefaultProps({ loading: true, isTransitioning: true })} />,
    );
    // When isTransitioning is true and images is empty and loading, the first branch
    // is skipped. The second branch renders the empty alert because images.length===0
    // and !loading is false — so the condition (images.length > 0 || !loading) is false
    // and the component returns null.
    expect(screen.queryByTestId('loader-spinner')).not.toBeInTheDocument();
  });

  it('returns null when images empty, loading true, and transitioning true', () => {
    const { container } = render(
      <ImagesGrid {...getDefaultProps({ loading: true, isTransitioning: true, images: [] })} />,
    );
    // The component returns null in this case (neither spinner nor alert)
    expect(container.firstChild).toBeNull();
  });
});
