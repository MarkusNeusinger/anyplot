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
 * error states render in the same frame without one. The tab label is decoration and hidden
 * from screen readers, since the section's name says what it is.
 *
 * The status line is the plot buttons' description (`STATUS_LINE_ID`); it changes with every
 * step line, so it is no live region itself. The hidden polite region beside it (`StepStatus`)
 * reads out the step when it changes, and that a paste is being read.
 */

import Box from '@mui/material/Box';

import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { useTheme } from 'src/hooks/useLayoutContext';
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
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

/** The frame's tab label, the site's `~/anyplot` breadcrumb with the page's path. */
export const FRAME_TAB = '~/anyplot.ai/agent';

export interface ChatFrameProps {
  /** The header row: the spec's title, the library and the language, and the admin's `⋯`. */
  header: React.ReactNode;
  children: React.ReactNode;
  /** A file dragged over the chat and dropped on it; left out while no session is open. */
  onDragEnter?: (event: React.DragEvent) => void;
  onDragOver?: (event: React.DragEvent) => void;
  onDragLeave?: (event: React.DragEvent) => void;
  onDrop?: (event: React.DragEvent) => void;
}

export function ChatFrame({ header, children, ...drop }: ChatFrameProps) {
  return (
    <Box
      component="section"
      aria-label="Chat"
      {...drop}
      sx={{ ...frameSx, display: 'flex', flexDirection: 'column', gap: CHAT_SECTION_GAP }}
    >
      <Box
        aria-hidden
        data-testid="chat-frame-tab"
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
        {FRAME_TAB}
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
}

/**
 * The frame's foot: `>>> step 2 of 2 · …`, the plot buttons' description, with the step's live
 * region beside it. The `>>>` is a glyph beside words, in the brand green on the dark page and
 * the darker green on the light one (4.8:1 rather than 3.1:1), as the mock has it; the words keep
 * the soft ink, legible in both themes.
 */
export function StatusLine({ state, line }: StatusLineProps) {
  const { isDark } = useTheme();
  return (
    <>
      <Box
        id={STATUS_LINE_ID}
        data-testid="data-step"
        data-step={line.step}
        sx={{ ...labelSx, color: 'var(--ink-soft)', lineHeight: 1.6, overflowWrap: 'anywhere' }}
      >
        <Box
          component="span"
          aria-hidden
          sx={{ color: isDark ? colors.primary : colors.primaryDark }}
        >
          {'>>> '}
        </Box>
        {line.text}
      </Box>
      <StepStatus state={state} />
    </>
  );
}
