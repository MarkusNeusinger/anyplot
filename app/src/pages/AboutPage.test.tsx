import { describe, expect, it, vi } from 'vitest';

import { AboutPage } from 'src/pages/AboutPage';
import { fireEvent, render, screen } from 'src/test-utils';

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({ trackPageview: vi.fn(), trackEvent: vi.fn() }),
}));

describe('AboutPage', () => {
  it('links the palette page through the router', () => {
    render(<AboutPage />);

    const link = screen.getByRole('link', { name: 'palette page' });
    expect(link).toHaveAttribute('href', '/palette');
    // A plain href renders the same anchor; only the router cancels the click's full page load.
    expect(fireEvent.click(link)).toBe(false);
  });

  it('links the stats, plots and mcp pages from the review, chat and mcp sections', () => {
    render(<AboutPage />);

    for (const [name, href] of [
      ['stats page', '/stats'],
      ['pick any plot', '/plots'],
      ['mcp page', '/mcp'],
    ]) {
      const link = screen.getByRole('link', { name });
      expect(link).toHaveAttribute('href', href);
      expect(fireEvent.click(link)).toBe(false);
    }
  });

  it('sends a plot request to the issue form, with no label or title prefilled', () => {
    render(<AboutPage />);

    expect(screen.getByRole('link', { name: /request_plot\(\)/ })).toHaveAttribute(
      'href',
      'https://github.com/MarkusNeusinger/anyplot/issues/new?template=request-new-plot.yml'
    );
  });
});
