import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { HelmetProvider } from 'react-helmet-async';

vi.mock('../hooks', () => ({
  useAnalytics: () => ({ trackPageview: vi.fn(), trackEvent: vi.fn() }),
}));

vi.mock('../components/Breadcrumb', () => ({
  Breadcrumb: () => <nav data-testid="breadcrumb">Breadcrumb</nav>,
}));

import { InteractivePage } from './InteractivePage';

const theme = createTheme();

function renderWithRoute(specId: string, library: string) {
  return render(
    <HelmetProvider>
      <ThemeProvider theme={theme}>
        <MemoryRouter initialEntries={[`/interactive/${specId}/${library}`]}>
          <Routes>
            <Route path="/interactive/:specId/:library" element={<InteractivePage />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    </HelmetProvider>
  );
}

const mockSpecData = {
  id: 'scatter-basic',
  title: 'Basic Scatter Plot',
  implementations: [
    { library_id: 'plotly', preview_html: 'https://example.com/scatter.html' },
    { library_id: 'matplotlib', preview_html: null },
  ],
};

describe('InteractivePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})));
    renderWithRoute('scatter-basic', 'plotly');
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders iframe after successful fetch', async () => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockSpecData),
      })
    ));

    renderWithRoute('scatter-basic', 'plotly');

    await waitFor(() => {
      const iframe = document.querySelector('iframe');
      expect(iframe).toBeTruthy();
    });
  });

  it('shows error when no interactive HTML available', async () => {
    vi.stubGlobal('fetch', vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          ...mockSpecData,
          implementations: [{ library_id: 'matplotlib', preview_html: null }],
        }),
      })
    ));

    renderWithRoute('scatter-basic', 'plotly');

    await waitFor(() => {
      expect(screen.getByText(/no interactive/i)).toBeInTheDocument();
    });
  });

  it('shows error on fetch failure', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new Error('Network error'))));

    renderWithRoute('scatter-basic', 'plotly');

    await waitFor(() => {
      expect(screen.getByText(/failed|error/i)).toBeInTheDocument();
    });
  });
});
