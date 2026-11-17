import { useCallback, useEffect } from 'react';

import { type BlockerFunction, type Location, useBlocker } from 'react-router-dom';

/** Set by `reloadWithoutWarning` until the `beforeunload` of its reload has passed every guard. */
let reloadOnPurpose = false;

/**
 * Reload past the leave warning: for a reload link the user clicked on
 * purpose, such as the agent chat's after an expired session (the work is
 * gone on the server already) or after no answer (the reload is the way back).
 * `reload` is the page's own; tests pass their stand-in.
 */
export function reloadWithoutWarning(reload: () => void = () => window.location.reload()): void {
  reloadOnPurpose = true;
  // Registered after every guard, so it clears the mark once they all let this reload pass.
  window.addEventListener(
    'beforeunload',
    () => {
      reloadOnPurpose = false;
    },
    { once: true }
  );
  reload();
}

/** Whether a navigation inside the app from `current` to `next` leaves the page. */
export type LeavesPage = (current: Location, next: Location) => boolean;

/** The default: another path is another page, and a query edit on the same path stays. */
export const leavesPath: LeavesPage = (current, next) => current.pathname !== next.pathname;

/**
 * Ask before the user leaves a page whose work lives only in memory, while
 * `when` holds. Two ways out, two guards:
 *
 * - A reload, a closed tab, a typed address or a full page link:
 *   `beforeunload`, whose dialog the browser words itself.
 * - A link inside the app or the back button: the router's blocker, with the
 *   browser's own `confirm` and `message`. `leaves` says which navigation is
 *   leaving: by default only one to another path, so the page's own query edits
 *   (`setSearchParams`) pass. A page whose query names what it holds passes its
 *   own rule, so a move to other content on the same path asks too. It is read
 *   on every navigation, so it should keep its identity (a module function, or
 *   `useCallback`).
 *
 * A reload the user asked for on purpose (`reloadWithoutWarning`) passes.
 *
 * Needs a data router (`createBrowserRouter`; `createMemoryRouter` in tests).
 */
export function useLeaveWarning(
  when: boolean,
  message: string,
  leaves: LeavesPage = leavesPath
): void {
  useEffect(() => {
    if (!when) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (reloadOnPurpose) return;
      event.preventDefault();
      // Chrome and Edge before 119 ask only when `returnValue` is set.
      event.returnValue = true;
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [when]);

  const shouldBlock = useCallback<BlockerFunction>(
    ({ currentLocation, nextLocation }) => when && leaves(currentLocation, nextLocation),
    [when, leaves]
  );
  const blocker = useBlocker(shouldBlock);
  useEffect(() => {
    if (blocker.state !== 'blocked') return;
    // As React Router's own prompt does: proceed after the dialog, outside this effect.
    if (window.confirm(message)) setTimeout(blocker.proceed, 0);
    else blocker.reset();
  }, [blocker, message]);
}
