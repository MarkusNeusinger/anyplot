import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  beginStay,
  endStay,
  noteStayInput,
  pageActive,
  setStayActive,
  STAY_MS,
} from 'src/analytics/stay';

/** Puts the page in front of the visitor, or takes it away. */
function page(visible: boolean, focused: boolean): void {
  vi.spyOn(document, 'visibilityState', 'get').mockReturnValue(visible ? 'visible' : 'hidden');
  vi.spyOn(document, 'hasFocus').mockReturnValue(focused);
}

describe('the ten seconds of a visit', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-14T10:00:00Z'));
    page(true, true);
  });

  afterEach(() => {
    endStay();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('is Google Analytics 4’s threshold for an engaged session', () => {
    expect(STAY_MS).toBe(10_000);
  });

  it('calls a page active only while it is visible and in focus', () => {
    expect(pageActive()).toBe(true);
    page(true, false);
    expect(pageActive()).toBe(false);
    page(false, true);
    expect(pageActive()).toBe(false);
  });

  it('comes once, after ten seconds in front of the visitor, and not again without input', () => {
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    vi.advanceTimersByTime(STAY_MS - 1);
    expect(stayed).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(stayed).toHaveBeenCalledExactlyOnceWith(false);

    vi.advanceTimersByTime(60_000);
    expect(stayed).toHaveBeenCalledTimes(1);
  });

  it('does not count a tab opened in the background until it is looked at', () => {
    page(false, false);
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    vi.advanceTimersByTime(5 * 60_000);
    expect(stayed).not.toHaveBeenCalled();

    page(true, true);
    setStayActive(true, Date.now());
    vi.advanceTimersByTime(STAY_MS);
    expect(stayed).toHaveBeenCalledTimes(1);
  });

  it('adds up the time in front of the visitor across a pause', () => {
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    vi.advanceTimersByTime(4_000);
    setStayActive(false, Date.now()); // another tab
    vi.advanceTimersByTime(60_000);
    setStayActive(true, Date.now());
    vi.advanceTimersByTime(5_999);
    expect(stayed).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(stayed).toHaveBeenCalledTimes(1);
  });

  it('counts by the clock, not by ticks: a timer that fires early waits out the rest', () => {
    const start = Date.now();
    const stayed = vi.fn();
    beginStay(start, stayed);

    // The timer is about to fire, and the clock shows only six seconds.
    vi.advanceTimersByTime(STAY_MS - 1);
    vi.setSystemTime(start + 6_000);
    vi.advanceTimersByTime(1);
    expect(stayed).not.toHaveBeenCalled();

    vi.advanceTimersByTime(3_998);
    expect(stayed).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(stayed).toHaveBeenCalledTimes(1);
  });

  it('says whether the visitor used a pointer, a finger or a key before the moment came', () => {
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);
    vi.advanceTimersByTime(3_000);
    noteStayInput();
    vi.advanceTimersByTime(7_000);

    expect(stayed).toHaveBeenCalledExactlyOnceWith(true);

    // The stay is over: more input says nothing more.
    noteStayInput();
    vi.advanceTimersByTime(60_000);
    noteStayInput();
    expect(stayed).toHaveBeenCalledTimes(1);
  });

  it('tells the first input after a moment that came without one, and nothing after it', () => {
    // Someone opens the page, fetches a coffee, then clicks around.
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);
    vi.advanceTimersByTime(STAY_MS);
    expect(stayed).toHaveBeenCalledExactlyOnceWith(false);

    vi.advanceTimersByTime(5 * 60_000);
    expect(stayed).toHaveBeenCalledTimes(1);
    noteStayInput();
    expect(stayed.mock.calls).toEqual([[false], [true]]);

    noteStayInput();
    vi.advanceTimersByTime(60_000);
    noteStayInput();
    expect(stayed).toHaveBeenCalledTimes(2);
  });

  it('runs no second clock while it waits for an input', () => {
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);
    vi.advanceTimersByTime(STAY_MS);

    setStayActive(false, Date.now());
    vi.advanceTimersByTime(60_000);
    setStayActive(true, Date.now());
    vi.advanceTimersByTime(60_000);
    expect(stayed).toHaveBeenCalledExactlyOnceWith(false);

    // Still waiting: the input is told all the same.
    noteStayInput();
    expect(stayed.mock.calls).toEqual([[false], [true]]);
  });

  it('starts over with a new visit, and forgets the input of the one before', () => {
    const first = vi.fn();
    const second = vi.fn();
    beginStay(Date.now(), first);
    noteStayInput();
    vi.advanceTimersByTime(9_000);

    beginStay(Date.now(), second);
    vi.advanceTimersByTime(9_999);
    expect(second).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);

    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledExactlyOnceWith(false);
  });

  it('starts over with a new visit, and forgets that the one before waited for an input', () => {
    const first = vi.fn();
    const second = vi.fn();
    beginStay(Date.now(), first);
    vi.advanceTimersByTime(STAY_MS);
    expect(first).toHaveBeenCalledExactlyOnceWith(false);

    beginStay(Date.now(), second);
    vi.advanceTimersByTime(2_000);
    noteStayInput();
    // The input belongs to the new stay, which has not stayed yet.
    expect(first).toHaveBeenCalledTimes(1);
    expect(second).not.toHaveBeenCalled();

    vi.advanceTimersByTime(8_000);
    expect(second).toHaveBeenCalledExactlyOnceWith(true);
    expect(first).toHaveBeenCalledTimes(1);
  });

  it('never comes for a stay that was ended, and ignores what follows it', () => {
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);
    vi.advanceTimersByTime(9_000);
    endStay();

    setStayActive(true, Date.now());
    noteStayInput();
    vi.advanceTimersByTime(60_000);
    expect(stayed).not.toHaveBeenCalled();
  });

  it('tells no input after a stay that was ended while it waited for one', () => {
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);
    vi.advanceTimersByTime(STAY_MS);
    endStay();

    noteStayInput();
    expect(stayed).toHaveBeenCalledExactlyOnceWith(false);
  });
});
