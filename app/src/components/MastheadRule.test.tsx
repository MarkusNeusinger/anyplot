import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { render as rtlRender } from '@testing-library/react';
import type { ReactElement } from 'react';
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

function renderAt(initialEntry: string, ui: ReactElement) {
  const theme = createTheme();
  return rtlRender(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[initialEntry]}>{ui}</MemoryRouter>
    </ThemeProvider>
  );
}

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

  it('keeps the `~/anyplot.ai` root marker visible on xs for short breadcrumbs', () => {
    const { container } = renderAt('/palette', <MastheadRule />);
    const rootMarker = container.querySelector<HTMLAnchorElement>('a[href="/"]');
    expect(rootMarker).not.toBeNull();
    const styles = collectStylesFor(rootMarker!);
    // Unconditional `display:inline` — no xs hide rule.
    expect(styles).toMatch(/display:\s*inline/);
    expect(styles).not.toMatch(/display:\s*none/);
  });

  it('hides the `~/anyplot.ai` root marker on xs for long breadcrumbs', () => {
    const { container } = renderAt('/scatter-basic-annotated/python/matplotlib', <MastheadRule />);
    const rootMarker = container.querySelector<HTMLAnchorElement>('a[href="/"]');
    expect(rootMarker).not.toBeNull();
    const styles = collectStylesFor(rootMarker!);
    // MUI compiles `{ xs: 'none', sm: 'inline' }` into a media-query block
    // with display:none at the xs (min-width:0px) breakpoint.
    expect(styles).toMatch(/@media\s*\(min-width:\s*0px\)[^}]*display:\s*none/);
  });
});

function collectStylesFor(el: Element): string {
  const classes = el.className.split(/\s+/).filter(Boolean);
  return Array.from(document.querySelectorAll('style'))
    .map((s) => s.textContent ?? '')
    .filter((css) => classes.some((c) => css.includes('.' + c)))
    .join('\n');
}
