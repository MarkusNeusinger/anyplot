import { useEffect } from 'react';

import { noteStayInput, pageActive, setStayActive } from 'src/analytics/stay';

/**
 * What counts as the visitor doing something, at once: a pointer, a finger or a key. Not
 * `scroll`, which a script can cause, and only events the browser marks as the user's own.
 * `click` and `mousedown` are here for what arrives without pointer events: a screen reader
 * activating from its virtual cursor, VoiceOver's double-tap, voice control. A script's
 * `element.click()` is not the user's own, so automation gains nothing from them. A pointer move
 * counts too, but only once the pointer has travelled (`pointerTravel`).
 */
const STAY_INPUTS = [
  'pointerdown',
  'mousedown',
  'click',
  'touchstart',
  'keydown',
  'wheel',
] as const;

/** How far a pointer travels, in CSS pixels, before a move of it counts as input. */
export const POINTER_TRAVEL_PX = 4;

/**
 * Whether the pointer has travelled `POINTER_TRAVEL_PX` from where it was first seen, in a
 * straight line; once it has, every move counts. The first move only records the position. A
 * script that sets the mouse once, and a cursor that stands still while the layout shifts under
 * it, give a single move or moves on one spot; a person's mouse always travels further, so the
 * rule costs no person.
 */
export function pointerTravel(): (x: number, y: number) => boolean {
  let origin: { x: number; y: number } | null = null;
  let travelled = false;
  return (x, y) => {
    if (travelled) return true;
    if (origin === null) {
      origin = { x, y };
      return false;
    }
    travelled = Math.hypot(x - origin.x, y - origin.y) >= POINTER_TRAVEL_PX;
    return travelled;
  };
}

/**
 * Tells the visit's ten-second clock (`src/analytics/stay.ts`) what the page is doing: whether
 * it is in front of the visitor, and whether the visitor did anything, before the ten seconds
 * or after them. Mounted once, in the root layout, so the pointer's first position is the first
 * one seen on the page, whatever route or visit follows.
 *
 * The clock itself starts with the visit, in `useAnalytics`; this hook only reports changes.
 * `pagehide` stops it whatever the visibility says: a page that goes into the back-forward
 * cache is still "visible" at that moment, and `pageshow` starts it again when it comes back.
 */
export function useStay(): void {
  useEffect(() => {
    const sync = () => setStayActive(pageActive(), Date.now());
    const leave = () => setStayActive(false, Date.now());
    const input = (event: Event) => {
      if (!event.isTrusted) return;
      // The page's activity first: a page can gain or lose focus without an event that says so,
      // and an iOS in-app webview reports focus only after the first touch.
      sync();
      noteStayInput();
    };
    const travelled = pointerTravel();
    const move = (event: PointerEvent) => {
      if (event.isTrusted && travelled(event.clientX, event.clientY)) input(event);
    };

    document.addEventListener('visibilitychange', sync);
    window.addEventListener('focus', sync);
    window.addEventListener('blur', sync);
    window.addEventListener('pageshow', sync);
    window.addEventListener('pagehide', leave);
    for (const type of STAY_INPUTS) {
      window.addEventListener(type, input, { capture: true, passive: true });
    }
    window.addEventListener('pointermove', move, { capture: true, passive: true });
    return () => {
      document.removeEventListener('visibilitychange', sync);
      window.removeEventListener('focus', sync);
      window.removeEventListener('blur', sync);
      window.removeEventListener('pageshow', sync);
      window.removeEventListener('pagehide', leave);
      for (const type of STAY_INPUTS) {
        window.removeEventListener(type, input, { capture: true });
      }
      window.removeEventListener('pointermove', move, { capture: true });
    };
  }, []);
}
