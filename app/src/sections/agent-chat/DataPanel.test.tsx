import { describe, expect, it, vi } from 'vitest';

import {
  type AgentSessionState,
  initialAgentState,
  type TranscriptionState,
} from 'src/hooks/useAgentSession';
import type { RoleSpec } from 'src/lib/agent';
import { bindingRows } from 'src/sections/agent-chat/bindings';
import { DataPanel } from 'src/sections/agent-chat/DataPanel';
import { render, screen, userEvent, within } from 'src/test-utils';

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
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={onBind}
        onConfirmData={vi.fn()}
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
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    expect(screen.getByRole('alert')).toHaveTextContent('the server refused these bindings');
    expect(
      screen.getByText("role 'x' needs numeric or datetime data, but column 'region' is text")
    ).toBeInTheDocument();
  });

  it('holds back confirm, create and parse while a theme renders', () => {
    const panel = (state: AgentSessionState) => (
      <DataPanel
        state={state}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    const { rerender } = render(panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true })));
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeDisabled();
    expect(screen.getByLabelText(/^x/)).toBeDisabled();

    rerender(
      panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true, dataConfirmed: true }))
    );
    expect(screen.getByRole('button', { name: '.create_plot()' })).toBeDisabled();
  });

  it('holds back the confirmation while a table read from text awaits its decision', () => {
    // The stored dataset and its bindings stay, but the user decides on the data first.
    render(
      <DataPanel
        state={stateWith({ x: 'month', y1: 'shoes' }, { transcription: TRANSCRIPTION })}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: '.create_plot()' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '.parse()' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '.use()' })).toBeEnabled();
  });
});

describe('DataPanel steps', () => {
  function renderPanel(state: AgentSessionState) {
    const onConfirmData = vi.fn();
    const onCreatePlot = vi.fn();
    const panel = (next: AgentSessionState) => (
      <DataPanel
        state={next}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={onConfirmData}
        onCreatePlot={onCreatePlot}
      />
    );
    const view = render(panel(state));
    return {
      onConfirmData,
      onCreatePlot,
      rerender: (next: AgentSessionState) => view.rerender(panel(next)),
    };
  }

  it('offers .confirm() once every required role has a column, and no .create_plot()', async () => {
    const { onConfirmData, rerender } = renderPanel(
      stateWith({ x: 'month' }, { bindingsComplete: false, missingRoles: ['y'] })
    );
    const confirm = screen.getByRole('button', { name: '.confirm()' });
    expect(confirm).toBeDisabled();
    expect(confirm).toHaveAccessibleDescription(
      '# step 1 — check the preview and the bindings, then confirm'
    );
    expect(screen.queryByRole('button', { name: '.create_plot()' })).not.toBeInTheDocument();

    rerender(stateWith({ x: 'month', y1: 'shoes' }));
    await userEvent.click(screen.getByRole('button', { name: '.confirm()' }));
    expect(onConfirmData).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('button', { name: '.create_plot()' })).not.toBeInTheDocument();

    // The confirmation in flight: the button says so and holds still.
    rerender(stateWith({ x: 'month', y1: 'shoes' }, { confirmBusy: true }));
    expect(screen.getByRole('button', { name: '.confirm() …' })).toBeDisabled();
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
  });

  it("shows the data's shape and .create_plot() after the confirmation", async () => {
    const { onCreatePlot } = renderPanel(
      stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true })
    );
    expect(screen.getByTestId('data-step')).toHaveTextContent('data fits · 1 row · 5 columns');
    expect(screen.queryByRole('button', { name: '.confirm()' })).not.toBeInTheDocument();
    const create = screen.getByRole('button', { name: '.create_plot()' });
    expect(create).toHaveAccessibleDescription('data fits · 1 row · 5 columns');
    await userEvent.click(create);
    expect(onCreatePlot).toHaveBeenCalledTimes(1);
  });

  it('names the reason of a refused confirmation', () => {
    renderPanel(
      stateWith({ x: 'month', y1: 'shoes' }, { confirmError: { code: 'no_dataset', ref: 'r-c' } })
    );
    expect(screen.getByRole('alert')).toHaveTextContent('parse the data first · ref r-c');
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeEnabled();
  });
});

// "Hund 7 Katze 3 und Vogel 4", read by the model into a table.
const TRANSCRIPTION: TranscriptionState = {
  text: 'animal,count\nHund,7\nKatze,3\nVogel,4\n',
  preview: [
    ['Hund', '7'],
    ['Katze', '3'],
    ['Vogel', '4'],
  ],
  profile: {
    rows: 3,
    columns: [
      { name: 'animal', dtype: 'text', missing: 0, unique: 3 },
      { name: 'count', dtype: 'integer', missing: 0, unique: 3 },
    ],
    source_format: 'csv',
    decimal: '.',
    warnings: [],
  },
  warnings: ['column count has only 3 values'],
  note: 'read "und" as a separator, not as an animal',
  bytes: 26,
};

function transcribedState(overrides: Partial<AgentSessionState> = {}): AgentSessionState {
  return {
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
    transcription: TRANSCRIPTION,
    ...overrides,
  };
}

describe('DataPanel transcription', () => {
  it('shows the table read from the text with its note and warnings', () => {
    render(
      <DataPanel
        state={transcribedState()}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    const card = within(screen.getByTestId('transcription-card'));
    expect(card.getByText('# read from your text — 3 rows, 2 columns')).toBeInTheDocument();
    expect(card.getByText('read "und" as a separator, not as an animal')).toBeInTheDocument();
    expect(card.getByText('column count has only 3 values')).toBeInTheDocument();
    expect(card.getAllByRole('columnheader').map(th => th.textContent)).toEqual([
      'animaltext',
      'countinteger',
    ]);
    expect(card.getAllByRole('row')).toHaveLength(4);
    expect(card.getByRole('cell', { name: 'Katze' })).toBeInTheDocument();
    // Nothing is stored yet: no bindings and no `.create_plot()`.
    expect(screen.queryByRole('button', { name: '.create_plot()' })).not.toBeInTheDocument();
  });

  it('leaves the note out when the model had none and names one row in the singular', () => {
    render(
      <DataPanel
        state={transcribedState({
          transcription: {
            ...TRANSCRIPTION,
            note: '',
            warnings: [],
            preview: [['Hund', '7']],
            profile: { ...TRANSCRIPTION.profile, rows: 1 },
          },
        })}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    expect(screen.getByText('# read from your text — 1 row, 2 columns')).toBeInTheDocument();
    expect(screen.queryByText('# note from the model')).not.toBeInTheDocument();
    expect(screen.queryByText('# warnings')).not.toBeInTheDocument();
  });

  it('.use() confirms and puts the CSV into the text box; .discard() drops it', async () => {
    const onConfirm = vi.fn();
    const onDiscard = vi.fn();
    render(
      <DataPanel
        state={transcribedState()}
        onParse={vi.fn()}
        onConfirmTranscription={onConfirm}
        onDiscardTranscription={onDiscard}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    const textbox = screen.getByLabelText(/# your data/);
    await userEvent.type(textbox, 'Hund 7 Katze 3 und Vogel 4');
    await userEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(onDiscard).toHaveBeenCalledTimes(1);
    expect(textbox).toHaveValue('Hund 7 Katze 3 und Vogel 4');

    await userEvent.click(screen.getByRole('button', { name: '.use()' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(textbox).toHaveValue(TRANSCRIPTION.text);
  });

  it('holds back .parse() until the user decides, and .use() while the session is busy', async () => {
    const onParse = vi.fn();
    const panel = (state: AgentSessionState) => (
      <DataPanel
        state={state}
        onParse={onParse}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onCreatePlot={vi.fn()}
      />
    );
    const { rerender } = render(panel(transcribedState()));
    await userEvent.type(screen.getByLabelText(/# your data/), 'animal,count');
    const parse = screen.getByRole('button', { name: '.parse()' });
    expect(parse).toBeDisabled();
    expect(parse).toHaveAccessibleDescription(
      'decide on the table below first: .use() or .discard()'
    );
    expect(screen.getByRole('button', { name: '.use()' })).toBeEnabled();

    // A theme render in flight: the confirmation's parse would race it.
    rerender(panel(transcribedState({ themeBusy: true })));
    expect(screen.getByRole('button', { name: '.use()' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '.discard()' })).toBeEnabled();

    rerender(panel(transcribedState({ transcription: null })));
    expect(screen.queryByTestId('transcription-card')).not.toBeInTheDocument();
    expect(screen.queryByText(/decide on the table/)).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(onParse).toHaveBeenCalledWith('animal,count');
  });
});
