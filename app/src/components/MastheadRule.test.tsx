import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, userEvent } from '../test-utils';

const trackEvent = vi.fn();
const cycle = vi.fn();
const setMode = vi.fn();

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent, trackPageview: vi.fn() }),
    useTheme: () => ({ mode: 'system', effective: 'light', isDark: false, setMode, cycle }),
    useLatestRelease: () => 'v1.2.3',
  };
});

import { MastheadRule } from './MastheadRule';

describe('MastheadRule', () => {
  beforeEach(() => {
    trackEvent.mockClear();
    cycle.mockClear();
    setMode.mockClear();
  });

  it('fires theme_toggle event with the next mode and cycles', async () => {
    const user = userEvent.setup();
    render(<MastheadRule />);

    // mode='system' → next is 'light'
    await user.click(screen.getByLabelText('Switch to light theme'));
    expect(trackEvent).toHaveBeenCalledWith('theme_toggle', { to: 'light' });
    expect(cycle).toHaveBeenCalled();
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
