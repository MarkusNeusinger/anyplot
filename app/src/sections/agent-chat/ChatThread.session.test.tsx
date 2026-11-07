/**
 * The thread renders the reducer's items in chapters (`threadModel.ts`): one long session,
 * replayed through the reducer and rendered the way the page renders it (`runView`, then
 * `ChatThread`), checked after every step. It has a workbook, a sheet pick, `.to_long()`, a
 * question, four plots, a data change in step 2, an undo and a `.to_long()` below a plot, a
 * library switch, a second paste, a table read from text and a formula.
 */

import { useState } from 'react';

import { describe, expect, it, vi } from 'vitest';

import {
  agentReducer,
  type AgentSessionState,
  initialAgentState,
  type PlotVersion,
} from 'src/hooks/useAgentSession';
import type { DatasetChanged, DatasetParsed, DatasetProfile } from 'src/lib/agent';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { runView } from 'src/sections/agent-chat/steps';
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

/** The thread as the page renders it: the run's view first (`runView`). */
function thread(state: AgentSessionState) {
  const view = runView(state);
  const shown = view.items === state.items ? state : { ...state, items: view.items };
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

const cards = (container: HTMLElement) =>
  [...container.querySelectorAll('[data-testid^="card-"]')].map(card => card.textContent);

/**
 * The thread as one short line per row: a chapter's line, a folded version's label (`▸ …`), the
 * open plot card's label, the live card, a turn and a reply as their text.
 */
function rows(container: HTMLElement): string[] {
  const log = container.querySelector('[role="log"]');
  return [...(log?.children ?? [])].map(child => {
    const label = child.querySelector(
      '[data-testid="data-stub-label"], [data-testid="result-label"]'
    );
    if (label) {
      return label.getAttribute('aria-expanded') === 'false'
        ? `▸ ${label.textContent?.replace(/^▸/, '')}`
        : `${label.textContent} ▾`;
    }
    return child.textContent ?? '';
  });
}

describe('ChatThread: the data versions of a long session', () => {
  it('reads in chapters, a new # data for each change after a plot, older versions folded', () => {
    mounts = 0;
    const steps = new Map(replay().map(({ name, state }) => [name, state]));
    const end = render(thread(steps.get('a formula over it')!));
    expect(rows(end.container)).toEqual([
      '# data',
      `❯${PASTE}`,
      // The card's own controls before the first plot: each version's stub stays above the card,
      // which stayed in place; the second paste froze the card itself into the last stub.
      '▸ data v1 · Bericht.xlsx · 13 rows × 4 cols',
      '▸ data v2 · sheet "2026" · 12 rows × 5 cols',
      '▸ data v3 · made long · 48 rows × 3 cols',
      'Sheet 2025: 13 rows.',
      'Sheet 2026: 12 rows.',
      '❯what is in Region?',
      'Four regions.',
      '# plot',
      '❯.create_plot() →# matplotlib',
      '▸ plot v1 · matplotlib · first plot',
      'Plot 1.',
      '❯a bigger title',
      '▸ plot v2 · matplotlib · a bigger title',
      'Bigger now.',
      // A data request after the plot: a new data chapter, the version before folded where the
      // card stood (above, in the first chapter), the card below the turn.
      '# data',
      '❯only the 2026 rows',
      'Kept the 2026 rows.',
      '▸ data v4 · changed · 24 rows × 3 cols',
      '▸ data v5 · undone · 48 rows × 3 cols',
      '# plot',
      '❯.update_plot() →# matplotlib',
      '▸ plot v3 · matplotlib',
      'Plot 3.',
      // `.to_long()` on the card above the plot: the card went on below the plot, a new chapter.
      '# data',
      '▸ data v6 · made long · 48 rows × 3 cols',
      '· plotting in seaborn from here, 2 decisions kept',
      '# plot',
      '❯.update_plot() →# seaborn',
      'plot v4 · seaborn · first plot ▾',
      'Plot 4.',
      '# data',
      `❯${SECOND}`,
      '▸ data v7 · pasted · 4 rows × 2 cols',
      '4 rows.',
      `❯${TEXT}`,
      '▸ data v8 · read from text · 1 row × 2 cols',
      '❯y = sin(x) instead',
      'Computed 200 rows.',
      'data card #1',
    ]);
  });

  it('mounts the data card once per paste and per table read from text', () => {
    mounts = 0;
    const steps = replay();
    const view = render(thread(START));
    const seen = steps.map(({ state }) => {
      view.rerender(thread(state));
      return cards(view.container).join(' | ');
    });
    // The card of the paste through every version, the moves and the plots, a new card for the
    // second paste, the table read from text in its own frame, which `.use()` turns into the card.
    expect(seen).toEqual([
      ...Array(13).fill('data card #1'),
      'data card #2',
      'data card #2 | transcription card #3',
      'data card #3',
      'data card #3',
    ]);
  });

  it('keeps the card mounted when a turn or a control after a plot moves it into a new chapter', () => {
    mounts = 0;
    const steps = new Map(replay().map(({ name, state }) => [name, state]));
    const view = render(thread(steps.get('a typed change of the plot')!));
    expect(cards(view.container)).toEqual(['data card #1']);
    // The card below the turn that changed the data, then below the plot its `.to_long()`
    // followed: each time the last row, under a `# data` line of its own.
    for (const name of ['its end', 'a plot of it', '.to_long() below that plot']) {
      view.rerender(thread(steps.get(name)!));
      expect(cards(view.container), name).toEqual(['data card #1']);
    }
    // The version before stays folded where the card stood, above the plot.
    const shown = rows(view.container);
    expect(shown.slice(-8)).toEqual([
      '▸ data v4 · changed · 24 rows × 3 cols',
      '▸ data v5 · undone · 48 rows × 3 cols',
      '# plot',
      '❯.update_plot() →# matplotlib',
      'plot v3 · matplotlib ▾',
      'Plot 3.',
      '# data',
      'data card #1',
    ]);
    const long = steps.get('.to_long() below that plot')!.items;
    expect(long[long.length - 1]).toMatchObject({ kind: 'data', id: 2 });
    expect(long[long.length - 2]).toMatchObject({ kind: 'assistant', text: 'Plot 3.' });
  });
});
