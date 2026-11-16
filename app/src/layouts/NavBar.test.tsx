import { beforeEach, describe, expect, it, vi } from 'vitest';

import { render, screen, styleAt, userEvent } from 'src/test-utils';

const trackEvent = vi.fn();
const navigate = vi.fn();

vi.mock('src/hooks', async () => {
  const actual = await vi.importActual<typeof import('src/hooks')>('src/hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
  };
});

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigate,
  };
});

import { NavBar } from 'src/layouts/NavBar';

describe('NavBar', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    navigate.mockClear();
  });

  it('lists eight pages, about last', () => {
    const { container } = render(<NavBar />);

    const targets = Array.from(container.querySelectorAll('ul a')).map(a => a.getAttribute('href'));
    expect(targets).toEqual([
      '/specs',
      '/plots',
      '/map',
      '/libraries',
      '/stats',
      '/palette',
      '/mcp',
      '/about',
    ]);
  });

  // Eight labels beside the logo and the search need about 750px, so phones and tablets keep the
  // two-row masthead and the single row starts at md (scratch measurements in the PR).
  it('keeps two rows below md and one from md', () => {
    const { container } = render(<NavBar />);

    const nav = container.querySelector('nav')!;
    for (const width of [320, 390, 600, 820, 899]) {
      expect(styleAt(nav, width).gridTemplateAreas).toBe('"logo search" "nav nav"');
    }
    for (const width of [900, 1440]) {
      expect(styleAt(nav, width).gridTemplateAreas).toBe('"logo nav search"');
    }
  });

  it('sends no event for the menu: the pageview that follows names the page', async () => {
    const user = userEvent.setup();
    const { container } = render(<NavBar />);

    // The labels render twice (full + short variant, CSS-hidden); we click the
    // anchor itself via href to avoid the duplicate-text ambiguity.
    await user.click(container.querySelector('a[href="/plots"]')!);
    await user.click(container.querySelector('a[href="/specs"]')!);
    await user.click(container.querySelector('a[href="/"]')!);

    expect(trackEvent).not.toHaveBeenCalled();
  });

  it('navigates on the search button, without an event', async () => {
    const user = userEvent.setup();
    render(<NavBar />);

    await user.click(screen.getByLabelText('Search plots'));
    expect(navigate).toHaveBeenCalledWith('/plots?focus=search');
    expect(trackEvent).not.toHaveBeenCalled();
  });

  it('navigates to debug on 5 clicks and stays there on 6', async () => {
    const user = userEvent.setup();
    const { container } = render(<NavBar />);

    // 5 clicks
    for (let i = 0; i < 5; i++) {
      await user.click(container.querySelector('a[href="/"]')!);
    }
    expect(navigate).toHaveBeenCalledWith('/debug');
    navigate.mockClear();

    // 1 more click (6 total) within the time window
    await user.click(container.querySelector('a[href="/"]')!);

    // should still navigate to debug, preventing default link to /
    expect(navigate).toHaveBeenCalledWith('/debug');
  });
});
