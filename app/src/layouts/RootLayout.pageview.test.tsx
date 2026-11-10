// The layout sends every page's pageview, and three things elsewhere depend on when it does:
// the scroll reset before it, a page's own layout effects before it (the gallery's address, the
// chat's admin mute), and the next page's layout after it. These tests run the real analytics
// hook against a real browser history, on the production host, with `window.plausible` stubbed.

import { useEffect, useLayoutEffect, useState } from 'react';

import { act, render, screen } from '@testing-library/react';
import { createBrowserRouter, redirect, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { setAnalyticsMuted } from 'src/analytics/mute';
import { useAnalytics } from 'src/hooks';
import { forgetLastPageview, setAnalyticsAmbientProps } from 'src/hooks/useAnalytics';
import { useUrlSync } from 'src/hooks/useUrlSync';
import type { ActiveFilters } from 'src/types';

vi.mock('src/hooks/useLayoutContext', async () => {
  const actual = await vi.importActual<typeof import('src/hooks/useLayoutContext')>(
    'src/hooks/useLayoutContext'
  );
  return {
    ...actual,
    useTheme: () => ({
      mode: 'dark' as const,
      effective: 'dark' as const,
      isDark: true,
      setMode: vi.fn(),
      cycle: vi.fn(),
    }),
  };
});
vi.mock('src/layouts/MastheadRule', () => ({ MastheadRule: () => null }));
vi.mock('src/layouts/NavBar', () => ({ NavBar: () => null }));
vi.mock('src/layouts/Footer', () => ({ Footer: () => null }));
vi.mock('src/components/FeedbackWidget', () => ({ FeedbackWidget: () => null }));

import { RootLayout } from 'src/layouts/RootLayout';

// Vitest's jsdom environment exposes its instance, which is the one way to move the document
// to another origin: the analytics hook records on `anyplot.ai` only.
declare const jsdom: { reconfigure: (options: { url: string }) => void };

const pagePainted = vi.fn();

/** A page that says when its own passive effect ran: after every layout effect of the commit. */
function Page({ name }: { name: string }) {
  useEffect(() => {
    pagePainted(name);
  }, [name]);
  return <div>{name}-page</div>;
}

/** The chat for an admin: analytics off while it is on screen (`AgentChatPage`). */
function MutedPage() {
  useLayoutEffect(() => {
    setAnalyticsMuted(true);
    return () => setAnalyticsMuted(false);
  }, []);
  return <div>muted-page</div>;
}

/** The gallery: it restores the filters of the last visit and writes them to the address. */
function Gallery() {
  const { trackPageview } = useAnalytics();
  const [activeFilters, setActiveFilters] = useState<ActiveFilters>([
    { category: 'lib', values: ['matplotlib'] },
  ]);
  useUrlSync({ activeFilters, onTrackPageview: trackPageview });
  return (
    <button onClick={() => setActiveFilters([{ category: 'lib', values: ['seaborn'] }])}>
      filter-seaborn
    </button>
  );
}

function renderApp(url: string) {
  window.history.replaceState({}, '', url);
  const router = createBrowserRouter([
    {
      element: <RootLayout />,
      children: [
        { index: true, element: <Page name="home" /> },
        { path: 'legal', element: <Page name="legal" /> },
        { path: 'agent', element: <MutedPage /> },
        { path: 'plots', element: <Gallery /> },
        { path: 'old-address', loader: () => redirect('/legal') },
        { path: ':specId', element: <Page name="hub" /> },
        { path: ':specId/:language/:library', element: <Page name="implementation" /> },
      ],
    },
  ]);
  render(<RouterProvider router={router} />);
  return router;
}

/** The pageviews sent so far, as the paths Plausible records. */
function pageviews(): string[] {
  return vi
    .mocked(window.plausible!)
    .mock.calls.filter(([event]) => event === 'pageview')
    .map(([, options]) => (options?.url ?? '').replace('https://anyplot.ai', ''));
}

describe('RootLayout pageviews', () => {
  let scrollSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    jsdom.reconfigure({ url: 'https://anyplot.ai/' });
    window.plausible = vi.fn();
    forgetLastPageview();
    pagePainted.mockClear();
    scrollSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  });

  afterEach(() => {
    scrollSpy.mockRestore();
    setAnalyticsMuted(false);
    setAnalyticsAmbientProps({ theme: '' });
    delete window.plausible;
    jsdom.reconfigure({ url: 'http://localhost:3000/' });
  });

  it('records the page the app loads on, with the theme', () => {
    renderApp('/legal');
    expect(window.plausible).toHaveBeenCalledWith('pageview', {
      url: 'https://anyplot.ai/legal',
      props: { theme: 'dark' },
    });
    expect(pageviews()).toEqual(['/legal']);
  });

  it('records the next page at the navigation: after the scroll reset, before the page itself', async () => {
    const router = renderApp('/');
    scrollSpy.mockClear();
    pagePainted.mockClear();

    await act(() => router.navigate('/legal'));

    expect(pageviews()).toEqual(['/', '/legal']);
    const sends = vi.mocked(window.plausible!).mock.invocationCallOrder;
    const sent = sends[sends.length - 1];
    // Plausible's script takes the scroll offset at the pageview as the new page's first depth.
    expect(scrollSpy).toHaveBeenCalledWith(0, 0);
    expect(scrollSpy.mock.invocationCallOrder[0]).toBeLessThan(sent);
    // A layout effect, not a passive one: the script still holds the height of the page being
    // left, which the browser replaces at the next page's first layout.
    expect(pagePainted).toHaveBeenCalledWith('legal');
    expect(sent).toBeLessThan(pagePainted.mock.invocationCallOrder[0]);
  });

  it('records a page again when the visitor comes back to it', async () => {
    const router = renderApp('/');
    await act(() => router.navigate('/legal'));
    await act(() => router.navigate(-1));
    expect(pageviews()).toEqual(['/', '/legal', '/']);
  });

  it('records a query that names a page, and none that does not', async () => {
    const router = renderApp('/scatter-basic');
    // The hub's language scope is a page of its own.
    await act(() => router.navigate('/scatter-basic?language=python', { replace: true }));
    // An implementation page's carousel scope and interactive view are not.
    await act(() => router.navigate('/scatter-basic/python/matplotlib?language=python'));
    await act(() =>
      router.navigate('/scatter-basic/python/matplotlib?language=python&view=interactive', {
        replace: true,
      })
    );
    expect(pageviews()).toEqual([
      '/scatter-basic',
      '/scatter-basic/language/python',
      '/scatter-basic/python/matplotlib',
    ]);
  });

  it('records no page for an address that only redirects', async () => {
    const router = renderApp('/');
    await act(() => router.navigate('/old-address'));
    expect(screen.getByText('legal-page')).toBeInTheDocument();
    expect(pageviews()).toEqual(['/', '/legal']);
  });

  it('records nothing for a page that mutes analytics in its own layout effect, and the next page again', async () => {
    // The chat page serving an admin: its layout effect runs before the layout's, and its
    // cleanup before the next page's pageview.
    const router = renderApp('/');
    await act(() => router.navigate('/agent'));
    expect(screen.getByText('muted-page')).toBeInTheDocument();
    expect(pageviews()).toEqual(['/']);

    await act(() => router.navigate('/legal'));
    expect(pageviews()).toEqual(['/', '/legal']);
  });

  it('records a gallery visit that restores its filters once, as the filtered page', async () => {
    // The gallery writes the remembered filters to the address in a layout effect of its own,
    // before the layout reads the address: one pageview, not `/plots` and then the filtered one.
    const router = renderApp('/');
    await act(() => router.navigate('/plots'));
    expect(window.location.search).toBe('?lib=matplotlib');
    expect(pageviews()).toEqual(['/', '/plots/lib/matplotlib']);

    // A filter change is a page of its own, with no navigation to tell the layout.
    await act(() => screen.getByText('filter-seaborn').click());
    expect(pageviews()).toEqual(['/', '/plots/lib/matplotlib', '/plots/lib/seaborn']);
  });
});
