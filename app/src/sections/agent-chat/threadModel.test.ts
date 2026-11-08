import { describe, expect, it } from 'vitest';

import {
  agentReducer,
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
} from 'src/hooks/useAgentSession';
import type { DatasetChanged, DatasetParsed, PlotResult } from 'src/lib/agent';
import {
  cutRequest,
  PLOT_SUMMARY_MAX,
  plotSummaries,
  threadModel,
} from 'src/sections/agent-chat/threadModel';

const PARSED = {
  preview: [['1', '2']],
  profile: {
    rows: 12,
    columns: [
      { name: 'a', dtype: 'number', missing: 0, unique: 12 },
      { name: 'b', dtype: 'number', missing: 0, unique: 12 },
    ],
    source_format: 'csv',
    decimal: '.',
    warnings: [],
  },
  bindings: [{ role: 'x', column: 'a' }],
  warnings: [],
  version: 1,
  can_undo: false,
  original_version: 1,
} as unknown as DatasetParsed;

const CHANGED = {
  ...PARSED,
  changes: ['made long'],
  version: 2,
  can_undo: true,
} as unknown as DatasetChanged;

const PLOT: PlotResult = {
  status: 'ok',
  reason: null,
  attempts: 1,
  artifacts: ['plot-light.png'],
  changes: [],
  residual_defects: [],
  version: 1,
};

type Action = Parameters<typeof agentReducer>[1];
type Step = (state: AgentSessionState) => AgentSessionState;
const run = (...steps: Step[]) =>
  steps.reduce((state, step) => step(state), {
    ...initialAgentState('matplotlib'),
    phase: 'ready',
    sessionId: 'S1',
  } as AgentSessionState);
const item =
  (next: Action): Step =>
  state =>
    agentReducer(state, next);
const paste = (chip: string) => item({ type: 'parse_done', parsed: PARSED, bytes: 10, chip });
const summary =
  (text: string): Step =>
  state =>
    agentReducer(
      agentReducer(state, {
        type: 'item',
        item: { kind: 'action', action: 'summarize_data', library: 'matplotlib' },
      }),
      { type: 'item', item: { kind: 'assistant', text } }
    );
/** A typed turn, its reply, and what it changed once its `done` arrived. */
const ask =
  (text: string, outcome: 'answer' | 'data' | 'plot', reply = 'Sure.'): Step =>
  state =>
    agentReducer(
      agentReducer(agentReducer(state, { type: 'item', item: { kind: 'user', text } }), {
        type: 'item',
        item: { kind: 'assistant', text: reply },
      }),
      { type: 'turn_outcome', outcome }
    );
/** The plot button's turn: its action, the card of the version it shipped, the reply. */
const plot =
  (version: number, library = 'matplotlib'): Step =>
  state =>
    (
      [
        { type: 'item', item: { kind: 'action', action: 'create_plot', library } },
        { type: 'item', item: { kind: 'plot', version } },
        { type: 'item', item: { kind: 'assistant', text: `Plot ${version}.` } },
      ] as Action[]
    ).reduce(agentReducer, state);
const switchTo = (library: string) =>
  item({
    type: 'library_done',
    library,
    eligibility: { eligible: true, status: 'clean', reasons: [] },
    target: { spec_id: 'scatter-basic', library },
    carry: null,
  });

const headings = (items: ChatItem[]) =>
  threadModel(items).rows.map(row =>
    row.kind === 'chapter' ? `# ${row.chapter.kind}` : `${row.item.kind}${row.folded ? ' ▸' : ''}`
  );

describe('threadModel', () => {
  it('opens with a data chapter and starts a plot chapter at the first plot turn', () => {
    const state = run(
      paste('▤ table'),
      summary('12 rows.'),
      ask('what is in b?', 'answer'),
      plot(1),
      ask('why is it blue?', 'answer'),
      plot(2)
    );
    const { chapters } = threadModel(state.items);
    expect(headings(state.items)).toEqual([
      '# data',
      'paste',
      'data',
      'action',
      'assistant',
      'user',
      'assistant',
      '# plot',
      'action',
      'plot ▸',
      'assistant',
      'user',
      'assistant',
      'action',
      'plot',
      'assistant',
    ]);
    expect(chapters.map(({ kind, start }) => ({ kind, start }))).toEqual([
      { kind: 'data', start: 1 },
      { kind: 'plot', start: state.items[6].id },
    ]);
    // Each chapter counts its own questions, for the count and its jump.
    expect(chapters[0].questions).toEqual([state.items[4].id]);
    expect(chapters[1].questions).toEqual([state.items[9].id]);
    expect(chapters[1].plotVersions).toEqual([1, 2]);
  });

  it('starts a new data chapter when a turn after a plot changes the data, with the older version folded', () => {
    const state = run(
      paste('▤ table'),
      summary('12 rows.'),
      plot(1),
      ask('only 2024 please', 'data', 'Kept the 2024 rows.'),
      item({ type: 'data_prepared', dataset: CHANGED }),
      plot(2)
    );
    expect(headings(state.items)).toEqual([
      '# data',
      'paste',
      'data_stub ▸',
      'action',
      'assistant',
      '# plot',
      'action',
      'plot ▸',
      'assistant',
      '# data',
      'user',
      // The turn's version stands before its reply, which streamed in before it.
      'data',
      'assistant',
      '# plot',
      'action',
      'plot',
      'assistant',
    ]);
    const { chapters } = threadModel(state.items);
    expect(chapters.map(chapter => chapter.dataVersions)).toEqual([[1], [], [2], []]);
  });

  it("keeps a card's own versions, a question and a switch in the chapter they fall in", () => {
    const state = run(
      paste('▤ Bericht.xlsx'),
      summary('12 rows.'),
      item({ type: 'data_prepared', dataset: CHANGED, toLong: true }),
      plot(1),
      ask('what does the dashed line mean?', 'answer'),
      switchTo('seaborn'),
      plot(2, 'seaborn')
    );
    expect(headings(state.items)).toEqual([
      '# data',
      'paste',
      // `.to_long()` before the plot: the earlier version stays under its paste, its summary
      // under it, and the card goes on at the end, in the same chapter.
      'data_stub ▸',
      'action',
      'assistant',
      'data',
      '# plot',
      'action',
      'plot ▸',
      'assistant',
      'user',
      'assistant',
      'switch',
      'action',
      'plot',
      'assistant',
    ]);
    const { chapters } = threadModel(state.items);
    expect(chapters[0].dataVersions).toEqual([1, 2]);
    expect(chapters[1]).toMatchObject({ switches: 1, plotVersions: [1, 2] });
  });

  it("opens a data chapter of its own for a card's control after a question, which keeps its chapter", () => {
    const state = run(
      paste('▤ table'),
      summary('12 rows.'),
      plot(1),
      ask('what does the dashed line mean?', 'answer'),
      item({ type: 'data_prepared', dataset: CHANGED, toLong: true })
    );
    expect(headings(state.items)).toEqual([
      '# data',
      'paste',
      'data_stub ▸',
      'action',
      'assistant',
      '# plot',
      'action',
      'plot',
      'assistant',
      'user',
      'assistant',
      '# data',
      'data',
    ]);
    const { chapters } = threadModel(state.items);
    expect(chapters[1].questions).toHaveLength(1);
  });

  it('reads a data turn from its outcome, a plot turn from a failed plot, and leaves a refusal where it falls', () => {
    const failed: ChatItem = {
      id: 3,
      kind: 'plot_failed',
      result: { ...PLOT, status: 'failed', reason: 'render', version: null },
    };
    const items: ChatItem[] = [
      { id: 1, kind: 'user', text: 'sum per month', outcome: 'data' },
      { id: 2, kind: 'user', text: 'draw it as you like' },
      failed,
      { id: 4, kind: 'user', text: 'tell me a joke' },
      { id: 5, kind: 'refusal', code: 'out_of_scope', text: 'Only plots.' },
    ];
    expect(headings(items)).toEqual([
      '# data',
      'user',
      '# plot',
      'user',
      'plot_failed',
      'user',
      'refusal',
    ]);
  });

  it("opens a data chapter at the card that a card's own control moved below a plot", () => {
    const state = run(
      paste('▤ table'),
      summary('12 rows.'),
      plot(1),
      item({ type: 'data_prepared', dataset: CHANGED, toLong: true }),
      item({ type: 'undo_done', parsed: PARSED }),
      plot(2)
    );
    // The second control finds no plot below the moved card: its stub goes above the card, and
    // both stay in the chapter the first one opened.
    expect(headings(state.items)).toEqual([
      '# data',
      'paste',
      'data_stub ▸',
      'action',
      'assistant',
      '# plot',
      'action',
      'plot ▸',
      'assistant',
      '# data',
      'data_stub ▸',
      'data',
      '# plot',
      'action',
      'plot',
      'assistant',
    ]);
    // The chapter starts at its first item, the stub right below the plot's reply.
    const { chapters } = threadModel(state.items);
    expect(state.items[7]).toMatchObject({ kind: 'data_stub', card: 2, snapshot: { n: 2 } });
    expect(chapters[2]).toMatchObject({
      kind: 'data',
      start: state.items[7].id,
      dataVersions: [1, 2],
    });
  });

  it('keeps a version shown twice apart: its own ids, the stub folded, the card open, counted once', () => {
    // Paste, `.to_long()`, `.undo()`: the server's v1, v2 and v1 again, back at the paste.
    const state = run(
      paste('▤ table'),
      summary('12 rows.'),
      item({ type: 'data_prepared', dataset: CHANGED, toLong: true }),
      item({ type: 'undo_done', parsed: PARSED })
    );
    const { rows, chapters } = threadModel(state.items);
    const ones = rows.flatMap(row =>
      row.kind === 'item' &&
      (row.item.kind === 'data' || row.item.kind === 'data_stub') &&
      row.item.snapshot?.n === 1
        ? [
            {
              id: row.item.id,
              kind: row.item.kind,
              folded: row.folded,
              label: row.item.snapshot.label,
            },
          ]
        : []
    );

    expect(ones).toEqual([
      { id: expect.any(Number), kind: 'data_stub', folded: true, label: 'data v1 · pasted' },
      { id: expect.any(Number), kind: 'data', folded: false, label: 'data v1 · back to v1' },
    ]);
    expect(new Set(state.items.map(entry => entry.id)).size).toBe(state.items.length);
    expect(ones[0].id).not.toBe(ones[1].id);
    expect(chapters.map(chapter => chapter.dataVersions)).toEqual([[1, 2]]);
  });

  it('leaves a paste whose table read from text was discarded in the chapter it falls in', () => {
    const transcription = {
      text: 'a,b\n1,2\n',
      preview: [['1', '2']],
      profile: PARSED.profile,
      warnings: [],
      note: '',
      bytes: 8,
    };
    const waiting = run(
      paste('▤ table'),
      summary('12 rows.'),
      plot(1),
      item({ type: 'transcribed', transcription, chip: '▤ text · 2 lines' })
    );
    // While it waits, the table read from text is data to decide on.
    expect(headings(waiting.items).slice(-3)).toEqual(['# data', 'paste', 'transcription']);
    const discarded = agentReducer(waiting, { type: 'transcription_clear' });
    expect(headings(discarded.items).slice(-4)).toEqual(['plot', 'assistant', 'paste', 'notice']);
    expect(threadModel(discarded.items).chapters.map(chapter => chapter.kind)).toEqual([
      'data',
      'plot',
    ]);
  });

  it('gives a thread without a turn one data chapter, and an empty thread none', () => {
    expect(threadModel([])).toEqual({ rows: [], chapters: [] });
    const copied: ChatItem[] = [{ id: 1, kind: 'data' }];
    expect(headings(copied)).toEqual(['# data', 'data']);
  });
});

describe('plotSummaries', () => {
  const libraries: Record<number, string> = { 1: 'matplotlib', 2: 'matplotlib', 3: 'seaborn' };
  const libraryOf = (version: number) => libraries[version];
  const create = (id: number, label = '.create_plot() →'): ChatItem => ({
    id,
    kind: 'action',
    action: 'create_plot',
    library: 'matplotlib',
    label,
  });

  it('names a plot by the request before it, the first plot of a library, or .start_over()', () => {
    const items: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      { id: 2, kind: 'data' },
      create(3),
      { id: 4, kind: 'plot', version: 1 },
      { id: 5, kind: 'assistant', text: 'Here it is.' },
      { id: 6, kind: 'user', text: 'title in German', outcome: 'plot' },
      { id: 7, kind: 'plot', version: 2 },
      { id: 8, kind: 'switch', from: 'matplotlib', library: 'seaborn', decisions: null },
      create(9, '.start_over()'),
      { id: 10, kind: 'plot', version: 3 },
    ];
    expect([...plotSummaries(items, libraryOf)]).toEqual([
      [1, 'first plot'],
      [2, 'title in German'],
      [3, '.start_over()'],
    ]);
  });

  it('names nothing for a later plot of a library that no request asked for', () => {
    const items: ChatItem[] = [
      create(1),
      { id: 2, kind: 'plot', version: 1 },
      create(3, 'plot the new data'),
      { id: 4, kind: 'plot', version: 2 },
      // A carry the chat started has no button and no request; its library's first plot.
      { id: 5, kind: 'action', action: 'carry_plot', library: 'seaborn' },
      { id: 6, kind: 'plot', version: 3 },
    ];
    expect([...plotSummaries(items, libraryOf)]).toEqual([
      [1, 'first plot'],
      [2, null],
      [3, 'first plot'],
    ]);
  });

  it('cuts a request to one line of 40 characters, the ellipsis included', () => {
    expect(cutRequest('  log scale\non   y  ')).toBe('log scale on y');
    const long = 'make the title bigger and move the legend outside the plot';
    expect(cutRequest(long)).toBe('make the title bigger and move the lege…');
    expect([...cutRequest(long)]).toHaveLength(PLOT_SUMMARY_MAX);
    expect(cutRequest('x'.repeat(PLOT_SUMMARY_MAX))).toBe('x'.repeat(PLOT_SUMMARY_MAX));
    // Cut on a space: the space before the ellipsis goes.
    expect(cutRequest(`${'a'.repeat(38)} bc`)).toBe(`${'a'.repeat(38)}…`);
  });
});
