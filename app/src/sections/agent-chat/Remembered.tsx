/**
 * The remembered decisions (the owner's "Gemerkt", since 2026-11-02): the plot
 * memory's entries, the decisions every later plot of the session takes over,
 * also in another library ("horizontal reference line at y = 7", "x-axis
 * label: 'Zeit (h)'"). The page shows it above the composer, where the next
 * plot is asked for and where the offer after a library switch counts these
 * decisions. Each entry has `.forget()`, which removes it from the memory: the
 * plot itself does not change, the next one no longer takes it over;
 * `.forget_all()` removes every entry, for a blank start. Nothing else clears
 * the memory: `.start_over()` keeps it (owner decision of 2026-11-02). Editing
 * an entry comes later; until then a change in words goes through the chat.
 *
 * The heading is one short line, `# remembered · 2 decisions` (`· full` once the
 * memory has no room), and what the list does is behind the ⓘ at its end, as the
 * experimental notice does it: the line above the composer stays quiet.
 *
 * While the memory is empty (or the server has none) nothing shows but a hidden
 * status region, which announces the last removal. `.hide()` folds the list
 * under its heading, for a long one. Like the language chip, the list holds its
 * own pending entry and failure line: the entry being removed is marked
 * `aria-disabled`, so the keyboard focus stays on its control, and once it is
 * gone the focus moves to the control now in its place, or the one above, or,
 * after the last entry, to `fallbackFocusRef` (the message box). The page
 * disables every control while anything else is in flight, which the server
 * would refuse with `409 run_active`; that also clears a stale failure line.
 */

import { useEffect, useId, useLayoutEffect, useMemo, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import { AgentApiError, type PlotMemory } from 'src/lib/agent';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import {
  describeMemoryFailure,
  REMEMBERED_DETAILS,
  REMEMBERED_FULL,
} from 'src/sections/agent-chat/messages';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import {
  actionButtonSx,
  labelSx,
  smallText,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors, typography } from 'src/theme';

export interface RememberedProps {
  /** The plot memory as the server last listed it; `null` before any list. */
  memory: PlotMemory | null;
  /** Something is in flight: the server would refuse a removal. */
  disabled: boolean;
  /** Remove one entry; rejects with an `AgentApiError` on failure. */
  onForget: (entryId: string) => Promise<void>;
  /** Remove every entry, a blank start; rejects with an `AgentApiError` on failure. */
  onForgetAll?: () => Promise<void>;
  /** Where the focus goes once the last entry is gone with the list. */
  fallbackFocusRef?: React.RefObject<HTMLElement | null>;
}

/** The pending marker of `.forget_all()`, which no entry id matches (`m` and digits). */
const ALL = '*';

export function Remembered({
  memory,
  disabled,
  onForget,
  onForgetAll,
  fallbackFocusRef,
}: RememberedProps) {
  const entries = useMemo(() => memory?.entries ?? [], [memory]);
  const [expanded, setExpanded] = useState(true);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [failure, setFailure] = useState<{ code: string; ref: string | null } | null>(null);
  const [announcement, setAnnouncement] = useState('');
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
  const headingId = useId();
  const listId = useId();

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
        setAnnouncement(entryId === ALL ? 'forgot every decision' : `forgot: ${text}`);
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

  const status = (
    <Box role="status" sx={visuallyHiddenSx}>
      {announcement}
    </Box>
  );
  if (entries.length === 0) return status;

  const count = `${entries.length} decision${entries.length === 1 ? '' : 's'}`;
  const full = memory !== null && entries.length >= memory.max_entries;
  return (
    <Box
      component="section"
      aria-labelledby={headingId}
      data-testid="plot-memory"
      sx={{
        borderLeft: '2px solid var(--rule)',
        pl: 1.5,
        display: 'flex',
        flexDirection: 'column',
        gap: 0.5,
        minWidth: 0,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          columnGap: 1,
        }}
      >
        {/* The ⓘ stands outside the heading, so the list's name is the heading's text alone. */}
        <Box sx={{ ...labelSx, lineHeight: 1.6, flex: '1 1 200px', minWidth: 0 }}>
          <Box component="span" id={headingId}>
            {`# remembered · ${count}${full ? ' · full' : ''}`}
          </Box>
          <InfoPopover
            label="About the remembered decisions"
            heading="# remembered"
            lines={[...(full ? [REMEMBERED_FULL] : []), ...REMEMBERED_DETAILS]}
          />
        </Box>
        <Box
          component="button"
          type="button"
          aria-expanded={expanded}
          aria-controls={listId}
          aria-label={expanded ? 'Hide the remembered decisions' : 'Show the remembered decisions'}
          onClick={() => setExpanded(!expanded)}
          sx={{ ...actionButtonSx, minHeight: 28, py: 0.25 }}
        >
          {expanded ? '.hide()' : '.show()'}
        </Box>
        {onForgetAll && (
          <Box
            component="button"
            type="button"
            onClick={() => void forget(ALL, 0, '')}
            disabled={(disabled || pendingId !== null) && pendingId !== ALL}
            aria-disabled={pendingId === ALL || undefined}
            aria-label="Forget all remembered decisions"
            title="a blank start: every next plot takes none of them over"
            sx={{
              ...actionButtonSx,
              minHeight: 28,
              py: 0.25,
              '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
            }}
          >
            {pendingId === ALL ? '.forget_all() …' : '.forget_all()'}
          </Box>
        )}
      </Box>
      <Box
        component="ul"
        id={listId}
        hidden={!expanded}
        sx={{ listStyle: 'none', m: 0, p: 0, display: expanded ? 'block' : 'none' }}
      >
        {entries.map((entry, index) => {
          const own = pendingId === entry.id;
          return (
            <Box
              component="li"
              key={entry.id}
              data-testid="memory-entry"
              sx={{
                display: 'flex',
                alignItems: 'baseline',
                columnGap: 1,
                py: 0.25,
                '& + &': { borderTop: '1px dashed var(--rule)' },
              }}
            >
              <Box
                sx={{
                  fontFamily: typography.mono,
                  fontSize: smallText,
                  color: 'var(--ink)',
                  lineHeight: 1.6,
                  flex: '1 1 auto',
                  minWidth: 0,
                  overflowWrap: 'anywhere',
                }}
              >
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
                sx={{
                  ...actionButtonSx,
                  flexShrink: 0,
                  minHeight: 28,
                  py: 0.25,
                  '&[aria-disabled="true"]': { opacity: 0.45, cursor: 'default' },
                }}
              >
                {own ? '.forget() …' : '.forget()'}
              </Box>
            </Box>
          );
        })}
      </Box>
      {failure && (
        <Box
          role="alert"
          sx={{
            fontFamily: typography.mono,
            fontSize: smallText,
            color: colors.error,
            overflowWrap: 'anywhere',
          }}
        >
          {describeMemoryFailure(failure.code, failure.ref)}
          <ReloadHint code={failure.code} />
        </Box>
      )}
      {status}
    </Box>
  );
}
