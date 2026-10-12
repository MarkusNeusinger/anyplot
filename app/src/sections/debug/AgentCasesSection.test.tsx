/**
 * The debug page's agent cases section against a stubbed BFF: the list and its
 * filters, `.more()`, the opened case with its renders as blob URLs, and the
 * triage changes with their optimistic update and revert.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { AgentCase, AgentCaseDetail } from 'src/lib/agent';
import { AgentCasesSection } from 'src/sections/debug/AgentCasesSection';
import { render, screen, userEvent, waitFor, within } from 'src/test-utils';

const A = '20261012T143005Z-1a2b3c4d';
const B = '20261011T090000Z-5e6f7a8b';
const C = '20261010T120000Z-99aa00bb';

function item(overrides: Partial<AgentCase> = {}): AgentCase {
  return {
    id: A,
    created_at: '2026-10-12T14:30:05Z',
    reaction: 'thumbs_down',
    message: 'the legend hides points',
    include_data: true,
    status: 'new',
    tags: ['legend'],
    spec_id: 'scatter-basic',
    library_id: 'matplotlib',
    locale: 'de-CH',
    result_version: 3,
    replaces: null,
    superseded_by: null,
    promoted_at: null,
    expected: null,
    model: 'gemini-3.8-flash',
    model_version: null,
    judge_model: 'gemini-3.8-flash',
    prompt_hash: '0123456789abcdef',
    pipeline_status: 'ok',
    attempts: 2,
    tokens: null,
    cost_estimate: null,
    files: ['plot-light.png', 'plot-dark.png', 'plot.py', 'data.csv', 'manifest.json'],
    user_hash: 'adm_0123456789abcdef',
    session_hash: 'fedcba9876543210',
    case_uri: `gs://anyplot-agent-cases/cases/${A}/`,
    manifest_schema: 1,
    updated_at: '2026-10-12T14:30:05Z',
    ...overrides,
  };
}

function detailOf(row: AgentCase, overrides: Partial<AgentCaseDetail> = {}): AgentCaseDetail {
  return {
    ...row,
    expired: false,
    transcript: [
      { role: 'user', text: 'make the legend smaller' },
      { role: 'assistant', text: 'I moved the legend.' },
    ],
    code: 'import pandas as pd\nax.legend(loc="upper left")\n',
    diff: '--- catalogue/scatter-basic/matplotlib.py\n+++ case/plot.py\n@@ -1 +1 @@\n-ax.legend()\n+ax.legend(loc="upper left")\n',
    catalogue_library_version: '3.10.1',
    snapshot_library_version: '3.10.0',
    residual_defects: ['VQ-03 light: overlap'],
    changes: ['legend moved'],
    result_reason: null,
    config: { provider: 'vertex', prompt_hashes: { root: 'aaaa1111' } },
    bindings: [{ role: 'x', column: 'year' }],
    siblings: [],
    ...overrides,
  };
}

const json = (status: number, body: unknown, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', ...headers },
  });

interface Call {
  method: string;
  url: URL;
  init: RequestInit;
}

let calls: Call[];
let listAnswer: (url: URL) => Response;
let detailAnswer: (id: string) => Response;
let patchAnswer: (id: string, body: Record<string, unknown>) => Response;

function stubFetch() {
  calls = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: string, init: RequestInit = {}) => {
      const url = new URL(input);
      const method = init.method ?? 'GET';
      calls.push({ method, url, init });
      const path = url.pathname;
      if (path === '/debug/agent/cases' && method === 'GET') return listAnswer(url);
      const file = path.match(/^\/debug\/agent\/cases\/([^/]+)\/files\/(.+)$/);
      if (file) {
        return new Response('png', { status: 200, headers: { 'Content-Type': 'image/png' } });
      }
      const one = path.match(/^\/debug\/agent\/cases\/([^/]+)$/);
      if (one && method === 'GET') return detailAnswer(one[1]);
      if (one && method === 'PATCH') {
        return patchAnswer(one[1], JSON.parse(String(init.body)) as Record<string, unknown>);
      }
      return json(404, { detail: 'not_found' });
    })
  );
}

const listCalls = () =>
  calls.filter(c => c.method === 'GET' && c.url.pathname === '/debug/agent/cases');
const lastQuery = () => {
  const list = listCalls();
  return list[list.length - 1]?.url.searchParams;
};
const patches = () => calls.filter(c => c.method === 'PATCH');

beforeEach(() => {
  listAnswer = () =>
    json(200, {
      items: [item(), item({ id: B, reaction: 'bug', message: 'axis labels overlap' })],
      has_more: false,
    });
  detailAnswer = id => json(200, detailOf(item({ id })));
  patchAnswer = (id, body) => json(200, { ...item({ id }), ...body });
  URL.createObjectURL = vi.fn(() => `blob:${Math.random()}`);
  URL.revokeObjectURL = vi.fn();
  stubFetch();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function renderSection(token = 'tok') {
  return render(<AgentCasesSection token={token} reloadCounter={0} />);
}

const row = (id: string) => document.querySelector(`[data-case-id="${id}"]`) as HTMLElement;

describe('AgentCasesSection list', () => {
  it('renders the rows of a page from the open queue, superseded hidden', async () => {
    renderSection();
    expect(screen.getByText('loading cases…')).toBeInTheDocument();
    expect(await screen.findByText('the legend hides points')).toBeInTheDocument();
    expect(screen.getByText('axis labels overlap')).toBeInTheDocument();
    expect(row(A)).toHaveTextContent('scatter-basic · matplotlib · v3');
    expect(row(A)).toHaveTextContent('thumbs down');
    expect(within(row(B)).getByText('bug')).toBeInTheDocument();
    expect(lastQuery()?.toString()).toBe('status=open');
    expect(listCalls()[0].init.headers).toMatchObject({ 'X-Admin-Token': 'tok' });
  });

  it('sends each filter in the query string', async () => {
    const user = userEvent.setup();
    renderSection();
    await screen.findByText('the legend hides points');

    await user.selectOptions(screen.getByLabelText('Filter by reaction'), 'bug');
    await waitFor(() => expect(lastQuery()?.get('reaction')).toBe('bug'));

    await user.selectOptions(screen.getByLabelText('Filter by status'), '');
    await waitFor(() => expect(lastQuery()?.has('status')).toBe(false));

    await user.selectOptions(screen.getByLabelText('Filter by library'), 'seaborn');
    await waitFor(() => expect(lastQuery()?.get('library')).toBe('seaborn'));

    await user.type(screen.getByLabelText('Filter by spec'), 'Scatter-Basic{Enter}');
    await waitFor(() => expect(lastQuery()?.get('spec')).toBe('scatter-basic'));

    // A text filter also applies when the field loses the focus.
    await user.type(screen.getByLabelText('Filter by model version'), 'gemini-3.8-flash-001');
    await user.tab();
    await waitFor(() => expect(lastQuery()?.get('model_version')).toBe('gemini-3.8-flash-001'));

    await user.type(screen.getByLabelText('Filter by tag'), 'legend{Enter}');
    await waitFor(() => expect(lastQuery()?.get('tag')).toBe('legend'));

    await user.click(screen.getByRole('checkbox', { name: 'show superseded' }));
    await waitFor(() => expect(lastQuery()?.get('include_superseded')).toBe('true'));
  });

  it('appends the next page with the last id as the cursor', async () => {
    const user = userEvent.setup();
    listAnswer = url =>
      url.searchParams.get('before') === B
        ? json(200, { items: [item({ id: C, message: 'third' })], has_more: false })
        : json(200, { items: [item(), item({ id: B })], has_more: true });
    renderSection();
    await user.click(await screen.findByRole('button', { name: 'Load more cases' }));
    expect(await screen.findByText('third')).toBeInTheDocument();
    expect(lastQuery()?.get('before')).toBe(B);
    expect(lastQuery()?.get('status')).toBe('open');
    expect(screen.queryByRole('button', { name: 'Load more cases' })).not.toBeInTheDocument();
  });

  it('marks a contradiction, a promotion, a superseded case and a case without data', async () => {
    listAnswer = () =>
      json(200, {
        items: [
          item({ reaction: 'thumbs_up', pipeline_status: 'needs_attention', include_data: false }),
          item({ id: B, promoted_at: '2026-10-12T15:00:00Z', superseded_by: A }),
        ],
        has_more: false,
      });
    renderSection();
    await screen.findAllByText('the legend hides points');
    expect(within(row(A)).getByText('contradicts pipeline')).toBeInTheDocument();
    expect(within(row(A)).getByText('no data')).toBeInTheDocument();
    expect(within(row(B)).getByText('promoted')).toBeInTheDocument();
    expect(within(row(B)).getByText('superseded')).toBeInTheDocument();
  });

  it('renders "no cases" for an answer without an items list', async () => {
    listAnswer = () => json(200, { total_specs: 3 });
    renderSection();
    expect(await screen.findByText('no cases with status "open"')).toBeInTheDocument();
  });

  it('renders the kill switch as one line', async () => {
    listAnswer = () => json(404, { detail: 'agent chat is not enabled' });
    renderSection();
    expect(await screen.findByText('agent chat is not enabled on this server')).toBeInTheDocument();
  });

  it('reads an unreadable failure as "failed to load cases" and never reloads the page', async () => {
    const replace = vi.fn();
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { ...window.location, replace },
    });
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve({ ok: false, status: 500 }))
    );
    renderSection();
    expect(await screen.findByRole('alert')).toHaveTextContent('failed to load cases');
    expect(replace).not.toHaveBeenCalled();
  });

  it('shows a list error with its ref', async () => {
    listAnswer = () => json(503, { detail: 'unavailable', ref: 'r-9' });
    renderSection();
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'the server is not ready (no database, or the admin gate is not configured) · ref r-9'
    );
  });
});

describe('AgentCasesSection triage', () => {
  it('changes a status with one PATCH, the CSRF header and the token', async () => {
    const user = userEvent.setup();
    renderSection();
    await screen.findByText('the legend hides points');
    await user.selectOptions(screen.getByLabelText(`Status of case ${A}`), 'in_progress');
    await waitFor(() => expect(patches()).toHaveLength(1));
    const [patch] = patches();
    expect(patch.url.pathname).toBe(`/debug/agent/cases/${A}`);
    expect(JSON.parse(String(patch.init.body))).toEqual({ status: 'in_progress' });
    expect(patch.init.headers).toMatchObject({
      'X-Anyplot-Client': 'agent-chat/1',
      'X-Admin-Token': 'tok',
      'Content-Type': 'application/json',
    });
    expect(screen.getByLabelText(`Status of case ${A}`)).toHaveValue('in_progress');
  });

  it('puts a refused change back and shows why with the ref', async () => {
    const user = userEvent.setup();
    patchAnswer = () => json(502, { detail: 'storage', ref: 'r-1' }, { 'X-Request-Id': 'r-1' });
    renderSection();
    await screen.findByText('the legend hides points');
    await user.selectOptions(screen.getByLabelText(`Status of case ${A}`), 'done');
    expect(await within(row(A)).findByRole('alert')).toHaveTextContent(
      'the case files could not be read · ref r-1'
    );
    expect(screen.getByLabelText(`Status of case ${A}`)).toHaveValue('new');
  });

  it('opens a case with both renders as blob URLs and revokes them on close', async () => {
    const user = userEvent.setup();
    renderSection();
    await user.click(await screen.findByRole('button', { name: `Open case ${A}` }));
    const article = await screen.findByRole('article', { name: `Case ${A}` });
    expect(
      calls.some(c => c.method === 'GET' && c.url.pathname === `/debug/agent/cases/${A}`)
    ).toBe(true);
    const light = await within(article).findByAltText('light render of scatter-basic (matplotlib)');
    const dark = await within(article).findByAltText('dark render of scatter-basic (matplotlib)');
    expect(light.getAttribute('src')).toMatch(/^blob:/);
    expect(dark.getAttribute('src')).toMatch(/^blob:/);
    const files = calls.filter(c => c.url.pathname.includes('/files/')).map(c => c.url.pathname);
    expect(files).toEqual([
      `/debug/agent/cases/${A}/files/plot-light.png`,
      `/debug/agent/cases/${A}/files/plot-dark.png`,
    ]);

    // The detail: the diff, the defect lines, the transcript, the config stamp.
    expect(within(article).getByLabelText(/^Diff from the catalogue/)).toHaveTextContent(
      '+ax.legend(loc="upper left")'
    );
    expect(within(article).getByText('VQ-03 light: overlap')).toBeInTheDocument();
    expect(within(article).getByText('make the legend smaller')).toBeInTheDocument();
    expect(within(article).getByText('root: aaaa1111')).toBeInTheDocument();
    expect(
      within(article).getByText('your reaction contradicts the pipeline outcome (ok)')
    ).toBeInTheDocument();
    expect(
      within(article).getByText(/library catalogue 3\.10\.1 · session 3\.10\.0/)
    ).toBeInTheDocument();

    await user.click(within(article).getByRole('button', { name: 'code' }));
    expect(within(article).queryByLabelText(/^Diff from the catalogue/)).not.toBeInTheDocument();

    await user.click(within(article).getByRole('button', { name: `Close case ${A}` }));
    expect(screen.queryByRole('article')).not.toBeInTheDocument();
    expect(URL.revokeObjectURL).toHaveBeenCalledTimes(2);
  });

  it('shows an expired case without its files', async () => {
    const user = userEvent.setup();
    detailAnswer = id =>
      json(
        200,
        detailOf(item({ id }), {
          expired: true,
          transcript: null,
          code: null,
          diff: null,
          snapshot_library_version: null,
          result_reason: null,
          config: null,
          residual_defects: [],
          changes: [],
          bindings: [],
        })
      );
    renderSection();
    await user.click(await screen.findByRole('button', { name: `Open case ${A}` }));
    const article = await screen.findByRole('article', { name: `Case ${A}` });
    expect(
      within(article).getByText(
        'the case files expired in the bucket (180-day lifecycle); the row and its triage state stay'
      )
    ).toBeInTheDocument();
    expect(within(article).queryByRole('img')).not.toBeInTheDocument();
    expect(calls.some(c => c.url.pathname.includes('/files/'))).toBe(false);
  });

  it('shows a missing render and a failed image', async () => {
    const user = userEvent.setup();
    detailAnswer = id => json(200, detailOf(item({ id, files: ['plot-light.png', 'plot.py'] })));
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: string, init: RequestInit = {}) => {
        const url = new URL(input);
        calls.push({ method: init.method ?? 'GET', url, init });
        if (url.pathname.endsWith('/files/plot-light.png')) {
          return json(404, { detail: 'not_found', ref: 'r-2' });
        }
        if (url.pathname === `/debug/agent/cases/${A}`) return detailAnswer(A);
        return listAnswer(url);
      })
    );
    renderSection();
    await user.click(await screen.findByRole('button', { name: `Open case ${A}` }));
    const article = await screen.findByRole('article', { name: `Case ${A}` });
    expect(await within(article).findByText('image failed (not_found)')).toBeInTheDocument();
    expect(within(article).getByText('no dark render')).toBeInTheDocument();
  });

  it('adds a tag, promotes a thumbs case and opens a sibling', async () => {
    const user = userEvent.setup();
    detailAnswer = id => json(200, detailOf(item({ id }), { siblings: id === A ? [B] : [] }));
    renderSection();
    await user.click(await screen.findByRole('button', { name: `Open case ${A}` }));
    const article = await screen.findByRole('article', { name: `Case ${A}` });

    await user.type(within(article).getByLabelText('Add a tag'), 'overlap{Enter}');
    await waitFor(() => expect(patches()).toHaveLength(1));
    expect(JSON.parse(String(patches()[0].init.body))).toEqual({ tags: ['legend', 'overlap'] });
    // The row in the list follows the detail.
    expect(await within(row(A)).findByText('overlap')).toBeInTheDocument();

    const promote = within(article).getByRole('button', { name: 'Promote to an eval case' });
    await waitFor(() => expect(promote).toBeEnabled());
    await user.click(promote);
    await waitFor(() => expect(patches()).toHaveLength(2));
    expect(JSON.parse(String(patches()[1].init.body))).toEqual({
      promoted: true,
      expected: 'rejected',
    });

    await user.click(within(article).getByRole('button', { name: `Open case ${B}` }));
    expect(await screen.findByRole('article', { name: `Case ${B}` })).toBeInTheDocument();
  });

  it('shows a refused change of the opened case under its controls', async () => {
    const user = userEvent.setup();
    patchAnswer = () => json(422, { detail: 'no_data', ref: 'r-3' });
    renderSection();
    await user.click(await screen.findByRole('button', { name: `Open case ${A}` }));
    const article = await screen.findByRole('article', { name: `Case ${A}` });
    await user.selectOptions(within(article).getByLabelText('Status'), 'done');
    expect(await within(article).findByRole('alert')).toHaveTextContent(
      'this case has no data file; the harness cannot run it · ref r-3'
    );
    expect(within(article).getByLabelText('Status')).toHaveValue('new');

    // Read in the detail, the line does not move to the row once the case closes.
    await user.click(within(article).getByRole('button', { name: `Close case ${A}` }));
    expect(within(row(A)).queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows a case that is gone and closes it', async () => {
    const user = userEvent.setup();
    detailAnswer = () => json(404, { detail: 'not_found', ref: 'r-4' });
    renderSection();
    await user.click(await screen.findByRole('button', { name: `Open case ${A}` }));
    expect(await screen.findByText('this case is gone · ref r-4')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Close the case' }));
    expect(screen.queryByText('this case is gone · ref r-4')).not.toBeInTheDocument();
  });
});
