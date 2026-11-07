/**
 * The keyboard focus follows the live data card (`DataPanel.tsx`) to its new version. A version a
 * turn or a paste makes moves the card to the thread's end, and so does one its own controls make
 * after a plot (`placeData` in `useAgentSession.ts`): React moves the card's node, and a browser
 * drops the focus of an element whose node moves (it lands on the page's body). A control can also
 * go with the version it made (`.to_long()` leaves with the offer it applied).
 *
 * So the card keeps the element inside it that held the focus last (`onFocus`), until the user
 * moves on: the focus leaves for another element (`onBlur` with a `relatedTarget` outside the
 * card), or a pointer presses anywhere outside the card, the page's background included, where
 * the body takes the focus with no element to name. A blur without either is a drop, not a
 * choice: the move, or a control that turned disabled while its step ran. When a new version
 * shows and the focus is nowhere (the body), it goes back to that element if it is still in the
 * card and enabled, else to the card's label on its border (`labelRef`, `CardFrame.tsx`). A
 * version of the card's own controls (`.undo()`, `.to_long()`, the pickers, `.use()` of a table
 * read from text, whose card turns into this one) puts the focus there even when the click gave
 * none (a button in Safari): the user acted on the card and its new place is where to look. The
 * focus scrolls the element into view, under the masthead (the page's `scroll-padding-top`).
 *
 * The focus stays where it is in every other case: in the message box while a turn the user sent
 * makes the version, or anywhere else the user moved it.
 */

import { useCallback, useEffect, useLayoutEffect, useRef } from 'react';

import type { DataSnapshot, DataVersionChange } from 'src/hooks/useAgentSession';

/**
 * The versions a card's own controls make: `.undo()`, `.to_long()`, the table and sheet pickers,
 * and `.use()` on the card of a table read from text.
 */
const OWN_CONTROLS: ReadonlySet<DataVersionChange> = new Set([
  'undo',
  'to_long',
  'table',
  'sheet',
  'transcription',
]);

export interface FollowFocus {
  /** The card's root, which holds the focus it follows. */
  cardRef: React.RefObject<HTMLElement | null>;
  /** The label on the card's border: where the focus goes when its element went. */
  labelRef: React.RefObject<HTMLElement | null>;
  onFocus: (event: React.FocusEvent<HTMLElement>) => void;
  onBlur: (event: React.FocusEvent<HTMLElement>) => void;
}

/** A control the focus should not land on now: a disabled button or select, or `aria-disabled`. */
function inert(element: HTMLElement): boolean {
  return (
    ('disabled' in element && (element as HTMLButtonElement).disabled) ||
    element.getAttribute('aria-disabled') === 'true'
  );
}

/** `version`: the version the card shows (`DataSnapshot` of its `data` item); none for a table read from text. */
export function useFollowFocus(version: DataSnapshot | undefined): FollowFocus {
  const cardRef = useRef<HTMLElement>(null);
  const labelRef = useRef<HTMLElement>(null);
  // The element inside the card that held the focus last, until the focus moved on to another.
  const held = useRef<HTMLElement | null>(null);
  const shown = useRef(version?.n);
  const n = version?.n;
  const own = !!version && OWN_CONTROLS.has(version.change);

  // After the commit that brought the version, the move included: the DOM is where it lands.
  useLayoutEffect(() => {
    if (n === shown.current) return;
    shown.current = n;
    const card = cardRef.current;
    const active = document.activeElement;
    if (!card || (active && active !== document.body)) return;
    const last = held.current;
    if (!last && !own) return;
    const target = last && card.contains(last) && !inert(last) ? last : labelRef.current;
    target?.focus();
  }, [n, own]);

  // A press anywhere outside the card is the user moving on, also where it gives no element the
  // focus (the page's background), so a later move never pulls the focus back into the card.
  useEffect(() => {
    const press = (event: PointerEvent) => {
      if (!(event.target instanceof Node) || !cardRef.current?.contains(event.target)) {
        held.current = null;
      }
    };
    document.addEventListener('pointerdown', press, true);
    return () => document.removeEventListener('pointerdown', press, true);
  }, []);

  const onFocus = useCallback((event: React.FocusEvent<HTMLElement>) => {
    held.current = event.target;
  }, []);
  const onBlur = useCallback((event: React.FocusEvent<HTMLElement>) => {
    const next = event.relatedTarget;
    if (next instanceof Node && !cardRef.current?.contains(next)) held.current = null;
  }, []);

  return { cardRef, labelRef, onFocus, onBlur };
}
