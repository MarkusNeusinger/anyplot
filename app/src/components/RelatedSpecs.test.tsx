import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';
import { RelatedSpecs } from './RelatedSpecs';

describe('RelatedSpecs', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  const mockRelated = [
    {
      id: 'line-basic',
      title: 'Basic Line Plot',
      preview_url: 'https://cdn.example.com/plots/line-basic/matplotlib/plot.png',
      library_id: 'matplotlib',
      similarity: 0.85,
      shared_tags: ['line', 'basic'],
    },
    {
      id: 'bar-basic',
      title: 'Basic Bar Chart',
      preview_url: 'https://cdn.example.com/plots/bar-basic/seaborn/plot.png',
      library_id: 'seaborn',
      similarity: 0.72,
      shared_tags: ['bar'],
    },
  ];

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders a placeholder while loading', () => {
    fetchMock.mockReturnValue(new Promise(() => {}));

    const { container } = render(<RelatedSpecs specId="scatter-basic" />);

    // Loading state reserves space with minHeight
    const placeholder = container.firstChild as HTMLElement;
    expect(placeholder).toBeInTheDocument();
    // Tab bar should not be visible during loading
    expect(screen.queryByText('Similar')).not.toBeInTheDocument();
  });

  it('renders spec cards with titles after fetch', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ related: mockRelated }),
    });

    render(<RelatedSpecs specId="scatter-basic" />);

    await waitFor(() => {
      expect(screen.getByText('Basic Line Plot')).toBeInTheDocument();
    });

    expect(screen.getByText('Basic Bar Chart')).toBeInTheDocument();
    expect(screen.getByText('Similar')).toBeInTheDocument();
  });

  it('shows shared tags count for each card', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ related: mockRelated }),
    });

    render(<RelatedSpecs specId="scatter-basic" />);

    await waitFor(() => {
      expect(screen.getByText('2 tags in common')).toBeInTheDocument();
    });
    expect(screen.getByText('1 tags in common')).toBeInTheDocument();
  });

  it('returns null when fetch returns empty results', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ related: [] }),
    });

    const { container } = render(<RelatedSpecs specId="scatter-basic" />);

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it('returns null on API error', async () => {
    fetchMock.mockResolvedValueOnce({ ok: false });

    const { container } = render(<RelatedSpecs specId="scatter-basic" />);

    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it('passes library param in URL when mode is full', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ related: mockRelated }),
    });

    render(<RelatedSpecs specId="scatter-basic" mode="full" library="matplotlib" />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });

    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain('mode=full');
    expect(url).toContain('library=matplotlib');
  });

  it('calls onHoverTags on mouse enter and clears on leave', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ related: mockRelated }),
    });

    const { userEvent } = await import('../test-utils');
    const user = userEvent.setup();
    const onHoverTags = vi.fn();

    render(<RelatedSpecs specId="scatter-basic" onHoverTags={onHoverTags} />);

    await waitFor(() => {
      expect(screen.getByText('Basic Line Plot')).toBeInTheDocument();
    });

    // Hover over the first card link
    const firstCard = screen.getByText('Basic Line Plot').closest('a')!;
    await user.hover(firstCard);
    expect(onHoverTags).toHaveBeenCalledWith(['line', 'basic']);

    await user.unhover(firstCard);
    expect(onHoverTags).toHaveBeenCalledWith([]);
  });

  it('renders "no preview" text when preview_url is null', async () => {
    const relatedWithNoPreview = [
      { ...mockRelated[0], preview_url: null },
    ];
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ related: relatedWithNoPreview }),
    });

    render(<RelatedSpecs specId="scatter-basic" />);

    await waitFor(() => {
      expect(screen.getByText('no preview')).toBeInTheDocument();
    });
  });
});
