/**
 * The ten seconds of a visit: how long the page has been in front of the visitor since the
 * visit began, the moment that time reaches `STAY_MS`, and whether the visitor did anything.
 *
 * Google Analytics 4 calls a session engaged when it "lasts longer than 10 seconds", has a
 * key event, or has two page views, and it counts those seconds only while the page is in
 * focus. Plausible has the other two conditions in its bounce and no clock for the first, so
 * the app keeps one and reports it (`stayed_10s`, `useAnalytics.ts`). The stats page counts a
 * visitor who stayed ten seconds and did something, in either order.
 *
 * - The clock runs only while the page is active: visible and focused. A tab opened in the
 *   background, a window behind another, or a page in the back-forward cache adds nothing.
 * - It counts by timestamps, not by ticks: a browser throttles or freezes a hidden page's
 *   timers, so every change of state books the time since the last one, and the timeout only
 *   wakes the clock when the rest of the ten seconds is due.
 * - It notes whether the visitor did anything with a pointer, a finger or a key. Scrolling is
 *   not asked: a page that scrolls itself says nothing.
 * - The caller is told at most twice per stay. At the moment, with whether input came before
 *   it; if none had, once more at the first input after it. Someone who opens a page, fetches a
 *   coffee and then clicks around stayed and did something, only in the other order.
 * - It knows nothing of Plausible and of what a visit is: the caller begins a stay when a
 *   visit begins and decides what the moment is worth.
 */

/** The active time a visit needs: Google Analytics 4's threshold for an engaged session. */
export const STAY_MS = 10_000;

interface Stay {
  /** Active time before the stretch that is running now. */
  banked: number;
  /** When the running stretch began; `null` while the page is not active. */
  runningSince: number | null;
  /** Whether a trusted pointer, touch or key event came during the stay. */
  input: boolean;
  /**
   * Told with `input` when the active time reaches `STAY_MS`; told `true` once more at the
   * first input after a moment that came without one.
   */
  onStayed: (input: boolean) => void;
  timer: ReturnType<typeof setTimeout> | undefined;
}

/** The stay whose clock is running or paused; `null` once its moment came. */
let stay: Stay | null = null;

/**
 * After a moment that came without input: the stay's `onStayed`, waiting for the first input.
 * The clock is done by then, so nothing but an input, a new stay or `endStay` changes it.
 */
let awaitingInput: ((input: boolean) => void) | null = null;

/** Whether the page is in front of the visitor now: visible, and its window in focus. */
export function pageActive(): boolean {
  return (
    typeof document !== 'undefined' && document.visibilityState === 'visible' && document.hasFocus()
  );
}

function wake(): void {
  if (!stay || stay.runningSince === null) return;
  const now = Date.now();
  const active = stay.banked + (now - stay.runningSince);
  if (active < STAY_MS) {
    // A throttled timer can also fire early against a clock that was set back: wait out the rest.
    stay.timer = setTimeout(wake, STAY_MS - active);
    return;
  }
  const { onStayed, input } = stay;
  stay = null;
  if (!input) awaitingInput = onStayed;
  onStayed(input);
}

/**
 * A visit begins at `now`: forget the stay before it and start counting for this one, at
 * once if the page is active.
 */
export function beginStay(now: number, onStayed: (input: boolean) => void): void {
  endStay();
  stay = { banked: 0, runningSince: null, input: false, onStayed, timer: undefined };
  setStayActive(pageActive(), now);
}

/**
 * The page became active or stopped being it at `now`: book the stretch, or start one. Once the
 * moment came there is no clock left to run, also while the stay waits for an input.
 */
export function setStayActive(active: boolean, now: number): void {
  if (!stay) return;
  if (active && stay.runningSince === null) {
    stay.runningSince = now;
    stay.timer = setTimeout(wake, Math.max(0, STAY_MS - stay.banked));
  } else if (!active && stay.runningSince !== null) {
    stay.banked += Math.max(0, now - stay.runningSince);
    stay.runningSince = null;
    clearTimeout(stay.timer);
    stay.timer = undefined;
  }
}

/**
 * The visitor used a pointer, a finger or a key. Before the moment it is noted for the moment;
 * after a moment that came without one it is told at once, and the stay is over.
 */
export function noteStayInput(): void {
  if (stay) {
    stay.input = true;
    return;
  }
  if (awaitingInput) {
    const onStayed = awaitingInput;
    awaitingInput = null;
    onStayed(true);
  }
}

/** Forgets the stay under way: its moment will not come, nor an input after it. */
export function endStay(): void {
  if (stay) clearTimeout(stay.timer);
  stay = null;
  awaitingInput = null;
}
