/**
 * The remembered decisions (the owner's "Gemerkt", since 2026-11-02): the plot memory's entries,
 * the decisions every later plot of the session takes over, also in another library ("horizontal
 * reference line at y = 7", "x-axis label: 'Zeit (h)'"). Since the v4 chapters they stand on a
 * chapter's line (`ChapterLine.tsx`): the latest `# plot` line, where the next plot takes them
 * over, and before the first plot the latest chapter's (`threadModel`'s `decisionsAt`).
 *
 * - `RememberedCount` is the line's `3 decisions ▾`, a button that unfolds the list under the line
 *   (`aria-expanded`, `aria-controls`), with `· full` beside it once the memory has no room. Never
 *   "0 decisions": nothing shows while the memory is empty or unknown.
 * - `Remembered` is the list itself, the thread's row right after that line, folded by default:
 *   each decision with `.forget()`, which removes it from the memory (the plot itself does not
 *   change, the next one no longer takes it over), then `.forget_all()`, which removes every one,
 *   for a blank start, and the ⓘ with what the list does, centred and wrapping as in the v4 mock.
 *   Nothing else clears the memory: `.start_over()` keeps it (owner decision of 2026-11-02).
 *   Editing an entry comes later; until then a change in words goes through the chat.
 *
 * The list is one keyed row of the thread, so when a newer chapter takes the decisions over the
 * row moves with them, and its own state (the entry being removed, a failure line) and a focus
 * inside it stay: a browser drops the focus of an element whose node moves, and React gives it back
 * after the commit to the element that had it, which is still in the page. The thread holds the
 * open state, which the count shows. The count itself is a new element on the new line, which
 * React cannot give the focus back to, so a focus on it follows it there (`handoffRef`). The list
 * itself is no live region of its own: the
 * thread's log does not read it out when it unfolds or gains an entry (`aria-live="off"`), and a
 * removal is announced by the page's status region outside the log (`onAnnounce`), which stays
 * mounted while the list comes and goes.
 *
 * Like the language chip, the list holds its own pending entry and failure line: the entry being
 * removed is marked `aria-disabled`, so the keyboard focus stays on its control, and once it is
 * gone the focus moves to the control now in its place, or the one above, or, after the last
 * entry, to `fallbackFocusRef` (the message box). The page disables every control while anything
 * else is in flight, which the server would refuse with `409 run_active`; that also clears a stale
 * failure line.
 */

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { AgentApiError, type PlotMemory } from 'src/lib/agent';
import { countOf } from 'src/sections/agent-chat/countOf';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import {
  describeMemoryFailure,
  REMEMBERED_DETAILS,
  REMEMBERED_FULL,
} from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { actionButtonSx, chapterControlSx, smallText } from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

/** Whether the memory is full: no room for one more decision. */
const isFull = (memory: PlotMemory) => memory.entries.length >= memory.max_entries;

export interface RememberedCountProps {
  memory: PlotMemory | null;
  /** The list under the line is open. */
  open: boolean;
  /** The list's id, which the count controls. */
  listId: string;
  onToggle: () => void;
  /**
   * Set while the count that had the focus unmounts, so the count on the next line takes it: the
   * thread's, shared by every line's count.
   */
  handoffRef: React.RefObject<boolean>;
}

/** The chapter line's `3 decisions ▾`, and `· full` once the memory has no room. */
export function RememberedCount({
  memory,
  open,
  listId,
  onToggle,
  handoffRef,
}: RememberedCountProps) {
  const ref = useRef<HTMLButtonElement>(null);
  // A newer chapter took the decisions over while the count had the focus: the focus moves along
  // with it, from the line it left to this one, in the same commit.
  useLayoutEffect(() => {
    const node = ref.current;
    if (node && handoffRef.current) {
      handoffRef.current = false;
      node.focus();
    }
    return () => {
      if (!node || node !== document.activeElement) return;
      handoffRef.current = true;
      // No count took it in this commit (the list went empty): no later one takes it either.
      queueMicrotask(() => {
        handoffRef.current = false;
      });
    };
  }, [handoffRef]);
  const count = memory?.entries.length ?? 0;
  if (!memory || count === 0) return null;
  return (
    <>
      <Box
        component="button"
        type="button"
        ref={ref}
        data-testid="decisions-toggle"
        aria-expanded={open}
        aria-controls={listId}
        // The words on screen first, then what they count (WCAG 2.5.3); the arrow is the state,
        // which `aria-expanded` says.
        aria-label={`${countOf(count, 'decision')} remembered`}
        onClick={onToggle}
        sx={{ ...chapterControlSx, color: 'var(--ink)' }}
      >
        {countOf(count, 'decision')}
        <span aria-hidden>{open ? ' ▴' : ' ▾'}</span>
      </Box>
      {isFull(memory) && (
        <Box component="span" sx={{ ml: 1 }}>
          <Box component="span" aria-hidden sx={{ mr: 1 }}>
            ·
          </Box>
          full
        </Box>
      )}
    </>
  );
}

export interface RememberedProps {
  /** The plot memory as the server last listed it; `null` before any list. */
  memory: PlotMemory | null;
  /** The list's id, which the chapter line's count controls. */
  id: string;
  /** The list is unfolded. */
  open: boolean;
  /** Something is in flight: the server would refuse a removal. */
  disabled: boolean;
  /** Remove one entry; rejects with an `AgentApiError` on failure. */
  onForget: (entryId: string) => Promise<void>;
  /** Remove every entry, a blank start; rejects with an `AgentApiError` on failure. */
  onForgetAll?: () => Promise<void>;
  /** Where the focus goes once the last entry is gone with the list. */
  fallbackFocusRef?: React.RefObject<HTMLElement | null>;
  /** Say what a removal did, in the page's status region outside the thread's log. */
  onAnnounce: (text: string) => void;
}

/** The pending marker of `.forget_all()`, which no entry id matches (`m` and digits). */
const ALL = '*';

/** The remembered decisions under their chapter line, each with `.forget()`, then `.forget_all()`. */
export function Remembered({
  memory,
  id,
  open,
  disabled,
  onForget,
  onForgetAll,
  fallbackFocusRef,
  onAnnounce,
}: RememberedProps) {
  const entries = useMemo(() => memory?.entries ?? [], [memory]);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [failure, setFailure] = useState<{ code: string; ref: string | null } | null>(null);
  // Something else started: the failure line, which is about an earlier attempt, goes.
  const [wasDisabled, setWasDisabled] = useState(disabled);
  if (disabled !== wasDisabled) {
    setWasDisabled(disabled);
    if (disabled && pendingId === null) setFailure(null);
  }
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const controls = useRef(new Map<string, HTMLButtonElement>());
  // The place of an entry the user removed: once it is gone, the focus moves to what took it.
  const removedAt = useRef<{ id: string; index: number } | null>(null);

  // Once the removal is over, the entry gone and the controls take the focus again: its place
  // goes to the control now in it. A refused removal keeps its control, which kept the focus.
  useLayoutEffect(() => {
    const removed = removedAt.current;
    if (!removed || pendingId !== null || disabled) return;
    if (entries.some(entry => entry.id === removed.id)) return;
    removedAt.current = null;
    // Only when the removed control had the focus (it went with it); a focus elsewhere stays.
    const active = document.activeElement;
    if (active && active !== document.body && active.isConnected) return;
    const next = entries[Math.min(removed.index, entries.length - 1)];
    const target = next ? controls.current.get(next.id) : fallbackFocusRef?.current;
    target?.focus();
  }, [entries, pendingId, disabled, fallbackFocusRef]);

  const forget = async (entryId: string, index: number, text: string) => {
    if (pendingId !== null) return;
    setPendingId(entryId);
    setFailure(null);
    removedAt.current = { id: entryId, index };
    try {
      if (entryId === ALL) await onForgetAll?.();
      else await onForget(entryId);
      if (mounted.current)
        onAnnounce(entryId === ALL ? 'forgot every decision' : `forgot: ${text}`);
    } catch (err) {
      removedAt.current = null;
      if (mounted.current) {
        setFailure(
          err instanceof AgentApiError
            ? { code: err.code, ref: err.shownRef }
            : { code: 'network', ref: null }
        );
      }
    } finally {
      if (mounted.current) setPendingId(null);
    }
  };

  // Empty, the list renders nothing while this component stays: it moves the focus once the last
  // entry went.
  if (entries.length === 0) return null;
  const full = memory !== null && isFull(memory);
  /** A `.verb()` of the list: the line's small size, the own pending one dimmed but focusable. */
  const verbSx = {
    ...actionButtonSx,
    flexShrink: 0,
    minHeight: 28,
    px: 0.75,
    py: 0.25,
    '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
  } as const;
  return (
    <Box
      id={id}
      data-testid="plot-memory"
      hidden={!open}
      aria-live="off"
      sx={{
        display: open ? 'flex' : 'none',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 0.5,
        minWidth: 0,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'baseline',
          justifyContent: 'center',
          columnGap: 2,
          rowGap: 0.25,
          minWidth: 0,
          fontFamily: typography.mono,
          fontSize: smallText,
          color: 'var(--ink-soft)',
          lineHeight: 1.6,
        }}
      >
        <Box
          component="ul"
          aria-label="Remembered decisions"
          sx={{
            listStyle: 'none',
            m: 0,
            p: 0,
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'baseline',
            justifyContent: 'center',
            columnGap: 2,
            rowGap: 0.25,
            minWidth: 0,
          }}
        >
          {entries.map((entry, index) => {
            const own = pendingId === entry.id;
            return (
              <Box
                component="li"
                key={entry.id}
                data-testid="memory-entry"
                sx={{ display: 'flex', alignItems: 'baseline', minWidth: 0 }}
              >
                <Box component="span" sx={{ minWidth: 0, overflowWrap: 'anywhere' }}>
                  {entry.text}
                </Box>
                <Box
                  component="button"
                  type="button"
                  ref={(node: HTMLButtonElement | null) => {
                    if (node) controls.current.set(entry.id, node);
                    else controls.current.delete(entry.id);
                  }}
                  onClick={() => void forget(entry.id, index, entry.text)}
                  // The own removal keeps its control focusable; every other one waits for it.
                  disabled={(disabled || pendingId !== null) && !own}
                  aria-disabled={own || undefined}
                  aria-label={`Forget: ${entry.text}`}
                  sx={verbSx}
                >
                  {own ? '.forget() …' : '.forget()'}
                </Box>
              </Box>
            );
          })}
        </Box>
        <Box component="span" sx={{ display: 'inline-flex', alignItems: 'center' }}>
          {onForgetAll && (
            <Box
              component="button"
              type="button"
              onClick={() => void forget(ALL, 0, '')}
              disabled={(disabled || pendingId !== null) && pendingId !== ALL}
              aria-disabled={pendingId === ALL || undefined}
              aria-label="Forget all remembered decisions"
              title="a blank start: every next plot takes none of them over"
              sx={verbSx}
            >
              {pendingId === ALL ? '.forget_all() …' : '.forget_all()'}
            </Box>
          )}
          <InfoPopover
            label="About the remembered decisions"
            heading="# remembered decisions"
            lines={[...(full ? [REMEMBERED_FULL] : []), ...REMEMBERED_DETAILS]}
          />
        </Box>
      </Box>
      {failure && (
        <Box
          role="alert"
          sx={{
            fontFamily: typography.mono,
            fontSize: smallText,
            color: colors.error,
            overflowWrap: 'anywhere',
            textAlign: 'center',
          }}
        >
          {describeMemoryFailure(failure.code, failure.ref)}
          <ReloadHint code={failure.code} />
        </Box>
      )}
    </Box>
  );
}
