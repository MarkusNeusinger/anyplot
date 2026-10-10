import { describe, expect, it, vi } from 'vitest';

import { type AgentSessionState, initialAgentState } from 'src/hooks/useAgentSession';
import type { RoleSpec } from 'src/lib/agent';
import { bindingRows } from 'src/sections/agent-chat/bindings';
import { DataPanel } from 'src/sections/agent-chat/DataPanel';
import { render, screen, userEvent } from 'src/test-utils';

const role = (name: string, overrides: Partial<RoleSpec> = {}): RoleSpec => ({
  name,
  kinds: ['numeric'],
  required: true,
  variadic: false,
  description: `${name} values`,
  ...overrides,
});

// line-multi: `x`, the series family `y1, y2, ...` and an optional `series`.
const ROLES = [
  role('x', { kinds: ['numeric', 'datetime'] }),
  role('y', { variadic: true, description: 'Multiple continuous series to compare' }),
  role('series', { kinds: ['categorical'], required: false }),
];

const COLUMNS = ['month', 'shoes', 'hats', 'scarves', 'region'].map(name => ({
  name,
  dtype: name === 'region' ? ('text' as const) : ('number' as const),
  missing: 0,
  unique: 3,
}));

function stateWith(bindings: Record<string, string>, overrides: Partial<AgentSessionState> = {}) {
  return {
    ...initialAgentState('matplotlib'),
    phase: 'ready' as const,
    sessionId: 'S1',
    dataset: {
      bytes: 100,
      parsed: {
        preview: [['2026-01', '1', '2', '3', 'north']],
        profile: {
          rows: 1,
          columns: COLUMNS,
          source_format: 'csv',
          decimal: '.',
          warnings: [],
        },
        bindings: [],
        warnings: [],
        roles: ROLES,
      },
    },
    roles: ROLES,
    bindings,
    bindingsComplete: true,
    ...overrides,
  };
}

describe('bindingRows', () => {
  it('gives every role a row and each family its members plus the next one', () => {
    const rows = bindingRows(ROLES, { x: 'month', y1: 'shoes', y2: 'hats' }, COLUMNS.length);
    expect(rows.map(row => [row.name, row.first, row.next])).toEqual([
      ['x', true, false],
      ['y1', true, false],
      ['y2', false, false],
      ['y3', false, true],
      ['series', true, false],
    ]);
  });

  it('shows a required family without a member as its first member', () => {
    const rows = bindingRows(ROLES, { x: 'month' }, COLUMNS.length);
    expect(rows.filter(row => row.role.name === 'y').map(row => [row.name, row.next])).toEqual([
      ['y1', false],
    ]);
  });

  it('stops offering members when every column is taken', () => {
    const rows = bindingRows([ROLES[1]], { y1: 'a', y2: 'b' }, 2);
    expect(rows.map(row => row.name)).toEqual(['y1', 'y2']);
  });
});

describe('DataPanel bindings', () => {
  it('marks required roles, names the kinds and binds the next family member', async () => {
    const onBind = vi.fn();
    render(
      <DataPanel
        state={stateWith({ x: 'month', y1: 'shoes' }, { missingRoles: [] })}
        onParse={vi.fn()}
        onBind={onBind}
        onCreatePlot={vi.fn()}
      />
    );
    expect(screen.getByText('numeric / datetime')).toBeInTheDocument();
    expect(screen.getByText('numeric · one column each')).toBeInTheDocument();
    expect(screen.getByLabelText(/^series/)).toHaveValue('');
    // The spec's own description is the role's tooltip; required roles carry a `*`.
    expect(screen.getAllByTitle('Multiple continuous series to compare')[0]).toHaveTextContent(
      /^y1 \*/
    );
    expect(screen.getByTitle('series values')).not.toHaveTextContent('*');
    await userEvent.selectOptions(screen.getByLabelText('y2'), 'hats');
    expect(onBind).toHaveBeenCalledWith('y2', 'hats');
  });

  it('lists the lines of a refused binding set', () => {
    render(
      <DataPanel
        state={stateWith(
          { x: 'month' },
          {
            bindingsError: {
              code: 'invalid',
              ref: 'r-b',
              errors: ["role 'x' needs numeric or datetime data, but column 'region' is text"],
            },
          }
        )}
        onParse={vi.fn()}
        onBind={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    expect(screen.getByRole('alert')).toHaveTextContent('the server refused these bindings');
    expect(
      screen.getByText("role 'x' needs numeric or datetime data, but column 'region' is text")
    ).toBeInTheDocument();
  });

  it('holds back create and parse while a theme renders', () => {
    render(
      <DataPanel
        state={stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true })}
        onParse={vi.fn()}
        onBind={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: '.create_plot()' })).toBeDisabled();
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
  });
});
