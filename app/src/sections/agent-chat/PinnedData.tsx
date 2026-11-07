/**
 * The data card's two halves, which stand apart since the card moved into the thread: the
 * sticky header above the thread (`PinnedHeader`), and the card's shell at its place in the
 * thread after the paste it came from (`DataCardShell`), a card frame with what the data holds
 * on its border (`CardFrame.tsx`, `data · 48 rows × 4 cols`). The page joins them through
 * `useDataCardView`.
 *
 * Once the data has been confirmed at least once, the header stays at the top of the thread
 * (`✓ data fits · …` in step 2, `! check again · …` when a change takes the session back to
 * step 1) and opens or scrolls to the card.
 */

import Box from '@mui/material/Box';
import GlobalStyles from '@mui/material/GlobalStyles';

import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { CardFrame } from 'src/sections/agent-chat/CardFrame';
import type { CardLabel } from 'src/sections/agent-chat/cardLabels';
import { dataShape } from 'src/sections/agent-chat/steps';
import {
  actionButtonSx,
  labelSx,
  PINNED_CLEARANCE,
  PINNED_TOP,
} from 'src/sections/agent-chat/styles';
import type { DataCardView } from 'src/sections/agent-chat/useDataCardView';
import { colors } from 'src/theme';

/** The card's line while the fan-out's panel is open, which the card names as its description. */
export const DATA_LOCK_TEXT =
  '# the data waits while all libraries plot it · .close() the panel to change it';
const DATA_LOCK_ID = 'agent-data-lock';

export interface PinnedHeaderProps {
  state: AgentSessionState;
  view: DataCardView;
}

/**
 * The sticky header above the thread. The live region that says the step, which it held until
 * the v4 frame, stands by the status line at the frame's foot (`StepStatus`, `ChatFrame.tsx`).
 */
export function PinnedHeader({ state, view }: PinnedHeaderProps) {
  const { pinned, confirmed, expanded, open, toggle } = view;
  const dataset = state.dataset;
  const hasTranscription = !!state.transcription;
  return (
    <>
      {/* While the header sticks, the page's focus and scrolling land below it (WCAG 2.4.11). */}
      {pinned && <GlobalStyles styles={{ html: { scrollPaddingTop: PINNED_CLEARANCE } }} />}
      {pinned && dataset && (
        <Box
          data-testid="data-pinned"
          sx={{
            position: 'sticky',
            top: PINNED_TOP,
            zIndex: 10,
            // One row: at phone width the line wraps beside the toggle, never under it,
            // so the header stays two lines high at most.
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            // Back at step 1 the header reads as a warning. The amber token is too light
            // for text on the light page (1.6:1), so it tints the surface instead.
            bgcolor: confirmed
              ? 'var(--bg-elevated)'
              : `color-mix(in srgb, ${colors.warning} 18%, var(--bg-elevated))`,
            border: '1px solid var(--rule)',
            borderLeft: `3px solid ${confirmed ? colors.primary : colors.warning}`,
            borderRadius: 1,
            pl: 1.5,
            pr: 0.75,
            py: 0.5,
            minWidth: 0,
          }}
        >
          <Box
            data-testid="data-summary"
            sx={{
              ...labelSx,
              color: 'var(--ink)',
              flex: '1 1 auto',
              minWidth: 0,
              overflowWrap: 'anywhere',
            }}
          >
            <Box
              component="span"
              aria-hidden
              sx={{ color: confirmed ? colors.success : colors.warning, mr: 0.75 }}
            >
              {confirmed ? '✓' : '!'}
            </Box>
            {confirmed ? (
              `data fits · ${dataShape(dataset)}`
            ) : (
              <>
                {/* What to do, in bold: the warning reads in the words, not only the colour. */}
                <Box component="span" data-tone="warning" sx={{ fontWeight: 600 }}>
                  {hasTranscription ? 'decide on the table first' : 'check again'}
                </Box>
                {hasTranscription ? ': .use() or .discard()' : ` · ${dataShape(dataset)}`}
              </>
            )}
          </Box>
          <Box
            component="button"
            type="button"
            onClick={toggle}
            // Step 1 again: the card is open, and the button leads to it.
            aria-expanded={confirmed ? expanded : undefined}
            aria-controls={open ? 'agent-data-card' : undefined}
            aria-label={
              !confirmed ? 'Go to the data' : expanded ? 'Hide the data' : 'Show the data'
            }
            sx={{ ...actionButtonSx, flex: 'none' }}
          >
            {confirmed && expanded ? '.hide()' : '.show()'}
          </Box>
        </Box>
      )}
    </>
  );
}

export interface DataCardShellProps {
  view: DataCardView;
  locked: boolean;
  /** The composer's plot button as it reads now (`plotButtonLabel`), which step 1's line names. */
  plotLabel: string;
  /** The label on the card's border, what the data holds (`dataCardLabel`). */
  label: CardLabel;
  children: React.ReactNode;
}

/** The card's frame at its place in the thread: the section the header's button controls. */
export function DataCardShell({ view, locked, plotLabel, label, children }: DataCardShellProps) {
  return (
    <CardFrame
      component="section"
      label={label.text}
      spokenLabel={label.spoken}
      labelTestId="data-card-label"
      aria-label="Your data"
      aria-describedby={locked ? DATA_LOCK_ID : undefined}
      // The thread is a polite live log: a dropdown or a preview changing in the card is no news
      // to read out. The card's own status lines keep their roles.
      aria-live="off"
      id="agent-data-card"
      data-testid="data-card"
      ref={view.cardRef}
    >
      {/* Why every control below waits: the fan-out's sessions copy this data. */}
      {locked && (
        <Box
          id={DATA_LOCK_ID}
          data-testid="data-lock"
          sx={{ ...labelSx, color: 'var(--ink)', mb: 1.5 }}
        >
          {DATA_LOCK_TEXT}
        </Box>
      )}
      {/* With the header above, one line says what a change here does; the line stays when the
          confirmation drops, so the controls below it do not jump. */}
      {view.pinned && (
        <Box sx={{ ...labelSx, mb: 1.5 }}>
          {view.confirmed
            ? '# a change here takes the data back to step 1, where you check it and .create_plot() again'
            : `# step 1 again: check the data, then ${plotLabel} below`}
        </Box>
      )}
      {children}
    </CardFrame>
  );
}
