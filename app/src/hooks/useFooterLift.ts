import { useEffect, useState } from 'react';

import { FAB_ROW_CENTER_XS } from 'src/theme/floating-actions';

/**
 * CSS transform that lifts the floating bottom-right buttons so they cannot
 * drift over the footer's last-line links once the page is fully scrolled.
 * Every piece of the corner (feedback FAB, its quick stack and toast, the
 * scroll-to-top button) applies the same value, so they move as one.
 *
 * Returns `'none'` while the footer is offscreen and on viewports from MUI's
 * sm breakpoint up, where the footer never reaches the button column.
 */
export function useFooterLift(): string {
  // Number of pixels the footer currently overlaps the viewport. When the
  // footer is offscreen, lift stays at 0 and the buttons sit at their normal
  // corner position.
  const [lift, setLift] = useState(0);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const footer = document.querySelector('footer');
    if (!footer) return;
    let rafId = 0;
    const update = () => {
      // Only narrow mobile viewports actually collide — at MUI's sm breakpoint
      // and above the footer's last link sits well left of the FAB row.
      if (window.innerWidth >= 600) {
        setLift(0);
        return;
      }
      const r = footer.getBoundingClientRect();
      setLift(Math.max(0, window.innerHeight - r.top));
    };
    const schedule = () => {
      if (rafId) return;
      rafId = window.requestAnimationFrame(() => {
        rafId = 0;
        update();
      });
    };
    update();
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    // On a direct deep link to a spec page the page is initially short — data
    // and images stream in over the next ~hundred ms — so on first paint the
    // footer sits high in the layout and the buttons lift dramatically before
    // settling. Watch the body for size changes so they drop back to the
    // corner once content stabilises.
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(schedule) : null;
    ro?.observe(document.body);
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      window.removeEventListener('scroll', schedule);
      window.removeEventListener('resize', schedule);
      ro?.disconnect();
    };
  }, []);
  // Once the footer enters far enough to cross the FAB row's centre line, lift
  // the buttons so the footer's top edge runs exactly through that centre.
  return lift > FAB_ROW_CENTER_XS ? `translateY(-${lift - FAB_ROW_CENTER_XS}px)` : 'none';
}
