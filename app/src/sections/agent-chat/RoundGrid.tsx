/**
 * The rounds of a plot run as a grid (`timeline.ts`): one row per round, its
 * label, the four steps in fixed columns so the same step of every round lines
 * up, and the round's outcome on the right (while a repair round runs, what it
 * repairs: `repairing layout, text size`; before a run's first step, where it
 * stands: `starting…`, `queued · 1 of 2`). A phone-width grid shows the short
 * step names without arrows and puts the round's label and outcome on a line
 * above its steps, so the four step columns stay aligned and fit a result card
 * on a 360 px screen (the card scrolls the grid sideways below that).
 *
 * Cells: a done step has a muted dot, the active one the primary dot, a failed
 * one a red ✗, a skipped one a hollow dot, a step still to come no dot. The
 * marker's slot has one width in every state, and the label column and the
 * first step column the width of their longest names, so a running grid stands
 * still while its steps advance and a repair round's row joins it; only its
 * outcome texts change.
 */

import Box from '@mui/material/Box';

import { type CellState, type GridRow, SHORT_STEP } from 'src/sections/agent-chat/timeline';
import { colors, fontSize, typography } from 'src/theme';

const TONE_COLOR = { ok: colors.primary, failed: colors.error, open: colors.warning } as const;

function MarkerShape({ state }: { state: CellState }) {
  if (state === 'failed') {
    return (
      <Box component="span" sx={{ color: colors.error, lineHeight: 1 }}>
        ✗
      </Box>
    );
  }
  if (state === 'upcoming') return null;
  return (
    <Box
      component="span"
      sx={{
        width: 7,
        height: 7,
        borderRadius: '50%',
        flexShrink: 0,
        boxSizing: 'border-box',
        ...(state === 'skipped'
          ? { border: '1px solid var(--ink-muted)', opacity: 0.6 }
          : {
              bgcolor: state === 'active' ? colors.primary : 'var(--ink-muted)',
              opacity: state === 'active' ? 1 : 0.5,
            }),
      }}
    />
  );
}

function Marker({ state }: { state: CellState }) {
  return (
    // One character wide in every state, the ✗ as much as a dot or no mark at all: a step that
    // turns active or fails would otherwise widen its column and push the steps after it right.
    <Box
      component="span"
      aria-hidden
      data-testid="step-marker"
      sx={{ width: '1ch', flexShrink: 0, display: 'inline-flex', justifyContent: 'center' }}
    >
      <MarkerShape state={state} />
    </Box>
  );
}

const STATE_WORD: Record<CellState, string> = {
  done: 'done',
  active: 'in progress',
  failed: 'failed',
  skipped: 'skipped',
  upcoming: 'next',
};

/** The widest round name (`second try`, `fourth try`), so the label column keeps its width when a repair round joins. */
const LABEL_WIDTH = '10ch';

/**
 * The first step column holds `adapting` in the first try and `repairing` in a repair round: the
 * longer name sets its width from the start, so the steps after it stay put when that row joins.
 */
const FIRST_STEP_WIDTH = {
  full: `${'repairing'.length}ch`,
  short: `${SHORT_STEP.repairing.length}ch`,
};

export function RoundGrid({
  rows,
  label,
  status = null,
}: {
  rows: GridRow[];
  label: string;
  /** Where a run stands before its first step (`starting…`), in the first row's outcome cell. */
  status?: string | null;
}) {
  return (
    <Box
      role="table"
      aria-label={label}
      sx={{
        display: 'grid',
        // Phone width: the steps alone set the columns; the label and the outcome share a line above them.
        gridTemplateColumns: { xs: 'repeat(4, auto) 1fr', sm: 'auto repeat(4, auto) 1fr' },
        columnGap: { xs: 0.75, sm: 1.5 },
        rowGap: { xs: 0.25, sm: 0.5 },
        alignItems: 'center',
        justifyContent: 'start',
        fontFamily: typography.mono,
        fontSize: { xs: fontSize.sm, sm: fontSize.md },
      }}
    >
      {rows.map((row, rowIndex) => {
        const running = row.outcome === null;
        const note = row.outcome?.text ?? row.repairs ?? (rowIndex === 0 ? status : null);
        // Explicit places, so every step sits in its column on both layouts.
        const line = { xs: 2 * rowIndex + 2, sm: rowIndex + 1 };
        const head = { xs: 2 * rowIndex + 1, sm: rowIndex + 1 };
        return (
          <Box role="row" key={row.attempt} sx={{ display: 'contents' }}>
            <Box
              role="rowheader"
              sx={{
                gridRow: head,
                gridColumn: { xs: '1 / 3', sm: '1' },
                mt: { xs: rowIndex ? 0.5 : 0, sm: 0 },
                // On a phone the label has a line of its own above the steps.
                minWidth: { xs: 0, sm: LABEL_WIDTH },
                color: running ? 'var(--ink)' : 'var(--ink-muted)',
                whiteSpace: 'nowrap',
              }}
            >
              {row.label}
            </Box>
            {row.cells.map((cell, index) => (
              <Box
                role="cell"
                key={cell.step}
                aria-current={cell.state === 'active' ? 'step' : undefined}
                aria-label={`${cell.step}, ${STATE_WORD[cell.state]}`}
                sx={{
                  gridRow: line,
                  gridColumn: { xs: `${index + 1}`, sm: `${index + 2}` },
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: { xs: 0.4, sm: 0.5 },
                  whiteSpace: 'nowrap',
                  color:
                    cell.state === 'active'
                      ? 'var(--ink)'
                      : cell.state === 'failed'
                        ? colors.error
                        : 'var(--ink-muted)',
                  opacity: cell.state === 'skipped' || cell.state === 'upcoming' ? 0.6 : 1,
                }}
              >
                <Marker state={cell.state} />
                <Box
                  component="span"
                  sx={{
                    display: { xs: 'none', sm: 'inline' },
                    minWidth: index === 0 ? FIRST_STEP_WIDTH.full : undefined,
                  }}
                >
                  {cell.step}
                </Box>
                <Box
                  component="span"
                  sx={{
                    display: { xs: 'inline', sm: 'none' },
                    minWidth: index === 0 ? FIRST_STEP_WIDTH.short : undefined,
                  }}
                >
                  {SHORT_STEP[cell.step]}
                </Box>
                {index < row.cells.length - 1 ? (
                  <Box
                    component="span"
                    aria-hidden
                    sx={{
                      color: 'var(--ink-muted)',
                      ml: 0.25,
                      display: { xs: 'none', sm: 'inline' },
                    }}
                  >
                    →
                  </Box>
                ) : null}
              </Box>
            ))}
            <Box
              role="cell"
              sx={{
                gridRow: head,
                gridColumn: { xs: '3 / -1', sm: '6' },
                mt: { xs: rowIndex ? 0.5 : 0, sm: 0 },
                // On a phone the outcome may wrap, so it never widens the step columns below it.
                minWidth: 0,
                whiteSpace: { xs: 'normal', sm: 'nowrap' },
                color: row.outcome
                  ? TONE_COLOR[row.outcome.tone]
                  : row.repairs
                    ? 'var(--ink-muted)'
                    : 'var(--ink)',
              }}
            >
              {note ?? ''}
            </Box>
          </Box>
        );
      })}
    </Box>
  );
}
