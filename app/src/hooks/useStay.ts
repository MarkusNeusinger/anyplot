import { useEffect } from 'react';

import { noteStayInput, pageActive, setStayActive } from 'src/analytics/stay';

/**
 * What counts as the visitor doing something: a pointer, a finger or a key. Not `scroll`,
 * which a script can cause, and only events the browser marks as the user's own.
 */
const STAY_INPUTS = ['pointerdown', 'pointermove', 'touchstart', 'keydown', 'wheel'] as const;

/**
 * Tells the visit's ten-second clock (`src/analytics/stay.ts`) what the page is doing: whether
 * it is in front of the visitor, and whether the visitor did anything, before the ten seconds
 * or after them. Mounted once, in the root layout.
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
      if (event.isTrusted) noteStayInput();
    };

    document.addEventListener('visibilitychange', sync);
    window.addEventListener('focus', sync);
    window.addEventListener('blur', sync);
    window.addEventListener('pageshow', sync);
    window.addEventListener('pagehide', leave);
    for (const type of STAY_INPUTS) {
      window.addEventListener(type, input, { capture: true, passive: true });
    }
    return () => {
      document.removeEventListener('visibilitychange', sync);
      window.removeEventListener('focus', sync);
      window.removeEventListener('blur', sync);
      window.removeEventListener('pageshow', sync);
      window.removeEventListener('pagehide', leave);
      for (const type of STAY_INPUTS) {
        window.removeEventListener(type, input, { capture: true });
      }
    };
  }, []);
}
