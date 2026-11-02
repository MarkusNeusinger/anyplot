import { type ComponentType, lazy } from 'react';

/**
 * `React.lazy` that renders `fallback` when the chunk does not load, instead of throwing.
 *
 * A lazy chunk that fails (a deploy replaced its hashed file, the connection dropped) would
 * otherwise reach the route's error page, which reloads the page and so ends the agent chat's
 * session, whose state lives only in the page.
 */
export function lazyOrFallback<P extends object>(
  load: () => Promise<{ default: ComponentType<P> }>,
  fallback: ComponentType<P>
) {
  return lazy(() => load().catch(() => ({ default: fallback })));
}
