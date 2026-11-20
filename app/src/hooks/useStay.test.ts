import { renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { beginStay, endStay, STAY_MS } from 'src/analytics/stay';
import { POINTER_TRAVEL_PX, pointerTravel, useStay } from 'src/hooks/useStay';

/** Puts the page in front of the visitor, or takes it away. */
function page(visible: boolean, focused: boolean): void {
  vi.spyOn(document, 'visibilityState', 'get').mockReturnValue(visible ? 'visible' : 'hidden');
  vi.spyOn(document, 'hasFocus').mockReturnValue(focused);
}

/**
 * Mounts the hook and returns its window listeners by event type: a test cannot make a trusted
 * event, so the listeners are called with stand-ins.
 */
function mountListeners(): Map<string, EventListener> {
  const listeners = new Map<string, EventListener>();
  const add = vi.spyOn(window, 'addEventListener');
  renderHook(() => useStay());
  for (const [type, listener] of add.mock.calls) listeners.set(type, listener as EventListener);
  return listeners;
}

/** A pointer move to (`x`, `y`), the visitor's own unless `isTrusted` says otherwise. */
const moveTo = (x: number, y: number, isTrusted = true): Event =>
  ({ isTrusted, clientX: x, clientY: y }) as unknown as Event;

describe('pointerTravel', () => {
  it('only records where the pointer is on its first move', () => {
    const travelled = pointerTravel();
    expect(travelled(100, 100)).toBe(false);
    expect(travelled(100, 100)).toBe(false);
  });

  it(`counts once the pointer is ${POINTER_TRAVEL_PX} px from there, in a straight line`, () => {
    const travelled = pointerTravel();
    travelled(100, 100);
    expect(travelled(102, 102)).toBe(false); // 2.8 px
    expect(travelled(100, 103.9)).toBe(false);
    expect(travelled(100 + POINTER_TRAVEL_PX, 100)).toBe(true);

    const diagonal = pointerTravel();
    diagonal(0, 0);
    expect(diagonal(3, 3)).toBe(true); // 4.2 px
  });

  it('keeps counting once the pointer has travelled, also back where it began', () => {
    const travelled = pointerTravel();
    travelled(0, 0);
    travelled(0, 10);
    expect(travelled(0, 0)).toBe(true);
  });

  it('measures from its own first position, not from another one’s', () => {
    const first = pointerTravel();
    first(0, 0);
    const second = pointerTravel();
    expect(second(50, 50)).toBe(false);
    expect(first(50, 50)).toBe(true);
  });
});

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
    const listeners = mountListeners();
    expect([...listeners.keys()]).toEqual(
      expect.arrayContaining([
        'pointerdown',
        'pointermove',
        'mousedown',
        'click',
        'touchstart',
        'keydown',
        'wheel',
      ])
    );
    // Scrolling is not asked: a page that scrolls itself says nothing.
    expect(listeners.has('scroll')).toBe(false);

    const scripted = vi.fn();
    beginStay(Date.now(), scripted);
    listeners.get('pointerdown')?.({ isTrusted: false } as Event);
    vi.advanceTimersByTime(STAY_MS);
    expect(scripted).toHaveBeenCalledExactlyOnceWith([]);

    const own = vi.fn();
    beginStay(Date.now(), own);
    listeners.get('keydown')?.({ isTrusted: true } as Event);
    vi.advanceTimersByTime(STAY_MS);
    expect(own).toHaveBeenCalledExactlyOnceWith(['key']);
  });

  it('after ten seconds without input, waits for the visitor’s own input, not a scripted one', () => {
    const listeners = mountListeners();

    const stayed = vi.fn();
    beginStay(Date.now(), stayed);
    vi.advanceTimersByTime(STAY_MS);
    expect(stayed).toHaveBeenCalledExactlyOnceWith([]);

    listeners.get('pointerdown')?.({ isTrusted: false } as Event);
    listeners.get('click')?.({ isTrusted: false } as Event);
    listeners.get('wheel')?.({ isTrusted: false } as Event);
    expect(stayed).toHaveBeenCalledTimes(1);

    // The late input is a pointer that travelled: its kind alone.
    listeners.get('pointermove')?.(moveTo(100, 100));
    listeners.get('pointermove')?.(moveTo(100, 100 + POINTER_TRAVEL_PX));
    listeners.get('pointermove')?.(moveTo(100, 120));
    listeners.get('keydown')?.({ isTrusted: true } as Event);
    expect(stayed.mock.calls).toEqual([[[]], [['move']]]);
  });

  it.each([
    ['pointerdown', 'press'],
    ['mousedown', 'press'],
    ['click', 'click'],
    ['touchstart', 'touch'],
    ['keydown', 'key'],
    ['wheel', 'wheel'],
  ])('takes a %s of the visitor’s own as input at once, of the kind %s', (type, action) => {
    const listeners = mountListeners();
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    listeners.get(type)?.({ isTrusted: true } as Event);
    vi.advanceTimersByTime(STAY_MS);
    expect(stayed).toHaveBeenCalledExactlyOnceWith([action]);
  });

  it('tells the kinds of a mouse click and a tap, each once', () => {
    const listeners = mountListeners();
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    // A mouse click is pointerdown, mousedown and click; a tap brings pointerdown, touchstart, click.
    for (const type of [
      'pointerdown',
      'mousedown',
      'click',
      'pointerdown',
      'touchstart',
      'click',
    ]) {
      listeners.get(type)?.({ isTrusted: true } as Event);
    }
    vi.advanceTimersByTime(STAY_MS);
    expect(stayed).toHaveBeenCalledExactlyOnceWith(['press', 'click', 'touch']);
  });

  it(`tells a move only once the pointer has travelled ${POINTER_TRAVEL_PX} px`, () => {
    const listeners = mountListeners();
    const short = vi.fn();
    beginStay(Date.now(), short);
    listeners.get('pointermove')?.(moveTo(640, 360));
    listeners.get('pointermove')?.(moveTo(642, 361));
    listeners.get('wheel')?.({ isTrusted: true } as Event);
    vi.advanceTimersByTime(STAY_MS);
    expect(short).toHaveBeenCalledExactlyOnceWith(['wheel']);

    // The same page: the pointer's first position stays where it was seen first.
    const far = vi.fn();
    beginStay(Date.now(), far);
    listeners.get('wheel')?.({ isTrusted: true } as Event);
    listeners.get('pointermove')?.(moveTo(640, 360 + POINTER_TRAVEL_PX));
    vi.advanceTimersByTime(STAY_MS);
    expect(far).toHaveBeenCalledExactlyOnceWith(['move', 'wheel']);
  });

  it('does not take a single pointer move as input, nor moves on one spot', () => {
    const listeners = mountListeners();
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    // A script sets the mouse once; a layout shift under a cursor that stands still.
    listeners.get('pointermove')?.(moveTo(640, 360));
    listeners.get('pointermove')?.(moveTo(640, 360));
    listeners.get('pointermove')?.(moveTo(641, 362));
    vi.advanceTimersByTime(STAY_MS);
    expect(stayed).toHaveBeenCalledExactlyOnceWith([]);
  });

  it(`takes a pointer that travelled ${POINTER_TRAVEL_PX} px as input`, () => {
    const listeners = mountListeners();
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    listeners.get('pointermove')?.(moveTo(640, 360));
    listeners.get('pointermove')?.(moveTo(640 + POINTER_TRAVEL_PX, 360));
    vi.advanceTimersByTime(STAY_MS);
    expect(stayed).toHaveBeenCalledExactlyOnceWith(['move']);
  });

  it('measures a pointer’s travel from its first move of the visitor’s own, not a scripted one', () => {
    const listeners = mountListeners();
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);

    listeners.get('pointermove')?.(moveTo(0, 0, false));
    listeners.get('pointermove')?.(moveTo(640, 360));
    listeners.get('pointermove')?.(moveTo(640, 362));
    vi.advanceTimersByTime(STAY_MS);
    expect(stayed).toHaveBeenCalledExactlyOnceWith([]);
  });

  it('brings the page’s activity up to date at an input, for a page that said nothing of it', () => {
    // An iOS in-app webview: visible, and it reports focus only after the first touch.
    page(true, false);
    const listeners = mountListeners();
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);
    vi.advanceTimersByTime(60_000);
    expect(stayed).not.toHaveBeenCalled();

    page(true, true); // no focus event
    listeners.get('touchstart')?.({ isTrusted: true } as Event);
    vi.advanceTimersByTime(STAY_MS - 1);
    expect(stayed).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(stayed).toHaveBeenCalledExactlyOnceWith(['touch']);
  });

  it('stops the clock at an input on a page that lost its focus without a blur', () => {
    const listeners = mountListeners();
    const stayed = vi.fn();
    beginStay(Date.now(), stayed);
    vi.advanceTimersByTime(4_000);

    // The mouse moves over the window, but its focus went elsewhere and no blur said so.
    page(true, false);
    listeners.get('wheel')?.({ isTrusted: true } as Event);
    vi.advanceTimersByTime(60_000);
    expect(stayed).not.toHaveBeenCalled();

    page(true, true);
    window.dispatchEvent(new Event('focus'));
    vi.advanceTimersByTime(5_999);
    expect(stayed).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(stayed).toHaveBeenCalledExactlyOnceWith(['wheel']);
  });

  it('takes its listeners away when the layout unmounts', () => {
    const remove = vi.spyOn(window, 'removeEventListener');
    const view = renderHook(() => useStay());
    view.unmount();

    expect(remove.mock.calls.map(([type]) => type)).toEqual(
      expect.arrayContaining([
        'focus',
        'blur',
        'pageshow',
        'pagehide',
        'pointerdown',
        'pointermove',
        'mousedown',
        'click',
        'keydown',
      ])
    );
  });
});
