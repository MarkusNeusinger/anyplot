import { beforeEach, describe, expect, it, vi } from 'vitest';

import { render, screen, userEvent } from 'src/test-utils';

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
