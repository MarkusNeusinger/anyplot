import { createRef } from 'react';

import { act } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { initialAgentState } from 'src/hooks/useAgentSession';
import { ChatFrame, StatusLine } from 'src/sections/agent-chat/ChatFrame';
import { LoadMood } from 'src/sections/agent-chat/LoadMood';
import { STATUS_LINE_ID, type StatusLineText } from 'src/sections/agent-chat/steps';
import { render, screen, userEvent } from 'src/test-utils';

const state = { ...initialAgentState('matplotlib'), phase: 'ready' as const, sessionId: 'S1' };
const line: StatusLineText = {
  step: 2,
  head: 'step 2 of 2',
  text: 'step 2 of 2 · data fits · 2 rows · 2 columns',
  run: null,
};

/** The phone width (`PHONE_QUERY`), as the page's `useMediaQuery` reads it. */
function asPhone() {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: query === '(max-width: 599.95px)',
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      onchange: null,
      dispatchEvent: vi.fn(),
    }))
  );
}

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('ChatFrame', () => {
  it('hides the tab path from screen readers and puts the mood beside it as a status of its own', () => {
    render(
      <ChatFrame header={null} mood={<LoadMood mood={{ kind: 'resting', until: '01:00' }} />}>
        <p>thread</p>
      </ChatFrame>
    );
    expect(screen.getByTestId('chat-frame-tab')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByTestId('chat-frame-tab')).toHaveTextContent(/^~\/anyplot\.ai\/agent$/);
    const mood = screen.getByRole('status');
    expect(mood).toHaveTextContent('resting until 01:00');
    expect(mood.closest('[aria-hidden]')).toBeNull();
    // The label reads as one line on the border, `~/anyplot.ai/agent · ● resting until 01:00`.
    expect(screen.getByTestId('chat-frame-label')).toHaveTextContent(
      '~/anyplot.ai/agent · ● the assistant is resting until 01:00'
    );
  });
});

describe('StatusLine', () => {
  const T0 = Date.UTC(2026, 10, 9, 12, 0, 0);
  const drawing: StatusLineText = {
    step: 2,
    head: 'step 2 of 2',
    text: 'step 2 of 2 · drawing your plot · usually 1–3 min',
    run: {
      words: 'drawing your plot',
      short: 'drawing',
      clockFrom: T0 - 42_000,
      tail: 'usually 1–3 min',
    },
  };

  it("counts the plot's time beside its words, and the plot button's description never reads it", () => {
    vi.useFakeTimers({ now: T0 });
    render(
      <>
        <StatusLine state={state} line={drawing} />
        <button type="button" aria-describedby={STATUS_LINE_ID}>
          .update_plot() →
        </button>
      </>
    );
    expect(document.getElementById(STATUS_LINE_ID)).toHaveTextContent(
      '>>> step 2 of 2 · drawing your plot · 0:42 · usually 1–3 min'
    );
    expect(screen.getByTestId('run-clock')).toHaveAttribute('aria-hidden', 'true');
    expect(screen.getByRole('button', { name: '.update_plot() →' })).toHaveAccessibleDescription(
      'step 2 of 2 · drawing your plot · usually 1–3 min'
    );
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByTestId('run-clock')).toHaveTextContent('0:43');
    // The hidden step region says the step, never the time.
    expect(screen.getByTestId('data-step-status')).not.toHaveTextContent(/\d:\d\d/);
  });

  it('reads `drawing · 0:42 · usually 1–3 min` on a phone', () => {
    asPhone();
    vi.useFakeTimers({ now: T0 });
    render(<StatusLine state={state} line={drawing} />);
    expect(document.getElementById(STATUS_LINE_ID)).toHaveTextContent(
      /^>>> step 2 of 2 · drawing · 0:42 · usually 1–3 min$/
    );
  });

  it('shows no clock where the run has none, and no usual time once it stops', () => {
    render(
      <StatusLine
        state={state}
        line={{
          ...drawing,
          text: 'step 2 of 2 · stopping…',
          run: { words: 'stopping…', short: 'stopping…', clockFrom: null, tail: '' },
        }}
      />
    );
    expect(document.getElementById(STATUS_LINE_ID)).toHaveTextContent(
      /^>>> step 2 of 2 · stopping…$/
    );
    expect(screen.queryByTestId('run-clock')).not.toBeInTheDocument();
  });

  it("holds .stop(), .start_over() and .feedback() at its end, outside the plot button's description", async () => {
    const user = userEvent.setup();
    const onStop = vi.fn();
    const onStartOver = vi.fn();
    const onFeedback = vi.fn();
    render(
      <StatusLine
        state={state}
        line={line}
        stop={{ stopping: false, onStop }}
        startOver={{ inert: false, onStartOver }}
        onFeedback={onFeedback}
      />
    );
    // The words alone carry the id the plot button names: its description reads no button names.
    expect(document.getElementById(STATUS_LINE_ID)).toHaveTextContent(
      '>>> step 2 of 2 · data fits · 2 rows · 2 columns'
    );
    expect(document.getElementById(STATUS_LINE_ID)).not.toHaveTextContent('.stop()');

    // `.stop()` is a real button that Tab reaches, first at the line's end.
    await user.tab();
    expect(screen.getByRole('button', { name: 'Stop' })).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(onStop).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole('button', { name: 'Start over' }));
    expect(onStartOver).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole('button', { name: 'Give feedback on this chat' }));
    expect(onFeedback).toHaveBeenCalledTimes(1);
  });

  it('keeps .stop() in place while the stop is on its way, and hands its focus to the box when the run ends', async () => {
    const user = userEvent.setup();
    const onStop = vi.fn();
    const box = document.createElement('textarea');
    document.body.appendChild(box);
    const focusAfter =
      createRef<HTMLElement | null>() as React.MutableRefObject<HTMLElement | null>;
    focusAfter.current = box;
    const { rerender } = render(
      <StatusLine
        state={state}
        line={line}
        stop={{ stopping: false, onStop }}
        focusAfterStop={focusAfter}
      />
    );
    const stop = screen.getByRole('button', { name: 'Stop' });
    stop.focus();
    await user.keyboard('{Enter}');

    rerender(
      <StatusLine
        state={state}
        line={line}
        stop={{ stopping: true, onStop }}
        focusAfterStop={focusAfter}
      />
    );
    expect(stop).toHaveAttribute('aria-disabled', 'true');
    expect(stop).toHaveTextContent('.stop() …');
    expect(stop).toHaveFocus();
    await user.keyboard('{Enter}');
    expect(onStop).toHaveBeenCalledTimes(1);

    // The run is over: the button goes, and the keyboard continues in the message box.
    rerender(<StatusLine state={state} line={line} stop={null} focusAfterStop={focusAfter} />);
    expect(screen.queryByRole('button', { name: 'Stop' })).not.toBeInTheDocument();
    expect(box).toHaveFocus();
    box.remove();
  });

  it('leaves the focus alone when .stop() goes without holding it, and never acts on an inert .start_over()', async () => {
    const user = userEvent.setup();
    const onStartOver = vi.fn();
    const box = document.createElement('textarea');
    document.body.appendChild(box);
    const focusAfter =
      createRef<HTMLElement | null>() as React.MutableRefObject<HTMLElement | null>;
    focusAfter.current = box;
    const { rerender } = render(
      <StatusLine
        state={state}
        line={line}
        stop={{ stopping: false, onStop: vi.fn() }}
        startOver={{ inert: true, onStartOver }}
        focusAfterStop={focusAfter}
      />
    );
    const startOver = screen.getByRole('button', { name: 'Start over' });
    expect(startOver).toHaveAttribute('aria-disabled', 'true');
    await user.click(startOver);
    expect(onStartOver).not.toHaveBeenCalled();
    expect(startOver).toHaveFocus();

    rerender(
      <StatusLine
        state={state}
        line={line}
        startOver={{ inert: false, onStartOver }}
        focusAfterStop={focusAfter}
      />
    );
    expect(startOver).toHaveFocus();
    expect(box).not.toHaveFocus();
    box.remove();
  });
});
