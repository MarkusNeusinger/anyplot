/**
 * The keyboard focus follows the live data card (`DataPanel.tsx`) to its new version. A version a
 * turn or a paste makes moves the card to the thread's end, and so does one its own controls make
 * after a plot (`placeData` in `useAgentSession.ts`): React moves the card's node, and a browser
 * drops the focus of an element whose node moves (it lands on the page's body). A control can also
 * go with the version it made (`.to_long()` leaves with the offer it applied).
 *
 * So the card keeps the element inside it that held the focus last (`onFocus`), until the focus
 * leaves for another element (`onBlur` with a `relatedTarget` outside the card). A blur without
 * one is a drop, not a choice: the move, a control that turned disabled while its step ran, or a
 * click on the page's background. When a new version shows and the focus is nowhere (the body),
 * it goes back to that element if it is still in the card and enabled, else to the card's label
 * on its border (`labelRef`, `CardFrame.tsx`). A version of the card's own controls
 * (`.undo()`, `.to_long()`, the pickers) puts the focus there even when the click gave none (a
 * button in Safari): the user acted on the card and its new place is where to look. The focus
 * scrolls the element into view, under the masthead (the page's `scroll-padding-top`).
 *
 * The focus stays where it is in every other case: in the message box while a turn the user sent
 * makes the version, or anywhere else the user moved it.
 */

import { useCallback, useLayoutEffect, useRef } from 'react';

import type { DataSnapshot, DataVersionChange } from 'src/hooks/useAgentSession';

/** The versions the card's own controls make: `.undo()`, `.to_long()`, the table and sheet pickers. */
const OWN_CONTROLS: ReadonlySet<DataVersionChange> = new Set(['undo', 'to_long', 'table', 'sheet']);

export interface FollowFocus {
  /** The card's root, which holds the focus it follows. */
  cardRef: React.RefObject<HTMLElement | null>;
  /** The label on the card's border: where the focus goes when its element went. */
  labelRef: React.RefObject<HTMLElement | null>;
  onFocus: (event: React.FocusEvent<HTMLElement>) => void;
  onBlur: (event: React.FocusEvent<HTMLElement>) => void;
}

/** A control that takes no focus now: a disabled button or select, or one marked inert. */
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

  const onFocus = useCallback((event: React.FocusEvent<HTMLElement>) => {
    held.current = event.target;
  }, []);
  const onBlur = useCallback((event: React.FocusEvent<HTMLElement>) => {
    const next = event.relatedTarget;
    if (next instanceof Node && !cardRef.current?.contains(next)) held.current = null;
  }, []);

  return { cardRef, labelRef, onFocus, onBlur };
}
