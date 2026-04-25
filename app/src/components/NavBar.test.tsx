import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '../test-utils';

const trackEvent = vi.fn();
const navigate = vi.fn();

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
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

import { NavBar } from './NavBar';

describe('NavBar', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    navigate.mockClear();
  });

  it('tracks nav_click on each menu link', async () => {
    const user = userEvent.setup();
    const { container } = render(<NavBar />);

    // The labels render twice (full + short variant, CSS-hidden); we click the
    // anchor itself via href to avoid the duplicate-text ambiguity.
    await user.click(container.querySelector('a[href="/plots"]')!);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'nav_plots', target: '/plots' });

    await user.click(container.querySelector('a[href="/specs"]')!);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'nav_specs', target: '/specs' });
  });

  it('tracks nav_click on the logo', async () => {
    const user = userEvent.setup();
    const { container } = render(<NavBar />);

    await user.click(container.querySelector('a[href="/"]')!);
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'nav_logo', target: '/' });
  });

  it('tracks nav_click and navigates on the search button', async () => {
    const user = userEvent.setup();
    render(<NavBar />);

    await user.click(screen.getByLabelText('Search plots'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', {
      source: 'nav_search',
      target: '/plots?focus=search',
    });
    expect(navigate).toHaveBeenCalledWith('/plots?focus=search');
  });
});
