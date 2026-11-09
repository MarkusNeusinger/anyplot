/**
 * The chat as one terminal-style window (style guide §7.9): a 1 px rule with a small radius on
 * the page's own colour, the tab label `~/anyplot.ai/agent` on its top border (the hero panel's
 * construction, §7.1), the header row in plain words inside it, then a dashed rule, the thread
 * and the composer, and at its foot the status line, `>>> step 1 of 2 · …`. The frame took the
 * place of the surface panel with its `# chat` label, the step header above it and the step lines
 * above the message box in the v4 design (2026-11-06).
 *
 * The section is the chat's landmark ("Chat") and takes a dropped file anywhere on it, which
 * becomes the message box's attachment (`useChatAttachment.ts`); the opening, ineligible and
 * error states render in the same frame without one. The tab label's path is decoration and
 * hidden from screen readers, since the section's name says what it is; the mood the page puts
 * after it (`● quiet`, `LoadMood.tsx`) is an element of its own beside it, a status region.
 *
 * The status line is the plot button's description (`STATUS_LINE_ID`); it changes with every
 * step line, so it is no live region itself. The hidden polite region beside it (`StepStatus`)
 * reads out the step when it changes, and that a paste is being read. While a plot is drawn the
 * line counts its time (`drawing your plot · 0:42 · usually 1–3 min`): the clock is hidden from
 * screen readers, so the description never reads it. At its end stand the actions besides the
 * step's own: `.stop()`, `.start_over()` and `.feedback()`.
 */

import { useLayoutEffect, useRef } from 'react';

import Box from '@mui/material/Box';
import useMediaQuery from '@mui/material/useMediaQuery';

import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { START_OVER_HELP } from 'src/sections/agent-chat/messages';
import { RunClock } from 'src/sections/agent-chat/RunClock';
import {
  STATUS_LINE_ID,
  type StatusLineText,
  stepAnnouncement,
} from 'src/sections/agent-chat/steps';
import {
  CHAT_SECTION_GAP,
  frameRuleSx,
  frameSx,
  labelSx,
  PHONE_QUERY,
  statusActionSx,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

/** The frame's tab label, the site's `~/anyplot` breadcrumb with the page's path. */
export const FRAME_TAB = '~/anyplot.ai/agent';

export interface ChatFrameProps {
  /** The header row: the spec's title, the library and the language, and the admin's `⋯`. */
  header: React.ReactNode;
  /** After the tab label's path on the top border: the service's mood (`LoadMood`), or nothing. */
  mood?: React.ReactNode;
  children: React.ReactNode;
  /** A file dragged over the chat and dropped on it; left out while no session is open. */
  onDragEnter?: (event: React.DragEvent) => void;
  onDragOver?: (event: React.DragEvent) => void;
  onDragLeave?: (event: React.DragEvent) => void;
  onDrop?: (event: React.DragEvent) => void;
}

export function ChatFrame({ header, mood = null, children, ...drop }: ChatFrameProps) {
  return (
    <Box
      component="section"
      aria-label="Chat"
      {...drop}
      sx={{ ...frameSx, display: 'flex', flexDirection: 'column', gap: CHAT_SECTION_GAP }}
    >
      {/* One label on the top border: the path, hidden from screen readers, and the mood after it,
          which a screen reader reads as a status of its own. */}
      <Box
        data-testid="chat-frame-label"
        sx={{
          ...labelSx,
          position: 'absolute',
          top: 0,
          left: { xs: 10, sm: 20 },
          transform: 'translateY(-50%)',
          px: { xs: 0.75, sm: 1 },
          bgcolor: 'var(--bg-page)',
          color: 'var(--ink-soft)',
          lineHeight: 1.4,
          whiteSpace: 'nowrap',
        }}
      >
        <span aria-hidden data-testid="chat-frame-tab">
          {FRAME_TAB}
        </span>
        {mood}
      </Box>
      {header}
      <FrameRule />
      {children}
    </Box>
  );
}

/** The frame's dashed rule: under the header row, and between the thread and the composer. */
export function FrameRule() {
  return <Box sx={frameRuleSx} />;
}

/** The hidden polite region that says the step when it changes; it stays mounted. */
export function StepStatus({ state }: { state: AgentSessionState }) {
  return (
    <Box data-testid="data-step-status" aria-live="polite" sx={visuallyHiddenSx}>
      {stepAnnouncement(state)}
    </Box>
  );
}

export interface StatusLineProps {
  state: AgentSessionState;
  /** The line's words after `>>>` (`statusLine` in `steps.ts`). */
  line: StatusLineText;
  /** `.stop()` while a run is in progress; null while none runs. */
  stop?: { stopping: boolean; onStop: () => void } | null;
  /** `.start_over()` once the confirmed data has a plot in this library; null without. */
  startOver?: { inert: boolean; onStartOver: () => void } | null;
  /** `.feedback()` before the first plot, which opens the chat's own feedback form; null without. */
  onFeedback?: (() => void) | null;
  /** Where the keyboard focus goes when `.stop()` held it and leaves with the run: the message box. */
  focusAfterStop?: React.RefObject<HTMLElement | null>;
}

/** The hidden help `.start_over()` names as its description. */
const START_OVER_HELP_ID = 'agent-start-over-help';

/**
 * The frame's foot: `>>> step 2 of 2 · …`, the plot button's description, with the step's live
 * region beside it, and at its end the actions that are not the step's: `.stop()` while a run is
 * in progress, a button of its own that Tab reaches, `.start_over()` once the library has a plot
 * and, before the first plot, `.feedback()`. The `>>>` is a terminal prompt glyph beside words,
 * in the one brand green in both themes, as the plot of the day's terminal has it (style guide
 * §4.4); the words keep the soft ink, legible in both themes. Only the words carry the id the
 * plot button names, so its description never reads the actions' names.
 */
export function StatusLine({
  state,
  line,
  stop = null,
  startOver = null,
  onFeedback = null,
  focusAfterStop,
}: StatusLineProps) {
  const actions = stop || startOver || onFeedback;
  // Read at the first render, so a phone never shows the long words first.
  const narrow = useMediaQuery(PHONE_QUERY, { noSsr: true });
  const run = line.run;
  return (
    <>
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          columnGap: 1.5,
          rowGap: 0.5,
        }}
      >
        <Box
          id={STATUS_LINE_ID}
          data-testid="data-step"
          data-step={line.step}
          sx={{
            ...labelSx,
            color: 'var(--ink-soft)',
            lineHeight: 1.6,
            overflowWrap: 'anywhere',
            flex: '1 1 16rem',
            minWidth: 0,
          }}
        >
          <Box component="span" aria-hidden sx={{ color: colors.primary }}>
            {'>>> '}
          </Box>
          {run ? (
            // While a plot is drawn: its words, its clock (hidden from the description) and how
            // long a plot usually takes; on a phone `drawing · 0:42 · usually 1–3 min`.
            <>
              {`${line.head} · ${narrow ? run.short : run.words}`}
              {run.clockFrom !== null && <RunClock from={run.clockFrom} prefix=" · " />}
              {run.tail ? ` · ${run.tail}` : ''}
            </>
          ) : (
            line.text
          )}
        </Box>
        {actions && (
          <Box
            data-testid="status-actions"
            sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, ml: 'auto' }}
          >
            {stop && (
              <StopButton
                stopping={stop.stopping}
                onStop={stop.onStop}
                focusAfter={focusAfterStop}
              />
            )}
            {startOver && (
              <Box
                component="button"
                type="button"
                onClick={() => {
                  if (!startOver.inert) startOver.onStartOver();
                }}
                aria-disabled={startOver.inert || undefined}
                aria-label="Start over"
                aria-describedby={START_OVER_HELP_ID}
                title={START_OVER_HELP}
                sx={statusActionSx}
              >
                .start_over()
              </Box>
            )}
            {onFeedback && (
              <Box
                component="button"
                type="button"
                onClick={onFeedback}
                aria-label="Give feedback on this chat"
                title="no plot yet? tell us what went wrong"
                sx={statusActionSx}
              >
                .feedback()
              </Box>
            )}
          </Box>
        )}
      </Box>
      {startOver && (
        <Box component="span" id={START_OVER_HELP_ID} sx={visuallyHiddenSx}>
          {START_OVER_HELP}
        </Box>
      )}
      <StepStatus state={state} />
    </>
  );
}

interface StopButtonProps {
  stopping: boolean;
  onStop: () => void;
  focusAfter?: React.RefObject<HTMLElement | null>;
}

/**
 * `.stop()`, framed in the error colour, for the run in progress. While the stop is on its way it says
 * so and is inert, and keeps the focus; when the run ends the button goes, and a focus it held
 * moves on to `focusAfter`, so the keyboard continues in the message box instead of at the
 * page's top. The check runs as the button unmounts, while it still holds the focus; the box
 * stands for as long as the session is open, so the one the button met when it came is the one.
 */
function StopButton({ stopping, onStop, focusAfter }: StopButtonProps) {
  const ref = useRef<HTMLButtonElement>(null);
  useLayoutEffect(() => {
    const button = ref.current;
    const next = focusAfter?.current ?? null;
    return () => {
      if (button && document.activeElement === button) next?.focus();
    };
  }, [focusAfter]);
  return (
    <Box
      component="button"
      type="button"
      ref={ref}
      onClick={() => {
        if (!stopping) onStop();
      }}
      aria-disabled={stopping || undefined}
      aria-label="Stop"
      // The words in the line's soft ink, legible in both themes (the red reads about 2.9:1 at
      // 13 px on the dark page); the red marks the button's boundary and its hover.
      sx={{
        ...statusActionSx,
        border: `1px solid ${colors.error}`,
        '&:hover:not(:disabled):not([aria-disabled="true"])': {
          color: colors.error,
          bgcolor: 'var(--bg-elevated)',
        },
      }}
    >
      {stopping ? '.stop() …' : '.stop()'}
    </Box>
  );
}
