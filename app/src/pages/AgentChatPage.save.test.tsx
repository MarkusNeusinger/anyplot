/**
 * The chat page's `.save()` in the admin menu: offered with a session, left out without
 * one, and wired to the bundle download. The flows of the page are in
 * AgentChatPage.test.tsx; this file stubs only the calls the header needs.
 */

import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { AgentChatPage } from 'src/pages/AgentChatPage';
import { theme } from 'src/theme';
import { ADMIN_HINT_KEY } from 'src/utils/adminAuth';

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    CONFIG: { ...actual.CONFIG, isDev: false, features: { agentChat: true } },
  };
});

const analytics = vi.hoisted(() => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }));
vi.mock('src/hooks/useAnalytics', () => ({ useAnalytics: () => analytics }));

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

const PAGE = '/agent?spec=scatter-basic&library=matplotlib&language=python';

let bundleSearch: string[];
/** The bundle route's answer; the default is a small bundle. */
let bundleAnswer: () => Response;

/** `opened` holds the session's opening until it resolves. */
function stubFetch(openStatus = 200, opened: Promise<void> = Promise.resolve()) {
  bundleSearch = [];
  bundleAnswer = () => json(200, { transcript: [], versions: [] });
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const method = init.method ?? 'GET';
      if (url.pathname.endsWith('/debug/agent/sessions') && method === 'POST') {
        await opened;
        return openStatus === 200
          ? json(200, {
              session_id: 'S1',
              eligibility: { eligible: true, status: 'clean', reasons: [] },
            })
          : json(openStatus, { detail: 'not_eligible', ref: 'r1' });
      }
      if (url.pathname.endsWith('/sessions/S1/bundle')) {
        bundleSearch.push(url.search);
        return bundleAnswer();
      }
      if (url.pathname.endsWith('/debug/agent/status')) {
        return json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true });
      }
      if (method === 'DELETE') return new Response(null, { status: 204 });
      return json(404, { detail: 'not_found' });
    })
  );
}

/** A data router, as in the app: the page's leave warning uses the router's blocker. */
function renderPage() {
  const router = createMemoryRouter([{ path: '/agent', element: <AgentChatPage /> }], {
    initialEntries: [PAGE],
  });
  return render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

let downloads: string[];

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem(ADMIN_HINT_KEY, '1');
  analytics.trackEvent.mockClear();
  downloads = [];
  URL.createObjectURL = vi.fn(() => 'blob:bundle');
  URL.revokeObjectURL = vi.fn();
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
    this: HTMLAnchorElement
  ) {
    downloads.push(this.download);
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

/** The admin menu's button; a test id, since the open popover hides the page from the a11y tree. */
const menuButton = () => screen.getByTestId('admin-menu');
const MENU = { name: 'Admin' } as const;

describe('AgentChatPage .save()', () => {
  it('saves the open session from the admin menu, without and with the data file', async () => {
    const user = userEvent.setup();
    stubFetch();
    renderPage();
    await screen.findByLabelText('Message');
    // Out of the header row: nothing of `.save()` shows until the menu opens.
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
    expect(screen.queryByRole('checkbox', { name: '# include data.csv' })).not.toBeInTheDocument();

    await user.click(menuButton());
    expect(menuButton()).toHaveAttribute('aria-expanded', 'true');
    const menu = screen.getByRole('dialog', MENU);
    expect(menu).toHaveTextContent('# save the session as a json file');
    // Unticked, as the feedback form's box (owner, 2026-11-06: the admin's chat is the visitors').
    expect(within(menu).getByRole('checkbox', { name: '# include data.csv' })).not.toBeChecked();
    await user.click(within(menu).getByRole('button', { name: 'Save' }));
    await waitFor(() => expect(downloads).toEqual(['anyplot-session-S1.json']));
    // The download started: the menu closes and gives the focus back to its button.
    await waitFor(() => expect(menuButton()).toHaveAttribute('aria-expanded', 'false'));
    await waitFor(() => expect(menuButton()).toHaveFocus());

    await user.click(menuButton());
    await user.click(screen.getByRole('checkbox', { name: '# include data.csv' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() =>
      expect(bundleSearch).toEqual(['?include_data=false', '?include_data=true'])
    );
    await waitFor(() =>
      expect(downloads).toEqual(['anyplot-session-S1.json', 'anyplot-session-S1.json'])
    );
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();

    // The box keeps the choice from one save to the next.
    await user.click(menuButton());
    expect(screen.getByRole('checkbox', { name: '# include data.csv' })).toBeChecked();
  });

  it('keeps the menu open with the failure line when a save fails', async () => {
    const user = userEvent.setup();
    stubFetch();
    bundleAnswer = () => json(413, { detail: 'too_large', ref: 'r-big' });
    renderPage();
    await screen.findByLabelText('Message');

    await user.click(menuButton());
    await user.click(screen.getByRole('button', { name: 'Save' }));

    const menu = screen.getByRole('dialog', MENU);
    expect(await within(menu).findByRole('alert')).toHaveTextContent(
      /^the session is over 32 MB, too large for one file$/
    );
    expect(menuButton()).toHaveAttribute('aria-expanded', 'true');
    expect(downloads).toEqual([]);
  });

  it('holds .save() back while the session opens, so the box shows what a save sends', async () => {
    const user = userEvent.setup();
    let open!: () => void;
    stubFetch(
      200,
      new Promise<void>(resolve => {
        open = resolve;
      })
    );
    renderPage();
    // The menu itself never waits; its `.save()` and the data box do until the session is open,
    // since the page renders the header anew then and a choice made before would be lost.
    expect(await screen.findByTestId('session-opening')).toBeInTheDocument();
    await user.click(menuButton());
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled();
    expect(screen.getByRole('checkbox', { name: '# include data.csv' })).toBeDisabled();
    await user.keyboard('{Escape}');

    open();
    await screen.findByLabelText('Message');
    await user.click(menuButton());
    const box = screen.getByRole('checkbox', { name: '# include data.csv' });
    expect(box).toBeEnabled();
    expect(box).not.toBeChecked();
  });

  it('offers no .save() when the session could not open', async () => {
    const user = userEvent.setup();
    stubFetch(422);
    renderPage();
    expect(await screen.findByText('not eligible')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save' })).not.toBeInTheDocument();
    await user.click(menuButton());
    expect(
      within(screen.getByRole('dialog', MENU)).queryByRole('button', { name: 'Save' })
    ).toBeNull();
  });
});
