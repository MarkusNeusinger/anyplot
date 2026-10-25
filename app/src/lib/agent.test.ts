import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  agentApi,
  agentFetch,
  browserLocale,
  caseListQuery,
  codeArtifact,
  convertAnswer,
  countBucket,
  longSuggestion,
  parseAgentEvent,
  renderedThemes,
  sizeBucket,
  toAgentApiError,
  toBase64,
} from 'src/lib/agent';
import { ACCESS_RELOAD_KEY } from 'src/utils/adminAuth';

const raw = (event: string, data: unknown) => ({
  event,
  data: typeof data === 'string' ? data : JSON.stringify(data),
});

describe('parseAgentEvent', () => {
  it('types the queued status and the pipeline steps', () => {
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
    });
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
    expect(language({ language: 'de', source: 'detected' })).toEqual({
      language: 'de',
      source: 'detected',
    });
    expect(language({ language: 'Klingon', source: 'chosen', extra: 1 })).toEqual({
      language: 'Klingon',
      source: 'chosen',
    });
    expect(language({ language: 'en', source: 'default' })).toEqual({
      language: 'en',
      source: 'default',
    });
    expect(language({ language: 'de', source: 'pasted' })).toEqual({
      language: 'de',
      source: 'pasted',
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

  it('clears the Access reload guard once an answer arrives', async () => {
    sessionStorage.setItem(ACCESS_RELOAD_KEY, '1');
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response('{}', { status: 200 }))
    );
    await agentFetch('/status', '');
    expect(sessionStorage.getItem(ACCESS_RELOAD_KEY)).toBeNull();
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
  });

  it('sends a locale the BFF accepts', () => {
    expect(browserLocale()).toMatch(/^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$/);
  });
});
