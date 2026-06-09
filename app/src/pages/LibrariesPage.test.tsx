import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { ReactNode } from 'react';
import { render, screen, userEvent } from '../test-utils';

const trackEvent = vi.fn();
const trackPageview = vi.fn();
const navigate = vi.fn();

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview }),
    useAppData: () => ({
      specsData: [],
      librariesData: [
        { id: 'matplotlib', name: 'Matplotlib', language: 'python', framework: 'none' },
        { id: 'muix', name: 'MUI X Charts', language: 'javascript', framework: 'react' },
      ],
      stats: { specs: 100, plots: 900, libraries: 15, lines_of_code: 50000 },
    }),
  };
});

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: ReactNode }) => <div data-testid="helmet">{children}</div>,
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => navigate };
});

import { LibrariesPage } from './LibrariesPage';

describe('LibrariesPage', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    trackPageview.mockClear();
    navigate.mockClear();
  });

  it('lists every library, including the muix React entry, by default', () => {
    render(<LibrariesPage />);
    expect(screen.getByText('muix')).toBeInTheDocument();
    expect(screen.getByText('matplotlib')).toBeInTheDocument();
  });

  it('shows a React framework badge on the muix card', () => {
    render(<LibrariesPage />);
    expect(screen.getByLabelText('Framework: React')).toBeInTheDocument();
  });

  it('filters to React-compatible libraries only (built generically off LIB_TO_FRAMEWORK)', async () => {
    const user = userEvent.setup();
    render(<LibrariesPage />);

    // Both visible before filtering.
    expect(screen.getByText('matplotlib')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'React-compatible' }));

    // muix stays (framework: react); matplotlib (framework: none) is filtered out.
    expect(screen.getByText('muix')).toBeInTheDocument();
    expect(screen.queryByText('matplotlib')).not.toBeInTheDocument();
    expect(trackEvent).toHaveBeenCalledWith('library_filter', { source: 'libraries_page', framework: 'react' });
  });

  it('restores the full list when "all libraries" is reselected', async () => {
    const user = userEvent.setup();
    render(<LibrariesPage />);

    await user.click(screen.getByRole('button', { name: 'React-compatible' }));
    expect(screen.queryByText('matplotlib')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'all libraries' }));
    expect(screen.getByText('matplotlib')).toBeInTheDocument();
    expect(screen.getByText('muix')).toBeInTheDocument();
  });
});
