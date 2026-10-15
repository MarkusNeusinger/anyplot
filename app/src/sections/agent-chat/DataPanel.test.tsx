import { describe, expect, it, vi } from 'vitest';

import {
  type AgentSessionState,
  initialAgentState,
  type TranscriptionState,
} from 'src/hooks/useAgentSession';
import type { RoleSpec } from 'src/lib/agent';
import { bindingRows } from 'src/sections/agent-chat/bindings';
import { DataPanel } from 'src/sections/agent-chat/DataPanel';
import { fireEvent, render, screen, userEvent, waitFor, within } from 'src/test-utils';

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

  it('warns under the dropdown when a role that needs values of 0 or more gets a negative column', () => {
    const radius = role('radius', { non_negative: true });
    const columns = [
      { name: 'angle', dtype: 'number' as const, missing: 0, unique: 3, min: 0 },
      { name: 'y', dtype: 'number' as const, missing: 0, unique: 3, min: -0.9996 },
    ];
    const base = stateWith({ radius: 'y' }, { roles: [radius], missingRoles: [] });
    const state = {
      ...base,
      dataset: base.dataset && {
        ...base.dataset,
        parsed: { ...base.dataset.parsed, profile: { ...base.dataset.parsed.profile, columns } },
      },
    };
    render(
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
    const hint = 'has negative values (down to -0.9996); radius needs values of 0 or more';
    expect(screen.getByTestId('sign-hint')).toHaveTextContent(hint);
    expect(screen.getByLabelText(/^radius/)).toHaveAccessibleDescription(hint);
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
      rerender({ ...confirmed, dataConfirmed: false, confirmLoss: 'bindings' });
      const summary = screen.getByTestId('data-summary');
      expect(summary).toHaveTextContent('confirm again · 1 row · 5 columns · version 1');
      // It reads as a warning: the phrase in bold, not only the colour of the `!`.
      const phrase = within(summary).getByText('confirm again');
      expect(phrase).toHaveAttribute('data-tone', 'warning');
      expect(phrase).toHaveStyle({ fontWeight: '600' });
      // The row next to `.confirm()` names what dropped it, as the thread's notice does.
      expect(screen.getByRole('button', { name: '.confirm()' })).toHaveAccessibleDescription(
        '# step 1 again — bindings changed · confirm the data again'
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
      expect(within(screen.getByTestId('data-summary')).queryByText('confirm again')).toBeNull();

      // Confirmed again, the reason is gone: a later step 1 without one reads as before.
      rerender({ ...confirmed, dataConfirmed: false, confirmLoss: null });
      expect(screen.getByTestId('data-step')).toHaveTextContent(
        '# step 1 — check the preview and the bindings, then confirm'
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

describe('DataPanel working states', () => {
  function renderPanel(state: AgentSessionState) {
    const panel = (next: AgentSessionState) => (
      <DataPanel
        state={next}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const view = render(panel(state));
    return { rerender: (next: AgentSessionState) => view.rerender(panel(next)) };
  }

  const summaryTurn = { kind: 'summarize_data' as const, steps: [], queue: null, stopping: false };

  it('says why the bindings and .confirm() wait, exactly while something runs', () => {
    const idle = stateWith({ x: 'month', y1: 'shoes' });
    const { rerender } = renderPanel(idle);
    expect(screen.queryByTestId('bindings-lock')).not.toBeInTheDocument();
    expect(screen.queryByTestId('parse-hint')).not.toBeInTheDocument();

    rerender({ ...idle, run: summaryTurn });
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(
      '# bindings and .confirm() wait while the assistant works …'
    );
    // The lock stays (the server would refuse the change); the controls keep their look.
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
    expect(screen.getByRole('button', { name: '.confirm()' })).toBeDisabled();

    // A binding change, a confirmation or a theme render reads the same: the assistant works.
    rerender({ ...idle, bindingsBusy: true });
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(/while the assistant works/);

    rerender(idle);
    expect(screen.queryByTestId('bindings-lock')).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^x/)).toBeEnabled();
  });

  it('says that the data is parsed, under .parse(), on the bindings and to a screen reader', async () => {
    const { rerender } = renderPanel(stateWith({ x: 'month', y1: 'shoes' }));
    await userEvent.type(screen.getByLabelText(/# your data/), 'a,b');
    rerender(stateWith({ x: 'month', y1: 'shoes' }, { parsing: true }));

    expect(screen.getByTestId('parse-hint')).toHaveTextContent('# parsing your data …');
    const parse = screen.getByRole('button', { name: '.parse() …' });
    expect(parse).toBeDisabled();
    expect(parse).toHaveAccessibleDescription('# parsing your data');
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(
      '# bindings and .confirm() wait while the data is parsed …'
    );
    expect(screen.getByTestId('data-step-status')).toHaveTextContent('parsing your data');

    // The first parse: no data yet, so no bindings, but the line under `.parse()` shows.
    rerender({
      ...initialAgentState('matplotlib'),
      phase: 'ready',
      sessionId: 'S1',
      parsing: true,
    });
    expect(screen.getByTestId('parse-hint')).toHaveTextContent('# parsing your data …');
    expect(screen.queryByTestId('bindings-lock')).not.toBeInTheDocument();
  });

  it('names only the bindings in step 2, where the card has no .confirm()', async () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true, themeBusy: true }));
    await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(
      '# bindings wait while the assistant works …'
    );
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
      'a run or another paste is in progress; wait for it to finish · ref r409'
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

  it('offers .send() for refused code, which the assistant runs', async () => {
    const CODE = 'np.linspace(0, 10, 100)';
    const { onSendFormula, rerender } = renderPanel(empty());
    const textbox = screen.getByLabelText(/# your data/);
    await userEvent.type(textbox, CODE);

    rerender(empty({ formula: CODE, formulaKind: 'code' }));
    const send = screen.getByRole('button', { name: '.send()' });
    expect(send).toHaveAccessibleDescription(
      'looks like code that makes data: send it to the chat? the assistant runs it in a sandbox and shows you the table.'
    );
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    await userEvent.click(send);
    expect(onSendFormula).toHaveBeenCalledTimes(1);
    expect(textbox).toHaveValue('');
  });

  it('asks to shorten code the chat cannot take, without .send()', () => {
    const long = 'x = np.arange(10)\n'.repeat(200);
    const { rerender } = renderPanel(empty());
    // The offer belongs to the text in the box; set it through a paste-sized change.
    fireEvent.change(screen.getByLabelText(/# your data/), { target: { value: long } });
    rerender(empty({ formula: long, formulaKind: 'code' }));

    expect(screen.getByTestId('formula-offer')).toHaveTextContent(
      'looks like code that makes data: shorten it to 2,000 characters'
    );
    expect(screen.queryByRole('button', { name: '.send()' })).not.toBeInTheDocument();
  });
});

describe('DataPanel code that made the data', () => {
  const CODE =
    'import numpy as np\nimport pandas as pd\n\nx = np.arange(4)\ndf = pd.DataFrame({"x": x, "y": x**2})\n';

  const withCode = (code: string | undefined) => {
    const base = stateWith({ x: 'month', y1: 'shoes' });
    return {
      ...base,
      dataset: base.dataset && { ...base.dataset, parsed: { ...base.dataset.parsed, code } },
    };
  };

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

  it('shows the python collapsed, and opens and closes it', async () => {
    render(panel(withCode(CODE)));

    const block = screen.getByTestId('data-code');
    expect(block).toHaveTextContent('# code that made this data · 4 lines of python');
    expect(within(block).queryByText(/pd\.DataFrame/)).not.toBeInTheDocument();
    const toggle = within(block).getByRole('button', { name: '.show()' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');

    await userEvent.click(toggle);
    expect(within(block).getByText(/pd\.DataFrame/)).toBeInTheDocument();
    expect(within(block).getByRole('button', { name: '.hide()' })).toHaveAttribute(
      'aria-expanded',
      'true'
    );

    await userEvent.click(within(block).getByRole('button', { name: '.hide()' }));
    expect(within(block).queryByText(/pd\.DataFrame/)).not.toBeInTheDocument();
  });

  it('shows nothing for a version without code', () => {
    render(panel(withCode(undefined)));
    expect(screen.queryByTestId('data-code')).not.toBeInTheDocument();
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

describe('DataPanel wide-table offer', () => {
  // The owner's sensor paste on box-basic: the service offers the long form.
  const OFFER = {
    kind: 'to_long' as const,
    columns: ['Sensor_A', 'Sensor_B', 'Sensor_C'],
    names_to: 'category',
    values_to: 'value',
    keys: [],
    rows: 9,
  };
  const offered = (overrides: Partial<AgentSessionState> = {}) => {
    const state = stateWith({}, { bindingsComplete: false, ...overrides });
    return {
      ...state,
      dataset: state.dataset && {
        ...state.dataset,
        parsed: { ...state.dataset.parsed, suggestion: OFFER },
      },
    };
  };
  const panel = (state: AgentSessionState, onToLong = vi.fn()) => (
    <DataPanel
      state={state}
      onParse={vi.fn()}
      onConfirmTranscription={vi.fn()}
      onDiscardTranscription={vi.fn()}
      onSendFormula={vi.fn()}
      onBind={vi.fn()}
      onConfirmData={vi.fn()}
      onUndo={vi.fn()}
      onToLong={onToLong}
    />
  );

  it('names the columns and applies the offer with one click', async () => {
    const onToLong = vi.fn();
    render(panel(offered(), onToLong));

    const hint = screen.getByTestId('data-long-hint');
    expect(hint).toHaveTextContent(
      '# wide table · this plot wants one category and one value column'
    );
    expect(hint).toHaveTextContent('Sensor_A, Sensor_B, Sensor_C → category and value, 9 rows');
    const button = screen.getByRole('button', { name: 'Make the table long' });
    expect(button).toHaveTextContent('.to_long()');
    await userEvent.click(button);
    expect(onToLong).toHaveBeenCalledTimes(1);
  });

  it('waits while it runs, says when it failed, and shows nothing without an offer', () => {
    const { rerender } = render(panel(offered({ toLongBusy: true })));
    expect(screen.getByRole('button', { name: 'Make the table long' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Make the table long' })).toHaveTextContent(
      '.to_long() …'
    );

    rerender(panel(offered({ toLongError: { code: 'no_suggestion', ref: null } })));
    expect(screen.getByRole('alert')).toHaveTextContent(
      'could not change the table (no_suggestion)'
    );

    rerender(panel(stateWith({})));
    expect(screen.queryByTestId('data-long-hint')).not.toBeInTheDocument();
  });
});

describe('DataPanel notes', () => {
  const NOTES = ['Rainfall per month, station Hohe Warte', 'Source: own measurements'];

  const withNotes = (lines: string[] | undefined) => {
    const base = stateWith({ x: 'month', y1: 'shoes' });
    return {
      ...base,
      dataset: base.dataset && {
        ...base.dataset,
        parsed: { ...base.dataset.parsed, context_lines: lines },
      },
    };
  };

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

  it('shows the notes sent to the assistant collapsed, and opens and closes them', async () => {
    render(panel(withNotes(NOTES)));

    const block = screen.getByTestId('data-notes');
    expect(block).toHaveTextContent('# notes sent to the assistant · 2 lines');
    expect(within(block).queryByText(NOTES[0])).not.toBeInTheDocument();

    const toggle = within(block).getByRole('button', { name: '.show()' });
    expect(toggle).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(toggle).toHaveTextContent('.hide()');
    expect(
      within(block)
        .getAllByRole('listitem')
        .map(item => item.textContent)
    ).toEqual(NOTES);

    await userEvent.click(toggle);
    expect(within(block).queryByText(NOTES[1])).not.toBeInTheDocument();
  });

  it('names a single line in the singular', () => {
    render(panel(withNotes([NOTES[1]])));
    expect(screen.getByTestId('data-notes')).toHaveTextContent(
      '# notes sent to the assistant · 1 line'
    );
  });

  it('shows nothing without notes or from an older server', () => {
    const { rerender } = render(panel(withNotes([])));
    expect(screen.queryByTestId('data-notes')).not.toBeInTheDocument();
    rerender(panel(withNotes(undefined)));
    expect(screen.queryByTestId('data-notes')).not.toBeInTheDocument();
  });
});

describe('DataPanel file drop', () => {
  const CSV = 'month,revenue\n2026-01,120\n2026-02,135\n';
  const emptyState = (overrides: Partial<AgentSessionState> = {}): AgentSessionState => ({
    ...initialAgentState('matplotlib'),
    phase: 'ready' as const,
    sessionId: 'S1',
    ...overrides,
  });

  function renderPanel(state: AgentSessionState = emptyState()) {
    const onParse = vi.fn();
    const onConfirmTranscription = vi.fn();
    const onTrack = vi.fn();
    const view = render(
      <DataPanel
        state={state}
        onParse={onParse}
        onConfirmTranscription={onConfirmTranscription}
        onDiscardTranscription={vi.fn()}
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
        onTrack={onTrack}
      />
    );
    return { ...view, onParse, onConfirmTranscription, onTrack };
  }

  const box = () => screen.getByLabelText(/# your data/) as HTMLTextAreaElement;
  const zone = () => screen.getByTestId('data-drop-zone');
  const drop = (file: File) =>
    fireEvent.drop(zone(), { dataTransfer: { files: [file], types: ['Files'] } });
  const csvFile = (text = CSV, name = 'sales.csv') => new File([text], name, { type: 'text/csv' });

  it('fills an empty box, says what it read, focuses .parse() and parses with the name beside the text', async () => {
    const { onParse, onTrack } = renderPanel();

    drop(csvFile());

    await waitFor(() => expect(box()).toHaveValue(CSV));
    expect(screen.getByTestId('file-status')).toHaveTextContent(
      '# read "sales.csv" as utf-8 · 3 lines · check it, then .parse()'
    );
    const parse = screen.getByRole('button', { name: '.parse()' });
    expect(parse).toHaveFocus();
    expect(onTrack).toHaveBeenCalledWith('agent_data_file', {
      kind: 'text',
      encoding: 'utf-8',
      outcome: 'filled',
    });
    // No auto-parse: the user presses `.parse()`.
    expect(onParse).not.toHaveBeenCalled();

    await userEvent.click(parse);
    expect(onParse).toHaveBeenCalledWith(CSV, 'sales.csv');
  });

  it('asks before it replaces text in the box: .keep() keeps it, .replace() takes the file', async () => {
    const { onTrack } = renderPanel();
    await userEvent.type(box(), 'a,b');

    drop(csvFile());

    const group = await screen.findByTestId('file-replace');
    expect(group).toHaveTextContent('replace the text in the box with "sales.csv" (3 lines)?');
    expect(within(group).getByRole('button', { name: '.replace()' })).toHaveFocus();
    await userEvent.click(within(group).getByRole('button', { name: '.keep()' }));
    expect(box()).toHaveValue('a,b');
    expect(screen.queryByTestId('file-replace')).not.toBeInTheDocument();
    expect(onTrack).toHaveBeenLastCalledWith('agent_data_file', {
      kind: 'text',
      encoding: 'utf-8',
      outcome: 'kept',
    });

    drop(csvFile());
    await userEvent.click(await screen.findByRole('button', { name: '.replace()' }));
    expect(box()).toHaveValue(CSV);
    expect(onTrack).toHaveBeenLastCalledWith('agent_data_file', {
      kind: 'text',
      encoding: 'utf-8',
      outcome: 'replaced',
    });
  });

  it('holds .replace() while the parse of the text in the box runs', async () => {
    const { rerender, onParse } = renderPanel();
    await userEvent.type(box(), 'a,b');
    drop(csvFile());
    await screen.findByTestId('file-replace');
    await userEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(onParse).toHaveBeenCalledWith('a,b');

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
    rerender(panel(emptyState({ parsing: true })));
    expect(screen.getByRole('button', { name: '.replace()' })).toBeDisabled();
    expect(box()).toHaveValue('a,b');

    rerender(panel(emptyState()));
    await userEvent.click(screen.getByRole('button', { name: '.replace()' }));
    expect(box()).toHaveValue(CSV);
  });

  it('refuses a file while a step runs and leaves the box alone', async () => {
    const { onTrack } = renderPanel(emptyState({ parsing: true }));

    drop(csvFile());

    expect(await screen.findByTestId('file-error')).toHaveTextContent('a step is still running');
    expect(box()).toHaveValue('');
    expect(onTrack).toHaveBeenCalledWith('agent_data_file', {
      kind: 'unknown',
      encoding: 'none',
      outcome: 'busy',
    });
    expect(screen.getByRole('button', { name: 'Open a data file' })).toBeDisabled();
  });

  it('answers a workbook and a pickle by their format', async () => {
    const { onTrack } = renderPanel();
    const zip = new Uint8Array([0x50, 0x4b, 0x03, 0x04, 0, 0, 0, 0]);

    drop(new File([zip], 'sales.xlsx'));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      '"sales.xlsx" is a spreadsheet: reading Excel and ODS files comes in a later step'
    );
    expect(onTrack).toHaveBeenCalledWith('agent_data_file', {
      kind: 'spreadsheet',
      encoding: 'none',
      outcome: 'refused',
    });

    drop(new File([new Uint8Array([0x80, 0x05, 0x95])], 'frame.pkl'));
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(
        'never read because loading one can run code'
      )
    );
    expect(box()).toHaveValue('');
  });

  it('reads a file chosen with .open() and a file pasted from the file manager', async () => {
    const { onParse } = renderPanel();
    const input = screen.getByTestId('data-file-input') as HTMLInputElement;
    expect(input.accept).toContain('text/csv');

    await userEvent.upload(input, csvFile(CSV, 'chosen.csv'));
    await waitFor(() => expect(box()).toHaveValue(CSV));
    // Typing keeps the name: the text is still the file's, edited.
    await userEvent.type(box(), '2026-03,150\n');
    await userEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(onParse).toHaveBeenLastCalledWith(`${CSV}2026-03,150\n`, 'chosen.csv');

    await userEvent.clear(box());
    fireEvent.paste(box(), {
      clipboardData: { files: [csvFile(CSV, 'pasted.tsv')], getData: () => '' },
    });
    await waitFor(() => expect(box()).toHaveValue(CSV));
    await userEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(onParse).toHaveBeenLastCalledWith(CSV, 'pasted.tsv');
  });

  it('lets pasted text through and forgets the file name', async () => {
    const { onParse } = renderPanel();
    drop(csvFile());
    await waitFor(() => expect(box()).toHaveValue(CSV));

    // Excel puts a picture of the cells next to their text: the text wins.
    const picture = new File([new Uint8Array([0x89, 0x50])], 'cells.png', { type: 'image/png' });
    const pasted = fireEvent.paste(box(), {
      clipboardData: { files: [picture], getData: () => '2026-03,150' },
    });
    expect(pasted).toBe(true); // not prevented: the browser pastes the text
    await userEvent.click(screen.getByRole('button', { name: '.parse()' }));
    expect(onParse).toHaveBeenLastCalledWith(CSV);
  });

  it('keeps the name for .use() on a table read from the file', async () => {
    const transcription: TranscriptionState = {
      text: 'name,count\nA,1\n',
      preview: [['A', '1']],
      profile: {
        rows: 1,
        columns: [
          { name: 'name', dtype: 'text', missing: 0, unique: 1 },
          { name: 'count', dtype: 'number', missing: 0, unique: 1 },
        ],
        source_format: 'csv',
        decimal: '.',
        warnings: [],
      },
      warnings: [],
      note: '',
      bytes: 20,
    };
    const { rerender, onConfirmTranscription } = renderPanel();
    drop(csvFile('A had one\n', 'notes.txt'));
    await waitFor(() => expect(box()).toHaveValue('A had one\n'));

    rerender(
      <DataPanel
        state={emptyState({ transcription })}
        onParse={vi.fn()}
        onConfirmTranscription={onConfirmTranscription}
        onDiscardTranscription={vi.fn()}
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole('button', { name: '.use()' }));
    expect(onConfirmTranscription).toHaveBeenCalledWith('notes.txt');

    // A new file takes the earlier text's table away, so `.use()` never stores it under the new name.
    const onDiscardTranscription = vi.fn();
    rerender(
      <DataPanel
        state={emptyState({ transcription })}
        onParse={vi.fn()}
        onConfirmTranscription={onConfirmTranscription}
        onDiscardTranscription={onDiscardTranscription}
        onSendFormula={vi.fn()}
        onBind={vi.fn()}
        onConfirmData={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    drop(csvFile(CSV, 'other.csv'));
    await userEvent.click(await screen.findByRole('button', { name: '.replace()' }));
    expect(onDiscardTranscription).toHaveBeenCalledTimes(1);
    expect(box()).toHaveValue(CSV);
  });

  it('drops the result of a slow read that a later file superseded', async () => {
    renderPanel();
    let release: (buffer: ArrayBuffer) => void = () => {};
    const slow = csvFile('slow,file\n1,2\n', 'slow.csv');
    const slowBytes = await slow.arrayBuffer();
    slow.arrayBuffer = () =>
      new Promise<ArrayBuffer>(resolve => {
        release = resolve;
      });

    drop(slow);
    drop(csvFile(CSV, 'fast.csv'));
    await waitFor(() => expect(box()).toHaveValue(CSV));
    release(slowBytes);
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(box()).toHaveValue(CSV);
    expect(screen.queryByTestId('file-replace')).not.toBeInTheDocument();
    expect(screen.getByTestId('file-status')).toHaveTextContent('"fast.csv"');
  });

  it('marks the box while a file is dragged over it and keeps the browser from opening a stray drop', () => {
    renderPanel();
    const transfer = { files: [], types: ['Files'], dropEffect: 'none' };

    fireEvent.dragEnter(zone(), { dataTransfer: transfer });
    expect(zone()).toHaveAttribute('data-drag', 'ready');
    expect(screen.getByText('drop the file to read it into the box')).toBeInTheDocument();
    fireEvent.dragLeave(zone(), { dataTransfer: transfer });
    expect(zone()).not.toHaveAttribute('data-drag');

    // A file dropped beside the box: prevented, so the page stays.
    expect(fireEvent.drop(document.body, { dataTransfer: transfer })).toBe(false);
    // A text drag keeps its default.
    expect(fireEvent.drop(document.body, { dataTransfer: { types: ['text/plain'] } })).toBe(true);
  });
});
