import { afterEach, describe, expect, it, vi } from 'vitest';

import { FEEDBACK_STATUS_OPTIONS } from 'src/sections/debug/constants';
import { CopyClaudePromptButton } from 'src/sections/debug/CopyClaudePromptButton';
import { type FeedbackMessage, FeedbackSection } from 'src/sections/debug/FeedbackSection';
import { FeedbackTopList, type FeedbackTopPage } from 'src/sections/debug/FeedbackTopList';
import { act, fireEvent, render, screen, userEvent, within } from 'src/test-utils';
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
  const originalClipboardDescriptor = Object.getOwnPropertyDescriptor(navigator, 'clipboard');

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: originalLocation,
    });
    if (originalClipboardDescriptor) {
      Object.defineProperty(navigator, 'clipboard', originalClipboardDescriptor);
    } else {
      Reflect.deleteProperty(navigator, 'clipboard');
    }
    vi.restoreAllMocks();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('copies a formatted Claude Code prompt to the clipboard and resets feedback after timeout', async () => {
    vi.useFakeTimers();
    userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    const writeText = vi.spyOn(navigator.clipboard, 'writeText').mockResolvedValue(undefined);
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

  it('renders messages with reactions and contact info and forwards status and filter changes', async () => {
    const user = userEvent.setup();
    const setFeedbackStatusFilter = vi.fn();
    const handleStatusChange = vi.fn();

    const { rerender } = render(
      <FeedbackSection
        topThumbsUp={TOP_UP}
        topThumbsDown={TOP_DOWN}
        feedbackStatusFilter="open"
        setFeedbackStatusFilter={setFeedbackStatusFilter}
        feedbackMessages={INITIAL_MESSAGES}
        handleStatusChange={handleStatusChange}
      />
    );

    expect(screen.getByText('Axis labels overlap on mobile')).toBeInTheDocument();
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

    // Find fb-1's status select within its message row instead of by index
    const fb1Message = screen.getByText('Axis labels overlap on mobile');
    const fb1Row = fb1Message.parentElement?.parentElement;
    expect(fb1Row).not.toBeNull();
    const fb1StatusSelect = within(fb1Row as HTMLElement).getByRole('combobox');
    expect(fb1StatusSelect).toHaveValue('new');

    await user.selectOptions(fb1StatusSelect, 'done');
    expect(handleStatusChange).toHaveBeenCalledWith('fb-1', 'done');

    // Status filter select calls its setter
    const filterSelect = screen.getByDisplayValue('open (new + in progress)');
    await user.selectOptions(filterSelect, 'done');
    expect(setFeedbackStatusFilter).toHaveBeenCalledWith('done');

    // Empty state with specific status filter
    rerender(
      <FeedbackSection
        topThumbsUp={TOP_UP}
        topThumbsDown={TOP_DOWN}
        feedbackStatusFilter="done"
        setFeedbackStatusFilter={setFeedbackStatusFilter}
        feedbackMessages={[]}
        handleStatusChange={handleStatusChange}
      />
    );
    expect(screen.getByText('no messages with status "done"')).toBeInTheDocument();

    // Empty state with all statuses ('')
    rerender(
      <FeedbackSection
        topThumbsUp={TOP_UP}
        topThumbsDown={TOP_DOWN}
        feedbackStatusFilter=""
        setFeedbackStatusFilter={setFeedbackStatusFilter}
        feedbackMessages={[]}
        handleStatusChange={handleStatusChange}
      />
    );
    expect(screen.getByText('no messages')).toBeInTheDocument();
  });
});
