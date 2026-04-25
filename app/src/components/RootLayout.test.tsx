import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '../test-utils';
import { Routes, Route } from 'react-router-dom';

const { setAmbient } = vi.hoisted(() => ({ setAmbient: vi.fn() }));

vi.mock('../hooks/useAnalytics', async () => {
  const actual = await vi.importActual<typeof import('../hooks/useAnalytics')>('../hooks/useAnalytics');
  return {
    ...actual,
    setAnalyticsAmbientProps: setAmbient,
  };
});

vi.mock('../hooks', async () => {
  const actual = await vi.importActual<typeof import('../hooks')>('../hooks');
  return {
    ...actual,
    useAnalytics: () => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }),
    useLatestRelease: () => null,
  };
});

vi.mock('../hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('../hooks/useLayoutContext')>('../hooks/useLayoutContext');
  return { ...actual, useTheme: () => ({ isDark: true, toggle: vi.fn() }) };
});

vi.mock('./MastheadRule', () => ({
  MastheadRule: () => <div data-testid="masthead" />,
}));
vi.mock('./NavBar', () => ({ NavBar: () => <div data-testid="nav" /> }));
vi.mock('./Footer', () => ({ Footer: () => <div data-testid="footer" /> }));

import { RootLayout } from './RootLayout';

describe('RootLayout', () => {
  beforeEach(() => {
    setAmbient.mockClear();
  });

  it('synchronously sets the theme ambient prop on render', () => {
    render(
      <Routes>
        <Route element={<RootLayout />}>
          <Route index element={<div>home</div>} />
        </Route>
      </Routes>
    );

    expect(setAmbient).toHaveBeenCalledWith({ theme: 'dark' });
  });
});
