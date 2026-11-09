import { describe, expect, it } from 'vitest';

import {
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
  type ParseResult,
} from 'src/hooks/useAgentSession';
import type { DatasetParsed, LongSuggestion, RoleSpec } from 'src/lib/agent';
import {
  boxData,
  type ChainRead,
  chainStep,
  endsWithQuestion,
  sameStopMark,
  stopMark,
  warnedRole,
} from 'src/sections/agent-chat/plotChain';
import type { Attachment } from 'src/sections/agent-chat/useChatAttachment';

const role = (name: string, extra: Partial<RoleSpec> = {}): RoleSpec => ({
  name,
  kinds: ['numeric'],
  required: true,
  variadic: false,
  description: '',
  ...extra,
});

const PARSED: DatasetParsed = {
  preview: [['1', '2']],
  profile: {
    rows: 3,
    columns: [
      { name: 'hours', dtype: 'number', missing: 0, unique: 3, min: 1, max: 3 },
      { name: 'score', dtype: 'number', missing: 0, unique: 3, min: -2, max: 9 },
    ],
    source_format: 'csv',
    decimal: '.',
    warnings: [],
  },
  bindings: [
    { role: 'x', column: 'hours' },
    { role: 'y', column: 'score' },
  ],
  warnings: [],
  version: 1,
};

/** The thread after the click's paste: the paste, its card, the summary and its reply. */
const READ_ITEMS: ChatItem[] = [
  { id: 4, kind: 'paste', text: '▤ table · 4 lines · 33 B' },
  { id: 5, kind: 'data' },
  { id: 6, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
  { id: 7, kind: 'assistant', text: 'Read 3 rows: hours on x, score on y.' },
];

/** A session after a clean reading: data stored, bound, checked, nothing in flight. */
function read(overrides: Partial<AgentSessionState> = {}): AgentSessionState {
  return {
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
    dataset: { parsed: PARSED, bytes: 33 },
    roles: [role('x'), role('y')],
    bindings: { x: 'hours', y: 'score' },
    bindingsComplete: true,
    bindingWarnings: [],
    items: [{ id: 1, kind: 'assistant', text: 'Earlier: which column is x?' }, ...READ_ITEMS],
    ...overrides,
  };
}

const stored: ParseResult = { outcome: 'stored', turnEnd: 'done' };
const chain = (overrides: Partial<ChainRead> = {}): ChainRead => ({
  result: stored,
  since: 4,
  rechecked: false,
  ...overrides,
});
const page = { plotAll: false, attachment: false };

describe('chainStep', () => {
  it('plots after a clean reading, whatever an earlier reply asked', () => {
    expect(chainStep(read(), chain(), page)).toEqual({ kind: 'plot' });
  });

  it('waits while anything is in flight or a switch the reading asked for is still to come', () => {
    expect(chainStep(read({ bindingsBusy: true }), chain(), page)).toEqual({ kind: 'wait' });
    expect(chainStep(read({ libraryBusy: true }), chain(), page)).toEqual({ kind: 'wait' });
    expect(
      chainStep(read({ chatSwitch: { library: 'seaborn', plot: true } }), chain(), page)
    ).toEqual({ kind: 'wait' });
  });

  it('ends without words of its own when nothing was stored, or the step line says what comes', () => {
    const end = { kind: 'stop', stop: null };
    for (const outcome of ['transcribed', 'failed', 'forwarded', 'skipped'] as const) {
      expect(chainStep(read(), chain({ result: { outcome, turnEnd: null } }), page)).toEqual(end);
    }
    // The turn never ended (the page unmounted), a required role without a column, the admin's
    // fan-out, a new attachment in the box, a table read from text to decide on.
    expect(
      chainStep(read(), chain({ result: { outcome: 'stored', turnEnd: null } }), page)
    ).toEqual(end);
    expect(
      chainStep(read({ bindingsComplete: false, missingRoles: ['y'] }), chain(), page)
    ).toEqual(end);
    expect(chainStep(read(), chain(), { ...page, plotAll: true })).toEqual(end);
    expect(chainStep(read(), chain(), { ...page, attachment: true })).toEqual(end);
    expect(chainStep(read({ phase: 'error' }), chain(), page)).toEqual(end);
  });

  it('never plots a second time after a plot click or a plot since the click', () => {
    const clicked = read({
      items: [
        ...READ_ITEMS,
        { id: 8, kind: 'action', action: 'create_plot', library: 'matplotlib' },
      ],
    });
    expect(chainStep(clicked, chain(), page)).toEqual({ kind: 'stop', stop: null });
    const plotted = read({ items: [...READ_ITEMS, { id: 8, kind: 'plot', version: 1 }] });
    expect(chainStep(plotted, chain(), page)).toEqual({ kind: 'stop', stop: null });
  });

  it('stops on a stopped, refused or failed reading, and on a refusal or an error after it', () => {
    const reason = (step: ReturnType<typeof chainStep>) =>
      step.kind === 'stop' ? step.stop?.reason : step.kind;
    expect(
      reason(chainStep(read(), chain({ result: { outcome: 'stored', turnEnd: 'stopped' } }), page))
    ).toBe('stopped');
    expect(
      reason(chainStep(read(), chain({ result: { outcome: 'stored', turnEnd: 'refused' } }), page))
    ).toBe('refused');
    expect(
      reason(chainStep(read(), chain({ result: { outcome: 'stored', turnEnd: 'error' } }), page))
    ).toBe('error');
    const refusal: ChatItem = { id: 9, kind: 'refusal', code: 'out_of_scope', text: 'no' };
    expect(reason(chainStep(read({ items: [...READ_ITEMS, refusal] }), chain(), page))).toBe(
      'refused'
    );
    // A chat switch the server refused leaves its error in the thread.
    const error: ChatItem = { id: 9, kind: 'error', code: 'not_eligible', ref: null };
    expect(reason(chainStep(read({ items: [...READ_ITEMS, error] }), chain(), page))).toBe('error');
  });

  it('stops on what the data card shows: the parser, several tables, a wide table, a bound column', () => {
    const withParsed = (parsed: Partial<DatasetParsed>) =>
      read({ dataset: { parsed: { ...PARSED, ...parsed }, bytes: 33 } });
    expect(chainStep(withParsed({ warnings: ['a', 'b'] }), chain(), page)).toEqual({
      kind: 'stop',
      stop: { reason: 'data_warnings', count: 2 },
    });
    expect(
      chainStep(withParsed({ tables: ['a · 3 rows', 'b · 2 rows'], table: 1 }), chain(), page)
    ).toEqual({ kind: 'stop', stop: { reason: 'tables', count: 2 } });
    const suggestion: LongSuggestion = {
      kind: 'to_long',
      columns: ['Mo', 'Tu'],
      names_to: 'Weekday',
      values_to: 'Value',
      keys: [],
      rows: 6,
      siblings: ['Mo', 'Tu'],
    };
    expect(chainStep(withParsed({ suggestion }), chain(), page)).toEqual({
      kind: 'stop',
      stop: { reason: 'wide' },
    });
    // `y` needs values of 0 or more, and `score` goes down to -2.
    const signed = read({ roles: [role('x'), role('y', { non_negative: true })] });
    expect(chainStep(signed, chain(), page)).toEqual({
      kind: 'stop',
      stop: { reason: 'binding_warning', role: 'y' },
    });
    expect(
      chainStep(read({ bindingsError: { code: 'invalid', ref: null } }), chain(), page)
    ).toEqual({
      kind: 'stop',
      stop: { reason: 'bindings_failed' },
    });
  });

  it("asks the binding check again once when its warnings are unknown, and stops on the server's", () => {
    expect(chainStep(read({ bindingWarnings: null }), chain(), page)).toEqual({ kind: 'recheck' });
    expect(chainStep(read({ bindingWarnings: null }), chain({ rechecked: true }), page)).toEqual({
      kind: 'stop',
      stop: null,
    });
    const repeated = "x: column 'hours' holds 2 values in 3 rows; the plot draws one value per x";
    expect(chainStep(read({ bindingWarnings: [repeated] }), chain(), page)).toEqual({
      kind: 'stop',
      stop: { reason: 'binding_warning', role: 'x' },
    });
  });

  it("stops on the reading's last reply when it asks a question", () => {
    const asked: ChatItem = { id: 8, kind: 'assistant', text: 'Is hours the x axis?' };
    expect(chainStep(read({ items: [...READ_ITEMS, asked] }), chain(), page)).toEqual({
      kind: 'stop',
      stop: { reason: 'question' },
    });
    // A question earlier in the reading that a later reply settled does not stop it.
    const settled: ChatItem = { id: 9, kind: 'assistant', text: 'I read hours as x.' };
    expect(chainStep(read({ items: [...READ_ITEMS, asked, settled] }), chain(), page)).toEqual({
      kind: 'plot',
    });
  });
});

describe('endsWithQuestion', () => {
  it.each([
    ['Is hours the x axis?', true],
    ['Ist Jahr die x-Achse? ', true],
    ['Which one: **x or y?**', true],
    ['“Is it daily?”', true],
    ['是每天吗？', true],
    ['هل هذا صحيح؟', true],
    ['Read 3 rows.', false],
    ['Read 3 rows (is it daily?).', false],
    ['', false],
  ])('%s → %s', (text, asks) => {
    expect(endsWithQuestion(text)).toBe(asks);
  });
});

describe('warnedRole', () => {
  it('names the role before the warning text, or the bindings', () => {
    expect(warnedRole("size: column 'r' has negative values (down to -1)")).toBe('size');
    expect(warnedRole("min_value and max_value: every value of 'lo' lies above")).toBe(
      'min_value and max_value'
    );
    expect(warnedRole('something without a role')).toBe('the bindings');
  });
});

describe('boxData', () => {
  const attachment = (status: Attachment['status']): Attachment => ({
    id: 1,
    via: 'file',
    text: 'a,b\n1,2\n',
    name: 'data.csv',
    lines: 2,
    bytes: 8,
    notes: [],
    converted: null,
    kind: 'text',
    encoding: 'utf-8',
    status,
    error: null,
    readingLine: null,
  });

  it('sends an attachment that the dataset route can take, with a note under the cap', () => {
    expect(boxData(attachment('ready'), 'make it blue')).toBe('attachment');
    expect(boxData(attachment('failed'), '')).toBe('attachment');
    expect(boxData(attachment('reading'), '')).toBeNull();
    expect(boxData(attachment('over_cap'), '')).toBeNull();
    expect(boxData(attachment('sending'), '')).toBeNull();
    expect(boxData(attachment('ready'), 'a'.repeat(2001))).toBeNull();
  });

  it('sends a table typed into the box, and never a message', () => {
    expect(boxData(null, 'hours,score\n1.5,52\n2.0,58\n3.0,61\n')).toBe('typed');
    expect(boxData(null, 'make the bars blue')).toBeNull();
    expect(boxData(null, '   ')).toBeNull();
  });
});

describe('stopMark', () => {
  it('holds while the data, the bindings, the thread and the library stay', () => {
    const state = read();
    const mark = stopMark(state);
    expect(sameStopMark(mark, { ...state })).toBe(true);
    expect(sameStopMark(mark, { ...state, bindings: { x: 'score', y: 'hours' } })).toBe(false);
    expect(sameStopMark(mark, { ...state, items: [...state.items, READ_ITEMS[0]] })).toBe(false);
    expect(sameStopMark(mark, { ...state, library: 'seaborn' })).toBe(false);
  });
});
