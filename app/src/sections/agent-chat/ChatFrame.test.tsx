import { createRef } from 'react';

import { describe, expect, it, vi } from 'vitest';

import { initialAgentState } from 'src/hooks/useAgentSession';
import { StatusLine } from 'src/sections/agent-chat/ChatFrame';
import { STATUS_LINE_ID } from 'src/sections/agent-chat/steps';
import { render, screen, userEvent } from 'src/test-utils';

const state = { ...initialAgentState('matplotlib'), phase: 'ready' as const, sessionId: 'S1' };
const line = { step: 2 as const, text: 'step 2 of 2 · drawing your plot · usually 1–3 min' };

describe('StatusLine', () => {
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
      '>>> step 2 of 2 · drawing your plot · usually 1–3 min'
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
