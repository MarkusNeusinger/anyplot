import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { ThemeProvider } from '@mui/material/styles';

import { AgentChatPage } from 'src/pages/AgentChatPage';
import { theme } from 'src/theme';
import { ADMIN_HINT_KEY } from 'src/utils/adminAuth';

const flags = vi.hoisted(() => ({ agentChat: true, isDev: false }));

vi.mock('src/global-config', async importOriginal => {
  const actual = await importOriginal<typeof import('src/global-config')>();
  return {
    ...actual,
    CONFIG: {
      ...actual.CONFIG,
      get isDev() {
        return flags.isDev;
      },
      features: {
        get agentChat() {
          return flags.agentChat;
        },
      },
    },
  };
});

vi.mock('react-helmet-async', () => ({
  Helmet: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Stable identities, like the real hook (effects depend on them).
const analytics = vi.hoisted(() => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }));
vi.mock('src/hooks/useAnalytics', () => ({ useAnalytics: () => analytics }));

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

let fetchMock: ReturnType<typeof vi.fn>;

function stubFetch(openStatus = 200) {
  fetchMock = vi.fn(async (input: string, init: RequestInit = {}) => {
    const url = new URL(input);
    const method = init.method ?? 'GET';
    if (url.pathname.endsWith('/debug/agent/sessions') && method === 'POST') {
      return openStatus === 200
        ? json(200, {
            session_id: 'S1',
            eligibility: { eligible: true, status: 'clean', reasons: [] },
          })
        : json(openStatus, { status: openStatus, message: 'admin required' });
    }
    if (url.pathname.endsWith('/debug/agent/status')) {
      return json(200, { libraries: ['matplotlib', 'seaborn'], enabled: true });
    }
    if (url.pathname.endsWith('/specs/scatter-basic')) {
      return json(200, {
        title: 'Basic Scatter Plot',
        implementations: [{ library_id: 'matplotlib' }, { library_id: 'seaborn' }],
      });
    }
    if (method === 'DELETE') return new Response(null, { status: 204 });
    return json(404, { detail: 'not_found' });
  });
  vi.stubGlobal('fetch', fetchMock);
}

function LocationProbe() {
  const current = useLocation();
  return <output data-testid="location">{`${current.pathname}${current.search}`}</output>;
}

function renderAt(url: string) {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route
            path="/debug/agent"
            element={
              <>
                <AgentChatPage />
                <LocationProbe />
              </>
            }
          />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>
  );
}

const PAGE = '/debug/agent?spec=scatter-basic&library=matplotlib&language=python';
const agentCalls = () =>
  fetchMock.mock.calls.filter(([input]) => String(input).includes('/debug/agent'));

beforeEach(() => {
  flags.agentChat = true;
  flags.isDev = false;
  localStorage.clear();
  analytics.trackEvent.mockClear();
  analytics.trackPageview.mockClear();
  stubFetch();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('AgentChatPage gating', () => {
  it('is the 404 page when the build has no agent chat', () => {
    flags.agentChat = false;
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(PAGE);
    expect(screen.getByLabelText('Page not found')).toBeInTheDocument();
    expect(agentCalls()).toHaveLength(0);
  });

  it('asks for the admin sign-in without the admin hint and calls nothing', () => {
    renderAt(PAGE);
    expect(screen.getByText(/this page is for admins/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '/debug' })).toHaveAttribute('href', '/debug');
    expect(agentCalls()).toHaveLength(0);
  });

  it('opens a session for an admin and records the open, then drops the source', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    renderAt(`${PAGE}&source=plot_page`);
    expect(await screen.findByLabelText(/# your data/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '.parse()' })).toBeInTheDocument();
    expect(analytics.trackPageview).toHaveBeenCalledWith('/debug/agent');
    expect(analytics.trackEvent).toHaveBeenCalledWith('agent_open', {
      library: 'matplotlib',
      source: 'plot_page',
      spec: 'scatter-basic',
    });
    await waitFor(() => expect(screen.getByTestId('location')).toHaveTextContent(PAGE));
    expect(await screen.findByText('← Basic Scatter Plot')).toBeInTheDocument();
  });

  it('lets local development in without the hint', async () => {
    flags.isDev = true;
    renderAt(PAGE);
    expect(await screen.findByLabelText(/# your data/)).toBeInTheDocument();
    expect(analytics.trackEvent).toHaveBeenCalledWith(
      'agent_open',
      expect.objectContaining({ source: 'direct' })
    );
  });

  it('explains the missing parameters instead of calling the BFF', () => {
    flags.isDev = true;
    renderAt('/debug/agent?spec=scatter-basic&library=excel');
    expect(screen.getByText(/open this page from a plot/)).toBeInTheDocument();
    expect(agentCalls()).toHaveLength(0);
  });

  it('clears the hint and asks for the sign-in when the BFF refuses the admin', async () => {
    localStorage.setItem(ADMIN_HINT_KEY, '1');
    stubFetch(401);
    renderAt(PAGE);
    expect(await screen.findByText(/this page is for admins/)).toBeInTheDocument();
    await waitFor(() => expect(localStorage.getItem(ADMIN_HINT_KEY)).toBeNull());
  });
});
