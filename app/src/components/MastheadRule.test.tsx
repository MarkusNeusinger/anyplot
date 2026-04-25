import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '../test-utils';

const trackEvent = vi.fn();
const toggle = vi.fn();

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
    useTheme: () => ({ isDark: false, toggle }),
    useLatestRelease: () => 'v1.2.3',
  };
});

import { MastheadRule } from './MastheadRule';

describe('MastheadRule', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    toggle.mockClear();
  });

  it('fires theme_toggle event before invoking the underlying toggle', async () => {
    const user = userEvent.setup();
    render(<MastheadRule />);

    await user.click(screen.getByLabelText('Switch to dark theme'));
    expect(trackEvent).toHaveBeenCalledWith('theme_toggle', { to: 'dark' });
    expect(toggle).toHaveBeenCalled();
  });

  it('tracks nav_click on the masthead logo, branch, and release links', async () => {
    const user = userEvent.setup();
    render(<MastheadRule />);

    await user.click(screen.getByText('~/anyplot.ai'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'masthead_logo', target: '/' });

    await user.click(screen.getByText('main'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'masthead_branch', target: 'github_main' });

    await user.click(screen.getByText('v1.2.3'));
    expect(trackEvent).toHaveBeenCalledWith('nav_click', { source: 'masthead_release', target: 'v1.2.3' });
  });
});
