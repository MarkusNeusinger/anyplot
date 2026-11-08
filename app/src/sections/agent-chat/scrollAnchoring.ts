/**
 * The page's scroll anchoring (`overflow-anchor` on the root), held off by whoever needs it off:
 * a running plot's progress timeline, whose grid grows only below what it shows
 * (`ProgressTimeline.tsx`), and the thread while it holds a reply still under a card that lands
 * above it (`HoldReadingPosition.tsx`). The holds count, so one never turns the anchoring back
 * on under another, and the page's own value comes back with the last.
 */

let holds = 0;
let before = '';

/** Turns the page's scroll anchoring off until the returned release is called (once). */
export function holdScrollAnchoring(): () => void {
  const root = document.documentElement;
  if (holds === 0) {
    before = root.style.overflowAnchor;
    root.style.overflowAnchor = 'none';
  }
  holds += 1;
  let released = false;
  return () => {
    if (released) return;
    released = true;
    holds -= 1;
    if (holds === 0) root.style.overflowAnchor = before;
  };
}
