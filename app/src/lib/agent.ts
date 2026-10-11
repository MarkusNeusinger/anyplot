/**
 * Client for the admin-only agent chat BFF (`/debug/agent/*`, api/routers/agent.py).
 *
 * The contract is documented in docs/reference/api.md ("Agent chat"); the
 * design in docs/concepts/agent-network.md. Every call goes through
 * `fetchWithAuth` (Cloudflare Access cookie or the admin token) against the
 * debug API base, and every state-changing call carries the CSRF header
 * `X-Anyplot-Client: agent-chat/1`. Errors arrive as
 * `{"detail": "<code>", "ref": "<request id>"}` and become `AgentApiError`.
 */

import { DEBUG_API_URL } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';
import type { SseEvent } from 'src/lib/sse';
import { clearAccessReloadGuard } from 'src/utils/adminAuth';

export const AGENT_CLIENT_HEADERS = { 'X-Anyplot-Client': 'agent-chat/1' } as const;
/** The BFF's limit on pasted data: 200 KB of UTF-8. */
export const MAX_DATASET_BYTES = 200 * 1024;
/** The BFF's limit on one chat message. */
export const MAX_MESSAGE_CHARS = 2000;
/** The libraries the agents service renders in phase 1; `/status` names the live set. */
export const DEFAULT_AGENT_LIBRARIES = ['matplotlib', 'seaborn'] as const;

export type Theme = 'light' | 'dark';
export type ArtifactName = 'plot-light.png' | 'plot-dark.png' | 'plot.py' | 'data.csv';
export const PNG_ARTIFACT: Record<Theme, ArtifactName> = {
  light: 'plot-light.png',
  dark: 'plot-dark.png',
};

// ============================================================================
// Payloads
// ============================================================================

export interface AgentStatus {
  libraries: string[];
  model?: string;
  provider?: string;
  waiting?: number;
  in_flight?: number;
  enabled: boolean;
}

export interface Eligibility {
  eligible: boolean;
  status: string;
  reasons: string[];
}

export interface SessionOpened {
  session_id: string;
  eligibility: Eligibility;
}

export type ColumnDtype = 'integer' | 'number' | 'datetime' | 'boolean' | 'text';
const COLUMN_DTYPES = new Set<string>(['integer', 'number', 'datetime', 'boolean', 'text']);

export interface ColumnProfile {
  name: string;
  dtype: ColumnDtype;
  missing: number;
  unique: number;
  min?: number | string | null;
  max?: number | string | null;
  top?: string[];
  /** The statistics of a numeric column (six significant digits); `null` for any other column. */
  mean?: number | null;
  median?: number | null;
}

export interface DatasetProfile {
  rows: number;
  columns: ColumnProfile[];
  source_format: string;
  decimal: string;
  warnings: string[];
}

export interface Binding {
  role: string;
  /** `null` leaves the role unbound. */
  column: string | null;
}

/**
 * One data role the spec declares. A single role binds under its own name; a
 * variadic family (`y`) binds its members `y1`, `y2`, ... and never its bare
 * name. A role without kinds accepts any column but has no default.
 */
export interface RoleSpec {
  name: string;
  /** `numeric`, `categorical`, `text`, `boolean`, `datetime`. */
  kinds: string[];
  required: boolean;
  variadic: boolean;
  /** The spec's own words for the role. */
  description: string;
}

export interface DatasetParsed {
  /** Up to 20 data rows (the header is `profile.columns[].name`). */
  preview: string[][];
  profile: DatasetProfile;
  /** The server's default bindings; roles it could not match are absent. */
  bindings: Binding[];
  warnings: string[];
  /** Every role of the spec; absent from an agents service older than this field. */
  roles?: RoleSpec[];
  /**
   * The data's version: a paste is 1, each change the assistant made to it one
   * more, each undo one less. `.undo()` is possible while it is above 1.
   */
  version: number;
}

/**
 * A data version the assistant made in step 1 (`done.dataset`, after its
 * `prepare_data` changed the data): the dataset route's shape without the
 * roles, plus one English line per operation. The data is unconfirmed again.
 */
export interface DatasetChanged {
  /** Up to 20 data rows (the header is `profile.columns[].name`). */
  preview: string[][];
  profile: DatasetProfile;
  /** The bindings carried over to the new version. */
  bindings: Binding[];
  warnings: string[];
  /** What changed, one line per operation, such as `dropped 1 row where Tier = 'Gesamt'`. */
  changes: string[];
  /** 2 or more: the paste is version 1. */
  version: number;
}

/**
 * The other answer of `POST .../dataset`: the pasted text was not a table, so
 * the server read it with a model and stored nothing. The page shows the table
 * for the user to check; confirming posts `text` again, which then parses and
 * stores like any pasted CSV. No bindings and no roles yet.
 */
export interface DatasetTranscribed {
  transcribed: true;
  /** The canonical CSV the model wrote: comma-separated, header line first. */
  text: string;
  /** Up to 20 data rows (the header is `profile.columns[].name`). */
  preview: string[][];
  profile: DatasetProfile;
  warnings: string[];
  /** At most 200 characters from the model about anything ambiguous; often empty. */
  note: string;
}

export type DatasetAnswer = DatasetParsed | DatasetTranscribed;

/** Whether the dataset answer is a transcription that awaits the user's confirmation. */
export function isTranscribed(answer: DatasetAnswer): answer is DatasetTranscribed {
  return (answer as Partial<DatasetTranscribed>).transcribed === true;
}

export interface BindingsApplied {
  bindings: Binding[];
  complete: boolean;
  /** Required roles without a column; a variadic family by its name (`y`). */
  missing_roles: string[];
}

/**
 * The answer of `POST .../dataset/confirm`: the user checked the stored data and
 * its bindings. The server drops the confirmation when the dataset or a binding
 * changes; until it holds, `.create_plot()` answers `not_ready` (`data_unconfirmed`).
 */
export interface DatasetConfirmed {
  confirmed: true;
  rows: number;
  columns: number;
}

export type PlotStatus = 'ok' | 'needs_attention' | 'failed' | 'not_ready';

export interface PlotResult {
  status: PlotStatus;
  reason?: string | null;
  attempts: number;
  artifacts: ArtifactName[];
  changes: string[];
  residual_defects: string[];
  /** The stored version's number (`ok` and `needs_attention`); `null` from an older server. */
  version: number | null;
}

export interface ThemeRendered {
  status: 'ok' | 'needs_attention' | 'failed';
  reason?: string | null;
  artifacts: ArtifactName[];
}

/**
 * The page's own chat turns: `summarize_data` asks the assistant for the step-1
 * summary of the stored data, `create_plot` starts step 2. Neither passes the
 * scope judge.
 */
export type TurnAction = 'create_plot' | 'summarize_data';

/** The body of `POST .../messages`: the user's words or one of the page's actions. */
export type TurnBody = { text: string } | { action: TurnAction };

// ============================================================================
// Errors
// ============================================================================

/** The strings of an array field; anything else is dropped. */
const strings = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];

export class AgentApiError extends Error {
  readonly status: number;
  /**
   * The BFF's code (`run_active`, `too_long`, ...), or `unreachable` when the
   * request got no answer the page can read (see `agentFetch`).
   */
  readonly code: string;
  /** The request id to quote, when the BFF minted one. */
  readonly ref: string | null;
  /** The binding check's lines of a refused `PUT /bindings` (`422 invalid`); empty otherwise. */
  readonly errors: string[];

  constructor(status: number, code: string, ref: string | null = null, errors: string[] = []) {
    super(`agent request failed: ${status} ${code}`);
    this.name = 'AgentApiError';
    this.status = status;
    this.code = code;
    this.ref = ref;
    this.errors = errors;
  }

  /** 401 and 403 from the admin gate: the browser is not (or no longer) signed in as an admin. */
  get unauthorized(): boolean {
    return this.status === 401 || (this.status === 403 && this.code === 'forbidden');
  }
}

const FALLBACK_CODES: Record<number, string> = {
  400: 'bad_request',
  401: 'unauthorized',
  403: 'forbidden',
  404: 'not_found',
  409: 'conflict',
  413: 'too_long',
  422: 'invalid',
  429: 'rate_limited',
  502: 'upstream',
  503: 'unavailable',
};

/** Read the error code and request id from a failed response, whatever its body shape. */
export async function toAgentApiError(response: Response): Promise<AgentApiError> {
  let code: string | null = null;
  let ref: string | null = response.headers.get('X-Request-Id');
  let errors: string[] = [];
  try {
    const body: unknown = await response.json();
    if (body && typeof body === 'object') {
      const record = body as Record<string, unknown>;
      if (typeof record.detail === 'string') code = record.detail;
      if (typeof record.ref === 'string') ref = record.ref;
      errors = strings(record.errors).slice(0, MAX_BINDING_ERRORS);
    }
  } catch {
    /* not JSON: the status decides */
  }
  // FastAPI's own validation 422 carries a list in `detail`; the admin gate a
  // `message`. Neither is one of the BFF's codes.
  if (code === 'agent chat is not enabled') code = 'not_enabled';
  return new AgentApiError(
    response.status,
    code ?? FALLBACK_CODES[response.status] ?? `http_${response.status}`,
    ref,
    errors
  );
}

/** The BFF passes at most this many binding check lines. */
const MAX_BINDING_ERRORS = 20;

// ============================================================================
// Requests
// ============================================================================

export function agentUrl(path: string): string {
  return `${DEBUG_API_URL}/debug/agent${path}`;
}

/**
 * A raw BFF call with the CSRF header; throws `AgentApiError` on a non-2xx status.
 *
 * A request that gets no readable answer becomes code `unreachable`. In
 * production that is usually an expired Cloudflare Access session: the API
 * answers with a cross-origin redirect to the Access login, which `fetch`
 * cannot follow and reports as a `TypeError`, exactly like a dropped
 * connection. The page offers a reload, which lets Access sign the admin in
 * again (`reloadOnceForAccess`). Any answer clears that reload's one-shot guard.
 */
export async function agentFetch(path: string, token: string, init: RequestInit = {}) {
  let response: Response;
  try {
    response = await fetchWithAuth(agentUrl(path), token, {
      ...init,
      headers: { ...AGENT_CLIENT_HEADERS, ...((init.headers as Record<string, string>) || {}) },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new AgentApiError(0, 'unreachable');
  }
  clearAccessReloadGuard();
  if (!response.ok) throw await toAgentApiError(response);
  return response;
}

async function agentJson<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await agentFetch(path, token, init);
  return (await response.json()) as T;
}

const post = (body?: unknown): RequestInit => ({
  method: 'POST',
  ...(body === undefined ? {} : { body: JSON.stringify(body) }),
});

const sessionPath = (sid: string) => `/sessions/${encodeURIComponent(sid)}`;

export const agentApi = {
  status: (token: string) => agentJson<AgentStatus>('/status', token),
  eligibility: (token: string, spec: string, library: string, signal?: AbortSignal) =>
    agentJson<Eligibility>(
      `/eligibility?spec=${encodeURIComponent(spec)}&library=${encodeURIComponent(library)}`,
      token,
      { signal }
    ),
  openSession: (token: string, specId: string, library: string, locale: string) =>
    agentJson<SessionOpened>('/sessions', token, post({ spec_id: specId, library, locale })),
  switchLibrary: (token: string, sid: string, specId: string, library: string) =>
    agentJson<SessionOpened>(
      `${sessionPath(sid)}/library`,
      token,
      post({ spec_id: specId, library })
    ),
  /**
   * A stored dataset, or a transcription of free text to confirm first (`isTranscribed`).
   * `confirmed` marks the table the user accepted with `.use()`: the server then never
   * hands the text to its transcriber again (a one-column table would otherwise be read
   * again), while the parse, the pre-filter, the judge and the store run as usual.
   */
  uploadDataset: (token: string, sid: string, text: string, confirmed = false) =>
    agentJson<DatasetAnswer>(
      `${sessionPath(sid)}/dataset`,
      token,
      post(confirmed ? { text, confirmed: true } : { text })
    ),
  putBindings: (token: string, sid: string, bindings: Binding[]) =>
    agentJson<BindingsApplied>(`${sessionPath(sid)}/bindings`, token, {
      method: 'PUT',
      body: JSON.stringify(bindings),
    }),
  /** Step 1's end: the stored dataset and its current bindings fit (`422 no_dataset` without one). */
  confirmDataset: (token: string, sid: string) =>
    agentJson<DatasetConfirmed>(`${sessionPath(sid)}/dataset/confirm`, token, post()),
  /**
   * `.undo()`: the version before the assistant's last change to the data is the
   * current dataset again, unconfirmed; answered like a paste. `422
   * nothing_to_undo` at the paste, `409 run_active` while a turn or a render runs.
   */
  undoDataset: (token: string, sid: string) =>
    agentJson<DatasetParsed>(`${sessionPath(sid)}/dataset/undo`, token, post()),
  /** Opens the chat turn's SSE stream; the caller reads it with `readSseEvents`. */
  postMessage: (token: string, sid: string, body: TurnBody, signal: AbortSignal) =>
    agentFetch(`${sessionPath(sid)}/messages`, token, {
      ...post(body),
      headers: { Accept: 'text/event-stream' },
      signal,
    }),
  cancel: async (token: string, sid: string) => {
    await agentFetch(`${sessionPath(sid)}/cancel`, token, { method: 'POST' });
  },
  renderTheme: (token: string, sid: string, version: number, theme: Theme) =>
    agentJson<ThemeRendered>(
      `${sessionPath(sid)}/versions/${version}/render`,
      token,
      post({ theme })
    ),
  artifact: async (token: string, sid: string, name: ArtifactName, version: number) => {
    const response = await agentFetch(`${sessionPath(sid)}/artifacts/${name}?v=${version}`, token);
    return response.blob();
  },
  /** `keepalive` lets the purge outlive the page (`pagehide`); best effort either way. */
  deleteSession: async (token: string, sid: string, { keepalive = false } = {}) => {
    await agentFetch(sessionPath(sid), token, { method: 'DELETE', keepalive });
  },
};

// ============================================================================
// Stream protocol anyplot/1
// ============================================================================

export const PIPELINE_STEPS = [
  'adapting',
  'checking',
  'rendering',
  'reviewing',
  'repairing',
] as const;
export type PipelineStep = (typeof PIPELINE_STEPS)[number];

export const STREAM_ERROR_CODES = [
  'capacity',
  'deadline',
  'guard_unavailable',
  'upstream',
  'internal',
] as const;
export type StreamErrorCode = (typeof STREAM_ERROR_CODES)[number];

export type AgentEvent =
  | { type: 'ready'; runId: string | null }
  | { type: 'queued'; position: number; waiting: number }
  | { type: 'step'; step: PipelineStep; attempt: number | null }
  | { type: 'message'; text: string }
  | { type: 'plot'; result: PlotResult }
  | { type: 'refusal'; code: string; text: string }
  | { type: 'error'; code: StreamErrorCode; ref: string | null }
  | {
      type: 'done';
      llmCalls: number | null;
      tokens: number | null;
      /**
       * The session's bindings after the run (the root may have changed them);
       * `null` when the server sent none (a refused turn, a gone session).
       */
      bindings: Binding[] | null;
      /** The server's step state after the run; `null` when it sent none. */
      dataConfirmed: boolean | null;
      /**
       * The data version the turn made (the assistant's `prepare_data`), which
       * replaces the page's preview; `null` when the data did not change.
       */
      dataset: DatasetChanged | null;
    };

const isInt = (value: unknown): value is number =>
  typeof value === 'number' && Number.isInteger(value) && value >= 0;

/**
 * The binding list of a `done` sync, or `null`. The list replaces the page's
 * bindings as a whole, so one malformed entry drops the whole list rather
 * than leaving a partial set on screen.
 */
function bindingList(value: unknown): Binding[] | null {
  if (!Array.isArray(value)) return null;
  const list: Binding[] = [];
  for (const entry of value) {
    if (!entry || typeof entry !== 'object') return null;
    const { role, column } = entry as Record<string, unknown>;
    if (typeof role !== 'string' || (column !== null && typeof column !== 'string')) return null;
    list.push({ role, column });
  }
  return list;
}

const isRecord = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === 'object' && !Array.isArray(value);
/** A profile's `min` or `max`: a number, a string, or `null` for anything else. */
const scalar = (value: unknown): number | string | null =>
  typeof value === 'number' || typeof value === 'string' ? value : null;
const finite = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) ? value : null;
const isRow = (row: unknown): row is string[] =>
  Array.isArray(row) && row.every(cell => typeof cell === 'string');

/** One column of a `done` dataset's profile, its documented fields only; `null` without a name or a known type. */
function columnProfile(value: unknown): ColumnProfile | null {
  if (!isRecord(value) || typeof value.name !== 'string') return null;
  if (typeof value.dtype !== 'string' || !COLUMN_DTYPES.has(value.dtype)) return null;
  return {
    name: value.name,
    dtype: value.dtype as ColumnDtype,
    missing: isInt(value.missing) ? value.missing : 0,
    unique: isInt(value.unique) ? value.unique : 0,
    min: scalar(value.min),
    max: scalar(value.max),
    top: strings(value.top),
    mean: finite(value.mean),
    median: finite(value.median),
  };
}

function datasetProfile(value: unknown): DatasetProfile | null {
  if (!isRecord(value) || !isInt(value.rows) || !Array.isArray(value.columns)) return null;
  const columns: ColumnProfile[] = [];
  for (const entry of value.columns) {
    const column = columnProfile(entry);
    if (!column) return null;
    columns.push(column);
  }
  return {
    rows: value.rows,
    columns,
    source_format: typeof value.source_format === 'string' ? value.source_format : '',
    decimal: typeof value.decimal === 'string' ? value.decimal : '.',
    warnings: strings(value.warnings),
  };
}

/**
 * The data version of a `done` event, or `null`. It replaces the page's
 * preview, bindings and step as a whole, so anything malformed drops all of it
 * rather than putting a table on screen that is not the server's.
 */
function datasetChanged(value: unknown): DatasetChanged | null {
  if (!isRecord(value) || !isInt(value.version) || value.version < 1) return null;
  const profile = datasetProfile(value.profile);
  const bindings = bindingList(value.bindings);
  if (!profile || !bindings) return null;
  if (!Array.isArray(value.preview) || !value.preview.every(isRow)) return null;
  return {
    preview: value.preview,
    profile,
    bindings,
    warnings: strings(value.warnings),
    changes: strings(value.changes),
    version: value.version,
  };
}

const ARTIFACT_NAMES = new Set<string>(['plot-light.png', 'plot-dark.png', 'plot.py', 'data.csv']);
const PLOT_STATUSES = new Set<string>(['ok', 'needs_attention', 'failed', 'not_ready']);

/**
 * Type one `anyplot/1` event; `null` drops it.
 *
 * The BFF already re-validates every event, so this is the second fence: an
 * unknown type, data that is not a JSON object, or a field of the wrong type
 * never reaches the UI. Unknown error codes read as `internal`, as on the BFF.
 */
export function parseAgentEvent(raw: SseEvent): AgentEvent | null {
  let data: unknown;
  try {
    data = JSON.parse(raw.data);
  } catch {
    return null;
  }
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null;
  const d = data as Record<string, unknown>;
  switch (raw.event) {
    case 'ready':
      return { type: 'ready', runId: typeof d.run_id === 'string' ? d.run_id : null };
    case 'status':
      if (d.step === 'queued') {
        if (!isInt(d.position) || !isInt(d.waiting)) return null;
        return { type: 'queued', position: d.position, waiting: d.waiting };
      }
      if (!PIPELINE_STEPS.includes(d.step as PipelineStep)) return null;
      return {
        type: 'step',
        step: d.step as PipelineStep,
        attempt: isInt(d.attempt) ? d.attempt : null,
      };
    case 'message':
      return typeof d.text === 'string' ? { type: 'message', text: d.text } : null;
    case 'plot':
      if (typeof d.status !== 'string' || !PLOT_STATUSES.has(d.status)) return null;
      return {
        type: 'plot',
        result: {
          status: d.status as PlotStatus,
          reason: typeof d.reason === 'string' ? d.reason : null,
          attempts: isInt(d.attempts) ? d.attempts : 0,
          artifacts: strings(d.artifacts).filter((name): name is ArtifactName =>
            ARTIFACT_NAMES.has(name)
          ),
          changes: strings(d.changes),
          residual_defects: strings(d.residual_defects),
          version: isInt(d.version) && d.version >= 1 ? d.version : null,
        },
      };
    case 'refusal':
      return {
        type: 'refusal',
        code: typeof d.code === 'string' ? d.code : 'out_of_scope',
        text: typeof d.text === 'string' ? d.text : '',
      };
    case 'error':
      return {
        type: 'error',
        code: STREAM_ERROR_CODES.includes(d.code as StreamErrorCode)
          ? (d.code as StreamErrorCode)
          : 'internal',
        ref: typeof d.ref === 'string' ? d.ref : null,
      };
    case 'done':
      return {
        type: 'done',
        llmCalls: isInt(d.llm_calls) ? d.llm_calls : null,
        tokens: isInt(d.tokens) ? d.tokens : null,
        bindings: bindingList(d.bindings),
        dataConfirmed: typeof d.data_confirmed === 'boolean' ? d.data_confirmed : null,
        dataset: datasetChanged(d.dataset),
      };
    default:
      return null;
  }
}

/** The theme a version rendered: the PNG among its artifacts (light wins a tie). */
export function renderedThemes(artifacts: readonly string[]): Theme[] {
  return (['light', 'dark'] as const).filter(theme => artifacts.includes(PNG_ARTIFACT[theme]));
}

/** A BCP 47 tag the BFF accepts (`^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$`, at most 16 chars). */
export function browserLocale(): string {
  const candidate = typeof navigator !== 'undefined' ? navigator.language : '';
  return /^[A-Za-z]{2,3}([_-][A-Za-z0-9]{1,8}){0,3}$/.test(candidate) && candidate.length <= 16
    ? candidate
    : 'en';
}

/** Low-cardinality size bucket for analytics; never the size itself. */
export function sizeBucket(bytes: number): string {
  if (bytes < 1024) return 'lt_1kb';
  if (bytes < 10 * 1024) return '1_10kb';
  if (bytes < 50 * 1024) return '10_50kb';
  if (bytes <= MAX_DATASET_BYTES) return '50_200kb';
  return 'over_200kb';
}

/** Low-cardinality count bucket for analytics (`1`, `2`, `3+`); below 1 reads as `1`. */
export function countBucket(count: number): '1' | '2' | '3+' {
  if (count <= 1) return '1';
  return count === 2 ? '2' : '3+';
}

export function utf8Bytes(text: string): number {
  return new TextEncoder().encode(text).length;
}
