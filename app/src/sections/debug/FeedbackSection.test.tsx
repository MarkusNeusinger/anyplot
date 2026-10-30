import { useEffect, useState } from 'react';

import { afterEach, describe, expect, it, vi } from 'vitest';

import { DEBUG_API_URL } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';
import {
  FEEDBACK_STATUS_OPTIONS,
  type FeedbackMessageFilter,
  type FeedbackStatus,
} from 'src/sections/debug/constants';
import { CopyClaudePromptButton } from 'src/sections/debug/CopyClaudePromptButton';
import { type FeedbackMessage, FeedbackSection } from 'src/sections/debug/FeedbackSection';
import { FeedbackTopList, type FeedbackTopPage } from 'src/sections/debug/FeedbackTopList';
import { act, fireEvent, render, screen, userEvent, waitFor } from 'src/test-utils';
import { colors } from 'src/theme';

const TOP_UP: FeedbackTopPage[] = [
  { path: '/scatter-basic', count: 14, last_seen: '2026-05-20T10:00:00Z' },
  { path: '/bar-grouped', count: 5, last_seen: null },
];

const TOP_DOWN: FeedbackTopPage[] = [
  { path: '/heatmap-annotated', count: 3, last_seen: '2026-05-19T08:00:00Z' },
];

const INITIAL_MESSAGES: FeedbackMessage[] = [
  {
    id: 'fb-1',
    reaction: 'bug',
    message: 'Axis labels overlap on mobile',
    contact: 'alice@example.com',
    path: '/scatter-basic',
    status: 'new',
    created_at: '2026-05-21T09:00:00Z',
  },
  {
    id: 'fb-2',
    reaction: 'idea',
    message: 'Add dark mode export',
    contact: null,
    path: null,
    status: 'in_progress',
    created_at: '2026-05-20T09:00:00Z',
  },
  {
    id: 'fb-3',
    reaction: 'thumbs_up',
    message: null,
    contact: null,
    path: '/bar-grouped',
    status: 'done',
    created_at: '2026-05-19T09:00:00Z',
  },
  {
    id: 'fb-4',
    reaction: 'thumbs_down',
    message: 'Colors are hard to distinguish',
    contact: null,
    path: '/heatmap-annotated',
    status: 'wont_solve',
    created_at: '2026-05-18T09:00:00Z',
  },
  {
    id: 'fb-5',
    reaction: null,
    message: 'General note without reaction',
    contact: null,
    path: null,
    status: 'new',
    created_at: '2026-05-17T09:00:00Z',
  },
];

function StatefulFeedbackHarness({ token = 'test-admin-token' }: { token?: string }) {
  const [filter, setFilter] = useState<FeedbackMessageFilter>('open');
  const [messages, setMessages] = useState<FeedbackMessage[]>([]);
  const [topUp, setTopUp] = useState<FeedbackTopPage[]>([]);
  const [topDown, setTopDown] = useState<FeedbackTopPage[]>([]);

  useEffect(() => {
    const qs = filter ? `?status=${filter}&limit=50` : '?limit=50';
    Promise.all([
      fetchWithAuth(`${DEBUG_API_URL}/debug/feedback/top?reaction=thumbs_up&limit=15`, token).then(
        r => (r.ok ? (r.json() as Promise<FeedbackTopPage[]>) : [])
      ),
      fetchWithAuth(
        `${DEBUG_API_URL}/debug/feedback/top?reaction=thumbs_down&limit=15`,
        token
      ).then(r => (r.ok ? (r.json() as Promise<FeedbackTopPage[]>) : [])),
      fetchWithAuth(`${DEBUG_API_URL}/debug/feedback/messages${qs}`, token).then(r =>
        r.ok ? (r.json() as Promise<FeedbackMessage[]>) : []
      ),
    ]).then(([up, down, msgs]) => {
      setTopUp(up);
      setTopDown(down);
      setMessages(msgs);
    });
  }, [filter, token]);

  const handleStatusChange = async (id: string, newStatus: string) => {
    const prev = messages;
    setMessages(prev.map(m => (m.id === id ? { ...m, status: newStatus as FeedbackStatus } : m)));
    try {
      const r = await fetchWithAuth(`${DEBUG_API_URL}/debug/feedback/${id}`, token, {
        method: 'PATCH',
        body: JSON.stringify({ status: newStatus }),
      });
      if (!r.ok) throw new Error(`${r.status}`);
    } catch {
      setMessages(prev);
    }
  };

  return (
    <FeedbackSection
      topThumbsUp={topUp}
      topThumbsDown={topDown}
      feedbackStatusFilter={filter}
      setFeedbackStatusFilter={setFilter}
      feedbackMessages={messages}
      handleStatusChange={handleStatusChange}
    />
  );
}

describe('Feedback constants', () => {
  it('lists the four feedback triage statuses in order', () => {
    expect(FEEDBACK_STATUS_OPTIONS).toEqual(['new', 'in_progress', 'done', 'wont_solve']);
  });
});

describe('FeedbackTopList', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('shows empty state when no entries exist and renders links and counts when populated', () => {
    const { rerender } = render(
      <FeedbackTopList title="👍 thumbs up" items={[]} accent={colors.success} />
    );
    expect(screen.getByText('👍 thumbs up')).toBeInTheDocument();
    expect(screen.getByText('no entries yet')).toBeInTheDocument();

    rerender(<FeedbackTopList title="👍 thumbs up" items={TOP_UP} accent={colors.success} />);
    expect(screen.queryByText('no entries yet')).not.toBeInTheDocument();
    expect(screen.getByText('14')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '/scatter-basic' })).toHaveAttribute(
      'href',
      '/scatter-basic'
    );
    expect(screen.getByRole('link', { name: '/bar-grouped' })).toHaveAttribute(
      'href',
      '/bar-grouped'
    );
  });
});

describe('CopyClaudePromptButton', () => {
  const originalLocation = window.location;
  const originalClipboard = navigator.clipboard;

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: originalClipboard,
    });
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('copies a formatted Claude Code prompt to the clipboard and resets feedback after timeout', async () => {
    vi.useFakeTimers();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText },
    });
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: {
        ...originalLocation,
        origin: 'https://anyplot.ai',
        href: 'https://anyplot.ai/debug',
      },
    });

    render(
      <CopyClaudePromptButton
        message="Legend overlaps data points"
        path="/scatter-basic"
        reaction="bug"
      />
    );

    const button = screen.getByRole('button', { name: 'Copy Claude Code prompt' });
    fireEvent.mouseOver(button);
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(screen.getByRole('tooltip')).toHaveTextContent('copy prompt for Claude Code');

    await act(async () => {
      fireEvent.click(button);
    });

    expect(writeText).toHaveBeenCalledTimes(1);
    expect(writeText.mock.calls[0][0]).toContain('https://anyplot.ai/scatter-basic');
    expect(writeText.mock.calls[0][0]).toContain('bug report');
    expect(writeText.mock.calls[0][0]).toContain('> Legend overlaps data points');

    // Tooltip text updates to the copied confirmation until the 2000ms timer expires
    expect(screen.getByRole('tooltip')).toHaveTextContent('copied — paste into Claude Code');

    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.getByRole('tooltip')).toHaveTextContent('copy prompt for Claude Code');
  });
});

describe('FeedbackSection', () => {
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('renders messages with reactions, contact info, status filter changes, and status updates via fetchWithAuth', async () => {
    const user = userEvent.setup();
    let patchShouldFail = false;

    const fetchMock = vi.fn((url: string, init?: RequestInit) => {
      if (url.includes('/debug/feedback/top?reaction=thumbs_up')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(TOP_UP) });
      }
      if (url.includes('/debug/feedback/top?reaction=thumbs_down')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(TOP_DOWN) });
      }
      if (url.includes('/debug/feedback/messages')) {
        const parsed = new URL(url, 'https://api.anyplot.ai');
        const status = parsed.searchParams.get('status');
        if (status === 'open') {
          return Promise.resolve({
            ok: true,
            json: () => Promise.resolve(INITIAL_MESSAGES),
          });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
      }
      if (init?.method === 'PATCH') {
        if (patchShouldFail) {
          return Promise.resolve({ ok: false, status: 500 });
        }
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'ok' }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
    });
    vi.stubGlobal('fetch', fetchMock);

    render(<StatefulFeedbackHarness />);

    // Wait for initial messages to render
    expect(await screen.findByText('Axis labels overlap on mobile')).toBeInTheDocument();
    expect(screen.getByText('contact: alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('Add dark mode export')).toBeInTheDocument();
    expect(screen.getByText('Colors are hard to distinguish')).toBeInTheDocument();
    expect(screen.getByText('General note without reaction')).toBeInTheDocument();

    // Reaction glyphs rendered
    expect(screen.getByText('🪲')).toBeInTheDocument();
    expect(screen.getByText('💡')).toBeInTheDocument();
    expect(screen.getByText('👍')).toBeInTheDocument();
    expect(screen.getByText('👎')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument();

    // Change the status of the first message (fb-1) from 'new' to 'done'
    const selects = screen.getAllByRole('combobox');
    // selects[0] is the section filter; selects[1] is fb-1's status select
    const firstMsgSelect = selects[1];
    expect(firstMsgSelect).toHaveValue('new');

    await user.selectOptions(firstMsgSelect, 'done');
    expect(firstMsgSelect).toHaveValue('done');

    const patchCall = fetchMock.mock.calls.find(call => call[1]?.method === 'PATCH');
    expect(patchCall?.[0]).toContain('/debug/feedback/fb-1');
    expect(patchCall?.[1]?.body).toBe(JSON.stringify({ status: 'done' }));

    // Failed PATCH reverts optimistic status update
    patchShouldFail = true;
    await user.selectOptions(firstMsgSelect, 'wont_solve');
    await waitFor(() => {
      expect(firstMsgSelect).toHaveValue('done');
    });

    // Filtering by a status with no messages shows the status-specific empty message
    const filterSelect = selects[0];
    await user.selectOptions(filterSelect, 'done');
    expect(await screen.findByText('no messages with status "done"')).toBeInTheDocument();

    // Filtering by all statuses ('') with no messages shows generic empty message
    await user.selectOptions(filterSelect, '');
    expect(await screen.findByText('no messages')).toBeInTheDocument();
  });
});
