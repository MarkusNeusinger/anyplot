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
 * - When it wakes, it asks the page again before the moment comes: a page can lose focus or be
 *   hidden without an event that says so. If the page is not active, the stretch is booked and
 *   the clock stops until the next change of activity. Since nothing says when the page left,
 *   the booked time can already reach ten seconds, and the moment then comes as soon as the page
 *   is active again, never while it is not.
 * - It notes whether the visitor did anything with a pointer, a finger or a key, and which kinds
 *   of input (`STAY_ACTIONS`), so a kind that one day fires by itself can be seen. Scrolling is
 *   not asked: a page that scrolls itself says nothing.
 * - The caller is told at most twice per stay. At the moment, with every kind of input that came
 *   before it, or none; if none had, once more at the first input after it, with that input's
 *   kind. Someone who opens a page, fetches a coffee and then clicks around stayed and did
 *   something, only in the other order.
 * - It knows nothing of Plausible and of what a visit is: the caller begins a stay when a
 *   visit begins and decides what the moment is worth.
 */

/** The active time a visit needs: Google Analytics 4's threshold for an engaged session. */
export const STAY_MS = 10_000;

/**
 * The kinds of input, in the order they are told: `move` a pointer that travelled, `press` a
 * pointer or mouse button pressed, `click` a click, `touch` a finger, `key` a key, `wheel` the
 * wheel. A closed list, so a kind that starts to fire by itself can be named and left out.
 */
export const STAY_ACTIONS = ['move', 'press', 'click', 'touch', 'key', 'wheel'] as const;

export type StayAction = (typeof STAY_ACTIONS)[number];

/**
 * Told the kinds of input, each once and in the order of `STAY_ACTIONS`: when the active time
 * reaches `STAY_MS`, every kind that came before it, or none; once more after a moment that came
 * with none, the one kind of the first input after it.
 */
export type OnStayed = (actions: readonly StayAction[]) => void;

interface Stay {
  /** Active time before the stretch that is running now. */
  banked: number;
  /** When the running stretch began; `null` while the page is not active. */
  runningSince: number | null;
  /** The kinds of trusted input that came during the stay; empty while none did. */
  actions: Set<StayAction>;
  onStayed: OnStayed;
  timer: ReturnType<typeof setTimeout> | undefined;
}

/** The stay whose clock is running or paused; `null` once its moment came. */
let stay: Stay | null = null;

/**
 * After a moment that came without input: the stay's `onStayed`, waiting for the first input.
 * The clock is done by then, so nothing but an input, a new stay or `endStay` changes it.
 */
let awaitingInput: OnStayed | null = null;

/** Whether the page is in front of the visitor now: visible, and its window in focus. */
export function pageActive(): boolean {
  return (
    typeof document !== 'undefined' && document.visibilityState === 'visible' && document.hasFocus()
  );
}

function wake(): void {
  if (!stay || stay.runningSince === null) return;
  const now = Date.now();
  if (!pageActive()) {
    // The page stopped being active without an event that said so: book the stretch and wait for
    // the next change of activity, so the moment never comes while nobody has the page in front.
    setStayActive(false, now);
    return;
  }
  const active = stay.banked + (now - stay.runningSince);
  if (active < STAY_MS) {
    // A throttled timer can also fire early against a clock that was set back: wait out the rest.
    stay.timer = setTimeout(wake, STAY_MS - active);
    return;
  }
  const { onStayed, actions } = stay;
  stay = null;
  if (actions.size === 0) awaitingInput = onStayed;
  onStayed(STAY_ACTIONS.filter(action => actions.has(action)));
}

/**
 * A visit begins at `now`: forget the stay before it and start counting for this one, at
 * once if the page is active.
 */
export function beginStay(now: number, onStayed: OnStayed): void {
  endStay();
  stay = { banked: 0, runningSince: null, actions: new Set(), onStayed, timer: undefined };
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
 * The visitor used a pointer, a finger or a key, of the kind `action`. Before the moment it is
 * noted for the moment; after a moment that came without one it is told at once, with its kind
 * alone, and the stay is over.
 */
export function noteStayInput(action: StayAction): void {
  if (stay) {
    stay.actions.add(action);
    return;
  }
  if (awaitingInput) {
    const onStayed = awaitingInput;
    awaitingInput = null;
    onStayed([action]);
  }
}

/** Forgets the stay under way: its moment will not come, nor an input after it. */
export function endStay(): void {
  if (stay) clearTimeout(stay.timer);
  stay = null;
  awaitingInput = null;
}
