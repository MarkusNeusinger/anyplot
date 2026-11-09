import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  agentApi,
  AgentApiError,
  agentFetch,
  ANONYMOUS_ID_KEY,
  anonymousId,
  browserLocale,
  caseListQuery,
  codeArtifact,
  convertAnswer,
  countBucket,
  hasPage,
  isPlotAction,
  laneOf,
  languageOffer,
  longSuggestion,
  parseAgentEvent,
  plotMemory,
  plotTarget,
  PUBLIC_LANE,
  publicLaneOpen,
  publicRoute,
  renderedThemes,
  sizeBucket,
  switchCarry,
  toAgentApiError,
  toBase64,
} from 'src/lib/agent';
import { resetTurnstile, TURNSTILE_HEADER } from 'src/lib/turnstile';
import { ACCESS_RELOAD_KEY } from 'src/utils/adminAuth';

const raw = (event: string, data: unknown) => ({
  event,
  data: typeof data === 'string' ? data : JSON.stringify(data),
});

describe('parseAgentEvent', () => {
  it('types the queued status and the pipeline steps', () => {
    // The wait's end, the step alone: a turn without pipeline steps clears its queue on it.
    expect(parseAgentEvent(raw('status', { step: 'started' }))).toEqual({ type: 'started' });
    expect(parseAgentEvent(raw('status', { step: 'queued', position: 2, waiting: 3 }))).toEqual({
      type: 'queued',
      position: 2,
      waiting: 3,
    });
    expect(parseAgentEvent(raw('status', { step: 'repairing', attempt: 2 }))).toEqual({
      type: 'step',
      step: 'repairing',
      attempt: 2,
      previous: null,
    });
  });

  it('reads how the round before a repair ended, and drops an outcome it does not know', () => {
    const step = (extra: Record<string, unknown>) =>
      parseAgentEvent(raw('status', { step: 'repairing', attempt: 2, ...extra }));

    expect(step({ outcome: 'review', findings: 3 })).toMatchObject({
      previous: { attempt: 1, outcome: 'review', findings: 3 },
    });
    expect(step({ outcome: 'exfiltrate', findings: 3 })).toMatchObject({ previous: null });
    expect(step({ outcome: 'review' })).toMatchObject({ previous: null });
    expect(
      parseAgentEvent(
        raw('plot', {
          status: 'ok',
          attempts: 2,
          rounds: [
            { attempt: 1, outcome: 'measured', findings: 1 },
            { attempt: 2, outcome: 'ok', findings: 0 },
            { attempt: 3, outcome: '<b>', findings: 0 },
          ],
        })
      )
    ).toMatchObject({
      result: {
        rounds: [
          { attempt: 1, outcome: 'measured', findings: 1 },
          { attempt: 2, outcome: 'ok', findings: 0 },
        ],
      },
    });
  });

  it('keeps a round without step or shipped mark as it came, and refuses ones of the wrong kind', () => {
    const rounds = (items: unknown[]) => {
      const event = parseAgentEvent(raw('plot', { status: 'ok', attempts: 1, rounds: items }));
      return event?.type === 'plot' ? event.result.rounds : null;
    };

    expect(rounds([{ attempt: 1, outcome: 'ok', findings: 0 }])).toEqual([
      { attempt: 1, outcome: 'ok', findings: 0 },
    ]);
    expect(
      rounds([{ attempt: 1, outcome: 'ok', findings: 0, step: 'reviewing', shipped: true }])
    ).toEqual([{ attempt: 1, outcome: 'ok', findings: 0, step: 'reviewing', shipped: true }]);
    expect(rounds([{ attempt: 1, outcome: 'ok', findings: 0, shipped: 'yes' }])).toEqual([]);
    expect(rounds([{ attempt: 1, outcome: 'ok', findings: 0, step: 'sleeping' }])).toEqual([]);
  });

  it('keeps only the documented plot fields and artifact names', () => {
    const event = parseAgentEvent(
      raw('plot', {
        status: 'needs_attention',
        attempts: 2,
        artifacts: ['plot-light.png', 'plot.py', 'data.csv', '../etc/passwd'],
        changes: ['bigger markers', 3],
        residual_defects: ['VQ-03 light: overlap'],
        error_details: 'Traceback …',
      })
    );
    expect(event).toEqual({
      type: 'plot',
      result: {
        status: 'needs_attention',
        reason: null,
        attempts: 2,
        artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
        changes: ['bigger markers'],
        residual_defects: ['VQ-03 light: overlap'],
        version: null,
        rounds: [],
      },
    });
  });

  it("keeps a JavaScript plot's page among its artifacts", () => {
    const event = parseAgentEvent(
      raw('plot', {
        status: 'ok',
        attempts: 1,
        artifacts: ['plot-light.png', 'plot.js', 'plot.html', 'data.csv', 'page.html'],
      })
    );
    expect(event).toMatchObject({
      result: { artifacts: ['plot-light.png', 'plot.js', 'plot.html', 'data.csv'] },
    });
  });

  it("keeps the server's version number and drops one that is not a positive integer", () => {
    const plot = (version: unknown) =>
      parseAgentEvent(raw('plot', { status: 'ok', attempts: 1, artifacts: [], version }));
    expect(plot(3)).toMatchObject({ type: 'plot', result: { version: 3 } });
    expect(plot(0)).toMatchObject({ result: { version: null } });
    expect(plot('3')).toMatchObject({ result: { version: null } });
    expect(plot(1.5)).toMatchObject({ result: { version: null } });
  });

  it('reads an unknown error code as internal and keeps the ref', () => {
    expect(parseAgentEvent(raw('error', { code: 'kaboom', ref: 'abc' }))).toEqual({
      type: 'error',
      code: 'internal',
      ref: 'abc',
    });
  });

  it("keeps the user's run limit as its own code", () => {
    expect(parseAgentEvent(raw('error', { code: 'run_limit', ref: 'abc' }))).toEqual({
      type: 'error',
      code: 'run_limit',
      ref: 'abc',
    });
  });

  it('drops unknown types, non-object data, malformed JSON and bad statuses', () => {
    expect(parseAgentEvent(raw('debug', { a: 1 }))).toBeNull();
    expect(parseAgentEvent(raw('message', '[1,2]'))).toBeNull();
    expect(parseAgentEvent(raw('message', '{not json'))).toBeNull();
    expect(parseAgentEvent(raw('status', { step: 'thinking' }))).toBeNull();
    expect(parseAgentEvent(raw('status', { step: 'queued', position: -1, waiting: 2 }))).toBeNull();
    expect(parseAgentEvent(raw('plot', { status: 'great' }))).toBeNull();
  });

  it('types ready, message, refusal and done', () => {
    expect(parseAgentEvent(raw('ready', { v: 'anyplot/1', run_id: 'r' }))).toEqual({
      type: 'ready',
      runId: 'r',
    });
    expect(parseAgentEvent(raw('message', { text: 'hi' }))).toEqual({
      type: 'message',
      text: 'hi',
    });
    expect(parseAgentEvent(raw('refusal', { code: 'budget', text: 'later' }))).toEqual({
      type: 'refusal',
      code: 'budget',
      text: 'later',
    });
    expect(parseAgentEvent(raw('done', {}))).toEqual({
      type: 'done',
      llmCalls: null,
      tokens: null,
      bindings: null,
      dataConfirmed: null,
      dataset: null,
      language: null,
      languageOffer: null,
      switch: null,
    });
  });

  it("reads done's turn outcome, an unknown value as unknown, and none as none", () => {
    const turn = (value: unknown) => {
      const event = parseAgentEvent(raw('done', { llm_calls: 1, turn: value }));
      return event?.type === 'done' ? event.turn : 'not done';
    };
    for (const value of ['answer', 'data', 'plot', 'switch', 'language', 'kept', 'memory']) {
      expect(turn(value)).toBe(value);
    }
    // A newer server's word: a change the page cannot name, never a question.
    expect(turn('restyled')).toBe('unknown');
    expect(turn(3)).toBe('unknown');
    expect(turn(['answer'])).toBe('unknown');
    // A refused, failed or stopped turn, or an older server: no field.
    expect(turn(undefined)).toBeUndefined();
    expect(turn(null)).toBeUndefined();
    expect(parseAgentEvent(raw('done', {}))).not.toHaveProperty('turn');
  });

  it("reads a version's kept and added decision ids, and no field as an unknown memory", () => {
    const memory = (value: unknown) => {
      const event = parseAgentEvent(
        raw('plot', { status: 'ok', attempts: 1, artifacts: [], version: 4, memory: value })
      );
      return event?.type === 'plot' ? event.result.memory : 'not a plot';
    };
    expect(memory({ kept: ['m1', 'm2', 'm3'], added: ['m4'] })).toEqual({
      kept: ['m1', 'm2', 'm3'],
      added: ['m4'],
    });
    // A session without memory: two empty lists, which is not the same as none.
    expect(memory({ kept: [], added: [] })).toEqual({ kept: [], added: [] });
    // An entry that is no id goes, the list stays; a malformed value is no field at all.
    expect(memory({ kept: ['m1', 'title in German', 7], added: [] })).toEqual({
      kept: ['m1'],
      added: [],
    });
    expect(memory({ kept: ['m1'] })).toBeUndefined();
    expect(memory(['m1'])).toBeUndefined();
    expect(memory(undefined)).toBeUndefined();
    expect(
      parseAgentEvent(raw('plot', { status: 'ok', attempts: 1, artifacts: [], version: 4 }))
    ).toMatchObject({ result: expect.not.objectContaining({ memory: expect.anything() }) });
  });

  it('reads where "plot the new data" started, and no field for any other value', () => {
    const base = (value: unknown) => {
      const event = parseAgentEvent(
        raw('plot', { status: 'ok', attempts: 1, artifacts: [], version: 2, new_data: value })
      );
      return event?.type === 'plot' ? event.result.new_data : 'not a plot';
    };
    for (const value of [
      'previous',
      'other_paste',
      'other_data',
      'bindings_changed',
      'kept_note',
      'no_plot',
    ]) {
      expect(base(value)).toBe(value);
    }
    expect(base('renamed')).toBeUndefined();
    expect(base(null)).toBeUndefined();
    expect(base(undefined)).toBeUndefined();
  });

  it("reads done's switch the user asked for in the chat, and drops one the page cannot make", () => {
    const done = (value: unknown) => parseAgentEvent(raw('done', { switch: value }));
    expect(done({ library: 'seaborn', plot: true })).toMatchObject({
      switch: { library: 'seaborn', plot: true },
    });
    expect(done({ library: 'ggplot2', plot: false })).toMatchObject({
      switch: { library: 'ggplot2', plot: false },
    });
    expect(done({ library: 'ggplot2' })).toMatchObject({
      switch: { library: 'ggplot2', plot: true },
    });
    expect(done({ library: 'excel', plot: true })).toMatchObject({ switch: null });
    expect(done('seaborn')).toMatchObject({ switch: null });
  });

  it("reads done's sync of the bindings and the step state", () => {
    expect(
      parseAgentEvent(
        raw('done', {
          llm_calls: 3,
          tokens: 900,
          bindings: [
            { role: 'x', column: 'score' },
            { role: 'y', column: null },
          ],
          data_confirmed: false,
        })
      )
    ).toEqual({
      type: 'done',
      llmCalls: 3,
      tokens: 900,
      bindings: [
        { role: 'x', column: 'score' },
        { role: 'y', column: null },
      ],
      dataConfirmed: false,
      dataset: null,
      language: null,
      languageOffer: null,
      switch: null,
    });
    expect(parseAgentEvent(raw('done', { bindings: [], data_confirmed: true }))).toMatchObject({
      bindings: [],
      dataConfirmed: true,
    });
  });

  it("reads done's session language and drops anything outside the pattern or the sources", () => {
    const language = (value: unknown) => {
      const event = parseAgentEvent(raw('done', { llm_calls: 1, language: value }));
      return event?.type === 'done' ? event.language : 'not done';
    };
    expect(language({ language: 'de', source: 'offer' })).toEqual({
      language: 'de',
      source: 'offer',
    });
    expect(language({ language: 'Klingon', source: 'chosen', extra: 1 })).toEqual({
      language: 'Klingon',
      source: 'chosen',
    });
    expect(language({ language: 'en', source: 'default' })).toEqual({
      language: 'en',
      source: 'default',
    });
    // An older server's detection: its sources read as nobody's pick.
    expect(language({ language: 'de', source: 'pasted' })).toEqual({
      language: 'de',
      source: 'default',
    });
    expect(language({ language: 'de', source: 'detected' })).toEqual({
      language: 'de',
      source: 'default',
    });
    // The chip shows the value as it comes: anything else is dropped whole.
    expect(language({ language: 'a/b', source: 'chosen' })).toBeNull();
    expect(language({ language: ' de', source: 'chosen' })).toBeNull();
    expect(language({ language: 'x'.repeat(41), source: 'chosen' })).toBeNull();
    expect(language({ language: 'de', source: 'guessed' })).toBeNull();
    expect(language({ language: 'de' })).toBeNull();
    expect(language('de')).toBeNull();
    expect(language(['de', 'chosen'])).toBeNull();
    expect(language(undefined)).toBeNull();
  });

  it("reads done's language offer, and drops one outside the pattern or the bases", () => {
    const offer = (value: unknown) => {
      const event = parseAgentEvent(
        raw('done', { language: { language: 'en', source: 'default', offer: value } })
      );
      return event?.type === 'done' ? event.languageOffer : 'not done';
    };
    expect(offer({ language: 'de', basis: 'message' })).toEqual({
      language: 'de',
      basis: 'message',
    });
    expect(offer({ language: 'sv', basis: 'data', extra: 1 })).toEqual({
      language: 'sv',
      basis: 'data',
    });
    expect(offer({ language: 'de', basis: 'guess' })).toBeNull();
    expect(offer({ language: 'de\nSYSTEM', basis: 'message' })).toBeNull();
    expect(offer({ basis: 'message' })).toBeNull();
    expect(offer('de')).toBeNull();
    expect(offer(undefined)).toBeNull();
    expect(languageOffer(undefined)).toBeNull();
  });

  it('drops a malformed binding list whole and a step state that is not a boolean', () => {
    const sync = (data: unknown) => parseAgentEvent(raw('done', data));
    // One bad entry: the list would replace every binding, so none of it is used.
    expect(
      sync({
        bindings: [
          { role: 'x', column: 'score' },
          { role: 'y', column: 3 },
        ],
      })
    ).toMatchObject({ bindings: null });
    expect(sync({ bindings: [null] })).toMatchObject({ bindings: null });
    expect(sync({ bindings: [{ column: 'score' }] })).toMatchObject({ bindings: null });
    expect(sync({ bindings: 'x=score' })).toMatchObject({ bindings: null });
    expect(sync({ data_confirmed: 'yes' })).toMatchObject({ dataConfirmed: null });
  });

  // `done.dataset` after the assistant's `prepare_data` changed the data.
  const DATASET = {
    preview: [
      ['2026-01', '12.5'],
      ['2026-02', '13'],
    ],
    profile: {
      rows: 2,
      columns: [
        { name: 'Monat', dtype: 'datetime', missing: 0, unique: 2, min: '2026-01', max: '2026-02' },
        {
          name: 'Anteil',
          dtype: 'number',
          missing: 0,
          unique: 2,
          min: 12.5,
          max: 13,
          top: ['12.5', '13'],
          mean: 12.75,
          median: 12.75,
        },
      ],
      source_format: 'csv',
      decimal: '.',
      warnings: [],
    },
    bindings: [
      { role: 'x', column: 'Monat' },
      { role: 'y', column: 'Anteil' },
    ],
    warnings: ['column Anteil: 1 cell could not be read'],
    context_lines: ['Anteil der Haushalte, Statistik Austria'],
    changes: ["Anteil: 2 cells read as numbers, unit '%' removed"],
    version: 2,
  };

  it('reads the data version a done carries, with the documented fields only', () => {
    const event = parseAgentEvent(
      raw('done', {
        llm_calls: 2,
        data_confirmed: false,
        bindings: DATASET.bindings,
        dataset: {
          ...DATASET,
          dataset_id: 'ds_secret',
          profile: {
            ...DATASET.profile,
            sample: [['2026-01', '12,5 %']],
            columns: DATASET.profile.columns.map(column => ({ ...column, internal: 1 })),
          },
        },
      })
    );
    expect(event).toMatchObject({ type: 'done', dataConfirmed: false });
    const dataset = event?.type === 'done' ? event.dataset : null;
    expect(dataset).toEqual({
      ...DATASET,
      profile: {
        ...DATASET.profile,
        columns: [
          {
            ...DATASET.profile.columns[0],
            top: [],
            mean: null,
            median: null,
          },
          DATASET.profile.columns[1],
        ],
      },
      // No offer in the event: the wide-table suggestion reads as none.
      suggestion: null,
    });
    expect(JSON.stringify(dataset)).not.toMatch(/ds_secret|sample|internal/);
  });

  it("reads the undo field and the original's number only as the server types them", () => {
    const dataset = (value: Record<string, unknown>) => {
      const event = parseAgentEvent(raw('done', { dataset: { ...DATASET, ...value } }));
      return event?.type === 'done' ? event.dataset : null;
    };
    // The session's numbering: a change of a second paste numbered 4, with the paste to undo.
    expect(dataset({ version: 5, can_undo: true, original_version: 4 })).toMatchObject({
      version: 5,
      can_undo: true,
      original_version: 4,
    });
    expect(dataset({ can_undo: false })).toMatchObject({ can_undo: false });
    // Anything else, and an older server's answer without them, leaves them out: no undo.
    const odd = dataset({ can_undo: 'yes', original_version: 0 });
    expect(odd).not.toBeNull();
    expect(odd).not.toHaveProperty('can_undo');
    expect(odd).not.toHaveProperty('original_version');
    expect(dataset({})).not.toHaveProperty('can_undo');
  });

  it('reads a wide-table offer strictly and drops a malformed one', () => {
    const offer = {
      kind: 'to_long',
      columns: ['Sensor_A', 'Sensor_B'],
      names_to: 'category',
      values_to: 'value',
      keys: [],
      rows: 6,
      siblings: ['Sensor_A', 'Sensor_B'],
    };
    expect(longSuggestion(offer)).toEqual(offer);
    // An older server sends no siblings: none to warn about.
    const older = { ...offer, siblings: undefined };
    expect(longSuggestion(older)).toEqual({ ...offer, siblings: [] });
    expect(longSuggestion({ ...offer, kind: 'to_wide' })).toBeNull();
    expect(longSuggestion({ ...offer, columns: ['Sensor_A'] })).toBeNull();
    expect(longSuggestion({ ...offer, rows: '6' })).toBeNull();
    expect(longSuggestion(null)).toBeNull();
  });

  it('drops a malformed data version whole and keeps the rest of done', () => {
    const sync = (dataset: unknown) =>
      parseAgentEvent(raw('done', { data_confirmed: false, dataset }));
    for (const malformed of [
      { ...DATASET, version: 0 },
      { ...DATASET, version: '2' },
      { ...DATASET, preview: [['2026-01', 12.5]] },
      { ...DATASET, preview: 'Monat,Anteil' },
      { ...DATASET, bindings: [{ role: 'x', column: 3 }] },
      { ...DATASET, profile: { ...DATASET.profile, rows: -1 } },
      {
        ...DATASET,
        profile: { ...DATASET.profile, columns: [{ name: 'Monat', dtype: 'timestamp' }] },
      },
      { ...DATASET, profile: undefined },
      [DATASET],
      'version 2',
    ]) {
      expect(sync(malformed)).toMatchObject({ dataset: null, dataConfirmed: false });
    }
    // Absent lists read as empty: a version without change lines still replaces the preview.
    expect(
      sync({ ...DATASET, changes: undefined, warnings: 'x', context_lines: undefined })
    ).toMatchObject({
      dataset: { changes: [], warnings: [], context_lines: [], version: 2 },
    });
  });

  // `done.dataset` after `generate_data` in a session without data: version 1, with the roles.
  const GENERATED = {
    preview: [
      ['-3.1415927', '-1.2246468e-16'],
      ['-3.1100183', ''],
    ],
    profile: {
      rows: 200,
      columns: [
        { name: 'x', dtype: 'number', missing: 0, unique: 200 },
        { name: 'y', dtype: 'number', missing: 3, unique: 197 },
      ],
      source_format: 'csv',
      decimal: '.',
      warnings: [],
    },
    bindings: [
      { role: 'x', column: 'x' },
      { role: 'y', column: 'y' },
    ],
    warnings: [],
    roles: [
      { name: 'x', kinds: ['numeric'], required: true, variadic: false, description: 'x values' },
      { name: 'y', kinds: ['numeric'], required: true, variadic: false, description: 'y values' },
    ],
    changes: [
      'generated 200 rows: x from -3.1416 to 3.1416, y = sin(x)',
      'y: 3 of 200 values are undefined and left empty',
    ],
    version: 1,
  };

  it('reads a first dataset the assistant generated: version 1, with the roles', () => {
    const event = parseAgentEvent(
      raw('done', { data_confirmed: false, bindings: GENERATED.bindings, dataset: GENERATED })
    );
    const dataset = event?.type === 'done' ? event.dataset : null;
    expect(dataset).toMatchObject({
      version: 1,
      roles: GENERATED.roles,
      changes: GENERATED.changes,
      bindings: GENERATED.bindings,
      preview: GENERATED.preview,
    });
    expect(dataset?.profile.columns.map(column => column.dtype)).toEqual(['number', 'number']);
  });

  it('keeps the documented role fields, caps the roles and drops a malformed list whole', () => {
    const roles = (value: unknown) => {
      const event = parseAgentEvent(raw('done', { dataset: { ...GENERATED, roles: value } }));
      return event?.type === 'done' ? event.dataset?.roles : 'no dataset';
    };
    expect(
      roles([{ name: 'x', kinds: ['numeric', 3], required: 'yes', internal: 1, description: 2 }])
    ).toEqual([
      {
        name: 'x',
        kinds: ['numeric'],
        required: false,
        variadic: false,
        description: '',
        non_negative: false,
        computed: false,
      },
    ]);
    expect(roles([{ name: 'radius', kinds: ['numeric'], non_negative: true }])).toMatchObject([
      { name: 'radius', non_negative: true },
    ]);
    expect(roles([{ name: 'sma', kinds: ['numeric'], computed: true }])).toMatchObject([
      { name: 'sma', computed: true },
    ]);
    const many = Array.from({ length: 60 }, (_, index) => ({
      ...GENERATED.roles[0],
      name: `r${index}`,
    }));
    expect(roles(many)).toHaveLength(50);
    // A malformed entry or list leaves the page's own roles in place; the data still arrives.
    expect(roles([GENERATED.roles[0], { kinds: ['numeric'] }])).toBeUndefined();
    expect(roles('x, y')).toBeUndefined();
    expect(roles(undefined)).toBeUndefined();
  });
});

describe('toAgentApiError', () => {
  it('reads the BFF code and ref', async () => {
    const error = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'run_active', ref: 'r-1' }), { status: 409 })
    );
    expect(error).toMatchObject({ status: 409, code: 'run_active', ref: 'r-1' });
    expect(error.unauthorized).toBe(false);
  });

  it('falls back to a code for the status when the body has none', async () => {
    const error = await toAgentApiError(
      new Response(JSON.stringify({ status: 401, message: 'no' }), { status: 401 })
    );
    expect(error).toMatchObject({ status: 401, code: 'unauthorized', ref: null });
    expect(error.unauthorized).toBe(true);
  });

  it('maps the kill switch message to not_enabled', async () => {
    const error = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'agent chat is not enabled' }), { status: 404 })
    );
    expect(error.code).toBe('not_enabled');
  });

  it('reads the cause of a refused paste as one line, text only', async () => {
    const refused = await toAgentApiError(
      new Response(
        JSON.stringify({
          detail: 'unparseable',
          ref: 'r',
          cause: 'the header has 3 fields,\n but line 3 has 4',
        }),
        { status: 422 }
      )
    );
    expect(refused).toMatchObject({
      code: 'unparseable',
      cause: 'the header has 3 fields, but line 3 has 4',
    });
    const odd = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'unparseable', cause: ['x'] }), { status: 422 })
    );
    expect(odd.cause).toBeNull();
  });

  it('reads the broken part of a damaged file from the closed set only', async () => {
    const damaged = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'file_corrupt', damage: 'parquet' }), { status: 422 })
    );
    expect(damaged.damage).toBe('parquet');
    const unknown = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'file_corrupt', damage: 'Traceback' }), { status: 422 })
    );
    expect(unknown.damage).toBeNull();
  });

  it("keeps the binding check's lines of a refused binding set", async () => {
    const error = await toAgentApiError(
      new Response(
        JSON.stringify({ detail: 'invalid', ref: 'r', errors: ["role 'y' takes y1", 7] }),
        { status: 422 }
      )
    );
    expect(error).toMatchObject({ code: 'invalid', errors: ["role 'y' takes y1"] });
  });

  it('reads the stored case of a row_missing and no case id from any other body', async () => {
    const missing = await toAgentApiError(
      new Response(
        JSON.stringify({ detail: 'row_missing', ref: 'r-1', case_id: '20261012T143005Z-1a2b3c4d' }),
        { status: 502 }
      )
    );
    expect(missing).toMatchObject({
      code: 'row_missing',
      ref: 'r-1',
      caseId: '20261012T143005Z-1a2b3c4d',
    });
    const storage = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'storage', case_id: 7 }), { status: 502 })
    );
    expect(storage.caseId).toBeNull();
  });

  it('reads the counts of a refused conversion, whole numbers only', async () => {
    const counted = await toAgentApiError(
      new Response(
        JSON.stringify({ detail: 'file_too_many_rows', measured: 21000, limit: 20000 }),
        { status: 422 }
      )
    );
    expect(counted).toMatchObject({ code: 'file_too_many_rows', measured: 21000, limit: 20000 });
    const odd = await toAgentApiError(
      new Response(JSON.stringify({ detail: 'file_corrupt', measured: '3', limit: 1.5 }), {
        status: 422,
      })
    );
    expect(odd).toMatchObject({ measured: null, limit: null });
  });
});

describe('AgentApiError.shownRef', () => {
  it('keeps the request id for a fault of the server or the connection', () => {
    expect(new AgentApiError(503, 'capacity', 'r-503').shownRef).toBe('r-503');
    expect(new AgentApiError(500, 'internal', 'r-500').shownRef).toBe('r-500');
    expect(new AgentApiError(0, 'unreachable', 'r-0').shownRef).toBe('r-0');
  });

  it('drops it for a refusal, which names its cause in the text', () => {
    for (const status of [409, 422, 429]) {
      expect(new AgentApiError(status, 'refused', 'r-4xx').shownRef).toBeNull();
    }
  });

  it('is null when there is no id to show', () => {
    expect(new AgentApiError(503, 'capacity').shownRef).toBeNull();
  });
});

describe('convertAnswer', () => {
  it('keeps the known fields and the positive warning counts', () => {
    expect(
      convertAnswer({
        text: 'a\n1\n',
        format: 'json',
        kind: 'parquet',
        rows: 1,
        columns: 1,
        sheet: null,
        sheets: ['x', 3],
        sheet_count: 0,
        warnings: { list_columns: 2, dropped_columns: 0, other: 5 },
        dropped: ['span', 7],
      })
    ).toEqual({
      text: 'a\n1\n',
      format: 'json',
      kind: 'parquet',
      rows: 1,
      columns: 1,
      sheet: null,
      sheets: ['x'],
      sheet_count: 0,
      warnings: { list_columns: 2 },
      dropped: ['span'],
    });
  });

  it('refuses an answer without text', () => {
    expect(convertAnswer({ kind: 'xlsx' })).toBeNull();
    expect(convertAnswer('text')).toBeNull();
  });

  it('posts the file as base64 with the chosen sheet', async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ text: 'a\n', kind: 'xlsx' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        })
    );
    vi.stubGlobal('fetch', fetchMock);
    const answer = await agentApi.convertFile('t', 'S1', toBase64(new Uint8Array([1, 2, 3])), 'B');
    expect(answer.text).toBe('a\n');
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toContain('/debug/agent/sessions/S1/dataset/convert');
    expect(JSON.parse(String(init.body))).toEqual({ data_base64: 'AQID', sheet: 'B' });
    vi.unstubAllGlobals();
  });
});

describe('caseListQuery', () => {
  it('sends only the keys that are set, include_superseded only when true', () => {
    expect(caseListQuery({})).toBe('');
    expect(caseListQuery({ status: 'open', include_superseded: false, spec: '' })).toBe(
      '?status=open'
    );
    expect(
      caseListQuery({
        reaction: 'bug',
        status: 'done',
        spec: 'scatter-basic',
        library: 'seaborn',
        model_version: 'm 1',
        tag: 'legend',
        include_superseded: true,
        before: '20261012T143005Z-1a2b3c4d',
        limit: 20,
      })
    ).toBe(
      '?reaction=bug&status=done&spec=scatter-basic&library=seaborn&model_version=m+1&tag=legend&include_superseded=true&before=20261012T143005Z-1a2b3c4d&limit=20'
    );
  });
});

describe('agentApi cases', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('reads an answer without an items list as an empty page', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ detail: 'x' }), { status: 200 }))
    );
    await expect(agentApi.listCases('', { status: 'open' })).resolves.toEqual({
      items: [],
      has_more: false,
    });
  });

  it('lists, reads and patches a case on the cases routes', async () => {
    const fetchMock = vi.fn(
      async () => new Response(JSON.stringify({ items: [], has_more: true }), { status: 200 })
    );
    vi.stubGlobal('fetch', fetchMock);
    await expect(agentApi.listCases('tok', { tag: 'legend' })).resolves.toEqual({
      items: [],
      has_more: true,
    });
    await agentApi.getCase('tok', 'A/1');
    await agentApi.patchCase('tok', 'A1', { status: 'done' });
    const urls = fetchMock.mock.calls.map(call => (call as unknown as [string])[0]);
    expect(urls[0]).toMatch(/\/debug\/agent\/cases\?tag=legend$/);
    expect(urls[1]).toMatch(/\/debug\/agent\/cases\/A%2F1$/);
    expect(urls[2]).toMatch(/\/debug\/agent\/cases\/A1$/);
    const [, init] = fetchMock.mock.calls[2] as unknown as [string, RequestInit];
    expect(init).toMatchObject({ method: 'PATCH', body: '{"status":"done"}' });
    expect((init.headers as Record<string, string>)['X-Anyplot-Client']).toBe('agent-chat/1');
  });

  it("asks for a version's page in a theme, and for every other file without one", async () => {
    const fetchMock = vi.fn(async () => new Response('<!doctype html>', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    const page = await agentApi.artifact('tok', 'S1', 'plot.html', 3, 'dark');
    expect(await page.text()).toBe('<!doctype html>');
    await agentApi.artifact('tok', 'S1', 'data.csv', 3);
    const urls = fetchMock.mock.calls.map(call => (call as unknown as [string])[0]);
    expect(urls[0]).toMatch(/\/debug\/agent\/sessions\/S1\/artifacts\/plot\.html\?v=3&theme=dark$/);
    expect(urls[1]).toMatch(/\/debug\/agent\/sessions\/S1\/artifacts\/data\.csv\?v=3$/);
  });

  it('fetches a case file as a blob through the proxy', async () => {
    const fetchMock = vi.fn(
      async () => new Response('png', { status: 200, headers: { 'Content-Type': 'image/png' } })
    );
    vi.stubGlobal('fetch', fetchMock);
    const blob = await agentApi.caseFile('tok', 'A1', 'plot-dark.png');
    expect(await blob.text()).toBe('png');
    expect((fetchMock.mock.calls[0] as unknown as [string])[0]).toMatch(
      /\/debug\/agent\/cases\/A1\/files\/plot-dark\.png$/
    );
  });
});

describe('the public lane', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
  });

  it('moves the session id out of the path', () => {
    expect(publicRoute('/sessions/S%2F1/dataset/undo')).toEqual({
      path: '/session/dataset/undo',
      session: 'S/1',
    });
    expect(publicRoute('/sessions/S1')).toEqual({ path: '/session', session: 'S1' });
    expect(publicRoute('/sessions/S1/artifacts/plot.py?v=2')).toEqual({
      path: '/session/artifacts/plot.py?v=2',
      session: 'S1',
    });
    expect(publicRoute('/sessions')).toEqual({ path: '/sessions', session: null });
    expect(publicRoute('/eligibility?spec=a&library=b')).toEqual({
      path: '/eligibility?spec=a&library=b',
      session: null,
    });
  });

  it('tells the lanes apart by the credential, and no header can carry the public one', () => {
    expect(laneOf(PUBLIC_LANE)).toBe('public');
    expect(laneOf('')).toBe('admin');
    expect(laneOf('an-admin-token')).toBe('admin');
    expect(PUBLIC_LANE).toContain('\u0000');
  });

  it('keeps one random tab id per tab', () => {
    const first = anonymousId();
    expect(first).toMatch(/^[A-Za-z0-9_-]{22,64}$/);
    expect(anonymousId()).toBe(first);
    expect(sessionStorage.getItem(ANONYMOUS_ID_KEY)).toBe(first);
    sessionStorage.clear();
    expect(anonymousId()).not.toBe(first);
  });

  it('calls /agent with the tab id and the session as headers, without a cookie or token', async () => {
    const fetchMock = vi.fn(async () => new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    await agentApi.undoDataset(PUBLIC_LANE, 'S/1');
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/agent\/session\/dataset\/undo$/);
    expect(url).not.toContain('/debug/');
    expect(url).not.toMatch(/S%2F1|S\/1/);
    expect(init.credentials).toBe('omit');
    const headers = init.headers as Record<string, string>;
    expect(headers['X-Anyplot-Session']).toBe('S/1');
    expect(headers['X-Anyplot-Anon']).toBe(anonymousId());
    expect(headers['X-Anyplot-Client']).toBe('agent-chat/1');
    expect(headers['X-Admin-Token']).toBeUndefined();
  });

  it('never touches the Access reload guard', async () => {
    sessionStorage.setItem(ACCESS_RELOAD_KEY, '1');
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{}', { status: 200 }))
    );
    await agentFetch('/status', PUBLIC_LANE);
    expect(sessionStorage.getItem(ACCESS_RELOAD_KEY)).toBe('1');
  });

  describe('the bot check', () => {
    afterEach(() => {
      vi.unstubAllEnvs();
      resetTurnstile();
      delete window.turnstile;
    });

    const sessionBody = JSON.stringify({ session_id: 'S1', eligibility: {} });

    function stubTurnstile(pass: boolean) {
      vi.stubEnv('VITE_TURNSTILE_SITE_KEY', '1x00000000000000000000AA');
      window.turnstile = {
        render: vi.fn((_container: HTMLElement, options: Record<string, unknown>) => {
          queueMicrotask(() =>
            pass
              ? (options.callback as (token: string) => void)('tok-1')
              : (options['error-callback'] as () => void)()
          );
          return 'w1';
        }),
        remove: vi.fn(),
      };
    }

    it('sends a fresh token when it opens a session or sends feedback on the public lane', async () => {
      stubTurnstile(true);
      const fetchMock = vi.fn(async () => new Response(sessionBody, { status: 200 }));
      vi.stubGlobal('fetch', fetchMock);

      await agentApi.openSession(PUBLIC_LANE, 'scatter-basic', 'matplotlib', 'en');
      await agentApi.sendFeedback(PUBLIC_LANE, 'S1', {
        reaction: 'bug',
        message: null,
        include_data: false,
        result_version: 1,
      });

      const sent = fetchMock.mock.calls.map(
        call => (call as unknown as [string, RequestInit])[1].headers as Record<string, string>
      );
      expect(sent.map(headers => headers[TURNSTILE_HEADER])).toEqual(['tok-1', 'tok-1']);
      expect(window.turnstile!.render).toHaveBeenCalledTimes(2);
    });

    it('never runs on the admin lane or on a call that acts on an open session', async () => {
      stubTurnstile(true);
      const fetchMock = vi.fn(async () => new Response(sessionBody, { status: 200 }));
      vi.stubGlobal('fetch', fetchMock);

      await agentApi.openSession('an-admin-token', 'scatter-basic', 'matplotlib', 'en');
      await agentApi.undoDataset(PUBLIC_LANE, 'S1');

      for (const call of fetchMock.mock.calls) {
        const headers = (call as unknown as [string, RequestInit])[1].headers as Record<
          string,
          string
        >;
        expect(headers[TURNSTILE_HEADER]).toBeUndefined();
      }
      expect(window.turnstile!.render).not.toHaveBeenCalled();
    });

    it('turns a check that fails in the browser into bot_check_failed, before any request', async () => {
      stubTurnstile(false);
      const fetchMock = vi.fn(async () => new Response(sessionBody, { status: 200 }));
      vi.stubGlobal('fetch', fetchMock);

      await expect(
        agentApi.openSession(PUBLIC_LANE, 'scatter-basic', 'matplotlib', 'en')
      ).rejects.toMatchObject({ name: 'AgentApiError', code: 'bot_check_failed', status: 0 });
      expect(fetchMock).not.toHaveBeenCalled();
    });

    it("reads the API's refusal as the same code", async () => {
      stubTurnstile(true);
      vi.stubGlobal(
        'fetch',
        vi.fn(
          async () =>
            new Response(JSON.stringify({ detail: 'bot_check_failed', ref: 'r1' }), { status: 403 })
        )
      );

      const refused = agentApi.openSession(PUBLIC_LANE, 'scatter-basic', 'matplotlib', 'en');

      await expect(refused).rejects.toMatchObject({ code: 'bot_check_failed', ref: 'r1' });
      await refused.catch((err: { unauthorized: boolean }) => expect(err.unauthorized).toBe(false));
    });
  });

  it('reads the door from GET /agent/lane, and anything else as closed', async () => {
    const answers = [
      new Response(JSON.stringify({ open: true }), { status: 200 }),
      new Response(JSON.stringify({ detail: 'agent chat is not enabled' }), { status: 404 }),
      new Response('not json', { status: 200 }),
    ];
    const fetchMock = vi.fn(async () => answers.shift()!);
    vi.stubGlobal('fetch', fetchMock);
    expect(await publicLaneOpen()).toBe(true);
    expect(await publicLaneOpen()).toBe(false);
    expect(await publicLaneOpen()).toBe(false);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/agent\/lane$/);
    expect(init.credentials).toBe('omit');
  });
});

describe('agentFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
  });

  it('reports a request without a readable answer as unreachable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.reject(new TypeError('Failed to fetch')))
    );
    await expect(agentFetch('/status', '')).rejects.toMatchObject({
      status: 0,
      code: 'unreachable',
    });
  });

  it('leaves the Access reload guard to the /debug page on the admin lane too', async () => {
    // The chat at `/agent` is not behind Access and never reloads for it; the guard is the
    // `/debug` page's alone, which sets and clears it.
    sessionStorage.setItem(ACCESS_RELOAD_KEY, '1');
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{}', { status: 200 }))
    );
    await agentFetch('/status', '');
    expect(sessionStorage.getItem(ACCESS_RELOAD_KEY)).toBe('1');
  });

  it('posts .undo() to the undo route with the CSRF header and no body', async () => {
    const answer = {
      preview: [['1', '2']],
      profile: { rows: 1, columns: [], source_format: 'csv', decimal: '.', warnings: [] },
      bindings: [],
      warnings: [],
      roles: [],
      version: 1,
    };
    const fetchMock = vi.fn(async () => new Response(JSON.stringify(answer), { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    await expect(agentApi.undoDataset('', 'S/1')).resolves.toEqual(answer);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/debug\/agent\/sessions\/S%2F1\/dataset\/undo$/);
    expect(init).toMatchObject({ method: 'POST' });
    expect(init.body).toBeUndefined();
    expect((init.headers as Record<string, string>)['X-Anyplot-Client']).toBe('agent-chat/1');
  });

  it('reads an undo at the paste as nothing_to_undo', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(JSON.stringify({ detail: 'nothing_to_undo', ref: 'r-u' }), { status: 422 })
      )
    );
    await expect(agentApi.undoDataset('', 'S1')).rejects.toMatchObject({
      status: 422,
      code: 'nothing_to_undo',
      ref: 'r-u',
    });
  });

  it('puts the chip language to the language route with the CSRF header and reads the answer', async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ language: 'en', source: 'chosen' }), { status: 200 })
    );
    vi.stubGlobal('fetch', fetchMock);
    await expect(agentApi.setLanguage('', 'S/1', 'English')).resolves.toEqual({
      language: 'en',
      source: 'chosen',
    });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/debug\/agent\/sessions\/S%2F1\/language$/);
    expect(init).toMatchObject({ method: 'PUT' });
    expect(JSON.parse(init.body as string)).toEqual({ language: 'English' });
    expect((init.headers as Record<string, string>)['X-Anyplot-Client']).toBe('agent-chat/1');
  });

  it('falls back to the value as sent for an answer it cannot read, and reads a 409', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 }))
    );
    await expect(agentApi.setLanguage('', 'S1', 'Klingon')).resolves.toEqual({
      language: 'Klingon',
      source: 'chosen',
    });
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(JSON.stringify({ detail: 'run_active', ref: 'r-l' }), { status: 409 })
      )
    );
    await expect(agentApi.setLanguage('', 'S1', 'de')).rejects.toMatchObject({
      status: 409,
      code: 'run_active',
      ref: 'r-l',
    });
  });

  it('sends an offer’s pick with via, and once more without it to a server from before the field', async () => {
    const bodies: unknown[] = [];
    let strict = false;
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url: string, init: RequestInit) => {
        const body = JSON.parse(init.body as string) as Record<string, string>;
        bodies.push(body);
        // A strict body from before `via`: the unknown key is a 422.
        if (strict && 'via' in body) {
          return new Response(JSON.stringify({ detail: 'invalid', ref: 'r-v' }), { status: 422 });
        }
        return new Response(
          JSON.stringify({ language: 'de', source: 'via' in body ? 'offer' : 'chosen' }),
          { status: 200 }
        );
      })
    );
    await expect(agentApi.setLanguage('', 'S1', 'de', 'offer')).resolves.toEqual({
      language: 'de',
      source: 'offer',
    });
    expect(bodies).toEqual([{ language: 'de', via: 'offer' }]);

    strict = true;
    bodies.length = 0;
    await expect(agentApi.setLanguage('', 'S1', 'de', 'offer')).resolves.toEqual({
      language: 'de',
      source: 'chosen',
    });
    expect(bodies).toEqual([{ language: 'de', via: 'offer' }, { language: 'de' }]);
    // The chip's pick never retries: a 422 there is the value's.
    bodies.length = 0;
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url: string, init: RequestInit) => {
        bodies.push(JSON.parse(init.body as string));
        return new Response(JSON.stringify({ detail: 'invalid', ref: 'r-x' }), { status: 422 });
      })
    );
    await expect(agentApi.setLanguage('', 'S1', 'x/y')).rejects.toMatchObject({ status: 422 });
    expect(bodies).toHaveLength(1);
  });

  it('sends the delete with keepalive when the page goes away', async () => {
    const fetchMock = vi.fn(async () => new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);
    await agentApi.deleteSession('', 'S1', { keepalive: true });
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init).toMatchObject({ method: 'DELETE', keepalive: true });
    expect((init.headers as Record<string, string>)['X-Anyplot-Client']).toBe('agent-chat/1');
  });
});

describe('agentApi.reportOutcome', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('posts the beacon with keepalive, the CSRF header and the three fields only', async () => {
    const fetchMock = vi.fn(async () => new Response(null, { status: 204 }));
    vi.stubGlobal('fetch', fetchMock);
    // A caller that slips in more than the contract allows: the client rebuilds the body.
    const smuggled = {
      action: 'feedback',
      version: 3,
      reaction: 'bug',
      message: 'the legend hides points',
      columns: ['revenue'],
    } as unknown as Parameters<typeof agentApi.reportOutcome>[2];
    await agentApi.reportOutcome('', 'S/1', smuggled);
    await agentApi.reportOutcome('', 'S/1', { action: 'downloaded_data', version: 3 });

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/debug\/agent\/sessions\/S%2F1\/outcome$/);
    expect(init).toMatchObject({ method: 'POST', keepalive: true });
    expect((init.headers as Record<string, string>)['X-Anyplot-Client']).toBe('agent-chat/1');
    expect(JSON.parse(init.body as string)).toEqual({
      action: 'feedback',
      version: 3,
      reaction: 'bug',
    });
    const [, second] = fetchMock.mock.calls[1] as unknown as [string, RequestInit];
    expect(JSON.parse(second.body as string)).toEqual({ action: 'downloaded_data', version: 3 });
  });

  it.each([
    ['a 429', () => Promise.resolve(new Response('{}', { status: 429 }))],
    ['a 404', () => Promise.resolve(new Response('{"detail":"not_found"}', { status: 404 }))],
    ['a 502', () => Promise.resolve(new Response('', { status: 502 }))],
    ['no network', () => Promise.reject(new TypeError('Failed to fetch'))],
  ])('swallows %s', async (_name, answer) => {
    vi.stubGlobal('fetch', vi.fn(answer));
    await expect(
      agentApi.reportOutcome('', 'S1', { action: 'saved_session', version: 0 })
    ).resolves.toBeUndefined();
  });
});

describe('agentApi.datasetCsv', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('reads the current version as text with a GET, never parsing it', async () => {
    const csv = 'city,value\n"Köln, Nord",1.50\nBonn,\n';
    const fetchMock = vi.fn(async () => new Response(csv, { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);
    const controller = new AbortController();

    await expect(agentApi.datasetCsv('', 'S/1', controller.signal)).resolves.toBe(csv);

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/debug\/agent\/sessions\/S%2F1\/dataset\/data\.csv$/);
    expect(init.method ?? 'GET').toBe('GET');
    expect(init.signal).toBe(controller.signal);
  });

  it('throws the route code, such as no_dataset before any data', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{"detail":"no_dataset","ref":"r1"}', { status: 422 }))
    );
    await expect(agentApi.datasetCsv('', 'S1')).rejects.toMatchObject({
      status: 422,
      code: 'no_dataset',
      ref: 'r1',
    });
  });
});

describe('agentApi library switch and plot memory', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  const CARRY = { decisions: 3, newer: 3, target_has_plot: false, from_plot: true, offer: true };
  const ENTRY = {
    id: 'm3',
    kind: 'reference_line',
    target: 'y',
    text: 'horizontal reference line at y = 7',
    expect: null,
    turn: 2,
  };

  it('posts the switch without a source and reads the target and the carry', async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            session_id: 'S1',
            eligibility: { eligible: true, status: 'clean', reasons: [] },
            target: { spec_id: 'scatter-basic', library: 'plotly' },
            carry: CARRY,
          }),
          { status: 200 }
        )
    );
    vi.stubGlobal('fetch', fetchMock);
    await expect(agentApi.switchLibrary('', 'S/1', 'scatter-basic', 'plotly')).resolves.toEqual({
      session_id: 'S1',
      eligibility: { eligible: true, status: 'clean', reasons: [] },
      target: { spec_id: 'scatter-basic', library: 'plotly' },
      carry: CARRY,
    });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/debug\/agent\/sessions\/S%2F1\/library$/);
    // `source` stays out: the BFF reads it as `menu`, and a page ahead of the API is no 422.
    expect(JSON.parse(init.body as string)).toEqual({
      spec_id: 'scatter-basic',
      library: 'plotly',
    });
  });

  it('names the chat as the source of a switch the user asked for there', async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            session_id: 'S1',
            eligibility: { eligible: true, status: 'clean', reasons: [] },
          }),
          { status: 200 }
        )
    );
    vi.stubGlobal('fetch', fetchMock);
    await agentApi.switchLibrary('', 'S1', 'scatter-basic', 'seaborn', 'chat');
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(init.body as string)).toEqual({
      spec_id: 'scatter-basic',
      library: 'seaborn',
      source: 'chat',
    });
  });

  it('reads the answer of a server without the plot memory as no target and no carry', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        async () =>
          new Response(
            JSON.stringify({
              session_id: 'S1',
              eligibility: { eligible: true, status: 'clean', reasons: [] },
            }),
            { status: 200 }
          )
      )
    );
    await expect(
      agentApi.switchLibrary('', 'S1', 'scatter-basic', 'seaborn')
    ).resolves.toMatchObject({ target: null, carry: null });
  });

  it('reads the memory with a GET and removes an entry with a DELETE', async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ entries: [ENTRY], max_entries: 30 }), { status: 200 })
    );
    vi.stubGlobal('fetch', fetchMock);
    await expect(agentApi.memory('', 'S/1')).resolves.toEqual({
      entries: [ENTRY],
      max_entries: 30,
      written: false, // an older server names none
    });
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toMatch(/\/debug\/agent\/sessions\/S%2F1\/memory$/);
    expect(init.method ?? 'GET').toBe('GET');

    fetchMock.mockImplementation(
      async () =>
        new Response(JSON.stringify({ entries: [], max_entries: 30, written: true }), {
          status: 200,
        })
    );
    await expect(agentApi.forgetMemory('', 'S/1', 'm3')).resolves.toEqual({
      entries: [],
      max_entries: 30,
      written: true,
    });
    const [deleteUrl, deleteInit] = fetchMock.mock.calls[1] as unknown as [string, RequestInit];
    expect(deleteUrl).toMatch(/\/debug\/agent\/sessions\/S%2F1\/memory\/m3$/);
    expect(deleteInit).toMatchObject({ method: 'DELETE' });
    expect((deleteInit.headers as Record<string, string>)['X-Anyplot-Client']).toBe('agent-chat/1');

    await expect(agentApi.forgetAllMemory('', 'S/1')).resolves.toMatchObject({ entries: [] });
    const [allUrl, allInit] = fetchMock.mock.calls[2] as unknown as [string, RequestInit];
    expect(allUrl).toMatch(/\/debug\/agent\/sessions\/S%2F1\/memory$/);
    expect(allInit).toMatchObject({ method: 'DELETE' });
  });

  it('refuses an entry id outside the pattern before any request, and reads the route codes', async () => {
    const fetchMock = vi.fn(
      async () =>
        new Response(JSON.stringify({ detail: 'run_active', ref: 'r-m' }), { status: 409 })
    );
    vi.stubGlobal('fetch', fetchMock);
    await expect(agentApi.forgetMemory('', 'S1', '../dataset')).rejects.toMatchObject({
      code: 'invalid',
    });
    expect(fetchMock).not.toHaveBeenCalled();
    await expect(agentApi.forgetMemory('', 'S1', 'm1')).rejects.toMatchObject({
      status: 409,
      code: 'run_active',
      ref: 'r-m',
    });
    // An answer that is no memory is the upstream's fault, never an empty list.
    fetchMock.mockImplementation(async () => new Response('{"ok":true}', { status: 200 }));
    await expect(agentApi.memory('', 'S1')).rejects.toMatchObject({ code: 'upstream' });
  });
});

describe('library switch and plot memory readers', () => {
  it('reads a carry with its five fields, and nothing half', () => {
    const carry = { decisions: 1, newer: 0, target_has_plot: true, from_plot: false, offer: false };
    expect(switchCarry(carry)).toEqual(carry);
    expect(switchCarry({ ...carry, extra: 'x' })).toEqual(carry);
    expect(switchCarry({ ...carry, decisions: -1 })).toBeNull();
    expect(switchCarry({ ...carry, newer: 1.5 })).toBeNull();
    expect(switchCarry({ ...carry, offer: 'yes' })).toBeNull();
    expect(switchCarry({ decisions: 1 })).toBeNull();
    expect(switchCarry(null)).toBeNull();
  });

  it('reads a target of two names', () => {
    expect(plotTarget({ spec_id: 'box-basic', library: 'd3' })).toEqual({
      spec_id: 'box-basic',
      library: 'd3',
    });
    expect(plotTarget({ spec_id: '', library: 'd3' })).toBeNull();
    expect(plotTarget({ library: 'd3' })).toBeNull();
    expect(plotTarget('d3')).toBeNull();
  });

  it('keeps the entries it can read, their documented fields only', () => {
    const memory = plotMemory({
      entries: [
        {
          id: 'm1',
          kind: 'axis_label',
          target: 'x',
          text: "x-axis label: 'Zeit (h)'",
          expect: 'Zeit (h)',
          turn: 3,
          secret: 'dropped',
        },
        { id: 'm2', kind: 'other', target: 'z', text: 't'.repeat(250), expect: '', turn: 'x' },
        { id: '../m3', kind: 'other', text: 'bad id' },
        { id: 'm4', kind: 'other', text: '   ' },
        'm5',
      ],
      max_entries: 30,
    });
    expect(memory).toEqual({
      entries: [
        {
          id: 'm1',
          kind: 'axis_label',
          target: 'x',
          text: "x-axis label: 'Zeit (h)'",
          expect: 'Zeit (h)',
          turn: 3,
        },
        { id: 'm2', kind: 'other', target: null, text: 't'.repeat(200), expect: null, turn: 0 },
      ],
      max_entries: 30,
      written: false,
    });
    expect(plotMemory({ entries: [] })).toEqual({ entries: [], max_entries: 30, written: false });
    expect(plotMemory({ entries: [], written: 'yes' })).toMatchObject({ written: false });
    expect(plotMemory({ entries: [], written: true })).toMatchObject({ written: true });
    expect(plotMemory({ entries: 'm1' })).toBeNull();
    expect(plotMemory([])).toBeNull();
  });

  it('counts both plot actions as plot runs', () => {
    expect(isPlotAction('create_plot')).toBe(true);
    expect(isPlotAction('carry_plot')).toBe(true);
    expect(isPlotAction('summarize_data')).toBe(false);
    expect(isPlotAction('message')).toBe(false);
  });
});

describe('helpers', () => {
  it('buckets sizes without exposing them', () => {
    expect(sizeBucket(10)).toBe('lt_1kb');
    expect(sizeBucket(5 * 1024)).toBe('1_10kb');
    expect(sizeBucket(20 * 1024)).toBe('10_50kb');
    expect(sizeBucket(200 * 1024)).toBe('50_200kb');
    expect(sizeBucket(200 * 1024 + 1)).toBe('200kb_1mb');
    expect(sizeBucket(1024 * 1024)).toBe('200kb_1mb');
    expect(sizeBucket(1024 * 1024 + 1)).toBe('over_1mb');
  });

  it('buckets counts without exposing them', () => {
    expect([0, 1, 2, 3, 12].map(countBucket)).toEqual(['1', '1', '2', '3+', '3+']);
  });

  it('names the rendered themes from the artifacts', () => {
    expect(renderedThemes(['plot-dark.png', 'plot.py'])).toEqual(['dark']);
    expect(renderedThemes(['plot.py'])).toEqual([]);
  });

  it('names the code artifact from the artifacts, plot.py without one', () => {
    expect(codeArtifact(['plot-light.png', 'plot.R', 'data.csv'])).toBe('plot.R');
    expect(codeArtifact(['plot-light.png', 'plot.tsx', 'data.csv'])).toBe('plot.tsx');
    expect(codeArtifact(['plot-light.png', 'data.csv'])).toBe('plot.py');
    expect(codeArtifact(['plot-light.png', 'plot.js', 'plot.html', 'data.csv'])).toBe('plot.js');
  });

  it('offers the page only for a version that lists it', () => {
    expect(hasPage(['plot-light.png', 'plot.js', 'plot.html', 'data.csv'])).toBe(true);
    expect(hasPage(['plot-light.png', 'plot.py', 'data.csv'])).toBe(false);
  });

  it('sends a locale the BFF accepts', () => {
    expect(browserLocale()).toMatch(/^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$/);
  });
});
