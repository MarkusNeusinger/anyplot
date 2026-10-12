/**
 * The chat page's session language chip in the header: disabled while the
 * session opens and while a turn runs, wired to the language route, and synced
 * by a turn's `done`. The flows of the page are in AgentChatPage.test.tsx; this
 * file stubs only the calls the header and one turn need.
 */

import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
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

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

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

const PAGE = '/debug/agent?spec=scatter-basic&library=matplotlib&language=python';

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
        const body = JSON.parse(String(init.body)) as { language: string };
        puts.push({ body, headers: init.headers as Record<string, string> });
        // The service's stored form: a known name as its code.
        const stored = body.language === 'Deutsch' ? 'de' : body.language;
        return json(200, { language: stored, source: 'chosen' });
      }
      if (url.pathname.endsWith('/sessions/S1/messages') && method === 'POST') {
        // The service's detection: the first typed message is German.
        const response = sse([
          ['message', { text: 'Die x-Achse zeigt die Lernstunden.' }],
          ['done', { llm_calls: 2, language: { language: 'de', source: 'detected' } }],
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

function renderPage() {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[PAGE]}>
        <AgentChatPage />
      </MemoryRouter>
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
  it('starts at lang: en, waits for the session, and takes a choice from the list', async () => {
    const user = userEvent.setup();
    let open!: () => void;
    stubFetch(
      new Promise<void>(resolve => {
        open = resolve;
      })
    );
    renderPage();
    // English by default, whatever the browser; disabled while the session opens.
    expect(await screen.findByTestId('language-chip')).toHaveTextContent(/^lang: en$/);
    expect(chip()).toBeDisabled();

    open();
    await waitFor(() => expect(chip()).toBeEnabled());
    await user.click(chip());
    const list = screen.getByRole('dialog', { name: 'Plot language' });
    await user.click(within(list).getByRole('button', { name: /German/ }));

    await waitFor(() => expect(chip()).toHaveTextContent(/^lang: de · chosen$/));
    expect(puts).toHaveLength(1);
    expect(puts[0].body).toEqual({ language: 'de' });
    expect(puts[0].headers['X-Anyplot-Client']).toBe('agent-chat/1');
    // A choice is the user's own: the thread stays quiet.
    expect(screen.queryByText(/detected from your message/)).not.toBeInTheDocument();
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
    await user.type(field, 'Deutsch{Enter}');
    await waitFor(() => expect(chip()).toHaveTextContent(/^lang: de · chosen$/));
    expect(puts.map(put => put.body)).toEqual([{ language: 'Deutsch' }]);
  });

  it("holds the chip during a turn and follows the turn's detected language with one notice", async () => {
    stubFetch();
    renderPage();
    await waitFor(() => expect(chip()).toBeEnabled());

    const box = screen.getByLabelText('Message');
    fireEvent.change(box, { target: { value: 'Was zeigt die x-Achse?' } });
    fireEvent.keyDown(box, { key: 'Enter' });
    // The server answers 409 run_active while a turn runs: the chip waits.
    await waitFor(() => expect(chip()).toBeDisabled());
    await waitFor(() => expect(releaseTurn).not.toBeNull());
    releaseTurn?.();

    expect(await screen.findByText('Die x-Achse zeigt die Lernstunden.')).toBeInTheDocument();
    await waitFor(() => expect(chip()).toHaveTextContent(/^lang: de · detected$/));
    expect(chip()).toBeEnabled();
    expect(
      screen.getByText(
        '# language: de · detected from your message · the lang chip in the header changes it'
      )
    ).toBeInTheDocument();
    expect(puts).toEqual([]);
  });
});
