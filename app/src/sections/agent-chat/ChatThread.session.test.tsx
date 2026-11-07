/**
 * The thread renders the reducer's data version items exactly as it rendered the items before
 * them: one long session, replayed through the reducer and rendered the way the page renders it
 * (`runView`, then `ChatThread`), against the items main's reducer built for the same actions
 * (captured at 2164ca3c0, before the version items).
 */

import { useState } from 'react';

import { describe, expect, it, vi } from 'vitest';

import {
  agentReducer,
  type AgentSessionState,
  type ChatItem,
  initialAgentState,
  type PlotVersion,
} from 'src/hooks/useAgentSession';
import type { DatasetChanged, DatasetParsed, DatasetProfile } from 'src/lib/agent';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { runView, shownItems } from 'src/sections/agent-chat/steps';
import type { ConvertedFile } from 'src/sections/agent-chat/useChatAttachment';
import { render } from 'src/test-utils';

vi.mock('src/components/CodeHighlighter', () => ({
  default: ({ code }: { code: string }) => <pre>{code}</pre>,
}));

type Action = Parameters<typeof agentReducer>[1];

const profile = (rows: number, names: string[]): DatasetProfile => ({
  rows,
  columns: names.map(name => ({ name, dtype: 'number', missing: 0, unique: rows })),
  source_format: 'csv',
  decimal: '.',
  warnings: [],
});
const parsed = (rows: number, names: string[], extra: object = {}) =>
  ({
    preview: [names.map(() => '1')],
    profile: profile(rows, names),
    bindings: [
      { role: 'x', column: names[0] },
      { role: 'y', column: names[1] },
    ],
    warnings: [],
    roles: [
      { name: 'x', kinds: [], required: true, variadic: false, description: '' },
      { name: 'y', kinds: [], required: true, variadic: false, description: '' },
    ],
    version: 1,
    ...extra,
  }) as DatasetParsed;
const changed = (rows: number, names: string[], changes: string[], version: number) =>
  ({ ...parsed(rows, names, { file_name: 'Bericht.xlsx' }), changes, version }) as DatasetChanged;
const workbook = (sheet: string): ConvertedFile => ({
  name: 'Bericht.xlsx',
  base64: 'UEs=',
  browserKind: 'spreadsheet',
  kind: 'xlsx',
  sheet,
  sheets: ['2025', '2026'],
  sheetCount: 2,
  text: 'a,b\n',
});
const plotVersion = (number: number, library: string): PlotVersion => ({
  number,
  library,
  theme: 'light',
  result: {
    status: 'ok',
    reason: null,
    attempts: 1,
    artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
    changes: [`change ${number}`],
    residual_defects: [],
    version: number,
  },
  images: {
    light: { state: 'ready', url: `blob:v${number}`, blob: new Blob(['png']), status: 'ok' },
  },
  code: { state: 'ready', text: `print(${number})\n` },
});

const item = (value: Extract<Action, { type: 'item' }>['item']): Action => ({
  type: 'item',
  item: value,
});
const reply = (text: string) => item({ kind: 'assistant', text });
const summary = (library: string, text: string): Action[] => [
  { type: 'run_start', kind: 'summarize_data' },
  item({ kind: 'action', action: 'summarize_data', library }),
  reply(text),
  { type: 'run_end' },
];
const plot = (number: number, label: string, library = 'matplotlib'): Action[] => {
  const action = library === 'matplotlib' ? 'create_plot' : 'carry_plot';
  return [
    { type: 'run_start', kind: action },
    item({ kind: 'action', action, library, label }),
    { type: 'run_step', step: 'adapting', attempt: 1, previous: null },
    { type: 'version_add', version: plotVersion(number, library) },
    item({ kind: 'plot', version: number }),
    reply(`Plot ${number}.`),
    { type: 'run_end' },
  ];
};
const confirm: Action[] = [{ type: 'confirm_start' }, { type: 'confirm_done' }];

const PASTE = '▤ Bericht.xlsx · sheet ‹2025› · 13 rows';
const SECOND = '▤ table · 4 lines · 46 B';
const TEXT = '▤ text · 3 lines · 30 B';

/** The session, step by step: each step's actions as the hook dispatches them. */
const STEPS: [string, Action[]][] = [
  [
    'a workbook',
    [
      { type: 'parse_start' },
      {
        type: 'parse_done',
        parsed: parsed(13, ['Region', 'Q1', 'Q2', 'Q3'], { file_name: 'Bericht.xlsx' }),
        bytes: 400,
        chip: PASTE,
        file: workbook('2025'),
      },
      ...summary('matplotlib', 'Sheet 2025: 13 rows.'),
    ],
  ],
  [
    'a sheet pick',
    [
      { type: 'parse_start' },
      {
        type: 'parse_done',
        parsed: parsed(12, ['Region', 'Q1', 'Q2', 'Q3', 'Q4'], { file_name: 'Bericht.xlsx' }),
        bytes: 420,
        file: workbook('2026'),
      },
      ...summary('matplotlib', 'Sheet 2026: 12 rows.'),
    ],
  ],
  [
    '.to_long()',
    [
      { type: 'to_long_start' },
      {
        type: 'data_prepared',
        toLong: true,
        dataset: changed(48, ['Region', 'Quarter', 'Sales'], ['made long'], 2),
      },
    ],
  ],
  [
    'a question',
    [
      { type: 'run_start', kind: 'message' },
      item({ kind: 'user', text: 'what is in Region?' }),
      reply('Four regions.'),
      { type: 'turn_outcome', outcome: 'answer' },
      { type: 'run_end' },
    ],
  ],
  ['the first plot', [...confirm, ...plot(1, '.create_plot() →')]],
  [
    'a typed change of the plot',
    [
      { type: 'run_start', kind: 'message' },
      item({ kind: 'user', text: 'a bigger title' }),
      { type: 'version_add', version: plotVersion(2, 'matplotlib') },
      item({ kind: 'plot', version: 2 }),
      reply('Bigger now.'),
      { type: 'turn_outcome', outcome: 'plot' },
      { type: 'run_end' },
    ],
  ],
  [
    'a data change in step 2, its turn still running',
    [
      { type: 'run_start', kind: 'message' },
      item({ kind: 'user', text: 'only the 2026 rows' }),
      reply('Kept the 2026 rows.'),
      {
        type: 'data_prepared',
        dataset: changed(24, ['Region', 'Quarter', 'Sales'], ['dropped 24 rows'], 3),
      },
      { type: 'server_sync', bindings: { x: 'Quarter', y: 'Sales' }, dataConfirmed: false },
      { type: 'turn_outcome', outcome: 'data' },
    ],
  ],
  ['its end', [{ type: 'run_end' }]],
  [
    '.undo()',
    [
      { type: 'undo_start' },
      {
        type: 'undo_done',
        parsed: parsed(48, ['Region', 'Quarter', 'Sales'], { version: 2 }),
      },
    ],
  ],
  ['a plot of it', [...confirm, ...plot(3, '.update_plot() →')]],
  [
    '.to_long() below that plot',
    [
      { type: 'to_long_start' },
      {
        type: 'data_prepared',
        toLong: true,
        dataset: changed(48, ['Region', 'Quarter', 'Sales'], ['made long'], 3),
      },
      ...confirm,
    ],
  ],
  [
    'a switch',
    [
      { type: 'library_start' },
      {
        type: 'library_done',
        library: 'seaborn',
        eligibility: { eligible: true, status: 'clean', reasons: [] },
        target: { spec_id: 'scatter-basic', library: 'seaborn' },
        carry: { decisions: 2, newer: 2, target_has_plot: false, from_plot: true, offer: true },
      },
    ],
  ],
  ['its carry', plot(4, '.update_plot() →', 'seaborn')],
  [
    'a second paste',
    [
      { type: 'parse_start' },
      { type: 'parse_done', parsed: parsed(4, ['a', 'b']), bytes: 46, chip: SECOND },
      ...summary('seaborn', '4 rows.'),
    ],
  ],
  [
    'a table read from text',
    [
      { type: 'parse_start' },
      {
        type: 'transcribed',
        chip: TEXT,
        transcription: {
          text: 'animal,count\nHund,7\n',
          preview: [['Hund', '7']],
          profile: profile(1, ['animal', 'count']),
          warnings: [],
          note: '',
          bytes: 30,
        },
      },
    ],
  ],
  [
    '.use()',
    [
      { type: 'parse_start' },
      {
        type: 'parse_done',
        parsed: parsed(1, ['animal', 'count']),
        bytes: 30,
        fromTranscription: true,
      },
    ],
  ],
  [
    'a formula over it',
    [
      { type: 'run_start', kind: 'message' },
      item({ kind: 'user', text: 'y = sin(x) instead' }),
      reply('Computed 200 rows.'),
      { type: 'data_prepared', dataset: changed(200, ['x', 'y'], ['generated 200 rows'], 2) },
      { type: 'turn_outcome', outcome: 'data' },
      { type: 'run_end' },
    ],
  ],
];

/** The items main's reducer built up to the turn that changed the data in step 2, still running. */
const MAIN_DURING_THE_CHANGE: ChatItem[] = [
  { id: 1, kind: 'paste', text: PASTE },
  { id: 2, kind: 'data' },
  { id: 3, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
  { id: 4, kind: 'assistant', text: 'Sheet 2025: 13 rows.' },
  { id: 5, kind: 'action', action: 'summarize_data', library: 'matplotlib' },
  { id: 6, kind: 'assistant', text: 'Sheet 2026: 12 rows.' },
  { id: 7, kind: 'user', text: 'what is in Region?' },
  { id: 8, kind: 'assistant', text: 'Four regions.' },
  {
    id: 9,
    kind: 'action',
    action: 'create_plot',
    library: 'matplotlib',
    label: '.create_plot() →',
  },
  { id: 10, kind: 'plot', version: 1 },
  { id: 11, kind: 'assistant', text: 'Plot 1.' },
  { id: 12, kind: 'user', text: 'a bigger title' },
  { id: 13, kind: 'plot', version: 2 },
  { id: 14, kind: 'assistant', text: 'Bigger now.' },
  { id: 15, kind: 'user', text: 'only the 2026 rows' },
  { id: 16, kind: 'assistant', text: 'Kept the 2026 rows.' },
];

/** The items main's reducer built for the whole session. */
const MAIN_AT_THE_END: ChatItem[] = [
  ...MAIN_DURING_THE_CHANGE.slice(0, 1),
  { id: 2, kind: 'data_stub', rows: 48, columns: 3 },
  ...MAIN_DURING_THE_CHANGE.slice(2),
  {
    id: 17,
    kind: 'action',
    action: 'create_plot',
    library: 'matplotlib',
    label: '.update_plot() →',
  },
  { id: 18, kind: 'plot', version: 3 },
  { id: 19, kind: 'assistant', text: 'Plot 3.' },
  { id: 20, kind: 'action', action: 'carry_plot', library: 'seaborn', label: '.update_plot() →' },
  { id: 21, kind: 'plot', version: 4 },
  { id: 22, kind: 'assistant', text: 'Plot 4.' },
  { id: 23, kind: 'paste', text: SECOND },
  { id: 24, kind: 'data_stub', rows: 4, columns: 2 },
  { id: 25, kind: 'action', action: 'summarize_data', library: 'seaborn' },
  { id: 26, kind: 'assistant', text: '4 rows.' },
  { id: 27, kind: 'paste', text: TEXT },
  { id: 28, kind: 'data' },
  { id: 29, kind: 'user', text: 'y = sin(x) instead' },
  { id: 30, kind: 'assistant', text: 'Computed 200 rows.' },
];

/**
 * The item list main's reducer built after every step, one token per item: its kind, a stub with
 * its shape, a plot with its version. The ids differ by design (the reducer gives a split stub and
 * a switch ids of their own), so the tokens pin what a fold can get wrong: which item stands
 * where, which stub shows which shape. The mount test below pins the React identities.
 */
const SUMMARIZED = 'paste data action assistant';
const SHEETS = `${SUMMARIZED} action assistant`;
const ASKED = `${SHEETS} user assistant`;
const PLOT_1 = `${ASKED} action plot:1 assistant`;
const PLOT_2 = `${PLOT_1} user plot:2 assistant`;
const CHANGED = `${PLOT_2} user assistant`;
const PLOT_3 = `${CHANGED} action plot:3 assistant`;
const PLOT_4 = `${PLOT_3} action plot:4 assistant`;
// The second paste froze the first card into a stub of the shape it showed last.
const FROZEN = PLOT_4.replace('paste data', 'paste stub:48x3');
const MAIN_FOLDS: string[] = [
  SUMMARIZED,
  SHEETS,
  SHEETS,
  ASKED,
  PLOT_1,
  PLOT_2,
  CHANGED,
  CHANGED,
  CHANGED,
  PLOT_3,
  PLOT_3,
  PLOT_3,
  PLOT_4,
  `${FROZEN} ${SUMMARIZED}`,
  `${FROZEN} ${SUMMARIZED} paste transcription`,
  `${FROZEN} paste stub:4x2 action assistant paste data`,
  `${FROZEN} paste stub:4x2 action assistant paste data user assistant`,
];
const tokens = (items: ChatItem[]) =>
  items
    .map(item =>
      item.kind === 'data_stub'
        ? `stub:${item.rows}x${item.columns}`
        : item.kind === 'plot'
          ? `plot:${item.version}`
          : item.kind
    )
    .join(' ');

const START: AgentSessionState = {
  ...initialAgentState('matplotlib'),
  phase: 'ready',
  sessionId: 'S1',
};

/** The state after every step, in order. */
function replay(): { name: string; state: AgentSessionState }[] {
  let state = START;
  return STEPS.map(([name, actions]) => {
    state = actions.reduce(agentReducer, state);
    return { name, state };
  });
}

/** How many data and table cards mounted so far: each mount numbers itself. */
let mounts = 0;
function Card({ part }: { part: string }) {
  const [mount] = useState(() => {
    mounts += 1;
    return mounts;
  });
  return <div data-testid={`card-${part}`}>{`${part} card #${mount}`}</div>;
}

/** The thread as the page renders it: the run's view first (`runView`), with `raw` the items as they are. */
function thread(state: AgentSessionState, raw = false) {
  const view = runView(state);
  const shown = raw || view.items === state.items ? state : { ...state, items: view.items };
  return (
    <ChatThread
      state={shown}
      specId="scatter-basic"
      language="python"
      onRequestTheme={vi.fn()}
      onFetchArtifact={vi.fn(async () => new Blob(['']))}
      onTrack={vi.fn()}
      renderData={part => <Card part={part} />}
      followReply={() => false}
    />
  );
}

const html = (state: AgentSessionState) => render(thread(state)).container.innerHTML;
const cards = (container: HTMLElement) =>
  [...container.querySelectorAll('[data-testid^="card-"]')].map(card => card.textContent);

describe('ChatThread: the data versions of a long session', () => {
  it('folds the version items into the list main built, after every step', () => {
    const steps = replay();
    expect(steps.map(({ state }) => tokens(shownItems(state.items)))).toEqual(MAIN_FOLDS);
    // The items themselves hold more: a stub per version and the switch.
    expect(steps.map(({ state }) => tokens(state.items))).not.toEqual(MAIN_FOLDS);
  });

  it('renders the version items as main rendered its items, during a turn and at the end', () => {
    const states = new Map(replay().map(({ name, state }) => [name, state]));
    const during = states.get('a data change in step 2, its turn still running')!;
    const end = states.get('a formula over it')!;
    // The reducer holds more: a stub per version, the switch.
    expect(during.items.length).toBeGreaterThan(MAIN_DURING_THE_CHANGE.length);
    expect(end.items.length).toBeGreaterThan(MAIN_AT_THE_END.length);
    expect(end.items.filter(next => next.kind === 'switch')).toHaveLength(1);

    for (const [state, main] of [
      [during, MAIN_DURING_THE_CHANGE],
      [end, MAIN_AT_THE_END],
    ] as const) {
      mounts = 0;
      const ours = html(state);
      mounts = 0;
      expect(ours).toBe(html({ ...state, items: main }));
    }
  });

  it('mounts the data card once per paste and per table read from text, as main did', () => {
    mounts = 0;
    const steps = replay();
    const view = render(thread(START));
    const seen = steps.map(({ state }) => {
      view.rerender(thread(state));
      return cards(view.container).join(' | ');
    });
    // Main: the card of the paste through every version and the plots, a new card for the
    // second paste, the table read from text in its own frame, which `.use()` turns into the card.
    expect(seen).toEqual([
      ...Array(13).fill('data card #1'),
      'data card #2',
      'data card #2 | transcription card #3',
      'data card #3',
      'data card #3',
    ]);
  });

  it('keeps the card mounted when a turn or a control after a plot moves it to the end', () => {
    mounts = 0;
    const steps = new Map(replay().map(({ name, state }) => [name, state]));
    const view = render(thread(steps.get('a typed change of the plot')!, true));
    expect(cards(view.container)).toEqual(['data card #1']);
    // The items as they are: the card below the turn that changed the data, then below the plot
    // its `.to_long()` followed.
    for (const name of ['its end', 'a plot of it', '.to_long() below that plot']) {
      const state = steps.get(name)!;
      view.rerender(thread(state, true));
      expect(cards(view.container), name).toEqual(['data card #1']);
    }
    const long = steps.get('.to_long() below that plot')!.items;
    expect(long[long.length - 1]).toMatchObject({ kind: 'data', id: 2 });
    expect(long[long.length - 2]).toMatchObject({ kind: 'assistant', text: 'Plot 3.' });
  });
});
