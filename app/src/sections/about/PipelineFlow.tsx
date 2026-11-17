import { useId } from 'react';

import Box from '@mui/material/Box';

import { PIPELINE_RULES, PIPELINE_STEPS, splitDetail } from 'src/sections/about/figureData';
import { codeBlockStyle, typography } from 'src/theme';

// The flow needs five columns as wide as "(up to 4 times)" at 13px (124.8px in MonoLisa) and four
// arrows between them, 712px inside the box: the 760px prose column holds it (728px inside), a
// narrower one does not. There the steps stand below one another, as the ASCII list did.
const FLOW_MIN_WIDTH = 712;
const ARROW_GAP = 22;
const STEP_COLUMN = 64;
const flow = `@container (min-width: ${FLOW_MIN_WIDTH}px)` as const;

const cellSx = {
  fontSize: '13px',
  lineHeight: 1.5,
  color: 'var(--ink-soft)',
  minWidth: 0,
  overflowWrap: 'anywhere',
} as const;

// Narrow, the name stands beside its action and my step; in the flow it heads its column above
// the rule.
const nameSx = {
  ...cellSx,
  color: 'var(--ink)',
  fontWeight: 500,
  gridRow: 'span 2',
  [flow]: {
    position: 'relative',
    gridRow: 1,
    fontSize: '14px',
    pb: 1,
    borderBottom: '1px solid var(--rule)',
  },
} as const;

// My own steps: the green the site gives text (--code-comment), which reaches 4.5:1 on the cream
// page where the brand green does not (style guide 4.4).
const meSx = { ...cellSx, color: 'var(--code-comment)', fontWeight: 500 } as const;

const arrowSx = {
  display: 'none',
  [flow]: {
    display: 'block',
    position: 'absolute',
    top: 0,
    bottom: '-1px',
    right: '100%',
    width: ARROW_GAP,
    textAlign: 'center',
    color: 'var(--ink-muted)',
    borderBottom: '1px solid var(--rule)',
  },
} as const;

/**
 * The pipeline of the about page: a flow of five steps with what ai does in each, my own steps in
 * green, and the rules under all of them. One ordered list, so a screen reader reads the steps in
 * order with their details; the arrows are drawn for the eye only.
 */
export function PipelineFlow() {
  const captionId = useId();
  return (
    <Box
      component="figure"
      aria-labelledby={captionId}
      sx={{
        ...codeBlockStyle,
        fontFamily: typography.mono,
        whiteSpace: 'normal',
        overflow: 'visible',
        m: 0,
        mt: 3,
        containerType: 'inline-size',
      }}
    >
      <Box
        id={captionId}
        sx={{ fontFamily: typography.mono, fontSize: '13px', color: 'var(--ink-muted)' }}
      >
        {'// pipeline'}
      </Box>
      <Box
        component="ol"
        sx={{
          listStyle: 'none',
          p: 0,
          m: 0,
          mt: 1.5,
          display: 'grid',
          rowGap: 1,
          [flow]: {
            mt: 1.75,
            gridTemplateColumns: 'repeat(5, minmax(0, 1fr))',
            columnGap: `${ARROW_GAP}px`,
            alignItems: 'start',
          },
        }}
      >
        {PIPELINE_STEPS.map(({ step, does, me }, i) => {
          const [action, detail] = splitDetail(does);
          return (
            <Box
              component="li"
              key={step}
              sx={{
                display: 'grid',
                gridTemplateColumns: `${STEP_COLUMN}px minmax(0, 1fr)`,
                columnGap: 1,
                alignItems: 'start',
                [flow]: {
                  gridRow: 'span 3',
                  gridTemplateRows: 'subgrid',
                  gridTemplateColumns: 'minmax(0, 1fr)',
                },
              }}
            >
              <Box sx={nameSx}>
                {i > 0 && (
                  <Box component="span" aria-hidden="true" sx={arrowSx}>
                    {step === 'fix' ? '⇄' : '→'}
                  </Box>
                )}
                {step}
              </Box>{' '}
              <Box
                sx={{
                  ...cellSx,
                  gridColumn: 2,
                  color: i === 0 ? 'var(--ink-muted)' : 'var(--ink-soft)',
                  [flow]: { gridColumn: 1, gridRow: 2 },
                }}
              >
                {action}
                {detail && (
                  <>
                    {' '}
                    <Box component="span" sx={{ display: 'block', color: 'var(--ink-muted)' }}>
                      {detail}
                    </Box>
                  </>
                )}
              </Box>
              {me && (
                <>
                  {' '}
                  <Box sx={{ ...meSx, gridColumn: 2, [flow]: { gridColumn: 1, gridRow: 3 } }}>
                    {me}
                  </Box>
                </>
              )}
            </Box>
          );
        })}
      </Box>
      <Box
        component="p"
        sx={{
          display: 'grid',
          gridTemplateColumns: `${STEP_COLUMN}px minmax(0, 1fr)`,
          columnGap: 1,
          m: 0,
          mt: 1,
          pt: 1,
          borderTop: '1px dashed var(--rule)',
          [flow]: {
            display: 'flex',
            alignItems: 'baseline',
            gap: 1.25,
            mt: 1.25,
            pt: 1.5,
          },
        }}
      >
        <Box component="span" sx={{ ...cellSx, color: 'var(--ink)', fontWeight: 500 }}>
          {PIPELINE_RULES.step}
        </Box>{' '}
        <Box
          component="span"
          aria-hidden="true"
          sx={{
            ...cellSx,
            display: 'none',
            color: 'var(--ink-muted)',
            [flow]: { display: 'inline' },
          }}
        >
          →
        </Box>{' '}
        <Box component="span" sx={meSx}>
          {PIPELINE_RULES.me}
        </Box>
      </Box>
    </Box>
  );
}
