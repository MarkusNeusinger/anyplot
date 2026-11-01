import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { createMemoryRouter, Link, RouterProvider, useLocation } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { reloadWithoutWarning, useLeaveWarning } from 'src/hooks/useLeaveWarning';

const MESSAGE = 'leave?';

function LocationProbe() {
  const current = useLocation();
  return <output data-testid="location">{`${current.pathname}${current.search}`}</output>;
}

function Page({ when }: { when: boolean }) {
  useLeaveWarning(when, MESSAGE);
  return (
    <>
      <LocationProbe />
      <Link to="/elsewhere">away</Link>
      <Link to="/page?all=1" replace>
        query
      </Link>
    </>
  );
}

function renderPage(when: boolean) {
  const router = createMemoryRouter(
    [
      { path: '/page', element: <Page when={when} /> },
      { path: '*', element: <LocationProbe /> },
    ],
    { initialEntries: ['/start', '/page'] }
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
});
