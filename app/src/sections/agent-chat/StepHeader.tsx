/**
 * The two steps of "Use with my data" as one quiet mono line above the panels:
 * `1 data · 2 plot`, the current step emphasised. Step 1 lasts until the user
 * confirms the data with `.confirm()`; a new parse or a binding change goes
 * back to it. It stays one line at phone width.
 */

import Box from '@mui/material/Box';

import { labelSx } from 'src/sections/agent-chat/styles';

export type AgentStep = 1 | 2;

const STEPS: { step: AgentStep; label: string }[] = [
  { step: 1, label: 'data' },
  { step: 2, label: 'plot' },
];

export function StepHeader({ current }: { current: AgentStep }) {
  return (
    <Box
      component="ol"
      aria-label="Steps"
      data-testid="agent-steps"
      sx={{
        ...labelSx,
        display: 'flex',
        flexWrap: 'nowrap',
        alignItems: 'baseline',
        whiteSpace: 'nowrap',
        listStyle: 'none',
        m: 0,
        mb: 1.5,
        p: 0,
      }}
    >
      {STEPS.map(({ step, label }, index) => {
        const active = step === current;
        return (
          <Box
            key={step}
            component="li"
            aria-current={active ? 'step' : undefined}
            sx={{
              color: active ? 'var(--ink)' : 'var(--ink-muted)',
              fontWeight: active ? 600 : 400,
            }}
          >
            {index > 0 && (
              <Box
                component="span"
                aria-hidden
                sx={{ color: 'var(--ink-muted)', fontWeight: 400, mx: 1 }}
              >
                ·
              </Box>
            )}
            {step} {label}
          </Box>
        );
      })}
    </Box>
  );
}
