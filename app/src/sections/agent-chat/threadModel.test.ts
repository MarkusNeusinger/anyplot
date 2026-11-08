import { describe, expect, it } from 'vitest';

import {
  agentReducer,
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
} from 'src/hooks/useAgentSession';
import type { DatasetChanged, DatasetParsed, NewDataBase, PlotResult } from 'src/lib/agent';
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
    expect(threadModel([])).toEqual({
      rows: [],
      chapters: [],
      answers: new Set(),
      decisionsAt: 0,
      decisionsEarlier: false,
    });
    const copied: ChatItem[] = [{ id: 1, kind: 'data' }];
    expect(headings(copied)).toEqual(['# data', 'data']);
  });
});

describe('threadModel: questions and the decisions', () => {
  const card: ChatItem = { id: 2, kind: 'data' };
  const reply = (id: number, text = 'Sure.'): ChatItem => ({ id, kind: 'assistant', text });

  it('counts a turn that changed nothing, and names the first reply of its turn as its answer', () => {
    const items: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      card,
      { id: 3, kind: 'user', text: 'what is in b?', outcome: 'answer' },
      reply(4),
      { id: 5, kind: 'notice', text: 'reply language: German' },
      reply(6, 'And one more line.'),
    ];
    const model = threadModel(items);
    expect(model.chapters[0].questions).toEqual([3]);
    expect([...model.answers]).toEqual([4]);
  });

  it('never counts the note sent with a paste, a turn that waits for its memory read, or a trailing ?', () => {
    const items: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      card,
      // Its reply summarizes the data that just came: "nothing changed" would be false.
      { id: 3, kind: 'user', text: 'is share a fraction?', outcome: 'answer', note: true },
      reply(4),
      // The read after it may still move it to `kept`.
      { id: 5, kind: 'user', text: 'what is on x?', outcome: 'answer' },
      reply(6),
      // No outcome (refused, failed, stopped, an outcome the page does not know): no question,
      // whatever the text says.
      { id: 7, kind: 'user', text: 'and on y?' },
      reply(8),
      { id: 9, kind: 'user', text: 'a log scale?', outcome: 'kept' },
      reply(10),
    ];
    const waiting = threadModel(items, 5);
    expect(waiting.chapters[0].questions).toEqual([]);
    expect(waiting.answers.size).toBe(0);
    // Once the read landed or failed, the question counts.
    const settled = threadModel(items, null);
    expect(settled.chapters[0].questions).toEqual([5]);
    expect([...settled.answers]).toEqual([6]);
  });

  it('never counts a turn that shows an error, which a later read of its cut stream marked', () => {
    const items: ChatItem[] = [
      { id: 1, kind: 'user', text: 'what is on x?', outcome: 'answer' },
      { id: 2, kind: 'error', code: 'network', ref: null },
      reply(3, 'The hours.'),
      { id: 4, kind: 'user', text: 'tell me a joke', outcome: 'answer' },
      { id: 5, kind: 'refusal', code: 'out_of_scope', text: 'Only plots.' },
    ];
    const model = threadModel(items);
    expect(model.chapters[0].questions).toEqual([]);
    expect(model.answers.size).toBe(0);
  });

  it('opens a chapter from a server data or plot, with and without a card in the turn', () => {
    const plotted: ChatItem = { id: 6, kind: 'plot', version: 1 };
    const items: ChatItem[] = [
      { id: 1, kind: 'paste', text: '▤ table' },
      card,
      // A server `plot` whose run the page showed nothing of (a result it could not read): the
      // server ran the plot pipeline, so the turn is about the plot all the same.
      { id: 3, kind: 'user', text: 'plot it in red', outcome: 'plot' },
      reply(4),
      { id: 5, kind: 'user', text: 'and a log scale', outcome: 'plot' },
      plotted,
      reply(7),
      // A server `data` without a card (the root's binding change) and one with its card.
      { id: 8, kind: 'user', text: 'swap the axes', outcome: 'data' },
      reply(9),
      { id: 10, kind: 'user', text: 'what is on x?', outcome: 'answer' },
      reply(11),
      { id: 12, kind: 'user', text: 'and a title', outcome: 'plot' },
      reply(13),
      { id: 14, kind: 'user', text: 'only 2024', outcome: 'data' },
      { id: 15, kind: 'data_stub', rows: 2, columns: 2, card: 2 },
      reply(16),
    ];
    expect(headings(items)).toEqual([
      '# data',
      'paste',
      'data',
      '# plot',
      'user',
      'assistant',
      'user',
      'plot',
      'assistant',
      '# data',
      'user',
      'assistant',
      'user',
      'assistant',
      '# plot',
      'user',
      'assistant',
      '# data',
      'user',
      'data_stub ▸',
      'assistant',
    ]);
  });

  it('puts the decisions on the latest plot line, and before the first plot on the latest line', () => {
    const before = run(paste('▤ table'), summary('12 rows.'), ask('what is in b?', 'answer'));
    expect(threadModel(before.items).decisionsAt).toBe(1);
    const after = run(
      paste('▤ table'),
      summary('12 rows.'),
      plot(1),
      ask('only 2024 please', 'data', 'Kept the 2024 rows.'),
      item({ type: 'data_prepared', dataset: CHANGED }),
      plot(2),
      ask('sum per month', 'data', 'Summed.'),
      item({ type: 'data_prepared', dataset: { ...CHANGED, version: 3 } })
    );
    const { chapters, decisionsAt } = threadModel(after.items);
    expect(chapters.map(chapter => chapter.kind)).toEqual(['data', 'plot', 'data', 'plot', 'data']);
    // The newest `# plot` line, where the next plot takes them over, above a newer `# data`.
    expect(decisionsAt).toBe(4);
  });

  it('puts them on the new data line after a paste with other columns, until the next plot', () => {
    // Owner decision of 2026-11-08: the user sees the decisions of the earlier plot before the next
    // plot takes them over, and can forget them there; a paste whose columns all carried keeps them
    // on the plot line.
    const other = item({
      type: 'parse_done',
      parsed: { ...PARSED, version: 2, columns_changed: true } as DatasetParsed,
      bytes: 10,
      chip: '▤ pendulum',
    });
    const pasted = run(paste('▤ table'), summary('12 rows.'), plot(1), other, summary('3 rows.'));
    const model = threadModel(pasted.items);
    expect(model.chapters.map(chapter => chapter.kind)).toEqual(['data', 'plot', 'data']);
    expect([model.decisionsAt, model.decisionsEarlier]).toEqual([3, true]);

    const plotted = run(paste('▤ table'), summary('12 rows.'), plot(1), other, plot(2));
    expect([
      threadModel(plotted.items).decisionsAt,
      threadModel(plotted.items).decisionsEarlier,
    ]).toEqual([4, false]);
    const same = run(paste('▤ table'), summary('12 rows.'), plot(1), paste('▤ again'));
    expect([threadModel(same.items).decisionsAt, threadModel(same.items).decisionsEarlier]).toEqual(
      [2, false]
    );
    // Before any plot the decisions have no earlier plot to come from.
    const first = run(other, summary('3 rows.'));
    expect(threadModel(first.items).decisionsEarlier).toBe(false);
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

  it('names where "plot the new data" started: the version before it, or the catalogue plot', () => {
    // Owner decision of 2026-11-08: the plot's `new_data` says whether the latest plot was the base.
    const newData = (id: number): ChatItem => ({
      id,
      kind: 'action',
      action: 'plot_new_data',
      library: 'matplotlib',
      label: 'plot the new data',
    });
    const items: ChatItem[] = [
      create(1),
      { id: 2, kind: 'plot', version: 1 },
      newData(3),
      { id: 4, kind: 'plot', version: 2 },
      newData(5),
      { id: 6, kind: 'plot', version: 4 },
    ];
    const bases: Record<number, NewDataBase> = { 2: 'previous', 4: 'other_paste' };
    expect([...plotSummaries(items, libraryOf, version => bases[version])]).toEqual([
      [1, 'first plot'],
      [2, 'new data on v1'],
      [4, 'new data, new from the catalogue'],
    ]);
    // A plot whose server named no base reads as before.
    expect(plotSummaries(items, libraryOf).get(2)).toBeNull();
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
