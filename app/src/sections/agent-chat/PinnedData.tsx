/**
 * Sticky pinned summary header and card shell for the agent chat's data panel
 * (`DataPanel.tsx`).
 *
 * Once the data has been confirmed at least once, the sticky header stays at
 * the top of the thread (`✓ data fits · …` in step 2, `! confirm again · …`
 * when a change takes the session back to step 1) and toggles or scrolls to the
 * full data card below it.
 */

import Box from '@mui/material/Box';
import GlobalStyles from '@mui/material/GlobalStyles';

import type { AgentSessionState } from 'src/hooks/useAgentSession';
import { countOf } from 'src/sections/agent-chat/countOf';
import {
  actionButtonSx,
  cardSx,
  labelSx,
  PINNED_CLEARANCE,
  PINNED_TOP,
} from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

/** The line the pinned header shows, and `.create_plot()` names as its description. */
export const DATA_SUMMARY_ID = 'agent-data-summary';

/** The card's line while the fan-out's panel is open, which the card names as its description. */
export const DATA_LOCK_TEXT =
  '# the data waits while all libraries plot it · .close() the panel to change it';
const DATA_LOCK_ID = 'agent-data-lock';

/** The data's shape in one line: `2 rows · 2 columns · version 1`. */
function dataShape(dataset: NonNullable<AgentSessionState['dataset']>): string {
  const { profile, version } = dataset.parsed;
  return `${countOf(profile.rows, 'row')} · ${countOf(profile.columns.length, 'column')} · version ${version ?? 1}`;
}

export interface PinnedDataProps {
  pinned: boolean;
  confirmed: boolean;
  expanded: boolean;
  open: boolean;
  locked: boolean;
  dataset: AgentSessionState['dataset'];
  hasTranscription: boolean;
  toggleRef?: React.Ref<HTMLButtonElement>;
  cardRef: React.RefObject<HTMLElement | null>;
  onToggle: () => void;
  children: React.ReactNode;
}

export function PinnedData({
  pinned,
  confirmed,
  expanded,
  open,
  locked,
  dataset,
  hasTranscription,
  toggleRef,
  cardRef,
  onToggle,
  children,
}: PinnedDataProps) {
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
            id={DATA_SUMMARY_ID}
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
                  {hasTranscription ? 'decide on the table first' : 'confirm again'}
                </Box>
                {hasTranscription ? ': .use() or .discard()' : ` · ${dataShape(dataset)}`}
              </>
            )}
          </Box>
          <Box
            component="button"
            type="button"
            ref={toggleRef}
            onClick={onToggle}
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

      {open && (
        <Box
          component="section"
          aria-label="Your data"
          aria-describedby={locked ? DATA_LOCK_ID : undefined}
          id="agent-data-card"
          data-testid="data-card"
          ref={cardRef}
          sx={cardSx}
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
          {/* With the header above it, one line says what a change here does; the line
              stays when the confirmation drops, so the controls below it do not jump. */}
          {pinned && (
            <Box sx={{ ...labelSx, mb: 1.5 }}>
              {confirmed
                ? '# a change here takes the data back to step 1, where you confirm it again'
                : '# step 1 again: check the data, then confirm it below'}
            </Box>
          )}
          {children}
        </Box>
      )}
    </>
  );
}
