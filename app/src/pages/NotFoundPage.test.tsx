import { beforeEach, describe, expect, it, vi } from 'vitest';

import { NotFoundPage } from 'src/pages/NotFoundPage';
import { render, screen } from 'src/test-utils';

const mockTrackEvent = vi.fn();

// Mock react-helmet-async to avoid provider requirement
vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

vi.mock('src/hooks/useAnalytics', () => ({
  useAnalytics: () => ({
    trackPageview: vi.fn(),
    trackEvent: mockTrackEvent,
  }),
}));

describe('NotFoundPage', () => {
  beforeEach(() => {
    mockTrackEvent.mockClear();
  });

  it('renders page.miss() heading', () => {
    render(<NotFoundPage />);
    expect(screen.getByRole('heading', { level: 1, name: /page not found/i })).toBeInTheDocument();
  });

  it('renders 404 sub-message', () => {
    render(<NotFoundPage />);
    expect(screen.getByText(/404 — no route matched/i)).toBeInTheDocument();
  });

  it('renders link back to home', () => {
    render(<NotFoundPage />);
    const link = screen.getByRole('link', { name: /go home/i });
    expect(link).toHaveAttribute('href', '/');
  });
});

describe('NotFoundPage analytics', () => {
  beforeEach(() => {
    mockTrackEvent.mockClear();
  });

  it('reports the miss with the path that was requested', () => {
    window.history.pushState({}, '', '/bar-basic/python/highcharts');
    render(<NotFoundPage />);
    expect(mockTrackEvent).toHaveBeenCalledWith('page_not_found', {
      path: '/bar-basic/python/highcharts',
      source: 'catch_all',
    });
  });

  it('distinguishes a routed-but-missing spec from an unmatched URL', () => {
    window.history.pushState({}, '', '/bar-basic/python/highcharts');
    render(<NotFoundPage source="spec_missing" />);
    expect(mockTrackEvent).toHaveBeenCalledWith('page_not_found', {
      path: '/bar-basic/python/highcharts',
      source: 'spec_missing',
    });
  });

  it('fires once per mount, not once per render', () => {
    const { rerender } = render(<NotFoundPage />);
    rerender(<NotFoundPage />);
    expect(mockTrackEvent).toHaveBeenCalledTimes(1);
  });
});
