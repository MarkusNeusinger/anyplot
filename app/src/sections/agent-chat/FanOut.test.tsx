import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { FanOut } from 'src/sections/agent-chat/FanOut';

vi.mock('src/hooks/useAnalytics', () => ({
  useAnalytics: () => ({ trackEvent: vi.fn(), trackPageview: vi.fn() }),
}));

interface Call {
  method: string;
  path: string;
  body: unknown;
}

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

const wire = (event: string, data: unknown) => `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;

/** A turn's stream the test ends: `finish` sends the plot and `done`. */
function liveTurn() {
  const encoder = new TextEncoder();
  let controller!: ReadableStreamDefaultController<Uint8Array>;
  const body = new ReadableStream<Uint8Array>({
    start(c) {
      controller = c;
      c.enqueue(encoder.encode(wire('status', { step: 'adapting', attempt: 1 })));
    },
  });
  return {
    response: new Response(body, { status: 200, headers: { 'Content-Type': 'text/event-stream' } }),
    finish: () => {
      controller.enqueue(encoder.encode(wire('plot', PLOT_OK)));
      controller.enqueue(encoder.encode(wire('done', { llm_calls: 3 })));
      controller.close();
    },
  };
}

const DATASET = {
  preview: [['1.5', '52']],
  profile: {
    rows: 1,
    columns: [
      { name: 'Study Hours', dtype: 'number', missing: 0, unique: 1 },
      { name: 'Exam Score', dtype: 'integer', missing: 0, unique: 1 },
    ],
    source_format: 'csv',
    decimal: '.',
    warnings: [],
  },
  bindings: [
    { role: 'x', column: 'Study Hours' },
    { role: 'y', column: 'Exam Score' },
  ],
  warnings: [],
  roles: [
    { name: 'x', kinds: ['numeric'], required: true, variadic: false, description: 'x' },
    { name: 'y', kinds: ['numeric'], required: true, variadic: false, description: 'y' },
  ],
  version: 1,
};

const PLOT_OK = {
  status: 'ok',
  reason: null,
  attempts: 1,
  artifacts: ['plot-light.png', 'plot.py', 'data.csv'],
  changes: [],
  residual_defects: [],
  version: 1,
};

const UPLOAD = { text: 'Study Hours,Exam Score\n1.5,52\n', confirmed: false, source: 'scores.csv' };
const BINDINGS = { x: 'Study Hours', y: 'Exam Score' };

let calls: Call[];
let turns: Map<string, ReturnType<typeof liveTurn>>;

/** The BFF: a session per library (`S-<library>`), `ineligible` libraries refused at the open. */
function mockBff(ineligible: string[] = []) {
  calls = [];
  turns = new Map();
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const path = new URL(input).pathname.replace(/^.*\/debug\/agent/, '');
      const method = init.method ?? 'GET';
      const body = typeof init.body === 'string' ? JSON.parse(init.body) : undefined;
      calls.push({ method, path, body });
      if (method === 'POST' && path === '/sessions') {
        const { library } = body as { library: string };
        if (ineligible.includes(library)) return json(422, { detail: 'not_eligible', ref: 'r' });
        return json(200, {
          session_id: `S-${library}`,
          eligibility: { eligible: true, status: 'clean', reasons: [] },
        });
      }
      const sid = path.split('/')[2];
      if (method === 'DELETE') return new Response(null, { status: 204 });
      if (path.endsWith('/dataset')) return json(200, DATASET);
      if (path.endsWith('/bindings')) {
        return json(200, { bindings: body, complete: true, missing_roles: [] });
      }
      if (path.endsWith('/dataset/confirm'))
        return json(200, { confirmed: true, rows: 1, columns: 2 });
      if (path.endsWith('/messages')) {
        const turn = liveTurn();
        turns.set(sid, turn);
        return turn.response;
      }
      if (path.includes('/artifacts/')) {
        return new Response('png', { status: 200, headers: { 'Content-Type': 'image/png' } });
      }
      return json(404, { detail: 'not_found', ref: null });
    })
  );
}

const plotTurns = () => calls.filter(call => call.path.endsWith('/messages'));
const card = (library: string) => screen.getByRole('article', { name: library });

function renderFanOut(libraries: string[], maxRuns: number, onClose = vi.fn()) {
  return render(
    <FanOut
      specId="scatter-basic"
      libraries={libraries}
      locale="en"
      token=""
      upload={UPLOAD}
      bindings={BINDINGS}
      maxRuns={maxRuns}
      onClose={onClose}
    />
  );
}

beforeEach(() => {
  URL.createObjectURL = vi.fn(() => 'blob:mock');
  URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('FanOut', () => {
  it('replays the upload in a session per library and runs at most maxRuns plots at once', async () => {
    mockBff();
    renderFanOut(['matplotlib', 'seaborn', 'altair'], 2);

    await waitFor(() => expect(plotTurns()).toHaveLength(2));
    // Every library stored the same upload with the same bindings, and no summary turn ran.
    for (const library of ['matplotlib', 'seaborn', 'altair']) {
      const upload = calls.find(call => call.path === `/sessions/S-${library}/dataset`);
      // The client sends `confirmed` only when it is true.
      expect(upload?.body).toEqual({ text: UPLOAD.text, source: UPLOAD.source });
      const put = calls.find(call => call.path === `/sessions/S-${library}/bindings`);
      expect(put?.body).toEqual([
        { role: 'x', column: 'Study Hours' },
        { role: 'y', column: 'Exam Score' },
      ]);
    }
    expect(plotTurns().map(call => call.body)).toEqual([
      { action: 'create_plot' },
      { action: 'create_plot' },
    ]);
    expect(within(card('altair')).getByTestId('fanout-status')).toHaveTextContent(
      'waiting for a free place…'
    );
    expect(screen.getByText(/0 of 3 done · at most 2 at a time/)).toBeInTheDocument();

    // A finished plot frees its place: the third library starts.
    turns.get('S-matplotlib')!.finish();
    await waitFor(() => expect(plotTurns()).toHaveLength(3));
    await waitFor(() =>
      expect(within(card('matplotlib')).getByTestId('fanout-status')).toHaveTextContent('v1 · ok')
    );
    expect(
      await within(card('matplotlib')).findByRole('img', { name: /matplotlib plot, version 1/ })
    ).toHaveAttribute('src', 'blob:mock');
    expect(within(card('altair')).getByTestId('fanout-status')).toHaveTextContent('adapting…');
  });

  it('frees the place of a library that cannot open, and deletes the sessions when it goes', async () => {
    mockBff(['plotnine']);
    const onClose = vi.fn();
    const view = renderFanOut(['plotnine', 'seaborn'], 1, onClose);

    await waitFor(() => expect(plotTurns()).toHaveLength(1));
    expect(plotTurns()[0].path).toBe('/sessions/S-seaborn/messages');
    expect(within(card('plotnine')).getByTestId('fanout-status')).toHaveTextContent('not eligible');

    fireEvent.click(screen.getByRole('button', { name: 'Stop the seaborn plot' }));
    await waitFor(() =>
      expect(calls.some(call => call.path === '/sessions/S-seaborn/cancel')).toBe(true)
    );

    fireEvent.click(screen.getByRole('button', { name: 'Close all libraries' }));
    expect(onClose).toHaveBeenCalledTimes(1);
    view.unmount();
    await waitFor(() =>
      expect(
        calls.some(call => call.method === 'DELETE' && call.path === '/sessions/S-seaborn')
      ).toBe(true)
    );
  });
});
