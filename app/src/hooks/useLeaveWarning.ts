import { useCallback, useEffect } from 'react';

import { type BlockerFunction, useBlocker } from 'react-router-dom';

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

/**
 * Ask before the user leaves a page whose work lives only in memory, while
 * `when` holds. Two ways out, two guards:
 *
 * - A reload, a closed tab, a typed address or a full page link:
 *   `beforeunload`, whose dialog the browser words itself.
 * - A link inside the app or the back button: the router's blocker, with the
 *   browser's own `confirm` and `message`. Only a navigation to another path
 *   asks; the page's own query edits (`setSearchParams`) stay on the path and pass.
 *
 * A reload the user asked for on purpose (`reloadWithoutWarning`) passes.
 *
 * Needs a data router (`createBrowserRouter`; `createMemoryRouter` in tests).
 */
export function useLeaveWarning(when: boolean, message: string): void {
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
    ({ currentLocation, nextLocation }) =>
      when && currentLocation.pathname !== nextLocation.pathname,
    [when]
  );
  const blocker = useBlocker(shouldBlock);
  useEffect(() => {
    if (blocker.state !== 'blocked') return;
    // As React Router's own prompt does: proceed after the dialog, outside this effect.
    if (window.confirm(message)) setTimeout(blocker.proceed, 0);
    else blocker.reset();
  }, [blocker, message]);
}
