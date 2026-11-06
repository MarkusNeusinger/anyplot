/**
 * Keeps the admin's own use of the agent chat out of the visitor numbers: while the switch is
 * on, `useAnalytics` sends no pageview and no event. The chat page turns it on while it serves
 * an admin (the admin lane, "view as visitor" and the fallback after an expired admin session
 * alike) and off again when it unmounts, before the next page records its own pageview
 * (docs/reference/plausible.md, "Agent chat").
 *
 * The Web Vitals measure the whole page load and report late (CLS and INP when the page is
 * hidden), so they stay muted for the rest of a load once the switch was on
 * (`analyticsMutedThisLoad`): an admin who moved on from the chat to another page still
 * reports nothing for that load.
 *
 * A module of its own, not part of `useAnalytics`: the page tests replace that module.
 */

let muted = false;
let mutedThisLoad = false;

export function setAnalyticsMuted(next: boolean): void {
  muted = next;
  if (next) mutedThisLoad = true;
}

export function analyticsMuted(): boolean {
  return muted;
}

/** The switch was on at some point of this page load. */
export function analyticsMutedThisLoad(): boolean {
  return mutedThisLoad;
}

/** Forget the page load's mute, for tests. */
export function resetAnalyticsMute(): void {
  muted = false;
  mutedThisLoad = false;
}
