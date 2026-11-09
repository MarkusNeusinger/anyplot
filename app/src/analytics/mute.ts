/**
 * Keeps the admin's own use of the agent chat out of the visitor numbers: while the switch is
 * on, `useAnalytics` sends no pageview and no event. The chat page turns it on while it serves
 * an admin (the admin lane, "view as visitor" and the fallback after an expired admin session
 * alike) and off again when it unmounts, before the next page records its own pageview
 * (docs/reference/plausible.md, "Agent chat").
 *
 * A module of its own, not part of `useAnalytics`: the page tests replace that module.
 */

let muted = false;

export function setAnalyticsMuted(next: boolean): void {
  muted = next;
}

export function analyticsMuted(): boolean {
  return muted;
}
