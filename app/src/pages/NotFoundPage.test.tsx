import { afterEach, describe, expect, it, vi } from 'vitest';

import { NotFoundPage } from 'src/pages/NotFoundPage';
import { render, screen } from 'src/test-utils';

describe('NotFoundPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
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

  it('sends no event of its own: the layout records the address as a pageview', () => {
    const plausible = vi.fn();
    vi.stubGlobal('plausible', plausible);
    window.history.pushState({}, '', '/bar-basic/python/highcharts');

    render(<NotFoundPage />);

    expect(plausible).not.toHaveBeenCalled();
  });
});
