/**
 * Where the data card is in view. The card stands in the thread after the paste it came from
 * (its `data` item, `ChatThread.tsx`); the pinned header that leads to it sticks above the
 * thread (`PinnedHeader` in `PinnedData.tsx`). The two sit in different subtrees, so the page
 * holds their shared state here.
 *
 * Step 1: the card is open. The click of `.create_plot()` confirms the data and collapses the
 * card with it; from then on the header stays, also when the page is back at step 1, so it
 * leads back to the card from anywhere in the thread and the content below it does not jump
 * when the confirmation drops. In step 2 the card shows only after the header's `.show()`,
 * which brings its top into view below the header; `.hide()` closes it and goes back to where
 * the user was reading. Back at step 1 the card is open anyway, and the header's button
 * scrolls to it.
 */

import { useLayoutEffect, useRef, useState } from 'react';

import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { inStep2 } from 'src/sections/agent-chat/steps';

export interface DataCardView {
  /** Step 2: the data and its bindings are confirmed. */
  confirmed: boolean;
  /** The header sticks above the thread: the data was confirmed at least once. */
  pinned: boolean;
  /** Step 2 only: the user opened the card with `.show()`. */
  expanded: boolean;
  /** Whether the card renders at its place in the thread. */
  open: boolean;
  cardRef: React.RefObject<HTMLElement | null>;
  /** The card of a table read from text that waits for its decision, at its own item. */
  transcriptionRef: React.RefObject<HTMLElement | null>;
  /**
   * The header's `.show()` and `.hide()`; in step 1 it brings the card into view, and while a
   * table read from text waits, that table's card, where `.use()` and `.discard()` are.
   */
  toggle: () => void;
}

export function useDataCardView(state: AgentSessionState): DataCardView {
  const [expanded, setExpanded] = useState(false);
  const cardRef = useRef<HTMLElement>(null);
  const transcriptionRef = useRef<HTMLElement>(null);
  // Where the commit after a toggle scrolls: the card's top after `.show()`, back to the
  // reading position from before it after `.hide()`.
  const scrollTarget = useRef<'card' | number | null>(null);
  const returnTo = useRef<number | null>(null);
  const confirmed = inStep2(state);
  const dataset = state.dataset;
  const open = !!dataset && (!confirmed || expanded);
  const everConfirmed = useRef(false);
  if (confirmed) everConfirmed.current = true;
  const pinned = !!dataset && everConfirmed.current;
  // The confirmation a plot button starts with (`.create_plot()` at the composer's end) collapses
  // the card as it starts; a later step 1 opens it in full anyway. A step 2 that returns without
  // it (a discarded table) keeps the card as the user left it. Adjusted while rendering, React's
  // pattern for state that follows a prop.
  const [confirmSeen, setConfirmSeen] = useState(state.confirmBusy);
  if (state.confirmBusy !== confirmSeen) {
    setConfirmSeen(state.confirmBusy);
    if (state.confirmBusy) setExpanded(false);
  }

  // `.show()` from far down the thread opens the card at its place higher up, out of view: bring
  // its top in below the pinned header (the page's scroll-padding keeps it clear). `.hide()` goes
  // back to where the user read. The card renders in the same commit, so its ref is set here.
  useLayoutEffect(() => {
    const target = scrollTarget.current;
    scrollTarget.current = null;
    if (target === 'card') {
      cardRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
    } else if (target !== null && target !== window.scrollY) {
      window.scrollTo({ top: target });
    }
  }, [expanded]);

  const toggle = () => {
    // Step 1 again: the card is open anyway, somewhere above; the header leads to it, or to the
    // table read from text whose decision it names, which waits in a card of its own.
    if (!confirmed) {
      const target = state.transcription ? transcriptionRef.current : cardRef.current;
      target?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
      return;
    }
    if (expanded) {
      scrollTarget.current = returnTo.current;
      returnTo.current = null;
    } else {
      returnTo.current = window.scrollY;
      scrollTarget.current = 'card';
    }
    setExpanded(!expanded);
  };

  return { confirmed, pinned, expanded, open, cardRef, transcriptionRef, toggle };
}
