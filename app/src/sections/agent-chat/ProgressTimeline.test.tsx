import { describe, expect, it } from 'vitest';

import type { RunState, TimelineStep } from 'src/hooks/useAgentSession';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import { roundLabel, timelineItems } from 'src/sections/agent-chat/timeline';
import { render, screen, within } from 'src/test-utils';

function run(steps: [TimelineStep, number | null][], extra: Partial<RunState> = {}): RunState {
  return {
    kind: 'create_plot',
    steps: steps.map(([step, attempt]) => ({ step, attempt })),
    queue: null,
    stopping: false,
    ...extra,
  };
}

const labels = (state: RunState) => timelineItems(state).map(item => `${item.state}:${item.label}`);

describe('ProgressTimeline', () => {
  it('shows the first try with its next steps', () => {
    expect(
      labels(
        run([
          ['adapting', 1],
          ['checking', 1],
        ])
      )
    ).toEqual(['past:adapting', 'active:checking', 'upcoming:rendering', 'upcoming:reviewing']);
  });

  it('folds the first try into one entry once the repair round starts', () => {
    // The owner's screenshot of 2026-10-12: every step again with "· attempt 2" read as many runs.
    const state = run([
      ['adapting', 1],
      ['checking', 1],
      ['rendering', 1],
      ['reviewing', 1],
      ['repairing', 2],
      ['checking', 2],
      ['rendering', 2],
    ]);

    expect(labels(state)).toEqual([
      'done:first try done',
      'past:repairing',
      'past:checking',
      'active:rendering',
      'upcoming:reviewing',
    ]);
    render(<ProgressTimeline run={state} />);
    const items = within(screen.getByRole('list', { name: 'Progress' })).getAllByRole('listitem');
    expect(items.map(item => item.textContent)).toEqual([
      'first try done→',
      'repairing→',
      'checking→',
      'rendering→',
      'reviewing',
    ]);
    expect(screen.queryByText(/attempt/)).not.toBeInTheDocument();
    expect(items[3]).toHaveAttribute('aria-current', 'step');
  });

  it('folds a first try that failed its checks the same way', () => {
    expect(
      labels(
        run([
          ['adapting', 1],
          ['checking', 1],
          ['repairing', 2],
        ])
      )
    ).toEqual([
      'done:first try done',
      'active:repairing',
      'upcoming:checking',
      'upcoming:rendering',
      'upcoming:reviewing',
    ]);
  });

  it('keeps the queue in front and shows its position while waiting', () => {
    expect(labels(run([['queued', null]], { queue: { position: 2, waiting: 3 } }))).toEqual([
      'active:queued · 2 of 3',
      'upcoming:adapting',
      'upcoming:checking',
      'upcoming:rendering',
      'upcoming:reviewing',
    ]);
    expect(
      labels(
        run([
          ['queued', null],
          ['adapting', 1],
        ])
      )[0]
    ).toBe('past:queued');
  });

  it('lists no next steps for a turn that is not a plot run', () => {
    expect(labels(run([['adapting', 1]], { kind: 'message' }))).toEqual(['active:adapting']);
  });

  it('names the rounds', () => {
    expect([1, 2, 3].map(roundLabel)).toEqual(['first try', 'repair 1', 'repair 2']);
  });

  it('says it is stopping after the current step', () => {
    render(
      <ProgressTimeline
        run={run(
          [
            ['adapting', 1],
            ['repairing', 2],
          ],
          { stopping: true }
        )}
      />
    );
    expect(screen.getByText(/repairing · stopping after this step…/)).toBeInTheDocument();
  });
});
