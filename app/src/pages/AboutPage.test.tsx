import { describe, expect, it, vi } from 'vitest';

import { AboutPage } from 'src/pages/AboutPage';
import { fireEvent, render, screen } from 'src/test-utils';

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({ trackEvent: vi.fn() }),
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

    // The stats page twice: the review's score distribution and the mcp section's machine readers.
    for (const [name, href, links] of [
      ['stats page', '/stats', 2],
      ['pick any plot', '/plots', 1],
      ['mcp page', '/mcp', 1],
    ] as const) {
      const found = screen.getAllByRole('link', { name });
      expect(found).toHaveLength(links);
      for (const link of found) {
        expect(link).toHaveAttribute('href', href);
        expect(fireEvent.click(link)).toBe(false);
      }
    }
  });

  it('names the machine readers on the stats page in the mcp section', () => {
    render(<AboutPage />);

    expect(
      screen.getByText(/how many assistants and crawlers read the catalogue and how many came/)
    ).toBeInTheDocument();
  });

  it('sends a plot request to the issue form, with no label or title prefilled', () => {
    render(<AboutPage />);

    expect(screen.getByRole('link', { name: /request_plot\(\)/ })).toHaveAttribute(
      'href',
      'https://github.com/MarkusNeusinger/anyplot/issues/new?template=request-new-plot.yml'
    );
  });
});
