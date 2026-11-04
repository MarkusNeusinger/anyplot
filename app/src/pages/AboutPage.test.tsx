import { describe, expect, it, vi } from 'vitest';

import { AboutPage } from 'src/pages/AboutPage';
import { render, screen } from 'src/test-utils';

vi.mock('src/hooks', () => ({
  useAnalytics: () => ({ trackPageview: vi.fn(), trackEvent: vi.fn() }),
}));

describe('AboutPage', () => {
  it('links the palette page through the router', () => {
    render(<AboutPage />);

    expect(screen.getByRole('link', { name: 'palette page' })).toHaveAttribute('href', '/palette');
  });

  it('sends a plot request to the issue form, with no label or title prefilled', () => {
    render(<AboutPage />);

    expect(screen.getByRole('link', { name: /request_plot\(\)/ })).toHaveAttribute(
      'href',
      'https://github.com/MarkusNeusinger/anyplot/issues/new?template=request-new-plot.yml'
    );
  });
});
