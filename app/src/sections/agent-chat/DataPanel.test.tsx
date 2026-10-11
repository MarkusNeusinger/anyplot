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

/** `scrollIntoView` as a spy: jsdom has none. */
function stubScrollIntoView() {
  const scroll = vi.fn();
  Object.defineProperty(Element.prototype, 'scrollIntoView', {
    value: scroll,
    configurable: true,
    writable: true,
  });
  return scroll;
}

function restoreScrollIntoView() {
  delete (Element.prototype as Partial<Element>).scrollIntoView;
}

/** The options of every `scrollIntoView` call on `element`. */
const scrolledTo = (scroll: ReturnType<typeof vi.fn>, element: Element) =>
  scroll.mock.contexts.flatMap((context, index) =>
    context === element ? [scroll.mock.calls[index][0]] : []
  );

/** Whether the page's styles hold the pinned header's scroll padding (40 + 64 px). */
const scrollPaddingRule = () =>
  [...document.querySelectorAll('style')].some(style =>
    /scroll-padding-top:\s*104px/.test(style.textContent ?? '')
  );

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
        version: 1,
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
        onSendFormula={vi.fn()}
        onBind={onBind}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
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
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    expect(screen.getByRole('alert')).toHaveTextContent('the server refused these bindings');
    expect(
      screen.getByText("role 'x' needs numeric or datetime data, but column 'region' is text")
    ).toBeInTheDocument();
  });

  it('holds back confirm, the bindings and parse while a theme renders, in both steps', async () => {
    const panel = (state: AgentSessionState) => (
      <DataPanel
        state={state}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const { rerender } = render(panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true })));
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeDisabled();
    expect(screen.getByLabelText(/^x/)).toBeDisabled();

    // Step 2: opening the card is only a look, so it works, but nothing in it starts.
    rerender(
      panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true, dataConfirmed: true }))
    );
    await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
    await userEvent.type(screen.getByLabelText(/# your data/), 'a,b');
    expect(screen.getByRole('button', { name: '.parse()' })).toBeDisabled();
  });

  it('holds back the confirmation while a table read from text awaits its decision', () => {
    // The stored dataset and its bindings stay, but the user decides on the data first.
    render(
      <DataPanel
        state={stateWith({ x: 'month', y1: 'shoes' }, { transcription: TRANSCRIPTION })}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '.parse()' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '.use()' })).toBeEnabled();
  });
});

describe('DataPanel steps', () => {
  function renderPanel(state: AgentSessionState) {
    const onConfirmData = vi.fn();
    const panel = (next: AgentSessionState) => (
      <DataPanel
        state={next}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={onConfirmData}
        onUndo={vi.fn()}
      />
    );
    const view = render(panel(state));
    return {
      onConfirmData,
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
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();

    rerender(stateWith({ x: 'month', y1: 'shoes' }));
    await userEvent.click(screen.getByRole('button', { name: '.confirm()' }));
    expect(onConfirmData).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();

    // The confirmation in flight: the button says so and holds still.
    rerender(stateWith({ x: 'month', y1: 'shoes' }, { confirmBusy: true }));
    expect(screen.getByRole('button', { name: '.confirm() …' })).toBeDisabled();
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
  });

  it('collapses into the pinned header after the confirmation, which .show() opens', async () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true }));
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'data fits · 1 row · 5 columns · version 1'
    );
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 2: the data is confirmed; create the plot below'
    );
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '.confirm()' })).not.toBeInTheDocument();
    // Step 2's action is the page composer's, not the card's.
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    const card = within(screen.getByRole('region', { name: 'Your data' }));
    expect(card.getByText(/a change here takes the data back to step 1/)).toBeInTheDocument();
    expect(card.getByLabelText(/^x/)).toBeEnabled();
    expect(card.queryByRole('button', { name: '.confirm()' })).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Hide the data' }));
    expect(screen.queryByRole('region', { name: 'Your data' })).not.toBeInTheDocument();
  });

  it('opens in full when the confirmation drops, and collapses at the next .confirm()', async () => {
    const scroll = stubScrollIntoView();
    try {
      const confirmed = stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true });
      const { onConfirmData, rerender } = renderPanel(confirmed);
      await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));

      // A binding change, a data change or an undo: the server dropped the confirmation.
      // The header stays and says so, and the line above the card stays in its place.
      rerender({ ...confirmed, dataConfirmed: false });
      expect(screen.getByTestId('data-summary')).toHaveTextContent(
        'confirm again · 1 row · 5 columns · version 1'
      );
      expect(
        screen.getByText('# step 1 again: check the data, then confirm it below')
      ).toBeVisible();
      expect(screen.queryByText(/a change here takes the data back/)).not.toBeInTheDocument();
      expect(screen.getByTestId('data-step-status')).toHaveTextContent(
        'step 1: check the data, then confirm it'
      );
      // The card is open in step 1 anyway: the header's button leads to its top.
      const go = screen.getByRole('button', { name: 'Go to the data' });
      expect(go).toHaveTextContent('.show()');
      expect(go).not.toHaveAttribute('aria-expanded');
      scroll.mockClear();
      await userEvent.click(go);
      expect(scrolledTo(scroll, screen.getByTestId('data-card'))).toEqual([
        { behavior: 'smooth', block: 'start' },
      ]);
      expect(screen.getByTestId('data-card')).toBeInTheDocument();

      await userEvent.click(screen.getByRole('button', { name: '.confirm()' }));
      expect(onConfirmData).toHaveBeenCalledTimes(1);

      rerender(confirmed);
      expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Show the data' })).toHaveAttribute(
        'aria-expanded',
        'false'
      );
    } finally {
      restoreScrollIntoView();
    }
  });

  it('brings the card in at its top on .show(), and .hide() goes back to the reading position', async () => {
    const scroll = stubScrollIntoView();
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
    const scrollY = vi.spyOn(window, 'scrollY', 'get').mockReturnValue(1400);
    try {
      const { unmount } = render(
        <DataPanel
          state={stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true })}
          onParse={vi.fn()}
          onConfirmTranscription={vi.fn()}
          onDiscardTranscription={vi.fn()}
          onSendFormula={vi.fn()}
          onBind={vi.fn()}
          onConfirmData={vi.fn()}
          onUndo={vi.fn()}
        />
      );
      // While the header sticks, the page keeps focus and scrolling clear of it.
      expect(scrollPaddingRule()).toBe(true);

      await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));
      expect(scrolledTo(scroll, screen.getByTestId('data-card'))).toEqual([
        { behavior: 'smooth', block: 'start' },
      ]);

      scrollY.mockReturnValue(380);
      await userEvent.click(screen.getByRole('button', { name: 'Hide the data' }));
      expect(scrollTo).toHaveBeenCalledWith({ top: 1400 });

      unmount();
      expect(scrollPaddingRule()).toBe(false);
    } finally {
      scrollY.mockRestore();
      scrollTo.mockRestore();
      restoreScrollIntoView();
    }
  });

  it('holds step 1 while a table read from text waits, and the header names the decision', () => {
    const confirmed = stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true });
    const { rerender } = renderPanel(confirmed);
    // The server keeps its confirmation until `.use()`, and a turn's sync can report it.
    rerender({ ...confirmed, transcription: TRANSCRIPTION });
    expect(screen.getByTestId('data-summary')).toHaveTextContent(
      'decide on the table first: .use() or .discard()'
    );
    expect(screen.getByTestId('transcription-card')).toBeVisible();
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeDisabled();
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 1: check the data, then confirm it'
    );
  });

  it('names the reason of a refused confirmation', () => {
    renderPanel(
      stateWith({ x: 'month', y1: 'shoes' }, { confirmError: { code: 'no_dataset', ref: 'r-c' } })
    );
    expect(screen.getByRole('alert')).toHaveTextContent('parse the data first · ref r-c');
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeEnabled();
  });
});

const CHANGES = [
  "renamed 'Study Hours' to 'Hours'",
  "dropped 1 row where Tier = 'Gesamt'",
  'summed Umsatz by Datum (month): 3 rows, 2 other columns dropped',
];

/** The panel after the assistant changed the data, now at `version`. */
function changedState(
  version: number,
  overrides: Partial<AgentSessionState> = {}
): AgentSessionState {
  const base = stateWith({ x: 'month', y1: 'shoes' });
  const dataset = base.dataset && { ...base.dataset, parsed: { ...base.dataset.parsed, version } };
  return {
    ...base,
    dataset,
    dataChange: { kind: 'changed', changes: CHANGES, version },
    ...overrides,
  };
}

describe('DataPanel data changes', () => {
  function renderPanel(state: AgentSessionState) {
    const onUndo = vi.fn();
    const panel = (next: AgentSessionState) => (
      <DataPanel
        state={next}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={onUndo}
      />
    );
    const view = render(panel(state));
    return { onUndo, rerender: (next: AgentSessionState) => view.rerender(panel(next)) };
  }

  it('lists what changed, line by line above the preview, with .undo()', async () => {
    const { onUndo } = renderPanel(changedState(2));
    const block = within(screen.getByTestId('data-change'));
    expect(block.getByText('# changed · version 2')).toBeInTheDocument();
    expect(block.getAllByRole('listitem').map(item => item.textContent)).toEqual(CHANGES);
    expect(
      screen.getByTestId('data-change').compareDocumentPosition(screen.getByText(/^# preview/)) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    const undo = screen.getByRole('button', { name: '.undo()' });
    expect(undo).toHaveAccessibleDescription('# changed · version 2');
    await userEvent.click(undo);
    expect(onUndo).toHaveBeenCalledTimes(1);
    // The changed data is unconfirmed: the panel is at step 1 again.
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeEnabled();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
  });

  it('names the version an undo brought back and holds .undo() at the paste', () => {
    const { rerender } = renderPanel(
      changedState(1, { dataChange: { kind: 'undone', version: 1 } })
    );
    const block = within(screen.getByTestId('data-change'));
    expect(block.getByText('# undone · back to version 1')).toBeInTheDocument();
    expect(block.queryAllByRole('listitem')).toHaveLength(0);
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();

    // Two changes, one undone: the first can still go.
    rerender(changedState(2, { dataChange: { kind: 'undone', version: 2 } }));
    expect(screen.getByText('# undone · back to version 2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '.undo()' })).toBeEnabled();
  });

  it('holds .undo() back while anything runs and says why an undo was refused', () => {
    const { rerender } = renderPanel(
      changedState(2, { run: { kind: 'message', steps: [], queue: null, stopping: false } })
    );
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();

    rerender(changedState(2, { undoBusy: true }));
    expect(screen.getByRole('button', { name: '.undo() …' })).toBeDisabled();

    // A run in another tab: the undo can be tried again.
    rerender(changedState(2, { undoError: { code: 'run_active', ref: 'r409' } }));
    expect(screen.getByRole('alert')).toHaveTextContent(
      'a run is in progress; wait for it to finish · ref r409'
    );
    expect(screen.getByRole('button', { name: '.undo()' })).toBeEnabled();

    // The history ended above the paste: nothing left to ask for.
    rerender(changedState(3, { undoError: { code: 'nothing_to_undo', ref: 'r422' } }));
    expect(screen.getByRole('alert')).toHaveTextContent(
      'there is no earlier version to go back to · ref r422'
    );
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();
  });

  it('shows no change block for data as pasted', () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }));
    expect(screen.queryByTestId('data-change')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /\.undo\(\)/ })).not.toBeInTheDocument();
  });

  it('names a first dataset the assistant generated, with nothing to undo', () => {
    const generated = 'generated 200 rows: x from -3.1416 to 3.1416, y = sin(x)';
    const undefinedValues = 'y: 3 of 200 values are undefined and left empty';
    renderPanel(
      changedState(1, {
        dataChange: { kind: 'changed', changes: [generated, undefinedValues], version: 1 },
      })
    );
    const block = within(screen.getByTestId('data-change'));
    expect(block.getByText('# changed · version 1')).toBeInTheDocument();
    expect(block.getAllByRole('listitem').map(item => item.textContent)).toEqual([
      generated,
      undefinedValues,
    ]);
    expect(screen.queryByRole('button', { name: /\.undo\(\)/ })).not.toBeInTheDocument();
    // Generated data is unconfirmed like a paste: step 1 ends with .confirm().
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeEnabled();
  });
});

describe('DataPanel formulas', () => {
  const FORMULA = 'y = sin(x), x von -pi bis pi';

  function renderPanel(state: AgentSessionState) {
    const onSendFormula = vi.fn();
    const onParse = vi.fn();
    const panel = (next: AgentSessionState) => (
      <DataPanel
        state={next}
        onParse={onParse}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onSendFormula={onSendFormula}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const view = render(panel(state));
    return {
      onSendFormula,
      onParse,
      rerender: (next: AgentSessionState) => view.rerender(panel(next)),
    };
  }

  const empty = (overrides: Partial<AgentSessionState> = {}): AgentSessionState => ({
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
    ...overrides,
  });

  it('names the chat as the other source of data until there is some', () => {
    const { rerender } = renderPanel(empty());
    const hint = 'or ask for a curve in the chat: y = sin(x), x from -pi to pi';
    expect(screen.getByLabelText(/# your data/)).toHaveAccessibleDescription(hint);

    rerender(stateWith({ x: 'month', y1: 'shoes' }));
    expect(screen.queryByText(hint)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/# your data/)).not.toHaveAccessibleDescription();
  });

  it('offers .send() for a refused formula, which empties the box', async () => {
    const { onSendFormula, onParse, rerender } = renderPanel(empty());
    const textbox = screen.getByLabelText(/# your data/);
    await userEvent.type(textbox, FORMULA);
    await userEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(onParse).toHaveBeenCalledWith(FORMULA);
    expect(screen.queryByTestId('formula-offer')).not.toBeInTheDocument();

    rerender(empty({ formula: FORMULA }));
    const send = screen.getByRole('button', { name: '.send()' });
    expect(send).toHaveAccessibleDescription(
      'looks like a formula: send it to the chat? the assistant computes the table from it.'
    );
    // A formula is no error: nothing is shown as one.
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    await userEvent.click(send);
    expect(onSendFormula).toHaveBeenCalledTimes(1);
    expect(textbox).toHaveValue('');
  });

  it('holds .send() back while anything runs', async () => {
    const { rerender } = renderPanel(empty());
    await userEvent.type(screen.getByLabelText(/# your data/), FORMULA);
    rerender(
      empty({ formula: FORMULA, run: { kind: 'message', steps: [], queue: null, stopping: false } })
    );
    expect(screen.getByRole('button', { name: '.send()' })).toBeDisabled();
  });

  it('takes the offer away once the box is edited', async () => {
    const { onSendFormula, rerender } = renderPanel(empty());
    const textbox = screen.getByLabelText(/# your data/);
    await userEvent.type(textbox, FORMULA);
    rerender(empty({ formula: FORMULA }));
    expect(screen.getByTestId('formula-offer')).toBeInTheDocument();

    // The offer was made for the refused text: newer text in the box is not sent in its place.
    await userEvent.type(textbox, ' und cos(x)');
    expect(screen.queryByTestId('formula-offer')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();
    expect(onSendFormula).not.toHaveBeenCalled();
    expect(textbox).toHaveValue(`${FORMULA} und cos(x)`);
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
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
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
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();
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
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
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
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
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
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
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
