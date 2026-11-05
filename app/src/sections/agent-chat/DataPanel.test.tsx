import { beforeAll, describe, expect, it, vi } from 'vitest';

import {
  type AgentSessionState,
  initialAgentState,
  type TranscriptionState,
} from 'src/hooks/useAgentSession';
import { AgentApiError, type ConvertAnswer, type RoleSpec } from 'src/lib/agent';
import { bindingRows } from 'src/sections/agent-chat/bindings';
import { DataPanel, DataViewUnavailable } from 'src/sections/agent-chat/DataPanel';
import { PinnedHeader } from 'src/sections/agent-chat/PinnedData';
import { useDataCardView } from 'src/sections/agent-chat/useDataCardView';
import { act, fireEvent, render, screen, userEvent, waitFor, within } from 'src/test-utils';

type PanelProps = Omit<React.ComponentProps<typeof DataPanel>, 'view' | 'part'>;

/**
 * The card as the page composes it: the pinned header above the thread, the stored data's card
 * at its item and the card of a table read from text at its own (`AgentChatPage`, `ChatThread`).
 */
function Panel(props: PanelProps) {
  const view = useDataCardView(props.state);
  return (
    <>
      <PinnedHeader state={props.state} view={view} />
      <DataPanel {...props} view={view} part="data" />
      <DataPanel {...props} view={view} part="transcription" />
    </>
  );
}

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
      <Panel
        state={stateWith({ x: 'month', y1: 'shoes' }, { missingRoles: [] })}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={onBind}
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

  it('draws line breaks and space runs of a preview cell visibly instead of folding them', () => {
    const base = stateWith({ x: 'month' }, { missingRoles: [] });
    const state = {
      ...base,
      dataset: base.dataset && {
        ...base.dataset,
        parsed: {
          ...base.dataset.parsed,
          preview: [['2026-01', '1', '2', '3', 'north\nwest  end']],
        },
      },
    };
    render(
      <Panel
        state={state}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const cell = screen.getByTitle('line break').closest('td');
    expect(cell).toHaveTextContent('north↵ (line break) west·· (2 spaces) end');
    expect(screen.getByTitle('2 spaces')).toBeInTheDocument();
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
      <Panel
        state={state}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const hint = 'has negative values (down to -0.9996); radius needs values of 0 or more';
    expect(screen.getByTestId('sign-hint')).toHaveTextContent(hint);
    expect(screen.getByLabelText(/^radius/)).toHaveAccessibleDescription(hint);
  });

  it('offers "computed by the plot" for a role the plot computes, and binds a column to it', async () => {
    const roles = [role('close'), role('sma', { required: false, computed: true })];
    const onBind = vi.fn();
    const { container } = render(
      <Panel
        state={stateWith({ close: 'shoes' }, { roles, missingRoles: [] })}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={onBind}
        onUndo={vi.fn()}
      />
    );
    const sma = screen.getByLabelText(/^sma/) as HTMLSelectElement;
    expect(sma.value).toBe('');
    expect(sma.options[0]).toHaveTextContent('— computed by the plot —');
    expect(container.querySelector('label[for="agent-role-sma"]')).not.toHaveTextContent('*');
    expect(container.querySelector('label[for="agent-role-close"]')).toHaveTextContent('close *');
    await userEvent.selectOptions(sma, 'hats');
    expect(onBind).toHaveBeenCalledWith('sma', 'hats');
  });

  it('lists the lines of a refused binding set', () => {
    render(
      <Panel
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
        onUndo={vi.fn()}
      />
    );
    expect(screen.getByRole('alert')).toHaveTextContent('the server refused these bindings');
    expect(
      screen.getByText("role 'x' needs numeric or datetime data, but column 'region' is text")
    ).toBeInTheDocument();
  });

  it('holds back the bindings while a theme renders, in both steps', async () => {
    const panel = (state: AgentSessionState) => (
      <Panel
        state={state}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const { rerender } = render(panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true })));
    expect(screen.getByLabelText(/^x/)).toBeDisabled();

    // Step 2: opening the card is only a look, so it works, but nothing in it starts.
    rerender(
      panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true, dataConfirmed: true }))
    );
    await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    expect(screen.getByLabelText(/^x/)).toBeDisabled();
  });

  it('shows no card before there is data or a table read from text', () => {
    render(
      <Panel
        state={{ ...initialAgentState('matplotlib'), phase: 'ready', sessionId: 'S1' }}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    // The data comes in through the message box: the card has nothing to show yet.
    expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
    expect(screen.getByTestId('data-step-status')).toBeEmptyDOMElement();
  });

  it('holds every action back while the fan-out panel copies the data, and says why', async () => {
    const onParse = vi.fn();
    const onUndo = vi.fn();
    const panel = (state: AgentSessionState, locked: boolean) => (
      <Panel
        state={state}
        onParse={onParse}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={onUndo}
        locked={locked}
      />
    );
    const changed: AgentSessionState = stateWith(
      { x: 'month', y1: 'shoes' },
      { dataChange: { kind: 'changed', changes: ['dropped 1 row'], version: 2 } }
    );
    const stored = changed.dataset;
    if (!stored) throw new Error('stateWith always holds a dataset');
    // Version 2, so `.undo()` shows and has something to undo once the panel closes.
    const versioned: AgentSessionState = {
      ...changed,
      dataset: { ...stored, parsed: { ...stored.parsed, version: 2 } },
    };
    const { rerender } = render(panel(versioned, true));
    const card = screen.getByRole('region', { name: 'Your data' });
    const line = '# the data waits while all libraries plot it · .close() the panel to change it';
    expect(screen.getByTestId('data-lock')).toHaveTextContent(line);
    expect(card).toHaveAccessibleDescription(line);
    // Nothing that changes the data or its confirmation starts; the session itself is idle.
    expect(screen.queryByTestId('bindings-lock')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();
    expect(screen.getByLabelText(/^x/)).toBeDisabled();

    // The panel closed: the card is the user's again.
    rerender(panel(versioned, false));
    expect(screen.queryByTestId('data-lock')).not.toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Your data' })).not.toHaveAccessibleDescription();
    expect(screen.getByLabelText(/^x/)).toBeEnabled();
    fireEvent.click(screen.getByRole('button', { name: '.undo()' }));
    expect(onUndo).toHaveBeenCalledTimes(1);
    expect(onParse).not.toHaveBeenCalled();
  });
});

describe('DataPanel steps', () => {
  function renderPanel(state: AgentSessionState) {
    const panel = (next: AgentSessionState) => (
      <Panel
        state={next}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const view = render(panel(state));
    return { rerender: (next: AgentSessionState) => view.rerender(panel(next)) };
  }

  it("has no button of either step: .create_plot() is the composer's", () => {
    const { rerender } = renderPanel(
      stateWith({ x: 'month' }, { bindingsComplete: false, missingRoles: ['y'] })
    );
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /\.confirm\(\)/ })).not.toBeInTheDocument();
    expect(screen.queryByTestId('data-step')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();

    // The confirmation `.create_plot()` starts with, in flight: the dropdowns hold still.
    rerender(stateWith({ x: 'month', y1: 'shoes' }, { confirmBusy: true }));
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

  it('opens in full when the confirmation drops, and collapses at the next .create_plot()', async () => {
    const scroll = stubScrollIntoView();
    try {
      const confirmed = stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true });
      const { rerender } = renderPanel(confirmed);
      await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));

      // A binding change, a data change or an undo: the server dropped the confirmation.
      // The header stays and says so, and the line above the card stays in its place.
      rerender({ ...confirmed, dataConfirmed: false, confirmLoss: 'bindings' });
      const summary = screen.getByTestId('data-summary');
      expect(summary).toHaveTextContent('check again · 1 row · 5 columns · version 1');
      // It reads as a warning: the phrase in bold, not only the colour of the `!`.
      const phrase = within(summary).getByText('check again');
      expect(phrase).toHaveAttribute('data-tone', 'warning');
      expect(phrase).toHaveStyle({ fontWeight: '600' });
      expect(
        screen.getByText('# step 1 again: check the data, then .create_plot() below')
      ).toBeVisible();
      expect(screen.queryByText(/a change here takes the data back/)).not.toBeInTheDocument();
      expect(screen.getByTestId('data-step-status')).toHaveTextContent(
        'step 1: check the data, then create the plot'
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

      // The user's `.create_plot()` at the composer's end starts with the confirmation: the
      // card collapses with it, although the user had opened it before the confirmation dropped.
      rerender({ ...confirmed, dataConfirmed: false, confirmLoss: 'bindings', confirmBusy: true });
      rerender(confirmed);
      expect(screen.queryByTestId('data-card')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Show the data' })).toHaveAttribute(
        'aria-expanded',
        'false'
      );
      expect(within(screen.getByTestId('data-summary')).queryByText('check again')).toBeNull();
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
        <Panel
          state={stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true })}
          onParse={vi.fn()}
          onConfirmTranscription={vi.fn()}
          onDiscardTranscription={vi.fn()}
          onBind={vi.fn()}
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
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 1: check the data, then create the plot'
    );
  });

  it("leads the header's button to the table read from text, where .use() and .discard() wait", async () => {
    const scroll = stubScrollIntoView();
    try {
      const confirmed = stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true });
      const { rerender } = renderPanel(confirmed);
      rerender({ ...confirmed, transcription: TRANSCRIPTION });
      scroll.mockClear();
      await userEvent.click(screen.getByRole('button', { name: 'Go to the data' }));
      expect(scrolledTo(scroll, screen.getByTestId('transcription-item'))).toEqual([
        { behavior: 'smooth', block: 'start' },
      ]);
      expect(scrolledTo(scroll, screen.getByTestId('data-card'))).toEqual([]);
    } finally {
      restoreScrollIntoView();
    }
  });

  it('keeps a card the user opened when step 2 returns without a confirmation', async () => {
    const confirmed = stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true });
    const { rerender } = renderPanel(confirmed);
    await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    // A table read from text, then discarded: step 1 and back, with no confirmation call.
    rerender({ ...confirmed, transcription: TRANSCRIPTION });
    rerender(confirmed);
    expect(screen.getByTestId('data-card')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hide the data' })).toBeInTheDocument();
  });
});

describe('DataPanel working states', () => {
  function renderPanel(state: AgentSessionState) {
    const panel = (next: AgentSessionState) => (
      <Panel
        state={next}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const view = render(panel(state));
    return { rerender: (next: AgentSessionState) => view.rerender(panel(next)) };
  }

  const summaryTurn = { kind: 'summarize_data' as const, steps: [], queue: null, stopping: false };

  it('says why the bindings wait, exactly while something runs', () => {
    const idle = stateWith({ x: 'month', y1: 'shoes' });
    const { rerender } = renderPanel(idle);
    expect(screen.queryByTestId('bindings-lock')).not.toBeInTheDocument();
    expect(screen.queryByTestId('parse-hint')).not.toBeInTheDocument();

    rerender({ ...idle, run: summaryTurn });
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(
      /^# bindings wait while the assistant works$/
    );
    // The lock stays (the server would refuse the change); the controls keep their look.
    expect(screen.getByLabelText(/^x/)).toBeDisabled();

    // A binding change, a confirmation or a theme render reads the same: the assistant works.
    rerender({ ...idle, bindingsBusy: true });
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(/while the assistant works/);

    rerender(idle);
    expect(screen.queryByTestId('bindings-lock')).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^x/)).toBeEnabled();
  });

  it('says that the data is parsed on the bindings and to a screen reader, with no loader of its own', () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }, { parsing: true }));

    // The attachment's chip in the composer holds the parse's one loader; the card only says it.
    expect(screen.queryByTestId('loader-spinner')).not.toBeInTheDocument();
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(
      /^# bindings wait while the data is parsed$/
    );
    expect(screen.getByTestId('data-step-status')).toHaveTextContent('parsing your data');
  });

  it('names the same bindings lock in step 2', async () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true, themeBusy: true }));
    await userEvent.click(screen.getByRole('button', { name: 'Show the data' }));
    expect(screen.getByTestId('bindings-lock')).toHaveTextContent(
      /^# bindings wait while the assistant works$/
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
      <Panel
        state={next}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
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
    // The changed data is unconfirmed: the panel is at step 1 again, the card open.
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 1: check the data, then create the plot'
    );
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

    // A run the server still holds for this window (a stopped run's last step): the undo can be tried again.
    rerender(changedState(2, { undoError: { code: 'run_active', ref: 'r409' } }));
    expect(screen.getByRole('alert')).toHaveTextContent(
      'a run or another paste is still in progress in this window; wait for it to finish · ref r409'
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
    // Generated data is unconfirmed like a paste: step 1, which the composer's .create_plot() ends.
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 1: check the data, then create the plot'
    );
  });
});

describe('DataPanel full view', () => {
  const CSV = 'month,shoes,hats,scarves,region\n2026-01,1,2,3,north\n';

  // The view is a lazy chunk with the whole grid: loaded once up front, so a busy test run
  // does not spend the queries' time on the first import.
  beforeAll(async () => {
    await import('src/sections/agent-chat/DataView');
  }, 30_000);

  function renderPanel(state: AgentSessionState, extra: Record<string, unknown> = {}) {
    render(
      <Panel
        state={state}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
        {...extra}
      />
    );
  }

  it('says in the card when the view did not load, and .close() leaves the page as it was', async () => {
    const onClose = vi.fn();
    render(<DataViewUnavailable onClose={onClose} />);
    expect(screen.getByRole('alert')).toHaveTextContent('the table view did not load');

    await userEvent.click(screen.getByRole('button', { name: '.close()' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('offers .view_all() only where the page can load the data', () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }));
    expect(screen.queryByRole('button', { name: /^View all/ })).not.toBeInTheDocument();
  });

  it('opens every row in the view, reports it once and gives the focus back on .close()', async () => {
    const load = vi.fn(() => Promise.resolve(CSV));
    const onDataViewShown = vi.fn();
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }), { onLoadData: load, onDataViewShown });
    const open = screen.getByRole('button', { name: 'View all 1 row' });
    expect(open).toHaveTextContent('.view_all()');
    expect(open).toHaveAttribute('aria-haspopup', 'dialog');

    await userEvent.click(open);
    const dialog = await screen.findByRole('dialog', { name: /every row · 1 row · 5 columns/ });
    expect(await within(dialog).findByText('north')).toBeInTheDocument();
    expect(load).toHaveBeenCalledTimes(1);
    expect(onDataViewShown).toHaveBeenCalledTimes(1);

    await userEvent.click(within(dialog).getByRole('button', { name: 'Close the data view' }));
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
    expect(open).toHaveFocus();
  });

  it('opens while a step runs and while the fan-out panel holds the data: it only reads', async () => {
    const load = vi.fn(() => Promise.resolve(CSV));
    renderPanel(
      stateWith(
        { x: 'month', y1: 'shoes' },
        { run: { kind: 'message', steps: [], queue: null, stopping: false } }
      ),
      { onLoadData: load, locked: true }
    );
    const open = screen.getByRole('button', { name: 'View all 1 row' });
    expect(open).toBeEnabled();
    await userEvent.click(open);
    expect(await screen.findByRole('grid')).toBeInTheDocument();
  });
});

describe('DataPanel tables', () => {
  // Live test round 5 of 2026-10-15: a report sheet with two tables one below the other.
  const REPORT = 'Branch,Q1\nNorth,1.5\n\nBranch,Staff\nNorth,24\n';
  const TABLES = ['Branch, Q1 · 1 row', 'Branch, Staff · 1 row'];

  function renderPanel() {
    const onParse = vi.fn();
    const panel = (next: AgentSessionState) => (
      <Panel
        state={next}
        onParse={onParse}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const view = render(
      panel({ ...initialAgentState('matplotlib'), phase: 'ready', sessionId: 'S1' })
    );
    return { onParse, rerender: (next: AgentSessionState) => view.rerender(panel(next)) };
  }

  function withTables(
    table: number,
    tables: unknown = TABLES,
    paste: { text: string; source?: string } | null = { text: REPORT, source: 'report.xlsx' }
  ): AgentSessionState {
    const state: AgentSessionState = stateWith({ x: 'month', y1: 'shoes' });
    const dataset = state.dataset;
    if (!dataset) throw new Error('stateWith has a dataset');
    return {
      ...state,
      dataset: {
        ...dataset,
        ...(paste ? { paste } : {}),
        parsed: { ...dataset.parsed, tables, table },
      },
    };
  }

  it('offers the other tables of the stored paste and parses its text again for the chosen one', async () => {
    const { onParse, rerender } = renderPanel();
    rerender(withTables(1));
    const picker = screen.getByLabelText('# table (2)');
    expect(picker).toHaveValue('1');
    expect(
      within(picker)
        .getAllByRole('option')
        .map(option => option.textContent)
    ).toEqual(['1 · Branch, Q1 · 1 row', '2 · Branch, Staff · 1 row']);

    // The tables are the stored paste's: its text again, with its file's name.
    await userEvent.selectOptions(picker, '2');
    expect(onParse).toHaveBeenLastCalledWith(REPORT, 'report.xlsx', 2, undefined);
  });

  it('shows no picker for one table, a malformed answer or a version without its paste', () => {
    const { rerender } = renderPanel();
    rerender(withTables(1, TABLES, null));
    expect(screen.queryByTestId('data-tables')).not.toBeInTheDocument();
    rerender(withTables(1, ['only one']));
    expect(screen.queryByTestId('data-tables')).not.toBeInTheDocument();
    rerender(withTables(3));
    expect(screen.queryByTestId('data-tables')).not.toBeInTheDocument();
    rerender(withTables(1, [1, 2]));
    expect(screen.queryByTestId('data-tables')).not.toBeInTheDocument();
    rerender(withTables(2));
    expect(screen.getByTestId('data-tables')).toBeInTheDocument();
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
    <Panel
      state={state}
      onParse={vi.fn()}
      onConfirmTranscription={vi.fn()}
      onDiscardTranscription={vi.fn()}
      onBind={vi.fn()}
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
      <Panel
        state={transcribedState()}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
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
      <Panel
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
        onUndo={vi.fn()}
      />
    );
    expect(screen.getByText('# read from your text — 1 row, 2 columns')).toBeInTheDocument();
    expect(screen.queryByText('# note from the model')).not.toBeInTheDocument();
    expect(screen.queryByText('# warnings')).not.toBeInTheDocument();
  });

  it('.use() confirms the table and .discard() drops it', async () => {
    const onConfirm = vi.fn();
    const onDiscard = vi.fn();
    render(
      <Panel
        state={transcribedState()}
        onParse={vi.fn()}
        onConfirmTranscription={onConfirm}
        onDiscardTranscription={onDiscard}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole('button', { name: '.discard()' }));
    expect(onDiscard).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole('button', { name: '.use()' }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('holds back .use() while the session is busy, and goes once the table is decided on', () => {
    const panel = (state: AgentSessionState) => (
      <Panel
        state={state}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    const { rerender } = render(panel(transcribedState()));
    expect(screen.getByRole('button', { name: '.use()' })).toBeEnabled();

    // A theme render in flight: the confirmation's parse would race it.
    rerender(panel(transcribedState({ themeBusy: true })));
    expect(screen.getByRole('button', { name: '.use()' })).toBeDisabled();
    expect(screen.getByRole('button', { name: '.discard()' })).toBeEnabled();

    rerender(panel(transcribedState({ transcription: null })));
    expect(screen.queryByTestId('transcription-card')).not.toBeInTheDocument();
    expect(screen.queryByText(/decide on the table/)).not.toBeInTheDocument();
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
    siblings: ['Sensor_A', 'Sensor_B', 'Sensor_C'],
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
    <Panel
      state={state}
      onParse={vi.fn()}
      onConfirmTranscription={vi.fn()}
      onDiscardTranscription={vi.fn()}
      onBind={vi.fn()}
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

  it('warns under a role that wants labels when it is bound to one of the side-by-side columns', () => {
    // Live test round 7: a heatmap's `y` on the numbers of `Mo` drew a meaningless matrix.
    const state = offered({ bindings: { x: 'month', series: 'shoes' } });
    const withSiblings = {
      ...state,
      dataset: state.dataset && {
        ...state.dataset,
        parsed: {
          ...state.dataset.parsed,
          suggestion: { ...OFFER, columns: ['shoes', 'hats'], siblings: ['shoes', 'hats'] },
        },
      },
    };
    render(panel(withSiblings));

    expect(screen.getByTestId('sign-hint')).toHaveTextContent(
      'one of 2 number columns that hold one measure side by side; series wants labels: .to_long() first'
    );
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
    <Panel
      state={state}
      onParse={vi.fn()}
      onConfirmTranscription={vi.fn()}
      onDiscardTranscription={vi.fn()}
      onBind={vi.fn()}
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

describe('DataPanel files and sheets', () => {
  function renderPanel(
    state: AgentSessionState,
    onConvert?: (dataBase64: string, sheet?: string) => Promise<ConvertAnswer>
  ) {
    const onParse = vi.fn();
    const onTrack = vi.fn();
    const panel = (next: AgentSessionState) => (
      <Panel
        state={next}
        onParse={onParse}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
        onTrack={onTrack}
        onConvert={onConvert}
      />
    );
    const view = render(panel(state));
    return { onParse, onTrack, rerender: (next: AgentSessionState) => view.rerender(panel(next)) };
  }

  const answer = (overrides: Partial<ConvertAnswer> = {}): ConvertAnswer => ({
    text: 'month,revenue\nJan,120\n',
    format: 'csv',
    kind: 'xlsx',
    rows: 1,
    columns: 2,
    sheet: '2024',
    sheets: ['2024', '2025'],
    sheet_count: 2,
    warnings: {},
    dropped: [],
    ...overrides,
  });

  /** Data parsed from a workbook's sheet: the page keeps the file for the sheet picker. */
  function fromWorkbook(name = 'Bericht.xlsx', sheets = ['2024', '2025']): AgentSessionState {
    const state: AgentSessionState = stateWith({ x: 'month', y1: 'shoes' });
    const { dataset } = state;
    if (!dataset) throw new Error('stateWith gives a dataset');
    return {
      ...state,
      dataset: {
        ...dataset,
        file: {
          name,
          base64: 'UEsDBA==',
          browserKind: 'spreadsheet',
          kind: 'xlsx',
          sheet: sheets[0],
          sheets,
          sheetCount: sheets.length,
          text: 'month,revenue\nJan,120\n',
        },
      },
    };
  }

  it('offers the other sheets of the workbook and parses the chosen one, read again on the server', async () => {
    const onConvert = vi.fn(async (_data: string, sheet?: string) =>
      answer({ text: 'a,b\n1,2\n', sheet: sheet ?? '2024' })
    );
    const { onParse, onTrack } = renderPanel(fromWorkbook(), onConvert);
    const picker = screen.getByLabelText(/# sheet/) as HTMLSelectElement;
    expect(screen.getByText('# sheet (2)')).toBeInTheDocument();
    expect(picker).toHaveValue('2024');
    expect(
      within(picker)
        .getAllByRole('option')
        .map(option => option.textContent)
    ).toEqual(['2024', '2025']);

    await userEvent.selectOptions(picker, '2025');
    expect(onConvert).toHaveBeenCalledWith('UEsDBA==', '2025');
    await waitFor(() =>
      expect(onParse).toHaveBeenCalledWith(
        'a,b\n1,2\n',
        'Bericht.xlsx · sheet ‹2025›',
        undefined,
        expect.objectContaining({ name: 'Bericht.xlsx', sheet: '2025', text: 'a,b\n1,2\n' })
      )
    );
    expect(onTrack).toHaveBeenCalledWith('agent_data_file', {
      kind: 'xlsx',
      encoding: 'none',
      outcome: 'sheet',
    });
  });

  it('names the sheet in angle quotes, so the data line never nests quotes', async () => {
    // Live test round 4 of 2026-10-15: the data line read `from "Museen_2025.xlsx · sheet "Übersicht""`.
    const onConvert = vi.fn(async () =>
      answer({ sheet: 'Übersicht', sheets: ['Jahr', 'Übersicht'] })
    );
    const { onParse } = renderPanel(
      fromWorkbook('Museen_2025.xlsx', ['Jahr', 'Übersicht']),
      onConvert
    );
    await userEvent.selectOptions(screen.getByLabelText(/# sheet/), 'Übersicht');
    await waitFor(() => expect(onParse).toHaveBeenCalled());
    const source = onParse.mock.calls[0][1] as string;
    expect(source).toBe('Museen_2025.xlsx · sheet ‹Übersicht›');
    expect(source).not.toContain('"');
  });

  it('says that the server reads the sheet beside the loader, and why it could not', async () => {
    let fail!: (error: unknown) => void;
    const onConvert = vi.fn(
      () =>
        new Promise<ConvertAnswer>((_resolve, reject) => {
          fail = reject;
        })
    );
    const { onParse } = renderPanel(fromWorkbook(), onConvert);
    await userEvent.selectOptions(screen.getByLabelText(/# sheet/), '2025');
    const reading = screen.getByTestId('sheet-reading');
    expect(reading).toHaveTextContent('# reading the sheet ‹2025› of "Bericht.xlsx" on the server');
    expect(within(reading).getByTestId('loader-spinner')).toBeInTheDocument();
    expect(screen.getByLabelText(/# sheet/)).toBeDisabled();

    await act(async () =>
      fail(
        new AgentApiError(422, 'file_too_many_rows', 'ref-1', [], null, {
          measured: 21000,
          limit: 20000,
        })
      )
    );
    expect(await screen.findByTestId('sheet-error')).toHaveTextContent(
      '"Bericht.xlsx" has more rows than a table may have; filter it, or copy a range and paste it (21,000 rows, the cap is 20,000) · ref ref-1'
    );
    expect(screen.queryByTestId('sheet-reading')).not.toBeInTheDocument();
    expect(onParse).not.toHaveBeenCalled();
  });

  it('shows no sheet picker for a file with one sheet or data from a paste', () => {
    const { rerender } = renderPanel(fromWorkbook('one.xlsx', ['only']));
    expect(screen.queryByTestId('file-sheets')).not.toBeInTheDocument();
    rerender(stateWith({ x: 'month', y1: 'shoes' }));
    expect(screen.queryByTestId('file-sheets')).not.toBeInTheDocument();
  });

  it('shows the file name the server kept, and a withheld one as withheld', () => {
    const withFile = (fileName: string): AgentSessionState => {
      const state: AgentSessionState = stateWith({});
      const { dataset } = state;
      if (!dataset) throw new Error('stateWith gives a dataset');
      return {
        ...state,
        dataset: { ...dataset, parsed: { ...dataset.parsed, file_name: fileName } },
      };
    };
    const { rerender } = renderPanel(withFile('sales.csv'));
    expect(screen.getByTestId('data-file-name')).toHaveTextContent('· from "sales.csv"');

    rerender(withFile('(name withheld)'));
    expect(screen.getByTestId('data-file-name')).toHaveTextContent(
      'name withheld by the content check'
    );
  });
});
