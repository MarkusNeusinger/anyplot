import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '../test-utils';

const trackEvent = vi.fn();

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

import { PlotOfTheDay } from './PlotOfTheDay';

// Mock sessionStorage
const sessionStorageMock: Record<string, string> = {};
const sessionStorageStub = {
  getItem: vi.fn((key: string) => sessionStorageMock[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { sessionStorageMock[key] = value; }),
  removeItem: vi.fn((key: string) => { delete sessionStorageMock[key]; }),
  clear: vi.fn(() => { Object.keys(sessionStorageMock).forEach(k => delete sessionStorageMock[k]); }),
  get length() { return Object.keys(sessionStorageMock).length; },
  key: vi.fn(() => null),
};

const mockData = {
  spec_id: 'scatter-basic',
  spec_title: 'Basic Scatter Plot',
  description: 'A scatter plot',
  library_id: 'matplotlib',
  library_name: 'Matplotlib',
  language: 'python',
  quality_score: 9,
  preview_url: 'https://cdn.example.com/plots/scatter-basic/matplotlib/plot.png',
  image_description: 'Shows data points with clear labels',
  library_version: '3.8.0',
  python_version: '3.12',
  date: '2026-04-11',
};

describe('PlotOfTheDay', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    // Reset sessionStorage mock state
    Object.keys(sessionStorageMock).forEach(k => delete sessionStorageMock[k]);
    vi.stubGlobal('sessionStorage', sessionStorageStub);
    sessionStorageStub.getItem.mockClear();
    sessionStorageStub.setItem.mockClear();
    trackEvent.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders a placeholder while loading', () => {
    // Never resolve the fetch, so component stays in loading state
    fetchMock.mockReturnValue(new Promise(() => {}));

    const { container } = render(<PlotOfTheDay />);

    // The loading state renders a Box with minHeight for CLS prevention
    const placeholder = container.firstChild as HTMLElement;
    expect(placeholder).toBeInTheDocument();
    // Should not show any text content yet
    expect(screen.queryByText('plot of the day')).not.toBeInTheDocument();
  });

  it('shows the card after successful fetch', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    render(<PlotOfTheDay />);

    await waitFor(() => {
      expect(screen.getByText('plot of the day')).toBeInTheDocument();
    });

    expect(screen.getByText('Basic Scatter Plot')).toBeInTheDocument();
  });

  it('shows image description when present', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    render(<PlotOfTheDay />);

    await waitFor(() => {
      expect(screen.getByText(/Shows data points with clear labels/)).toBeInTheDocument();
    });
  });

  it('shows library version and python version in bottom bar', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    render(<PlotOfTheDay />);

    await waitFor(() => {
      expect(screen.getByText(/Matplotlib 3\.8\.0/)).toBeInTheDocument();
      expect(screen.getByText(/Python 3\.12/)).toBeInTheDocument();
    });
  });

  it('returns null immediately when dismissed via sessionStorage', () => {
    sessionStorageMock['potd_dismissed'] = 'true';

    const { container } = render(<PlotOfTheDay />);

    // Dismissed state returns null — no DOM output
    expect(container.firstChild).toBeNull();
    // Should not have fetched
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('returns null after API error', async () => {
    fetchMock.mockResolvedValueOnce({ ok: false });

    const { container } = render(<PlotOfTheDay />);

    await waitFor(() => {
      // After loading finishes with error, data is null so component returns null
      expect(container.firstChild).toBeNull();
    });
  });

  it('dismisses on close button click', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const { userEvent } = await import('../test-utils');
    const user = userEvent.setup();

    const { container } = render(<PlotOfTheDay />);

    await waitFor(() => {
      expect(screen.getByText('plot of the day')).toBeInTheDocument();
    });

    const dismissButton = screen.getByLabelText('Dismiss plot of the day');
    await user.click(dismissButton);

    // After dismiss, component should return null
    expect(container.firstChild).toBeNull();
    expect(sessionStorageStub.setItem).toHaveBeenCalledWith('potd_dismissed', 'true');
    expect(trackEvent).toHaveBeenCalledWith('potd_dismiss', expect.objectContaining({ spec: 'scatter-basic', library: 'matplotlib' }));
  });

  it('tracks nav_click when the image, title and source link are clicked', async () => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockData),
    });

    const { userEvent } = await import('../test-utils');
    const user = userEvent.setup();

    render(<PlotOfTheDay />);

    await waitFor(() => {
      expect(screen.getByText('plot of the day')).toBeInTheDocument();
    });

    await user.click(screen.getByText('Basic Scatter Plot'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'potd_title' }));

    const sourceLink = screen.getByText(/python plots\/scatter-basic\/matplotlib\.py/);
    expect(sourceLink.getAttribute('href')).toMatch(
      /\/blob\/main\/plots\/scatter-basic\/implementations\/python\/matplotlib\.py$/,
    );
    await user.click(sourceLink);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', expect.objectContaining({ source: 'potd_source_link' }));
  });

  it('hides library version when it is "unknown"', async () => {
    const dataWithUnknownVersion = { ...mockData, library_version: 'unknown' };
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(dataWithUnknownVersion),
    });

    render(<PlotOfTheDay />);

    await waitFor(() => {
      expect(screen.getByText('plot of the day')).toBeInTheDocument();
    });

    // Should show "Matplotlib" without " unknown" appended
    // The bottom bar text node should contain just "Matplotlib" followed by python version
    const bottomText = screen.getByText(/Matplotlib/);
    expect(bottomText.textContent).not.toContain('unknown');
  });
});
