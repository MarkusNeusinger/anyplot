import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  type AgentSessionState,
  type DataSnapshot,
  initialAgentState,
  type TranscriptionState,
} from 'src/hooks/useAgentSession';
import { AgentApiError, type ConvertAnswer, type RoleSpec } from 'src/lib/agent';
import { bindingRows } from 'src/sections/agent-chat/bindings';
import { StepStatus } from 'src/sections/agent-chat/ChatFrame';
import { DataPanel, DataViewUnavailable } from 'src/sections/agent-chat/DataPanel';
import { act, fireEvent, render, screen, userEvent, waitFor, within } from 'src/test-utils';

type PanelProps = Omit<React.ComponentProps<typeof DataPanel>, 'part'>;

/**
 * The card as the page composes it: the stored data's card at its item and the card of a table
 * read from text at its own (`AgentChatPage`, `ChatThread`), and the step's live region by the
 * status line at the frame's foot.
 */
function Panel(props: PanelProps) {
  return (
    <>
      <DataPanel {...props} part="data" />
      <DataPanel {...props} part="transcription" />
      <StepStatus state={props.state} />
    </>
  );
}

/** The bindings' heading while nothing runs. */
const IDLE_HEADING = /^# bindings — which column plays which role$/;

/** `.change()` on the bindings line: the dropdowns open. */
const openBindings = () =>
  fireEvent.click(screen.getByRole('button', { name: 'Change the bindings' }));

/** `matchMedia` at phone width, which the card reads at its first render. */
function stubPhone() {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({
      matches: query === '(max-width: 599.95px)',
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      onchange: null,
      dispatchEvent: vi.fn(),
    }))
  );
}

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
  it('gives every role one row, a family its members and the next one', () => {
    const rows = bindingRows(ROLES, { x: 'month', y1: 'shoes', y2: 'hats' }, COLUMNS.length);
    expect(rows.map(row => [row.name, row.members, row.next])).toEqual([
      ['x', [], null],
      [
        'y',
        [
          ['y1', 'shoes'],
          ['y2', 'hats'],
        ],
        'y3',
      ],
      ['series', [], null],
    ]);
  });

  it('offers a required family without a member its first one', () => {
    const rows = bindingRows(ROLES, { x: 'month' }, COLUMNS.length);
    expect(rows.find(row => row.name === 'y')).toMatchObject({ members: [], next: 'y1' });
  });

  it('stops offering members when every column is taken', () => {
    const rows = bindingRows([ROLES[1]], { y1: 'a', y2: 'b' }, 2);
    expect(rows.map(row => [row.name, row.members.length, row.next])).toEqual([['y', 2, null]]);
  });
});

describe('DataPanel card', () => {
  afterEach(() => vi.unstubAllGlobals());

  const panel = (state: AgentSessionState) => (
    <Panel
      state={state}
      onParse={vi.fn()}
      onConfirmTranscription={vi.fn()}
      onDiscardTranscription={vi.fn()}
      onBind={vi.fn()}
      onUndo={vi.fn()}
      onLoadData={vi.fn(async () => '')}
    />
  );

  it('carries what the data holds on its border, in words for a screen reader', () => {
    render(panel(stateWith({ x: 'month', y1: 'shoes' })));
    const label = screen.getByTestId('data-card-label');
    expect(label).toHaveTextContent(/^data · 1 row × 5 cols data, 1 row by 5 columns$/);
    expect(within(label).getByText('data · 1 row × 5 cols')).toHaveAttribute('aria-hidden');
    expect(screen.queryByText('# your data')).not.toBeInTheDocument();
    // How the data came stays inside: the shape is the label's.
    expect(screen.getByTestId('data-source')).toHaveTextContent(/^read as csv$/);
  });

  it('heads each preview column with its name and its type in the words of the card', () => {
    const base = stateWith({ x: 'month' });
    const columns = [
      { name: 'month', dtype: 'datetime' as const, missing: 0, unique: 1 },
      { name: 'units', dtype: 'integer' as const, missing: 0, unique: 1 },
      { name: 'share', dtype: 'number' as const, missing: 0, unique: 1 },
      { name: 'region', dtype: 'text' as const, missing: 0, unique: 1 },
      { name: 'open', dtype: 'boolean' as const, missing: 0, unique: 1 },
    ];
    const state = {
      ...base,
      dataset: base.dataset && {
        ...base.dataset,
        parsed: {
          ...base.dataset.parsed,
          profile: { ...base.dataset.parsed.profile, columns },
        },
      },
    };
    render(panel(state));
    expect(screen.getAllByRole('columnheader').map(cell => cell.textContent)).toEqual([
      'month · date',
      'units · number',
      'share · number',
      'region · text',
      'open · boolean',
    ]);
  });

  it('says the bindings in one line, x across and y up, and opens the dropdowns on .change()', () => {
    render(panel(stateWith({ x: 'month', y1: 'shoes', y2: 'hats' })));
    // An optional role left open says nothing; a family's columns stand side by side.
    expect(screen.getByTestId('bindings-line')).toHaveTextContent(
      /^x \(across\): month · y \(up\): shoes, hats$/
    );
    expect(screen.queryByTestId('bindings-editor')).not.toBeInTheDocument();
    const toggle = screen.getByRole('button', { name: 'Change the bindings' });
    expect(toggle).toHaveTextContent(/^\.change\(\)$/);
    expect(toggle).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(toggle);
    expect(toggle).toHaveAccessibleName('Hide the bindings');
    expect(toggle).toHaveTextContent(/^\.hide\(\)$/);
    expect(toggle).toHaveAttribute('aria-expanded', 'true');
    expect(toggle).toHaveAttribute('aria-controls', screen.getByTestId('bindings-editor').id);
    expect(screen.getByLabelText(/^x/)).toHaveValue('month');

    fireEvent.click(toggle);
    expect(screen.queryByTestId('bindings-editor')).not.toBeInTheDocument();
    expect(toggle).toHaveAccessibleName('Change the bindings');
  });

  it('names no direction for other roles, and marks a required role without a column', () => {
    const roles = [role('category', { kinds: ['categorical'] }), role('value')];
    render(panel(stateWith({ category: 'region' }, { roles, missingRoles: ['value'] })));
    expect(screen.getByTestId('bindings-line')).toHaveTextContent(
      /^category: region · value: —no column yet$/
    );
  });

  it('says when the plot names no roles, and when no optional role has a column yet', () => {
    const { rerender } = render(panel(stateWith({}, { roles: [] })));
    expect(screen.getByTestId('bindings-line')).toHaveTextContent(
      /^this plot names no data roles$/
    );
    rerender(panel(stateWith({}, { roles: [role('series', { required: false })] })));
    expect(screen.getByTestId('bindings-line')).toHaveTextContent(/^no column bound yet$/);
  });

  it('opens the dropdowns by themselves for a missing role, and keeps them open after the fix', () => {
    const complete = stateWith({ x: 'month', y1: 'shoes' });
    const { rerender } = render(panel(complete));
    expect(screen.queryByTestId('bindings-editor')).not.toBeInTheDocument();

    // A required role lost its column: the dropdowns come, the toggle says they are open.
    rerender(panel(stateWith({ x: 'month' }, { missingRoles: ['y'] })));
    expect(screen.getByTestId('bindings-editor')).toBeInTheDocument();
    expect(screen.getByText('* required: pick a column for y')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Hide the bindings' })).toHaveAttribute(
      'aria-expanded',
      'true'
    );

    // Fixed: the dropdown the user just used stays where it is, until `.hide()`.
    rerender(panel(complete));
    expect(screen.getByTestId('bindings-editor')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Hide the bindings' }));
    expect(screen.queryByTestId('bindings-editor')).not.toBeInTheDocument();
  });

  it('opens the dropdowns by themselves when the server refused the bindings', () => {
    const refused = stateWith(
      { x: 'region' },
      { bindingsError: { code: 'invalid', ref: 'r-b', errors: ['x is text'] } }
    );
    render(panel(refused));
    expect(screen.getByTestId('bindings-editor')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('the server refused these bindings');
  });

  it('shows a bound column’s warning under the line while the dropdowns are closed', () => {
    const radius = role('radius', { non_negative: true });
    const columns = [{ name: 'y', dtype: 'number' as const, missing: 0, unique: 3, min: -2 }];
    const base = stateWith({ radius: 'y' }, { roles: [radius] });
    const state = {
      ...base,
      dataset: base.dataset && {
        ...base.dataset,
        parsed: { ...base.dataset.parsed, profile: { ...base.dataset.parsed.profile, columns } },
      },
    };
    render(panel(state));
    expect(screen.getAllByTestId('sign-hint').map(line => line.textContent)).toEqual([
      'y: has negative values (down to -2); radius needs values of 0 or more',
    ]);
    // Open, the warning stands under its dropdown instead, once.
    openBindings();
    expect(screen.getAllByTestId('sign-hint').map(line => line.textContent)).toEqual([
      'has negative values (down to -2); radius needs values of 0 or more',
    ]);
  });

  it('shows no preview on a phone, and .view_all() beside .change() on the action line', () => {
    stubPhone();
    render(panel(stateWith({ x: 'month', y1: 'shoes' })));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.queryByText(/^# preview/)).not.toBeInTheDocument();
    const actions = within(screen.getByTestId('data-actions'));
    expect(actions.getAllByRole('button').map(button => button.textContent)).toEqual([
      '.view_all()',
      '.change()',
    ]);
    expect(actions.getByRole('button', { name: 'View all 1 row' })).toHaveAttribute(
      'aria-haspopup',
      'dialog'
    );
  });

  it('shows the preview with .view_all() beside it from sm up, and .change() at the line’s end', () => {
    render(panel(stateWith({ x: 'month', y1: 'shoes' })));
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.queryByTestId('data-actions')).not.toBeInTheDocument();
    const line = screen.getByTestId('bindings-line').parentElement as HTMLElement;
    expect(within(line).getByRole('button', { name: 'Change the bindings' })).toBeInTheDocument();
  });
});

describe('DataPanel bindings line pairs', () => {
  // jsdom has no picker: the stub stands in for the browser's `showPicker` on a dropdown.
  const showPicker = vi.fn();
  beforeEach(() => {
    Object.defineProperty(HTMLSelectElement.prototype, 'showPicker', {
      value: showPicker,
      configurable: true,
    });
  });
  afterEach(() => {
    delete (HTMLSelectElement.prototype as Partial<HTMLSelectElement>).showPicker;
    showPicker.mockReset();
  });

  const panel = (state: AgentSessionState, props: Partial<PanelProps> = {}) => (
    <Panel
      state={state}
      onParse={vi.fn()}
      onConfirmTranscription={vi.fn()}
      onDiscardTranscription={vi.fn()}
      onBind={vi.fn()}
      onUndo={vi.fn()}
      onLoadData={vi.fn(async () => '')}
      {...props}
    />
  );
  const line = () => within(screen.getByTestId('bindings-line'));

  it('makes each pair a button named by its action and its words, the line reading as before', () => {
    const roles = [...ROLES, role('size')];
    render(
      panel(stateWith({ x: 'month', y1: 'shoes', y2: 'hats' }, { roles, missingRoles: ['size'] }))
    );
    const pairs = line().getAllByRole('button');
    expect(pairs).toHaveLength(3);
    expect(pairs[0]).toHaveAccessibleName('Change the column for x (across): month');
    expect(pairs[1]).toHaveAccessibleName('Change the columns for y (up): shoes, hats');
    expect(pairs[2]).toHaveAccessibleName('Pick a column for size: none yet');
    expect(screen.getByTestId('bindings-line')).toHaveTextContent(
      /^x \(across\): month · y \(up\): shoes, hats · size: —no column yet$/
    );
  });

  it('opens the dropdowns on a click on a pair, that role’s dropdown focused and its list open', () => {
    const onLook = vi.fn();
    render(panel(stateWith({ x: 'month', y1: 'shoes' }), { onLook }));
    expect(screen.queryByTestId('bindings-editor')).not.toBeInTheDocument();

    fireEvent.click(
      line().getByRole('button', { name: 'Change the column for x (across): month' })
    );
    expect(screen.getByTestId('bindings-editor')).toBeInTheDocument();
    const x = screen.getByLabelText(/^x/);
    expect(x).toHaveFocus();
    expect(showPicker.mock.contexts).toEqual([x]);
    // A look at the data, as `.change()`; the toggle says the dropdowns are open.
    expect(onLook).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: 'Hide the bindings' })).toHaveAttribute(
      'aria-expanded',
      'true'
    );

    // Open already, a family's pair puts the focus on its `+`; its menu stays closed.
    fireEvent.click(line().getByRole('button', { name: 'Change the column for y (up): shoes' }));
    expect(screen.getByRole('button', { name: '+ y: add a column' })).toHaveFocus();
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(showPicker).toHaveBeenCalledTimes(1);
  });

  it('keeps the focus on the dropdown when the browser opens no list for the page', () => {
    showPicker.mockImplementationOnce(() => {
      throw new DOMException('no user activation', 'NotAllowedError');
    });
    render(panel(stateWith({ x: 'month', y1: 'shoes' })));
    fireEvent.click(
      line().getByRole('button', { name: 'Change the column for x (across): month' })
    );
    expect(screen.getByLabelText(/^x/)).toHaveFocus();
  });

  it('puts the focus on a family’s last × once every column is taken', () => {
    const all = { y1: 'month', y2: 'shoes', y3: 'hats', y4: 'scarves', y5: 'region' };
    render(panel(stateWith({ x: 'month', ...all })));
    fireEvent.click(line().getByRole('button', { name: /^Change the columns for y/ }));
    expect(screen.queryByRole('button', { name: '+ y: add a column' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove region from y' })).toHaveFocus();
  });

  it('keeps the pairs words while the dropdowns would not answer', () => {
    const words = /^x \(across\): month · y \(up\): shoes$/;
    const { rerender } = render(panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true })));
    expect(screen.getByTestId('bindings-line')).toHaveTextContent(words);
    expect(line().queryAllByRole('button')).toEqual([]);
    // `.change()` still opens them, to look: they are disabled.
    expect(screen.getByRole('button', { name: 'Change the bindings' })).toBeEnabled();

    // The fan-out's panel copies the data.
    rerender(panel(stateWith({ x: 'month', y1: 'shoes' }), { locked: true }));
    expect(line().queryAllByRole('button')).toEqual([]);

    // No session to bind on.
    rerender(panel(stateWith({ x: 'month', y1: 'shoes' }, { sessionId: null })));
    expect(line().queryAllByRole('button')).toEqual([]);

    rerender(panel(stateWith({ x: 'month', y1: 'shoes' })));
    expect(line().getAllByRole('button')).toHaveLength(2);
    expect(screen.getByTestId('bindings-line')).toHaveTextContent(words);
  });

  it('hands the focus to .change() when a step starts under a focused pair', () => {
    const { rerender } = render(panel(stateWith({ x: 'month', y1: 'shoes' })));
    line().getByRole('button', { name: 'Change the column for x (across): month' }).focus();
    rerender(panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true })));
    expect(line().queryAllByRole('button')).toEqual([]);
    expect(screen.getByRole('button', { name: 'Change the bindings' })).toHaveFocus();

    // A step that starts while the focus is elsewhere leaves it there.
    rerender(panel(stateWith({ x: 'month', y1: 'shoes' })));
    screen.getByRole('button', { name: 'View all 1 row' }).focus();
    rerender(panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true })));
    expect(screen.getByRole('button', { name: 'View all 1 row' })).toHaveFocus();
  });

  it('reaches each pair by Tab, opens on Enter and gives the focus back after Escape', async () => {
    render(panel(stateWith({ x: 'month', y1: 'shoes' })));
    screen.getByRole('button', { name: 'View all 1 row' }).focus();
    await userEvent.tab();
    const x = line().getByRole('button', { name: 'Change the column for x (across): month' });
    expect(x).toHaveFocus();
    await userEvent.tab();
    expect(
      line().getByRole('button', { name: 'Change the column for y (up): shoes' })
    ).toHaveFocus();
    await userEvent.tab();
    expect(screen.getByRole('button', { name: 'Change the bindings' })).toHaveFocus();

    x.focus();
    await userEvent.keyboard('{Enter}');
    expect(screen.getByLabelText(/^x/)).toHaveFocus();
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByTestId('bindings-editor')).not.toBeInTheDocument();
    expect(x).toHaveFocus();
  });

  it('closes a family’s menu on Escape first, then the dropdowns, the focus back on the pair', async () => {
    render(panel(stateWith({ x: 'month', y1: 'shoes' })));
    const y = line().getByRole('button', { name: 'Change the column for y (up): shoes' });
    await userEvent.click(y);
    const add = screen.getByRole('button', { name: '+ y: add a column' });
    await userEvent.click(add);
    expect(screen.getByRole('menu')).toBeInTheDocument();

    await userEvent.keyboard('{Escape}');
    await waitFor(() => expect(screen.queryByRole('menu')).not.toBeInTheDocument());
    expect(screen.getByTestId('bindings-editor')).toBeInTheDocument();
    expect(add).toHaveFocus();

    await userEvent.keyboard('{Escape}');
    expect(screen.queryByTestId('bindings-editor')).not.toBeInTheDocument();
    expect(y).toHaveFocus();
  });

  it('gives the focus to .change() after Escape in the dropdowns it opened', async () => {
    render(panel(stateWith({ x: 'month', y1: 'shoes' })));
    const toggle = screen.getByRole('button', { name: 'Change the bindings' });
    await userEvent.click(toggle);
    screen.getByLabelText(/^x/).focus();
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByTestId('bindings-editor')).not.toBeInTheDocument();
    expect(toggle).toHaveFocus();
    expect(toggle).toHaveAccessibleName('Change the bindings');
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
    openBindings();
    // The kinds in the start item's words, as the chips say them.
    expect(screen.getByText('numbers or dates')).toBeInTheDocument();
    expect(screen.getByText('numbers · one column each')).toBeInTheDocument();
    expect(screen.getByLabelText(/^series/)).toHaveValue('');
    // The spec's own description is the role's tooltip; required roles carry a `*`.
    expect(screen.getByTitle('Multiple continuous series to compare')).toHaveTextContent(/^y \*/);
    expect(screen.getByTitle('series values')).not.toHaveTextContent('*');
    // The family's columns are chips in a list the row names, and `+ y` adds the next member.
    const chips = within(screen.getByRole('list', { name: /^y \*/ })).getAllByRole('listitem');
    expect(chips.map(chip => chip.textContent)).toEqual(['shoes×', '+ y ▾']);
    await userEvent.click(screen.getByRole('button', { name: '+ y: add a column' }));
    await userEvent.click(screen.getByRole('menuitem', { name: 'hats (number)' }));
    expect(onBind).toHaveBeenCalledWith('y2', 'hats');
  });

  it("removes a family's column with its ×, and offers the columns left in a menu", async () => {
    // Two series or eight: one row of chips, never a dropdown per member.
    const onBind = vi.fn();
    render(
      <Panel
        state={stateWith({ x: 'month', y1: 'shoes', y2: 'hats' }, { missingRoles: [] })}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={onBind}
        onUndo={vi.fn()}
      />
    );
    openBindings();
    expect(screen.queryByLabelText('y1')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Remove shoes from y' }));
    expect(onBind).toHaveBeenCalledWith('y1', null);

    // A menu button: its name starts with what it shows, and it says whether its menu is open.
    const add = screen.getByRole('button', { name: '+ y: add a column' });
    expect(add).toHaveAttribute('aria-haspopup', 'menu');
    expect(add).toHaveAttribute('aria-expanded', 'false');
    await userEvent.click(add);
    expect(add).toHaveAttribute('aria-expanded', 'true');
    // The columns the family holds are no choice; one the role cannot take is greyed out with the reason.
    const items = screen.getAllByRole('menuitem');
    expect(items.map(item => item.textContent)).toEqual([
      'month (number)',
      'scarves (number)',
      'region (text) · y takes numbers',
    ]);
    expect(items[2]).toHaveAttribute('aria-disabled', 'true');
    await userEvent.keyboard('{Escape}');
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  });

  it('keeps the keyboard in the row after a change, once the controls answer again', async () => {
    const props = {
      onParse: vi.fn(),
      onConfirmTranscription: vi.fn(),
      onDiscardTranscription: vi.fn(),
      onBind: vi.fn(),
      onUndo: vi.fn(),
    };
    const before = stateWith({ x: 'month', y1: 'shoes', y2: 'hats' }, { missingRoles: [] });
    const { rerender } = render(<Panel state={before} {...props} />);
    openBindings();
    await userEvent.click(screen.getByRole('button', { name: 'Remove shoes from y' }));
    // The change is on its way: the controls wait, then the next chip takes the removed one's place.
    rerender(<Panel state={{ ...before, bindingsBusy: true }} {...props} />);
    rerender(
      <Panel state={stateWith({ x: 'month', y1: 'hats' }, { missingRoles: [] })} {...props} />
    );
    expect(screen.getByRole('button', { name: 'Remove hats from y' })).toHaveFocus();
  });

  it("gives the last chip's place to `+`, which follows it", async () => {
    const props = {
      onParse: vi.fn(),
      onConfirmTranscription: vi.fn(),
      onDiscardTranscription: vi.fn(),
      onBind: vi.fn(),
      onUndo: vi.fn(),
    };
    const before = stateWith({ x: 'month', y1: 'shoes', y2: 'hats' }, { missingRoles: [] });
    const { rerender } = render(<Panel state={before} {...props} />);
    openBindings();
    await userEvent.click(screen.getByRole('button', { name: 'Remove hats from y' }));
    rerender(<Panel state={{ ...before, bindingsBusy: true }} {...props} />);
    rerender(
      <Panel state={stateWith({ x: 'month', y1: 'shoes' }, { missingRoles: [] })} {...props} />
    );
    expect(screen.getByRole('button', { name: '+ y: add a column' })).toHaveFocus();
  });

  it('gives the focus to the chip that took the last column, where `+` goes', async () => {
    const props = {
      onParse: vi.fn(),
      onConfirmTranscription: vi.fn(),
      onDiscardTranscription: vi.fn(),
      onBind: vi.fn(),
      onUndo: vi.fn(),
    };
    // Every column but `scarves` in the family: adding it leaves nothing for `+`.
    const four = { x: 'month', y1: 'shoes', y2: 'hats', y3: 'month', y4: 'region' };
    const before = stateWith(four, { missingRoles: [] });
    const { rerender } = render(<Panel state={before} {...props} />);
    openBindings();
    await userEvent.click(screen.getByRole('button', { name: '+ y: add a column' }));
    await userEvent.click(screen.getByRole('menuitem', { name: 'scarves (number)' }));
    rerender(<Panel state={{ ...before, bindingsBusy: true }} {...props} />);
    rerender(
      <Panel state={stateWith({ ...four, y5: 'scarves' }, { missingRoles: [] })} {...props} />
    );
    expect(screen.queryByRole('button', { name: '+ y: add a column' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Remove scarves from y' })).toHaveFocus();
  });

  it('leaves the focus where the user put it meanwhile', async () => {
    const props = {
      onParse: vi.fn(),
      onConfirmTranscription: vi.fn(),
      onDiscardTranscription: vi.fn(),
      onBind: vi.fn(),
      onUndo: vi.fn(),
    };
    const before = stateWith({ x: 'month', y1: 'shoes', y2: 'hats' }, { missingRoles: [] });
    const { rerender } = render(<Panel state={before} {...props} />);
    openBindings();
    await userEvent.click(screen.getByRole('button', { name: 'Remove shoes from y' }));
    rerender(<Panel state={{ ...before, bindingsBusy: true }} {...props} />);
    const series = screen.getByLabelText(/^series/);
    series.removeAttribute('disabled');
    series.focus();
    rerender(
      <Panel state={stateWith({ x: 'month', y1: 'hats' }, { missingRoles: [] })} {...props} />
    );
    expect(screen.getByLabelText(/^series/)).toHaveFocus();
  });

  it("names a family's negative column in its warning", () => {
    const area = role('y', { variadic: true, non_negative: true });
    const columns = [
      { name: 'month', dtype: 'number' as const, missing: 0, unique: 3, min: 1 },
      { name: 'loss', dtype: 'number' as const, missing: 0, unique: 3, min: -4 },
    ];
    const base = stateWith({ y1: 'month', y2: 'loss' }, { roles: [area], missingRoles: [] });
    const state = {
      ...base,
      dataset: base.dataset && {
        ...base.dataset,
        parsed: {
          ...base.dataset.parsed,
          profile: { ...base.dataset.parsed.profile, columns },
          roles: [area],
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
    openBindings();
    expect(screen.getAllByTestId('sign-hint').map(line => line.textContent)).toEqual([
      'loss: has negative values (down to -4); y needs values of 0 or more',
    ]);
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
    openBindings();
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
    // A role the plot computes says nothing on the line while it is left open.
    expect(screen.getByTestId('bindings-line')).toHaveTextContent(/^close: shoes$/);
    openBindings();
    const sma = screen.getByLabelText(/^sma/) as HTMLSelectElement;
    expect(sma.value).toBe('');
    expect(sma.options[0]).toHaveTextContent('— computed by the plot —');
    expect(container.querySelector('label[for="agent-role-sma"]')).not.toHaveTextContent('*');
    expect(container.querySelector('label[for="agent-role-close"]')).toHaveTextContent('close *');
    await userEvent.selectOptions(sma, 'hats');
    expect(onBind).toHaveBeenCalledWith('sma', 'hats');
  });

  it('greys out the columns a role cannot take, with the reason, and never sends them', () => {
    render(
      <Panel
        state={stateWith({ x: 'month', y1: 'shoes' })}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={vi.fn()}
      />
    );
    openBindings();
    const option = (select: RegExp, column: string) =>
      [...(screen.getByLabelText(select) as HTMLSelectElement).options].find(
        item => item.value === column
      );

    // The reason in the chips' words: what the role takes.
    expect(option(/^x/, 'region')).toHaveTextContent('region (text) · x takes numbers or dates');
    expect(option(/^x/, 'region')).toBeDisabled();
    expect(option(/^series/, 'shoes')).toHaveTextContent(
      'shoes (number) · series takes categories'
    );
    expect(option(/^series/, 'region')).toBeEnabled();
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
    // Opening the dropdowns is only a look, so `.change()` works while the session is busy.
    openBindings();
    expect(screen.getByLabelText(/^x/)).toBeDisabled();

    // Step 2: the card stays open as it was, the dropdowns too, and nothing in it starts.
    rerender(
      panel(stateWith({ x: 'month', y1: 'shoes' }, { themeBusy: true, dataConfirmed: true }))
    );
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
      dataset: { ...stored, parsed: { ...stored.parsed, version: 2, can_undo: true } },
    };
    const { rerender } = render(panel(versioned, true));
    openBindings();
    const card = screen.getByRole('region', { name: 'Your data' });
    const line = '# the data waits while all libraries plot it · .close() the panel to change it';
    expect(screen.getByTestId('data-lock')).toHaveTextContent(line);
    expect(card).toHaveAccessibleDescription(line);
    // Nothing that changes the data or its confirmation starts; the session itself is idle.
    expect(screen.getByTestId('bindings-heading')).toHaveTextContent(IDLE_HEADING);
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

  it('stays open in both steps, through the confirmation and back to step 1', () => {
    const confirmed = stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true });
    const { rerender } = renderPanel(stateWith({ x: 'month', y1: 'shoes' }));
    const card = screen.getByRole('region', { name: 'Your data' });
    openBindings();
    // The confirmation `.create_plot()` starts with, then step 2: the same card, open as it was,
    // its dropdowns too; no header, no `.show()` or `.hide()` for the card.
    rerender(stateWith({ x: 'month', y1: 'shoes' }, { confirmBusy: true }));
    rerender(confirmed);
    expect(screen.getByRole('region', { name: 'Your data' })).toBe(card);
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 2: the data is confirmed; create the plot below'
    );
    expect(within(card).getByLabelText(/^x/)).toBeEnabled();
    expect(screen.queryByRole('button', { name: /the data$/ })).not.toBeInTheDocument();
    expect(screen.queryByText(/a change here takes the data back/)).not.toBeInTheDocument();
    // Step 2's action is the page composer's, not the card's.
    expect(screen.queryByRole('button', { name: 'Create plot' })).not.toBeInTheDocument();

    // A binding change, a data change or an undo dropped the confirmation: the status line at
    // the frame's foot names it, and the card says nothing of its own.
    rerender({ ...confirmed, dataConfirmed: false, confirmLoss: 'bindings' });
    expect(screen.getByRole('region', { name: 'Your data' })).toBe(card);
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 1: check the data, then create the plot'
    );
    expect(screen.queryByText(/step 1 again/)).not.toBeInTheDocument();
  });

  it('holds step 1 while a table read from text waits, beside the open card', () => {
    const confirmed = stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true });
    const { rerender } = renderPanel(confirmed);
    // The server keeps its confirmation until `.use()`, and a turn's sync can report it.
    rerender({ ...confirmed, transcription: TRANSCRIPTION });
    expect(screen.getByTestId('transcription-card')).toBeVisible();
    expect(screen.getByTestId('data-card')).toBeVisible();
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 1: check the data, then create the plot'
    );
  });
});

describe('DataPanel version', () => {
  afterEach(() => vi.unstubAllGlobals());

  const snapshot = (n: number, change: DataSnapshot['change'], summary: string): DataSnapshot => ({
    n,
    change,
    summary,
    label: `data v${n} · ${summary}`,
    rows: 1,
    columns: 5,
    sheet: null,
    fileName: null,
    changes: [],
    preview: [],
    profile: { rows: 1, columns: COLUMNS, source_format: 'csv', decimal: '.', warnings: [] },
  });

  /**
   * The live card as the thread holds it: an item among others in one list, where a new version
   * can move it to the end under its own key, as `ChatThread` renders the card's `data` item.
   */
  function Thread({
    state,
    version,
    last,
    onUndo,
  }: {
    state: AgentSessionState;
    version: DataSnapshot;
    last: boolean;
    onUndo: () => void;
  }) {
    const card = (
      <DataPanel
        key="card"
        state={state}
        part="data"
        version={version}
        onParse={vi.fn()}
        onConfirmTranscription={vi.fn()}
        onDiscardTranscription={vi.fn()}
        onBind={vi.fn()}
        onUndo={onUndo}
        onToLong={vi.fn()}
      />
    );
    const plot = <div key="plot">plot v1</div>;
    return <div>{last ? [plot, card] : [card, plot]}</div>;
  }

  it('carries its version on its border: the number, how it came and the shape', () => {
    render(
      <Thread
        state={stateWith({ x: 'month', y1: 'shoes' })}
        version={snapshot(3, 'to_long', 'made long')}
        last={false}
        onUndo={vi.fn()}
      />
    );
    const label = screen.getByTestId('data-card-label');
    expect(label).toHaveTextContent(
      /^data v3 · made long · 1 row × 5 cols Data v3, made long, 1 row by 5 columns$/
    );
    expect(within(label).getByText('data v3 · made long · 1 row × 5 cols')).toHaveAttribute(
      'aria-hidden'
    );
    // A target for the focus from code only, never in the tab order.
    expect(label).toHaveAttribute('tabindex', '-1');
  });

  it('keeps the focus on .undo() when the version it made moves the card below the plot', async () => {
    const onUndo = vi.fn();
    const before = changedState(3);
    const view = render(
      <Thread
        state={before}
        version={snapshot(3, 'turn', 'changed')}
        last={false}
        onUndo={onUndo}
      />
    );
    const card = screen.getByTestId('data-card');
    const undo = within(card).getByRole('button', { name: '.undo()' });
    await userEvent.click(undo);
    expect(onUndo).toHaveBeenCalledTimes(1);
    expect(undo).toHaveFocus();

    // The undo runs, then lands: back to v2 under its own number, the card at the thread's end,
    // with one more version to undo.
    view.rerender(
      <Thread
        state={changedState(3, { undoBusy: true })}
        version={snapshot(3, 'turn', 'changed')}
        last={false}
        onUndo={onUndo}
      />
    );
    view.rerender(
      <Thread
        state={changedState(2, { dataChange: { kind: 'undone', version: 2 } })}
        version={snapshot(2, 'undo', 'back to v2')}
        last
        onUndo={onUndo}
      />
    );
    // The same card, moved: the plot stands above it now, and the focus is back on `.undo()`.
    expect(screen.getByTestId('data-card')).toBe(card);
    expect(card.previousElementSibling).toHaveTextContent('plot v1');
    expect(within(card).getByRole('button', { name: '.undo()' })).toHaveFocus();
  });

  it("puts the focus on the card's label when the control went with its version", async () => {
    const plain = stateWith({ x: 'month', y1: 'shoes' });
    const offer = {
      kind: 'to_long' as const,
      columns: ['shoes', 'hats', 'scarves'],
      names_to: 'item',
      values_to: 'sold',
      keys: [],
      rows: 3,
      siblings: [],
    };
    const before = {
      ...plain,
      dataset: plain.dataset && {
        ...plain.dataset,
        parsed: { ...plain.dataset.parsed, suggestion: offer },
      },
    };
    const view = render(
      <Thread
        state={before}
        version={snapshot(1, 'paste', 'pasted')}
        last={false}
        onUndo={vi.fn()}
      />
    );
    const toLong = screen.getByRole('button', { name: 'Make the table long' });
    await userEvent.click(toLong);
    expect(toLong).toHaveFocus();
    // `.to_long()` applied: the offer is gone with its button, and the card moved below the plot.
    view.rerender(
      <Thread
        state={stateWith({ x: 'month', y1: 'shoes' })}
        version={snapshot(2, 'to_long', 'made long')}
        last
        onUndo={vi.fn()}
      />
    );
    expect(screen.queryByRole('button', { name: 'Make the table long' })).not.toBeInTheDocument();
    expect(screen.getByTestId('data-card-label')).toHaveFocus();
  });

  it('leaves the focus where the user is when a turn makes the version', async () => {
    const box = document.createElement('textarea');
    document.body.append(box);
    try {
      const view = render(
        <Thread
          state={stateWith({ x: 'month', y1: 'shoes' })}
          version={snapshot(1, 'paste', 'pasted')}
          last={false}
          onUndo={vi.fn()}
        />
      );
      // The user was in the card, then went on to the message box and sent a data request.
      await userEvent.click(
        within(screen.getByTestId('data-card')).getByRole('button', {
          name: 'Change the bindings',
        })
      );
      box.focus();
      view.rerender(
        <Thread
          state={stateWith({ x: 'month', y1: 'shoes' })}
          version={snapshot(2, 'turn', 'changed')}
          last
          onUndo={vi.fn()}
        />
      );
      expect(box).toHaveFocus();
    } finally {
      box.remove();
    }
  });

  it('follows a press that gave no focus (Safari), unless a press outside came after it', () => {
    const plain = (next: DataSnapshot, last: boolean, state = changedState(2)) => (
      <Thread state={state} version={next} last={last} onUndo={vi.fn()} />
    );
    const undone = changedState(1, { dataChange: { kind: 'undone', version: 1 } });
    // A press on `.undo()` that focuses nothing, as Safari's click on a button does.
    const view = render(plain(snapshot(2, 'turn', 'changed'), false));
    fireEvent.pointerDown(
      within(screen.getByTestId('data-card')).getByRole('button', { name: '.undo()' })
    );
    view.rerender(plain(snapshot(1, 'undo', 'back to v1'), true, undone));
    expect(screen.getByTestId('data-card-label')).toHaveFocus();
    view.unmount();

    // The same press, then one on the page outside while the version is on its way.
    const again = render(plain(snapshot(2, 'turn', 'changed'), false));
    fireEvent.pointerDown(
      within(screen.getByTestId('data-card')).getByRole('button', { name: '.undo()' })
    );
    fireEvent.pointerDown(document.body);
    again.rerender(plain(snapshot(1, 'undo', 'back to v1'), true, undone));
    expect(document.body).toHaveFocus();
    again.unmount();

    // The keyboard visited `.change()` before; the press names `.undo()`, which can still go
    // back one more step, so the focus lands on it, never on the control visited earlier.
    const visited = render(plain(snapshot(3, 'turn', 'changed'), false, changedState(3)));
    const card = within(screen.getByTestId('data-card'));
    const change = card.getByRole('button', { name: 'Change the bindings' });
    change.focus();
    change.blur();
    fireEvent.pointerDown(card.getByRole('button', { name: '.undo()' }));
    visited.rerender(
      plain(
        snapshot(2, 'undo', 'back to v2'),
        true,
        changedState(2, { dataChange: { kind: 'undone', version: 2 } })
      )
    );
    expect(card.getByRole('button', { name: '.undo()' })).toHaveFocus();
  });

  it('never pulls the focus back into the card after a press on the page outside it', async () => {
    const view = render(
      <Thread
        state={stateWith({ x: 'month', y1: 'shoes' })}
        version={snapshot(1, 'paste', 'pasted')}
        last={false}
        onUndo={vi.fn()}
      />
    );
    const change = within(screen.getByTestId('data-card')).getByRole('button', {
      name: 'Change the bindings',
    });
    await userEvent.click(change);
    expect(change).toHaveFocus();
    // A click on the page's background: the body takes the focus, with no element to name.
    fireEvent.pointerDown(document.body);
    change.blur();
    view.rerender(
      <Thread
        state={stateWith({ x: 'month', y1: 'shoes' })}
        version={snapshot(2, 'turn', 'changed')}
        last
        onUndo={vi.fn()}
      />
    );
    expect(document.body).toHaveFocus();
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

  it('says why the bindings wait in their heading, exactly while something runs', () => {
    const idle = stateWith({ x: 'month', y1: 'shoes' });
    const { rerender } = renderPanel(idle);
    openBindings();
    const heading = () => screen.getByTestId('bindings-heading');
    expect(heading()).toHaveTextContent(IDLE_HEADING);
    expect(screen.queryByTestId('parse-hint')).not.toBeInTheDocument();

    rerender({ ...idle, run: summaryTurn });
    // The heading swaps in its place: a second line under it read as the heading twice and moved
    // the dropdowns as it came and went.
    expect(heading()).toHaveTextContent(/^# bindings — wait while the assistant works$/);
    expect(screen.queryByText(/^# bindings wait while/)).not.toBeInTheDocument();
    // The lock stays (the server would refuse the change); the controls keep their look.
    expect(screen.getByLabelText(/^x/)).toBeDisabled();

    // A binding change, a confirmation or a theme render reads the same: the assistant works.
    rerender({ ...idle, bindingsBusy: true });
    expect(heading()).toHaveTextContent(/wait while the assistant works$/);

    rerender(idle);
    expect(heading()).toHaveTextContent(IDLE_HEADING);
    expect(screen.getByLabelText(/^x/)).toBeEnabled();
  });

  it('keeps every heading of the bindings in one place, the unseen ones hidden from a screen reader', () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }));
    openBindings();
    const heading = screen.getByTestId('bindings-heading');
    // The three texts stack in one grid cell, so a swap never changes the heading's line count.
    const stack = [...(heading.parentElement?.children ?? [])];
    expect(stack.map(item => item.textContent)).toEqual([
      '# bindings — which column plays which role',
      '# bindings — wait while the assistant works',
      '# bindings — wait while the data is parsed',
    ]);
    expect(
      stack.filter(item => item !== heading).map(item => item.getAttribute('aria-hidden'))
    ).toEqual(['true', 'true']);
  });

  it('says that the data is parsed on the bindings and to a screen reader, with no loader of its own', () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }, { parsing: true }));
    openBindings();

    // The attachment's chip in the composer holds the parse's one loader; the card only says it.
    expect(screen.queryByTestId('loader-spinner')).not.toBeInTheDocument();
    expect(screen.getByTestId('bindings-heading')).toHaveTextContent(
      /^# bindings — wait while the data is parsed$/
    );
    expect(screen.getByTestId('data-step-status')).toHaveTextContent('parsing your data');
  });

  it('names the same bindings lock in step 2', async () => {
    renderPanel(stateWith({ x: 'month', y1: 'shoes' }, { dataConfirmed: true, themeBusy: true }));
    openBindings();
    expect(screen.getByTestId('bindings-heading')).toHaveTextContent(
      /^# bindings — wait while the assistant works$/
    );
  });
});

const CHANGES = [
  "renamed 'Study Hours' to 'Hours'",
  "dropped 1 row where Tier = 'Gesamt'",
  'summed Umsatz by Datum (month): 3 rows, 2 other columns dropped',
];

/**
 * The panel after the assistant changed the data, now at `version`, as the server answers a
 * chain of changes on one paste numbered 1: a version to undo while it is above the paste.
 */
function changedState(
  version: number,
  overrides: Partial<AgentSessionState> = {}
): AgentSessionState {
  const base = stateWith({ x: 'month', y1: 'shoes' });
  const dataset = base.dataset && {
    ...base.dataset,
    parsed: { ...base.dataset.parsed, version, can_undo: version > 1, original_version: 1 },
  };
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
    // No version number in the block: the card's label on its border names the version.
    expect(block.getByText('# changed')).toBeInTheDocument();
    expect(block.getAllByRole('listitem').map(item => item.textContent)).toEqual(CHANGES);
    expect(
      screen.getByTestId('data-change').compareDocumentPosition(screen.getByText(/^# preview/)) &
        Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();
    const undo = screen.getByRole('button', { name: '.undo()' });
    expect(undo).toHaveAccessibleDescription('# changed');
    await userEvent.click(undo);
    expect(onUndo).toHaveBeenCalledTimes(1);
    // The changed data is unconfirmed: the panel is at step 1 again, the card open.
    expect(screen.getByTestId('data-step-status')).toHaveTextContent(
      'step 1: check the data, then create the plot'
    );
  });

  it('says an undo brought the version before back, and holds .undo() at the paste', () => {
    const { rerender } = renderPanel(
      changedState(1, { dataChange: { kind: 'undone', version: 1 } })
    );
    const block = within(screen.getByTestId('data-change'));
    expect(block.getByText('# undone · back to the version before')).toBeInTheDocument();
    expect(block.queryAllByRole('listitem')).toHaveLength(0);
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();

    // Two changes, one undone: the first can still go.
    rerender(changedState(2, { dataChange: { kind: 'undone', version: 2 } }));
    expect(screen.getByText('# undone · back to the version before')).toBeInTheDocument();
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

  it("reads .undo() from the server's can_undo, never from the version's number", () => {
    const at = (version: number, canUndo: boolean, overrides: Partial<AgentSessionState> = {}) => {
      const state = changedState(version, overrides);
      return {
        ...state,
        dataset: state.dataset && {
          ...state.dataset,
          parsed: { ...state.dataset.parsed, can_undo: canUndo },
        },
      };
    };
    // Back at a second paste, numbered 4 in the session: nothing to undo, whatever the number.
    const { rerender } = renderPanel(at(4, false, { dataChange: { kind: 'undone', version: 4 } }));
    expect(screen.getByRole('button', { name: '.undo()' })).toBeDisabled();
    // Its change, v5, can go back.
    rerender(at(5, true));
    expect(screen.getByRole('button', { name: '.undo()' })).toBeEnabled();
    // A change with nothing before it (a table computed as new data): no `.undo()` at all,
    // whatever its number.
    rerender(at(3, false));
    expect(screen.queryByRole('button', { name: /\.undo\(\)/ })).not.toBeInTheDocument();
    // An older server sends no `can_undo`: the page asks for no undo it cannot be sure of.
    const older = changedState(2);
    rerender({
      ...older,
      dataset: older.dataset && {
        ...older.dataset,
        parsed: { ...older.dataset.parsed, can_undo: undefined },
      },
    });
    expect(screen.queryByRole('button', { name: /\.undo\(\)/ })).not.toBeInTheDocument();
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
    expect(block.getByText('# changed')).toBeInTheDocument();
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
      'animal · text',
      'count · number',
    ]);
    expect(card.getAllByRole('row')).toHaveLength(4);
    expect(card.getByRole('cell', { name: 'Katze' })).toBeInTheDocument();
    // Its frame's label says what waits there.
    expect(screen.getByTestId('transcription-label')).toHaveTextContent(
      /^read from text · 3 rows × 2 cols table read from text, 3 rows by 2 columns$/
    );
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
      '"Bericht.xlsx" has more rows than a table may have; filter it, or copy a range and paste it (21,000 rows, the cap is 20,000)'
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
