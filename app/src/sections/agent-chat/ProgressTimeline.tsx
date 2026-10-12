/**
 * The progress of the running turn, from its `status` events: the wait in the
 * run queue (with the position), then the pipeline steps of the current round.
 * The first try runs adapting, checking, rendering and reviewing; a repair
 * round, when the checks or the review asked for one, runs repairing,
 * checking, rendering and reviewing. Steps the round has not reached yet show
 * in muted ink without a dot, so the path is visible up front.
 *
 * A finished round folds into one entry (`first try done`); the entries come
 * from `timelineItems` in `timeline.ts`.
 *
 * The page mounts it for a `create_plot` run and for any turn that waits in
 * the queue or reached a pipeline step (`showsTimeline` in `steps.ts`). A turn
 * without steps, the summary or a question, has the thread's in-progress line
 * instead, so `starting…` and a step-less `stopping…` belong to plot runs.
 */

import Box from '@mui/material/Box';

import type { RunState } from 'src/hooks/useAgentSession';
import { labelSx } from 'src/sections/agent-chat/styles';
import { timelineItems } from 'src/sections/agent-chat/timeline';
import { colors, fontSize, typography } from 'src/theme';

const arrow = (
  <Box component="span" aria-hidden sx={{ color: 'var(--ink-muted)', ml: 0.5 }}>
    →
  </Box>
);

export function ProgressTimeline({ run }: { run: RunState }) {
  const items = timelineItems(run);
  const active = items.find(item => item.state === 'active');

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
      {items.length === 0 && (
        <Box component="li" sx={{ color: 'var(--ink)' }}>
          {run.stopping ? 'stopping…' : 'starting…'}
        </Box>
      )}
      {items.map((item, index) => {
        const more = index < items.length - 1;
        if (item.state === 'upcoming') {
          return (
            <Box component="li" key={item.key} sx={{ ...labelSx, fontSize: fontSize.md }}>
              {item.label}
              {more ? arrow : null}
            </Box>
          );
        }
        const isActive = item === active;
        return (
          <Box
            component="li"
            key={item.key}
            aria-current={isActive ? 'step' : undefined}
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.5,
              color: isActive ? 'var(--ink)' : 'var(--ink-muted)',
            }}
          >
            {item.state !== 'done' && (
              <Box
                component="span"
                aria-hidden
                sx={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  bgcolor: isActive ? colors.primary : 'var(--ink-muted)',
                  opacity: isActive ? 1 : 0.5,
                  flexShrink: 0,
                }}
              />
            )}
            {item.label}
            {/* A stopped run ends at its next step boundary; the server's `done` confirms it. */}
            {isActive && run.stopping
              ? item.key.startsWith('queued')
                ? ' · leaving the queue…'
                : ' · stopping after this step…'
              : ''}
            {more ? arrow : null}
          </Box>
        );
      })}
    </Box>
  );
}
