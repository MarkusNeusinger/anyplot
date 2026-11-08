/**
 * The chat page's session language chip in the header: disabled while the
 * session opens and while a turn runs, wired to the language route, and synced
 * by a turn's `done`. The flows of the page are in AgentChatPage.test.tsx; this
 * file stubs only the calls the header and one turn need.
 */

import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
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

const sse = (events: [string, unknown][]) =>
  new Response(
    events.map(([event, data]) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`).join(''),
    { status: 200, headers: { 'Content-Type': 'text/event-stream' } }
  );

const PAGE = '/agent?spec=scatter-basic&library=matplotlib&language=python';

interface Put {
  body: unknown;
  headers: Record<string, string>;
}

let puts: Put[];
let releaseTurn: (() => void) | null;

/** `opened` holds the session's opening until it resolves; every turn waits for `releaseTurn`. */
function stubFetch(opened: Promise<void> = Promise.resolve()) {
  puts = [];
  releaseTurn = null;
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const method = init.method ?? 'GET';
      if (url.pathname.endsWith('/debug/agent/sessions') && method === 'POST') {
        await opened;
        return json(200, {
          session_id: 'S1',
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      if (url.pathname.endsWith('/sessions/S1/language') && method === 'PUT') {
        const body = JSON.parse(String(init.body)) as { language: string; via?: string };
        puts.push({ body, headers: init.headers as Record<string, string> });
        // The service's stored form: a known name as its code.
        const stored = body.language.toLowerCase() === 'deutsch' ? 'de' : body.language;
        return json(200, { language: stored, source: body.via === 'offer' ? 'offer' : 'chosen' });
      }
      if (url.pathname.endsWith('/sessions/S1/messages') && method === 'POST') {
        // The typed message is German: the reply stays English, and the done offers German.
        const offered = {
          language: 'en',
          source: 'default',
          offer: { language: 'de', basis: 'message' },
        };
        const response = sse([
          ['message', { text: 'The x axis shows the study hours.' }],
          ['done', { llm_calls: 2, language: offered }],
        ]);
        return new Promise<Response>(resolve => {
          releaseTurn = () => resolve(response);
        });
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

const chip = () => screen.getByTestId('language-chip');

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem(ADMIN_HINT_KEY, '1');
  analytics.trackEvent.mockClear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('AgentChatPage language chip', () => {
  it('starts at English, waits for the session, and takes a choice from the list', async () => {
    const user = userEvent.setup();
    let open!: () => void;
    stubFetch(
      new Promise<void>(resolve => {
        open = resolve;
      })
    );
    renderPage();
    // English by default, whatever the browser; disabled while the session opens.
    expect(await screen.findByTestId('language-chip')).toHaveTextContent(/^English ▾$/);
    expect(chip()).toHaveAccessibleName('Reply language: English, default. Change');
    expect(chip()).toBeDisabled();

    open();
    await waitFor(() => expect(chip()).toBeEnabled());
    await user.click(chip());
    const list = screen.getByRole('dialog', { name: 'Language of the replies and the plot' });
    await user.click(within(list).getByRole('button', { name: /German/ }));

    await waitFor(() => expect(chip()).toHaveTextContent(/^Deutsch ▾$/));
    expect(chip()).toHaveAccessibleName('Reply language: Deutsch, chosen. Change');
    expect(puts).toHaveLength(1);
    expect(puts[0].body).toEqual({ language: 'de' });
    expect(puts[0].headers['X-Anyplot-Client']).toBe('agent-chat/1');
    // A choice is the user's own: the thread stays quiet.
    expect(screen.queryByTestId('language-offer')).not.toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_language', { via: 'header' });
  });

  it('shows the server form of a typed language and refuses one outside the pattern', async () => {
    const user = userEvent.setup();
    stubFetch();
    renderPage();
    await waitFor(() => expect(chip()).toBeEnabled());

    await user.click(chip());
    const field = within(screen.getByRole('dialog')).getByRole('textbox', {
      name: 'Other language',
    });
    await user.type(field, 'a/b{Enter}');
    expect(
      within(screen.getByRole('dialog')).getByText('# letters a–z, spaces and hyphens, up to 40')
    ).toBeInTheDocument();
    expect(puts).toEqual([]);

    await user.clear(field);
    await user.type(field, 'deutsch{Enter}');
    // The server's form `de`, which the chip names by its endonym, never the typed `deutsch`.
    await waitFor(() =>
      expect(chip()).toHaveAccessibleName('Reply language: Deutsch, chosen. Change')
    );
    expect(chip()).toHaveTextContent(/^Deutsch ▾$/);
    expect(puts.map(put => put.body)).toEqual([{ language: 'deutsch' }]);
  });

  /** Sends a typed message and lets its turn end. */
  async function sendTurn(text: string) {
    const box = screen.getByLabelText('Message');
    fireEvent.change(box, { target: { value: text } });
    fireEvent.keyDown(box, { key: 'Enter' });
    // The server answers 409 run_active while a turn runs: the chip waits.
    await waitFor(() => expect(chip()).toBeDisabled());
    await waitFor(() => expect(releaseTurn).not.toBeNull());
    releaseTurn?.();
    await waitFor(() => expect(chip()).toBeEnabled());
  }

  it('holds the chip during a turn, then offers the language the turn found and keeps English', async () => {
    stubFetch();
    renderPage();
    await waitFor(() => expect(chip()).toBeEnabled());

    await sendTurn('Was zeigt die x-Achse?');

    expect(await screen.findByText('The x axis shows the study hours.')).toBeInTheDocument();
    expect(chip()).toHaveAccessibleName('Reply language: English, default. Change');
    // One short line with its button; what the button sets is behind its ⓘ.
    const line = screen.getByTestId('language-offer');
    expect(line).toHaveTextContent(/^# German detected in your message.*\.switch\(\)$/);
    fireEvent.click(within(line).getByRole('button', { name: 'About the language offer' }));
    const details = within(await screen.findByRole('dialog', { name: 'About the language offer' }));
    expect(details.getAllByRole('listitem').map(item => item.textContent)).toEqual([
      'replies and plot labels in German',
      'until then everything stays English',
      'the menu at the top changes it any time',
    ]);
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_language', { via: 'shown' });
    expect(puts).toEqual([]);
  });

  it('takes the offer with .switch(): the replies and the plot labels, the line names them', async () => {
    const user = userEvent.setup();
    stubFetch();
    renderPage();
    await waitFor(() => expect(chip()).toBeEnabled());
    await sendTurn('Was zeigt die x-Achse?');
    const line = await screen.findByTestId('language-offer');

    await user.click(
      within(line).getByRole('button', { name: 'Switch the replies and plot labels to German' })
    );

    await waitFor(() => expect(chip()).toHaveTextContent(/^Deutsch ▾$/));
    expect(chip()).toHaveAccessibleName('Reply language: Deutsch, chosen from the offer. Change');
    expect(puts.map(put => put.body)).toEqual([{ language: 'de', via: 'offer' }]);
    expect(screen.getByTestId('language-offer')).toHaveTextContent(
      /^# replies and plot labels: Deutsch$/
    );
    // The button is gone: its focus moved to the line, never to the page.
    expect(screen.getByTestId('language-offer')).toHaveFocus();
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_language', { via: 'offer' });
  });

  it('closes an open offer when the user picks at the top instead', async () => {
    const user = userEvent.setup();
    stubFetch();
    renderPage();
    await waitFor(() => expect(chip()).toBeEnabled());
    await sendTurn('Was zeigt die x-Achse?');
    expect(
      await screen.findByRole('button', { name: 'Switch the replies and plot labels to German' })
    ).toBeEnabled();

    await user.click(chip());
    const list = screen.getByRole('dialog', { name: 'Language of the replies and the plot' });
    await user.click(within(list).getByRole('button', { name: /French/ }));

    await waitFor(() => expect(chip()).toHaveTextContent(/^Français ▾$/));
    // The line stays as a record of what was found; its button goes.
    expect(screen.getByTestId('language-offer')).toHaveTextContent(
      /^# German detected in your message$/
    );
    expect(
      screen.queryByRole('button', { name: 'Switch the replies and plot labels to German' })
    ).toBeNull();
  });
});
