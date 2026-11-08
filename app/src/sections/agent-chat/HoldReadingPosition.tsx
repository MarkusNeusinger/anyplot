/**
 * Holds the reading position still when the live data card lands above a reply the user may be
 * reading (`ChatThread.tsx`). A turn's data version arrives with its `done`, after the reply
 * streamed in, and the card goes in directly after the turn's message, before that reply
 * (`placeData` in `useAgentSession.ts`, owner, 2026-11-07). The browser's own scroll anchoring
 * does not hold the reply: Chrome anchors on the first node in view, here the user's message
 * above the card, so the reply and everything below it moved down by the card's height (240 px at
 * 1440×900, 295 px at 390×844, measured on the BFF mock), and Safari has no scroll anchoring.
 *
 * So the thread does it itself, the way React's `getSnapshotBeforeUpdate` is meant for: just
 * before the commit that moves the card in front of a reply already on screen, it notes where that
 * reply stands and turns the browser's anchoring off for the commit (`holdScrollAnchoring`), so
 * the two never adjust twice; after it, it scrolls the page by the distance the reply moved and
 * gives the anchoring back on the next frame. A reply below the window's bottom edge, which the
 * user cannot be reading, is left where it lands.
 */

import { Component, type ReactNode } from 'react';

import type { ChatItem } from 'src/hooks/useAgentSession';
import { holdScrollAnchoring } from 'src/sections/agent-chat/scrollAnchoring';

/** The attribute every reply's wrapper carries, with the reply's item id (`ChatThread.tsx`). */
export const REPLY_ATTRIBUTE = 'data-reply';

interface HoldReadingPositionProps {
  /** The thread's items as rendered in this commit. */
  items: readonly ChatItem[];
  /** The thread's log element, which holds the replies; the rows stay its own children. */
  log: React.RefObject<HTMLElement | null>;
  children: ReactNode;
}

interface Held {
  reply: Element;
  top: number;
  release: () => void;
}

/**
 * The reply that the live card now stands directly before, when the card was not already there:
 * the item the commit moves the card in front of, which the user has seen.
 */
function replyUnderCard(before: readonly ChatItem[], after: readonly ChatItem[]): number | null {
  let card = -1;
  for (let index = after.length - 1; index >= 0; index -= 1) {
    if (after[index].kind === 'data') {
      card = index;
      break;
    }
  }
  const next = after[card + 1];
  if (card < 0 || !next || !['assistant', 'refusal', 'error'].includes(next.kind)) return null;
  const was = before.findIndex(item => item.id === next.id);
  if (was < 0) return null;
  return before[was - 1]?.id === after[card].id ? null : next.id;
}

export class HoldReadingPosition extends Component<HoldReadingPositionProps> {
  getSnapshotBeforeUpdate(previous: HoldReadingPositionProps): Held | null {
    const log = this.props.log.current;
    if (previous.items === this.props.items || !log) return null;
    const id = replyUnderCard(previous.items, this.props.items);
    if (id === null) return null;
    const reply = log.querySelector(`[${REPLY_ATTRIBUTE}="${id}"]`);
    if (!reply) return null;
    const top = reply.getBoundingClientRect().top;
    if (top >= window.innerHeight) return null;
    return { reply, top, release: holdScrollAnchoring() };
  }

  componentDidUpdate(_previous: HoldReadingPositionProps, _state: unknown, held: Held | null) {
    if (!held) return;
    const moved = held.reply.getBoundingClientRect().top - held.top;
    if (moved) window.scrollBy({ top: moved, behavior: 'instant' });
    window.requestAnimationFrame(() => held.release());
  }

  render() {
    // No element of its own: the rows stay the log's children, laid out as before.
    return this.props.children;
  }
}
