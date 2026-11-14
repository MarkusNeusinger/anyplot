import { renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { beginStay, endStay, STAY_MS } from 'src/analytics/stay';
import { useStay } from 'src/hooks/useStay';

/** Puts the page in front of the visitor, or takes it away. */
function page(visible: boolean, focused: boolean): void {
  vi.spyOn(document, 'visibilityState', 'get').mockReturnValue(visible ? 'visible' : 'hidden');
  vi.spyOn(document, 'hasFocus').mockReturnValue(focused);
}

describe('useStay', () => {
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

  it('stops the visit’s clock when the window loses focus, and starts it when it is back', () => {
    renderHook(() => useStay());
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    vi.advanceTimersByTime(4_000);
    page(true, false);
    window.dispatchEvent(new Event('blur'));
    vi.advanceTimersByTime(60_000);
    expect(stayed).not.toHaveBeenCalled();

    page(true, true);
    window.dispatchEvent(new Event('focus'));
    vi.advanceTimersByTime(5_999);
    expect(stayed).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(stayed).toHaveBeenCalledTimes(1);
  });

  it('stops it for a hidden tab and for a page that leaves, and starts it when it is shown', () => {
    renderHook(() => useStay());
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    vi.advanceTimersByTime(3_000);
    page(false, true);
    document.dispatchEvent(new Event('visibilitychange'));
    vi.advanceTimersByTime(60_000);
    page(true, true);
    document.dispatchEvent(new Event('visibilitychange'));
    vi.advanceTimersByTime(3_000);
    // Into the back-forward cache: the page is still "visible" at that moment.
    window.dispatchEvent(new Event('pagehide'));
    vi.advanceTimersByTime(60_000);
    expect(stayed).not.toHaveBeenCalled();

    window.dispatchEvent(new Event('pageshow'));
    vi.advanceTimersByTime(3_999);
    expect(stayed).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(stayed).toHaveBeenCalledTimes(1);
  });

  it('takes a pointer, a finger or a key of the visitor’s own as input, and no scripted event', () => {
    // A test cannot make a trusted event, so the listeners are taken from the registration.
    const listeners = new Map<string, EventListener>();
    const add = vi.spyOn(window, 'addEventListener');
    renderHook(() => useStay());
    for (const [type, listener] of add.mock.calls) listeners.set(type, listener as EventListener);
    expect([...listeners.keys()]).toEqual(
      expect.arrayContaining(['pointerdown', 'pointermove', 'touchstart', 'keydown', 'wheel'])
    );
    // Scrolling is not asked: a page that scrolls itself says nothing.
    expect(listeners.has('scroll')).toBe(false);

    const scripted = vi.fn();
    beginStay(Date.now(), scripted);
    listeners.get('pointerdown')?.({ isTrusted: false } as Event);
    vi.advanceTimersByTime(STAY_MS);
    expect(scripted).toHaveBeenCalledExactlyOnceWith(false);

    const own = vi.fn();
    beginStay(Date.now(), own);
    listeners.get('keydown')?.({ isTrusted: true } as Event);
    vi.advanceTimersByTime(STAY_MS);
    expect(own).toHaveBeenCalledExactlyOnceWith(true);
  });

  it('takes its listeners away when the layout unmounts', () => {
    const remove = vi.spyOn(window, 'removeEventListener');
    const view = renderHook(() => useStay());
    view.unmount();

    expect(remove.mock.calls.map(([type]) => type)).toEqual(
      expect.arrayContaining(['focus', 'blur', 'pageshow', 'pagehide', 'pointerdown', 'keydown'])
    );
  });
});
