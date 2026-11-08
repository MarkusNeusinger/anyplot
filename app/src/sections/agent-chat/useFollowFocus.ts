/**
 * The keyboard focus follows the live data card (`DataPanel.tsx`) to its new version. A version a
 * turn makes moves the card after that turn's message, and one its own controls make moves it to
 * the thread's end, before and after a plot alike (`placeData` in `useAgentSession.ts`): React
 * moves the card's node, and a browser drops the focus of an element whose node moves (it lands on
 * the page's body). A control can also go with the version it made (`.to_long()` leaves with the
 * offer it applied).
 *
 * So the card keeps the element inside it that held the focus last (`onFocus`), until the user
 * moves on: the focus leaves for another element (`onBlur` with a `relatedTarget` outside the
 * card), or a pointer presses anywhere outside the card, the page's background included, where
 * the body takes the focus with no element to name. A blur without either is a drop, not a
 * choice: the move, or a control that turned disabled while its step ran. When a new version
 * shows and the focus is nowhere (the body), it goes back to that element if it is still in the
 * card and enabled, else to the card's label on its border (`labelRef`, `CardFrame.tsx`). A
 * version of the card's own controls (`.undo()`, `.to_long()`, the pickers) puts the focus there
 * even when the click gave none (a button in Safari): the user acted on the card and its new
 * place is where to look,
 * unless their last press or focus went outside the card while the version was on its way (a
 * sheet read takes seconds). The focus scrolls the element into view, under the masthead (the
 * page's `scroll-padding-top`).
 *
 * The focus stays where it is in every other case: in the message box while a turn the user sent
 * makes the version, or anywhere else the user moved it.
 */

import { useCallback, useEffect, useLayoutEffect, useRef } from 'react';

import type { DataSnapshot, DataVersionChange } from 'src/hooks/useAgentSession';

/**
 * The versions the card's own controls make: `.undo()`, `.to_long()`, the table and sheet
 * pickers. `.use()` is not among them: the card of a table read from text unmounts while its
 * table parses, so the data card it turns into mounts anew and has nothing to follow.
 */
const OWN_CONTROLS: ReadonlySet<DataVersionChange> = new Set(['undo', 'to_long', 'table', 'sheet']);

export interface FollowFocus {
  /** The card's root, which holds the focus it follows. */
  cardRef: React.RefObject<HTMLElement | null>;
  /** The label on the card's border: where the focus goes when its element went. */
  labelRef: React.RefObject<HTMLElement | null>;
  onFocus: (event: React.FocusEvent<HTMLElement>) => void;
  onBlur: (event: React.FocusEvent<HTMLElement>) => void;
}

/** The elements a press on the card names as the control the user used. */
const CONTROLS = 'button, select, input, textarea, a[href], [tabindex]';

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
  // The user's last press or focus was outside the card: a version of its own controls that
  // lands later (a sheet read takes seconds) then leaves the focus where it is, also in Safari,
  // where a press on a button gives it no focus to remember.
  const away = useRef(true);
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
    if (!last && (!own || away.current)) return;
    const target = last && card.contains(last) && !inert(last) ? last : labelRef.current;
    target?.focus();
  }, [n, own]);

  // A press anywhere outside the card is the user moving on, also where it gives no element the
  // focus (the page's background), so a later move never pulls the focus back into the card. A
  // press on a control inside the card names that control, also where the press gives it no focus
  // (a button in Safari), so the focus lands on it as after a click in Chrome, never on a control
  // the keyboard visited before.
  useEffect(() => {
    const press = (event: PointerEvent) => {
      const card = cardRef.current;
      const inside = event.target instanceof Element && !!card?.contains(event.target);
      away.current = !inside;
      if (!inside) {
        held.current = null;
        return;
      }
      const control = (event.target as Element).closest<HTMLElement>(CONTROLS);
      if (control && card?.contains(control)) held.current = control;
    };
    document.addEventListener('pointerdown', press, true);
    return () => document.removeEventListener('pointerdown', press, true);
  }, []);

  const onFocus = useCallback((event: React.FocusEvent<HTMLElement>) => {
    held.current = event.target;
    away.current = false;
  }, []);
  const onBlur = useCallback((event: React.FocusEvent<HTMLElement>) => {
    const next = event.relatedTarget;
    if (next instanceof Node && !cardRef.current?.contains(next)) {
      held.current = null;
      away.current = true;
    }
  }, []);

  return { cardRef, labelRef, onFocus, onBlur };
}
