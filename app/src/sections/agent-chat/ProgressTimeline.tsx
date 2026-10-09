/**
 * The progress of the running turn, from its `status` events: the wait in the
 * run queue (with the position), then the pipeline steps adapting, checking,
 * rendering, reviewing and, when the review asked for one, repairing. Steps
 * the run has not reached yet show in muted ink without a dot, so the path is
 * visible up front.
 */

import Box from '@mui/material/Box';

import type { RunState, TimelineStep } from 'src/hooks/useAgentSession';
import { labelSx } from 'src/sections/agent-chat/styles';
import { colors, fontSize, typography } from 'src/theme';

const EXPECTED: TimelineStep[] = ['adapting', 'checking', 'rendering', 'reviewing'];

function stepLabel(step: TimelineStep, attempt: number | null, run: RunState): string {
  if (step === 'queued') {
    return run.queue ? `queued · ${run.queue.position} of ${run.queue.waiting}` : 'queued';
  }
  return attempt && attempt > 1 ? `${step} · attempt ${attempt}` : step;
}

export function ProgressTimeline({ run }: { run: RunState }) {
  const reached = run.steps.map(entry => entry.step);
  const upcoming =
    run.kind === 'create_plot' ? EXPECTED.filter(step => !reached.includes(step)) : [];
  const current = run.steps.length - 1;

  return (
    <Box
      component="ol"
      aria-label="Progress"
      aria-live="polite"
      sx={{
        listStyle: 'none',
        m: 0,
        p: 0,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        columnGap: 1,
        rowGap: 0.5,
        fontFamily: typography.mono,
        fontSize: fontSize.md,
      }}
    >
      {run.steps.length === 0 && (
        <Box component="li" sx={{ color: 'var(--ink)' }}>
          {run.stopping ? 'stopping…' : 'starting…'}
        </Box>
      )}
      {run.steps.map((entry, index) => {
        const active = index === current;
        return (
          <Box
            component="li"
            key={`${entry.step}-${index}`}
            aria-current={active ? 'step' : undefined}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.5,
              color: active ? 'var(--ink)' : 'var(--ink-muted)',
            }}
          >
            <Box
              component="span"
              aria-hidden
              sx={{
                width: 7,
                height: 7,
                borderRadius: '50%',
                bgcolor: active ? colors.primary : 'var(--ink-muted)',
                opacity: active ? 1 : 0.5,
                flexShrink: 0,
              }}
            />
            {stepLabel(entry.step, entry.attempt, run)}
            {active && run.stopping ? ' · stopping…' : ''}
            {index < current || upcoming.length > 0 ? (
              <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', ml: 0.5 }}>
                →
              </Box>
            ) : null}
          </Box>
        );
      })}
      {upcoming.map((step, index) => (
        <Box component="li" key={step} sx={{ ...labelSx, fontSize: fontSize.md }}>
          {step}
          {index < upcoming.length - 1 ? (
            <Box component="span" aria-hidden sx={{ ml: 1 }}>
              →
            </Box>
          ) : null}
        </Box>
      ))}
    </Box>
  );
}
