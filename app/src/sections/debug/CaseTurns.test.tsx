/**
 * The case detail's turn matrix on invented records: a row per turn with its
 * chips, the details a click opens, and the empty states.
 */

import { describe, expect, it } from 'vitest';

import type { AgentCaseTurn } from 'src/lib/agent';
import { CaseTurns } from 'src/sections/debug/CaseTurns';
import { render, screen, userEvent, within } from 'src/test-utils';

const turn = (overrides: Partial<AgentCaseTurn>): AgentCaseTurn => ({
  turn: 1,
  action: 'text',
  kind: 'talk',
  refusal: null,
  error: null,
  tools: [],
  tools_dropped: 0,
  guards: [{ guard: 'scope_guard', verdict: 'in_scope' }],
  guards_dropped: 0,
  prep_ops: [],
  prep_ops_dropped: 0,
  ...overrides,
});

const RECORDS = [
  turn({}),
  turn({
    turn: 2,
    kind: 'prep',
    tools: [
      { tool: 'prepare_data', verdict: 'allowed', outcome: 'error', code: 'invalid_operations' },
      { tool: 'prepare_data', verdict: 'allowed', outcome: 'changed', code: null },
    ],
    tools_dropped: 1,
    prep_ops: ['derive'],
  }),
  turn({
    turn: 3,
    kind: 'refused',
    refusal: 'rate_limited',
    guards: [{ guard: 'message_limit', verdict: 'rate_limited' }],
  }),
  turn({ turn: 3, action: 'create_plot', kind: 'plot' }),
];

describe('CaseTurns', () => {
  it('shows one row per turn and opens its whole record on a click', async () => {
    const user = userEvent.setup();
    render(<CaseTurns turns={{ records: RECORDS, dropped: 0 }} />);

    expect(screen.getByText('4 turns · 2 flagged')).toBeInTheDocument();
    const rows = within(screen.getByRole('list', { name: 'Turns' })).getAllByRole('button');
    expect(rows).toHaveLength(4);
    expect(rows[0]).toHaveTextContent('no tool call, no guard fired');
    expect(rows[1]).toHaveTextContent('prepare_data: error · invalid_operations');
    expect(rows[2]).toHaveTextContent('message_limit: rate_limited');
    expect(rows[3]).toHaveTextContent('create_plot');

    await user.click(rows[1]);
    expect(rows[1]).toHaveAttribute('aria-expanded', 'true');
    const details = document.getElementById(rows[1].getAttribute('aria-controls') ?? '');
    expect(details).not.toBeNull();
    const panel = within(details as HTMLElement);
    expect(panel.getByText('message → prep')).toBeInTheDocument();
    expect(panel.getByText('scope_guard: in_scope')).toBeInTheDocument();
    expect(panel.getByText('1 later call not recorded')).toBeInTheDocument();
    expect(panel.getByText('derive')).toBeInTheDocument();

    // The turn refused before the judge shares its number with the next one, and says so.
    await user.click(rows[2]);
    expect(screen.getByText(/2 records share turn 3/)).toBeInTheDocument();

    await user.click(rows[1]);
    expect(rows[1]).toHaveAttribute('aria-expanded', 'false');
    expect(screen.queryByText('message → prep')).not.toBeInTheDocument();
  });

  it('lists the shape of each call under it', async () => {
    const user = userEvent.setup();
    const asked = {
      tool: 'query_data',
      verdict: 'allowed',
      outcome: 'ok',
      code: null,
      shape: {
        operations: [
          {
            op: 'keep_rows',
            mode: 'where',
            target: null,
            order: null,
            conditions: [{ test: 'gt', value_shape: 'number', column_kind: 'integer' }],
            how: null,
            period: null,
            keys: null,
            type: null,
            date_format: null,
            decimal: null,
            unit: null,
            keep: null,
            family: null,
          },
        ],
        from_version: 'current',
        limit: true,
        base: null,
        theme: null,
        combine: null,
        change_request: null,
        expected_texts: null,
        remember: null,
        applies_to: null,
        plot: null,
      },
    };
    const profile = { tool: 'get_dataset_profile', verdict: 'allowed', outcome: 'ok', code: null };
    render(<CaseTurns turns={{ records: [turn({ tools: [asked, profile] })], dropped: 0 }} />);

    const row = screen.getByRole('button');
    await user.click(row);

    const details = document.getElementById(row.getAttribute('aria-controls') ?? '');
    expect(details).not.toBeNull();
    const panel = within(details as HTMLElement);
    expect(panel.getByText('from_version: current · limit: named')).toBeInTheDocument();
    expect(
      panel.getByText('keep_rows · mode: where · conditions: integer column gt number value')
    ).toBeInTheDocument();
    // A call without a shape has no lines under it.
    expect(panel.getByText('get_dataset_profile').querySelector('ul')).toBeNull();
    expect((details as HTMLElement).querySelectorAll('ol > li ul li')).toHaveLength(2);
  });

  it('names what a bound left out without an empty list', async () => {
    const user = userEvent.setup();
    const record = turn({ guards: [], guards_dropped: 3 });
    render(<CaseTurns turns={{ records: [record], dropped: 0 }} />);

    await user.click(screen.getByRole('button'));

    expect(screen.getByText('3 earlier verdicts not recorded')).toBeInTheDocument();
    // Calls and prep ops read `none`; the guards' entry holds its note alone.
    expect(screen.getAllByText('none')).toHaveLength(2);
    expect(document.querySelectorAll('dl ol')).toHaveLength(0);
  });

  it('says why a case has no rows', () => {
    const { rerender } = render(<CaseTurns turns={null} />);
    expect(screen.getByText(/no turn record: this case was sent before/)).toBeInTheDocument();
    rerender(<CaseTurns turns={{ records: [], dropped: 0 }} />);
    expect(screen.getByText(/no turn recorded/)).toBeInTheDocument();
    rerender(<CaseTurns turns={{ records: [], dropped: 60 }} />);
    expect(screen.getByText("the record kept none of the session's 60 turns")).toBeInTheDocument();
  });
});
