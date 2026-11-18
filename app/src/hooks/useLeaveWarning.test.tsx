import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { createMemoryRouter, Link, RouterProvider, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  type LeavesPage,
  leavesPath,
  reloadWithoutWarning,
  useLeaveWarning,
} from 'src/hooks/useLeaveWarning';

const MESSAGE = 'leave?';

/** A page whose query names what it holds (`item`): another item on the same path is leaving. */
const leavesItem: LeavesPage = (current, next) =>
  leavesPath(current, next) ||
  new URLSearchParams(current.search).get('item') !== new URLSearchParams(next.search).get('item');

function LocationProbe() {
  const current = useLocation();
  return <output data-testid="location">{`${current.pathname}${current.search}`}</output>;
}

function Page({ when, leaves }: { when: boolean; leaves?: LeavesPage }) {
  useLeaveWarning(when, MESSAGE, leaves);
  return (
    <>
      <LocationProbe />
      <Link to="/elsewhere">away</Link>
      <Link to="/page?all=1" replace>
        query
      </Link>
      <Link to="/page?item=1&all=1" replace>
        same item
      </Link>
      <Link to="/page?item=2">other item</Link>
    </>
  );
}

function renderPage(
  when: boolean,
  { leaves, entries = ['/start', '/page'] }: { leaves?: LeavesPage; entries?: string[] } = {}
) {
  const router = createMemoryRouter(
    [
      { path: '/page', element: <Page when={when} leaves={leaves} /> },
      { path: '*', element: <LocationProbe /> },
    ],
    { initialEntries: entries }
  );
  return { router, ...render(<RouterProvider router={router} />) };
}

/** Dispatch a `beforeunload` as the browser does: whether a listener cancelled it. */
function leavePage(): boolean {
  const event = new Event('beforeunload', { cancelable: true });
  window.dispatchEvent(event);
  return event.defaultPrevented;
}

const location = () => screen.getByTestId('location').textContent;

afterEach(() => {
  vi.restoreAllMocks();
});

describe('useLeaveWarning', () => {
  it('cancels beforeunload only while it holds, and lets go on unmount', () => {
    const view = renderPage(true);
    expect(leavePage()).toBe(true);
    view.unmount();
    expect(leavePage()).toBe(false);

    renderPage(false);
    expect(leavePage()).toBe(false);
  });

  it('lets a reload the user asked for pass, and asks again for the next one', () => {
    renderPage(true);
    let cancelled: boolean | null = null;
    // The browser runs the reload's `beforeunload` while the reload starts.
    reloadWithoutWarning(() => {
      cancelled = leavePage();
    });
    expect(cancelled).toBe(false);
    expect(leavePage()).toBe(true);
  });

  it('asks before a link leaves the path, and stays when the user declines', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    renderPage(true);

    fireEvent.click(screen.getByRole('link', { name: 'away' }));
    await waitFor(() => expect(confirm).toHaveBeenCalledWith(MESSAGE));
    expect(location()).toBe('/page');
  });

  it('leaves when the user agrees', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true);
    renderPage(true);

    fireEvent.click(screen.getByRole('link', { name: 'away' }));
    await waitFor(() => expect(location()).toBe('/elsewhere'));
    expect(confirm).toHaveBeenCalledTimes(1);
  });

  it('asks before the back button leaves the path', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const { router } = renderPage(true);

    void router.navigate(-1);
    await waitFor(() => expect(confirm).toHaveBeenCalledWith(MESSAGE));
    expect(location()).toBe('/page');
  });

  it("lets the page's own query edits pass without asking", async () => {
    const confirm = vi.spyOn(window, 'confirm');
    renderPage(true);

    fireEvent.click(screen.getByRole('link', { name: 'query' }));
    await waitFor(() => expect(location()).toBe('/page?all=1'));
    expect(confirm).not.toHaveBeenCalled();
  });

  it('asks nothing while it does not hold', async () => {
    const confirm = vi.spyOn(window, 'confirm');
    renderPage(false);

    fireEvent.click(screen.getByRole('link', { name: 'away' }));
    await waitFor(() => expect(location()).toBe('/elsewhere'));
    expect(confirm).not.toHaveBeenCalled();
  });

  it('lets any query edit pass by default, also one that names other content', async () => {
    const confirm = vi.spyOn(window, 'confirm');
    renderPage(true, { entries: ['/start', '/page?item=1'] });

    fireEvent.click(screen.getByRole('link', { name: 'other item' }));
    await waitFor(() => expect(location()).toBe('/page?item=2'));
    expect(confirm).not.toHaveBeenCalled();
  });

  describe("with the page's own rule", () => {
    it('asks before a link to other content on the same path, and stays when declined', async () => {
      const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
      renderPage(true, { leaves: leavesItem, entries: ['/start', '/page?item=1'] });

      fireEvent.click(screen.getByRole('link', { name: 'other item' }));
      await waitFor(() => expect(confirm).toHaveBeenCalledWith(MESSAGE));
      expect(location()).toBe('/page?item=1');
    });

    it('lets a query edit that keeps the content pass without asking', async () => {
      const confirm = vi.spyOn(window, 'confirm');
      renderPage(true, { leaves: leavesItem, entries: ['/start', '/page?item=1'] });

      fireEvent.click(screen.getByRole('link', { name: 'same item' }));
      await waitFor(() => expect(location()).toBe('/page?item=1&all=1'));
      expect(confirm).not.toHaveBeenCalled();
    });

    it('asks before the back button returns to the same path without the content', async () => {
      const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
      const { router } = renderPage(true, {
        leaves: leavesItem,
        entries: ['/page', '/page?item=1'],
      });

      void router.navigate(-1);
      await waitFor(() => expect(confirm).toHaveBeenCalledWith(MESSAGE));
      expect(location()).toBe('/page?item=1');
      expect(router.state.location.search).toBe('?item=1');

      // Agreed the second time: the blocker was reset, so the same move asks again and goes.
      confirm.mockReturnValue(true);
      void router.navigate(-1);
      await waitFor(() => expect(location()).toBe('/page'));
      expect(confirm).toHaveBeenCalledTimes(2);
    });

    it('still asks before another path', async () => {
      const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
      renderPage(true, { leaves: leavesItem, entries: ['/start', '/page?item=1'] });

      fireEvent.click(screen.getByRole('link', { name: 'away' }));
      await waitFor(() => expect(confirm).toHaveBeenCalledWith(MESSAGE));
      expect(location()).toBe('/page?item=1');
    });
  });
});
