import { useCallback, useEffect } from 'react';

import { type BlockerFunction, useBlocker } from 'react-router-dom';

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
 * Needs a data router (`createBrowserRouter`; `createMemoryRouter` in tests).
 */
export function useLeaveWarning(when: boolean, message: string): void {
  useEffect(() => {
    if (!when) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
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
