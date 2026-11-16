/**
 * The chat page inside the site's layout, for the one thing the two decide together: where the
 * site's round feedback button stands. The layout leaves it out wherever the address names a chat
 * (`RootLayout`); the page brings it back where it shows no chat there, the closed notice
 * (`LaneClosed`). So the button stands exactly once wherever no chat is open, and never beside an
 * open chat, which offers feedback of its own. Both sides are real here; only the layout's
 * masthead, navigation and footer are stubbed.
 */

import { render, screen, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { resetAgentLaneProbe } from 'src/hooks/useAgentLaneOpen';
import { RootLayout } from 'src/layouts/RootLayout';
import { AgentChatPage } from 'src/pages/AgentChatPage';
import { theme } from 'src/theme';

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    AGENT_CHAT_ENABLED: true,
    CONFIG: { ...actual.CONFIG, isDev: false, features: { agentChat: true } },
  };
});

const analytics = vi.hoisted(() => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }));
vi.mock('src/hooks/useAnalytics', async importOriginal => {
  const actual = await importOriginal<typeof import('src/hooks/useAnalytics')>();
  return { ...actual, useAnalytics: () => analytics, setAnalyticsAmbientProps: vi.fn() };
});

vi.mock('src/layouts/MastheadRule', () => ({ MastheadRule: () => <div /> }));
vi.mock('src/layouts/NavBar', () => ({ NavBar: () => <div /> }));
vi.mock('src/layouts/Footer', () => ({ Footer: () => <footer /> }));

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

let laneOpen: boolean;
/** The public lane's answer to a session's open: 200 opens it, 401 refuses it. */
let sessionStatus: number;

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
  resetAgentLaneProbe();
  laneOpen = true;
  sessionStatus = 200;
  // The layout resets the scroll on every navigation; jsdom has no scrolling.
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const method = init.method ?? 'GET';
      if (url.pathname.endsWith('/agent/lane')) {
        return laneOpen ? json(200, { open: true }) : json(404, { detail: 'not enabled' });
      }
      if (url.pathname.endsWith('/agent/sessions') && method === 'POST') {
        return sessionStatus === 200
          ? json(200, {
              session_id: 'S1',
              eligibility: { eligible: true, status: 'clean', reasons: [] },
            })
          : json(sessionStatus, { detail: 'unauthorized', ref: 'r-u' });
      }
      if (url.pathname.endsWith('/agent/status')) {
        return json(200, { libraries: ['matplotlib'], enabled: true });
      }
      if (method === 'DELETE') return new Response(null, { status: 204 });
      return json(404, { detail: 'not_found' });
    })
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function renderAt(path: string) {
  const router = createMemoryRouter(
    [{ element: <RootLayout />, children: [{ path: '/agent', element: <AgentChatPage /> }] }],
    { initialEntries: [path] }
  );
  render(
    <ThemeProvider theme={theme}>
      <RouterProvider router={router} />
    </ThemeProvider>
  );
}

const CHAT = '/agent?spec=scatter-basic&library=matplotlib&language=python';
const siteButtons = () => screen.queryAllByRole('button', { name: 'Open feedback' });

describe("the site's feedback button on /agent", () => {
  it('stands once on the closed notice at a chat address, where the layout leaves it out', async () => {
    laneOpen = false;
    renderAt(CHAT);
    await screen.findByText(/the assistant is closed right now/);
    expect(siteButtons()).toHaveLength(1);
  });

  it('stands once on the closed notice without a plot, where the layout shows it', async () => {
    laneOpen = false;
    renderAt('/agent');
    await screen.findByText(/the assistant is closed right now/);
    expect(siteButtons()).toHaveLength(1);
  });

  it('stands once on the closed notice after the public lane refused the session', async () => {
    sessionStatus = 401;
    renderAt(CHAT);
    await screen.findByText(/the assistant is closed right now/);
    expect(siteButtons()).toHaveLength(1);
  });

  it('stands once on the explainer', async () => {
    renderAt('/agent');
    await screen.findByTestId('agent-intro');
    expect(siteButtons()).toHaveLength(1);
  });

  it('is absent while a chat is open, which offers feedback of its own', async () => {
    renderAt(CHAT);
    await screen.findByLabelText('Message');
    await waitFor(() => expect(screen.getByTestId('language-chip')).toBeEnabled());
    expect(siteButtons()).toHaveLength(0);
    expect(screen.queryByText(/the assistant is closed right now/)).not.toBeInTheDocument();
  });
});
