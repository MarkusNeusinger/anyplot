import { act } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { elapsedClock, queuePlace } from 'src/sections/agent-chat/messages';
import { RunClock } from 'src/sections/agent-chat/RunClock';
import type { WorkingLineText } from 'src/sections/agent-chat/steps';
import { WorkingLine } from 'src/sections/agent-chat/WorkingLine';
import { render, screen } from 'src/test-utils';

const T0 = Date.UTC(2026, 10, 9, 12, 0, 0);
const drawing: WorkingLineText = {
  kind: 'drawing',
  text: 'drawing your plot · second try',
  short: 'drawing · second try',
  clockFrom: T0 - 42_000,
};

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('elapsedClock and queuePlace', () => {
  it('reads an elapsed time as M:SS, past an hour as H:MM:SS, never below zero', () => {
    expect(elapsedClock(0)).toBe('0:00');
    expect(elapsedClock(42_000)).toBe('0:42');
    expect(elapsedClock(72_999)).toBe('1:12');
    expect(elapsedClock(4.5 * 60_000)).toBe('4:30');
    expect(elapsedClock(3_723_000)).toBe('1:02:03');
    expect(elapsedClock(-5_000)).toBe('0:00');
  });

  it('names a place in the queue: next at its head, then ordinals', () => {
    expect([1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 101].map(queuePlace)).toEqual([
      'next',
      '2nd',
      '3rd',
      '4th',
      '11th',
      '12th',
      '13th',
      '21st',
      '22nd',
      '23rd',
      '101st',
    ]);
  });
});

describe('RunClock', () => {
  it('ticks once a second, hidden from screen readers', () => {
    vi.useFakeTimers({ now: T0 });
    render(<RunClock from={T0 - 42_000} />);
    const clock = screen.getByTestId('run-clock');
    expect(clock).toHaveTextContent(/^0:42$/);
    expect(clock).toHaveAttribute('aria-hidden', 'true');
    act(() => vi.advanceTimersByTime(1000));
    expect(clock).toHaveTextContent(/^0:43$/);
    act(() => vi.advanceTimersByTime(17_000));
    expect(clock).toHaveTextContent(/^1:00$/);
  });

  it('reads the right time after a throttled gap: it counts the time, never its ticks', () => {
    vi.useFakeTimers({ now: T0 });
    render(<RunClock from={T0} />);
    // A background tab ran no timer for a minute; the next tick shows the minute.
    vi.setSystemTime(T0 + 60_000);
    expect(screen.getByTestId('run-clock')).toHaveTextContent(/^0:00$/);
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByTestId('run-clock')).toHaveTextContent(/^1:01$/);
  });

  it('turns over on the whole second, so two clocks of one run never disagree', () => {
    // The working line's clock and the status line's mount a moment apart.
    const from = T0 - 42_300;
    vi.useFakeTimers({ now: T0 });
    render(<RunClock from={from} />);
    act(() => vi.advanceTimersByTime(400));
    render(<RunClock from={from} />);
    const [first, second] = screen.getAllByTestId('run-clock');
    expect(first).toHaveTextContent(/^0:42$/);
    expect(second).toHaveTextContent(/^0:42$/);
    act(() => vi.advanceTimersByTime(300));
    expect(first).toHaveTextContent(/^0:43$/);
    expect(second).toHaveTextContent(/^0:43$/);
    act(() => vi.advanceTimersByTime(999));
    expect(first).toHaveTextContent(/^0:43$/);
    act(() => vi.advanceTimersByTime(1));
    expect([first.textContent, second.textContent]).toEqual(['0:44', '0:44']);
  });

  it('stops ticking when it goes', () => {
    vi.useFakeTimers({ now: T0 });
    const { unmount } = render(<RunClock from={T0} />);
    expect(vi.getTimerCount()).toBe(1);
    unmount();
    expect(vi.getTimerCount()).toBe(0);
  });
});

describe('WorkingLine', () => {
  it('stands beside the site loader with its words and clock, the clock out of the read text', () => {
    vi.useFakeTimers({ now: T0 });
    render(<WorkingLine line={drawing} drawing />);
    const line = screen.getByTestId('working-line');
    expect(line).toHaveTextContent(/^drawing your plot · second try · 0:42$/);
    const loader = screen.getByTestId('loader-spinner');
    expect(loader).toHaveAttribute('aria-hidden', 'true');
    expect(loader).toHaveAttribute('data-size', 'inline');
    expect(screen.getByTestId('run-clock')).toHaveAttribute('aria-hidden', 'true');
    // What a screen reader gets of the line: the words alone.
    const read = line.cloneNode(true) as HTMLElement;
    for (const hidden of read.querySelectorAll('[aria-hidden="true"]')) hidden.remove();
    expect(read.textContent).toBe('drawing your plot · second try');
  });

  it('reads the short form on a phone', () => {
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
    vi.useFakeTimers({ now: T0 });
    render(
      <WorkingLine line={{ ...drawing, text: 'drawing your plot', short: 'drawing' }} drawing />
    );
    expect(screen.getByTestId('working-line')).toHaveTextContent(/^drawing · 0:42$/);
  });

  it('shows no clock for a line without one', () => {
    render(
      <WorkingLine
        line={{
          kind: 'waiting',
          text: 'waiting · you are 3rd',
          short: 'waiting · you are 3rd',
          clockFrom: null,
        }}
        drawing
      />
    );
    expect(screen.getByTestId('working-line')).toHaveTextContent(/^waiting · you are 3rd$/);
    expect(screen.queryByTestId('run-clock')).not.toBeInTheDocument();
  });

  it("turns the page's scroll anchoring off while a plot is drawn, and back after it", () => {
    // A browser holding a node below in place scrolled the page under the run's progress.
    const root = document.documentElement;
    root.style.overflowAnchor = 'auto';
    const { rerender, unmount } = render(<WorkingLine line={drawing} drawing />);
    expect(root.style.overflowAnchor).toBe('none');
    // Below the run's card, while the reply is written, the page anchors again.
    rerender(
      <WorkingLine
        line={{
          kind: 'writing',
          text: 'writing the reply',
          short: 'writing the reply',
          clockFrom: null,
        }}
        drawing={false}
      />
    );
    expect(root.style.overflowAnchor).toBe('auto');
    rerender(<WorkingLine line={drawing} drawing />);
    expect(root.style.overflowAnchor).toBe('none');
    unmount();
    expect(root.style.overflowAnchor).toBe('auto');
    root.style.overflowAnchor = '';
  });
});
