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
/** The BFF's limit on pasted data: 1 MB of UTF-8 (200 KB before 2026-10-14). */
export const MAX_DATASET_BYTES = 1024 * 1024;
/** The BFF's limit on one chat message. */
export const MAX_MESSAGE_CHARS = 2000;
/**
 * A session language: a short language name or code in Latin letters (`de`,
 * `English`, `Swedish`), as the agents service and the BFF define it
 * (`agents/anyplot/language.py`, `LANGUAGE_PATTERN`). The server matches the
 * value as sent, so the page trims before it tests and sends.
 */
export const LANGUAGE_PATTERN = /^[A-Za-z][A-Za-z -]{0,39}$/;
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
 * How the session language was set: `default` (nobody yet, English), `pasted`
 * (the notes or the column names of a paste before any typed message),
 * `detected` (the session's first typed message), `chosen` (the header's chip
 * or a request in the chat). Only `chosen` is final.
 */
export type LanguageSource = 'default' | 'pasted' | 'detected' | 'chosen';

/**
 * The session language: the assistant's replies and every text in the plot.
 * Named `plotLanguage` in the page, because `language` there is the
 * programming language of the code (`?language=python`).
 */
export interface PlotLanguage {
  /** The server's stored form: a known name as its code (`English` is `en`), anything else as typed. */
  language: string;
  source: LanguageSource;
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
  /** The role needs values of 0 or more (the server's `data/signs.py`); absent from an older server. */
  non_negative?: boolean;
  /**
   * The plot computes the role when no column is bound (the server's `data/computed.py`): a
   * rolling average, a Bollinger band. Optional; absent from an older server.
   */
  computed?: boolean;
}

/**
 * The service's wide-table offer (`agents/anyplot/data/shape.py`): the table holds
 * the same quantity side by side (`columns`) where the spec wants one category and
 * one value column. `.to_long()` turns `columns` into `names_to` and `values_to`
 * (`keys`, date columns, stay), `rows` long.
 */
export interface LongSuggestion {
  kind: 'to_long';
  columns: string[];
  names_to: string;
  values_to: string;
  keys: string[];
  rows: number;
}

export interface DatasetParsed {
  /** Up to 20 data rows (the header is `profile.columns[].name`). */
  preview: string[][];
  profile: DatasetProfile;
  /** The server's default bindings; roles it could not match are absent. */
  bindings: Binding[];
  warnings: string[];
  /**
   * The notes the user pasted above or below the table (a title, a source
   * line, a sentence about the columns), one line each, that the server kept
   * for the assistant after its checks; absent from an older server.
   */
  context_lines?: string[];
  /**
   * The name of the file the data was dropped from, as the server screened it
   * (`(name withheld)` when it refused it); absent for pasted or computed data.
   * Never a note: the assistant reads it as data, never as a request.
   */
  file_name?: string;
  /** Every role of the spec; absent from an agents service older than this field. */
  roles?: RoleSpec[];
  /**
   * The Python that computed this version (the assistant's `run_data_code`, as it
   * ran in the sandbox); absent for a paste and every other version.
   */
  code?: string;
  /** The wide-table offer, or `null`; absent from an older server. */
  suggestion?: LongSuggestion | null;
  /**
   * The data's version: a paste is 1, each change the assistant made to it one
   * more, each undo one less. `.undo()` is possible while it is above 1.
   */
  version: number;
  /**
   * The paste's answer only: the session language after it, which a paste
   * before any typed message or choice sets from the language of its notes or
   * column names (`pasted`). Read it through `plotLanguage`; absent from an
   * older server.
   */
  language?: unknown;
}

/**
 * A data version the assistant made in step 1 (`done.dataset`): its
 * `prepare_data` changed the data, its `generate_data` computed a table from
 * a formula, or its `run_data_code` ran the user's code. The dataset route's
 * shape plus one English line per operation. The data is unconfirmed again.
 */
export interface DatasetChanged {
  /** Up to 20 data rows (the header is `profile.columns[].name`). */
  preview: string[][];
  profile: DatasetProfile;
  /** The bindings carried over to the new version, or a generated table's defaults. */
  bindings: Binding[];
  warnings: string[];
  /** The notes pasted with the data, carried over to every version made from it. */
  context_lines?: string[];
  /** The dropped file's name, carried over like the notes. */
  file_name?: string;
  /**
   * Every role of the spec, at most `MAX_DONE_ROLES`; absent from an agents
   * service older than this field, and dropped whole when one entry is malformed.
   */
  roles?: RoleSpec[];
  /** The Python that computed the version (`run_data_code`); absent for every other change. */
  code?: string;
  /** The wide-table offer for the new version, or `null`; absent from an older server. */
  suggestion?: LongSuggestion | null;
  /**
   * What changed, one line per operation, such as `dropped 1 row where Tier =
   * 'Gesamt'` or `generated 200 rows: x from -3.1416 to 3.1416, y = sin(x)`.
   */
  changes: string[];
  /**
   * The next version after a change (2 or more), or 1 when `generate_data`
   * made the session's first data, which has nothing to undo.
   */
  version: number;
}

/** The spec roles a `done` event's `dataset` lists at most (the service's `MAX_DONE_ROLES`). */
export const MAX_DONE_ROLES = 50;

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
  /** Roles that need values of 0 or more and got negative ones; never a refusal. Absent from an older server. */
  warnings?: string[];
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

/** How one pipeline round (an attempt) ended; `RoundOutcome` in `agents/anyplot/schemas.py`. */
export const ROUND_OUTCOMES = [
  'ok',
  'review',
  'measured',
  'render_failed',
  'check_failed',
  'answer_unusable',
  'unreviewed',
  'error',
] as const;
export type RoundOutcome = (typeof ROUND_OUTCOMES)[number];

export interface Round {
  attempt: number;
  outcome: RoundOutcome;
  /** The findings the round passed on: review lines, measured defects or check failures. */
  findings: number;
  /** The pipeline step the round ended in; absent from an older server. */
  step?: PipelineStep;
  /** The round whose render the result shipped; not always the last (a repair that failed its check). */
  shipped?: boolean;
}

export interface PlotResult {
  status: PlotStatus;
  reason?: string | null;
  attempts: number;
  artifacts: ArtifactName[];
  changes: string[];
  residual_defects: string[];
  /** The stored version's number (`ok` and `needs_attention`); `null` from an older server. */
  version: number | null;
  /** How each attempt ended, in order; absent from an older server or a saved session. */
  rounds?: Round[];
}

export interface ThemeRendered {
  status: 'ok' | 'needs_attention' | 'failed';
  reason?: string | null;
  artifacts: ArtifactName[];
}

/** The site feedback's reaction set (api/routers/feedback.py, `FEEDBACK_REACTIONS`). */
export const FEEDBACK_REACTIONS = ['thumbs_up', 'thumbs_down', 'bug', 'idea'] as const;
export type FeedbackReaction = (typeof FEEDBACK_REACTIONS)[number];
/** The BFF's limit on a feedback message, after the strip; the site feedback's own. */
export const MAX_FEEDBACK_CHARS = 500;

/** The body of `POST .../feedback`: quick feedback on one result version. */
export interface FeedbackBody {
  reaction: FeedbackReaction;
  /** `null` without a text. */
  message: string | null;
  /** Store the version's `data.csv` with the case. */
  include_data: boolean;
  /** The version's number, 1 to 999, or 0 for the chat itself (a session without a plot). */
  result_version: number;
  /** The case id of the earlier submission for this version, when this one is an edit of it. */
  replaces?: string;
}

/** A case's version as the triage shows it: `v2`, or `chat, no plot` for version 0. */
export function caseVersionLabel(resultVersion: number): string {
  return resultVersion === 0 ? 'chat, no plot' : `v${resultVersion}`;
}

/** The answer of `POST .../feedback`: the stored case and its file names. */
export interface FeedbackStored {
  case_id: string;
  stored: string[];
}

// The triage of the stored cases: the "agent cases" section of /debug
// (`GET|PATCH /debug/agent/cases...`). The `agent_feedback` row is the source of
// truth for status, tags, the expected outcome and the promotion; the bucket
// holds the files until its lifecycle rule deletes them.

/** The site feedback's statuses; `done` and `wont_solve` retire a case. */
export const CASE_STATUSES = ['new', 'in_progress', 'done', 'wont_solve'] as const;
export type CaseStatus = (typeof CASE_STATUSES)[number];
/** The outcome a promoted case carries into the regression harness. */
export type CaseExpected = 'accepted' | 'rejected';
export type CaseFileName =
  'plot-light.png' | 'plot-dark.png' | 'plot.py' | 'data.csv' | 'manifest.json';
/** A tag is a lowercase slug; a case has at most `MAX_TAGS`. */
export const TAG_PATTERN = /^[a-z0-9-]{1,40}$/;
export const MAX_TAGS = 10;

/** One `agent_feedback` row; timestamps are UTC ISO 8601 with `Z`. */
export interface AgentCase {
  id: string;
  created_at: string;
  reaction: FeedbackReaction;
  message: string | null;
  include_data: boolean;
  status: CaseStatus;
  tags: string[];
  spec_id: string | null;
  library_id: string | null;
  /** The session's UI locale (`de-CH`). */
  locale: string | null;
  result_version: number;
  /** The case an edit replaced, as sent; it supersedes that row only for the same session and version. */
  replaces: string | null;
  superseded_by: string | null;
  promoted_at: string | null;
  expected: CaseExpected | null;
  model: string | null;
  model_version: string | null;
  judge_model: string | null;
  prompt_hash: string | null;
  /** The agents service's outcome: `ok`, `needs_attention`, `failed`, `not_ready`. */
  pipeline_status: string | null;
  attempts: number | null;
  tokens: number | null;
  cost_estimate: number | null;
  /** The objects the case holds in the bucket. */
  files: string[];
  user_hash: string;
  session_hash: string;
  case_uri: string;
  manifest_schema: number;
  updated_at: string;
}

export interface AgentCasePage {
  items: AgentCase[];
  /** A further page exists: pass the last item's id as `before`. */
  has_more: boolean;
}

export interface TranscriptTurn {
  role: 'user' | 'assistant';
  text: string;
}

/**
 * One case: the row plus what its `manifest.json` adds. With `expired` the
 * lifecycle rule has deleted the files: every field read from the manifest is
 * `null` or empty, the row and `siblings` remain.
 */
export interface AgentCaseDetail extends AgentCase {
  expired: boolean;
  transcript: TranscriptTurn[] | null;
  /** The version's `plot.py` as exported. */
  code: string | null;
  /** Unified diff from the catalogue's implementation (at triage time) to `code`. */
  diff: string | null;
  catalogue_library_version: string | null;
  snapshot_library_version: string | null;
  residual_defects: string[];
  changes: string[];
  result_reason: string | null;
  /** The config stamp: provider, model, judge_model, location, versions, prompt_hashes. */
  config: Record<string, unknown> | null;
  bindings: { role: string; column: string }[];
  /** Other rows of the same session hash and result version, oldest first. */
  siblings: string[];
}

/** The list's filters; an unset key is left out of the query string. */
export interface CaseListQuery {
  reaction?: FeedbackReaction;
  /** A status, or `open` for `new` and `in_progress`. */
  status?: CaseStatus | 'open';
  spec?: string;
  library?: string;
  model_version?: string;
  tag?: string;
  /** Show the rows an edit superseded (hidden by default). */
  include_superseded?: boolean;
  /** The exclusive cursor: the last item's id of the page before. */
  before?: string;
  limit?: number;
}

/** A triage change; `tags` replaces the whole list, `promoted` sets or clears `promoted_at`. */
export interface CasePatch {
  status?: CaseStatus;
  tags?: string[];
  promoted?: boolean;
  expected?: CaseExpected;
}

/** The query string of a case list: only the keys that are set, `include_superseded` only when true. */
export function caseListQuery(query: CaseListQuery): string {
  const params = new URLSearchParams();
  const text = (key: string, value: string | undefined) => {
    if (value) params.set(key, value);
  };
  text('reaction', query.reaction);
  text('status', query.status);
  text('spec', query.spec);
  text('library', query.library);
  text('model_version', query.model_version);
  text('tag', query.tag);
  if (query.include_superseded) params.set('include_superseded', 'true');
  text('before', query.before);
  if (query.limit !== undefined) params.set('limit', String(query.limit));
  const qs = params.toString();
  return qs ? `?${qs}` : '';
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
  /**
   * The case a `502 row_missing` stored in the bucket although its table row is
   * missing, so the page can name it in the next edit's `replaces`; `null` otherwise.
   */
  readonly caseId: string | null;

  constructor(
    status: number,
    code: string,
    ref: string | null = null,
    errors: string[] = [],
    caseId: string | null = null
  ) {
    super(`agent request failed: ${status} ${code}`);
    this.name = 'AgentApiError';
    this.status = status;
    this.code = code;
    this.ref = ref;
    this.errors = errors;
    this.caseId = caseId;
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
  let caseId: string | null = null;
  try {
    const body: unknown = await response.json();
    if (body && typeof body === 'object') {
      const record = body as Record<string, unknown>;
      if (typeof record.detail === 'string') code = record.detail;
      if (typeof record.ref === 'string') ref = record.ref;
      errors = strings(record.errors).slice(0, MAX_BINDING_ERRORS);
      if (typeof record.case_id === 'string') caseId = record.case_id;
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
    errors,
    caseId
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

/**
 * The name the BFF gives a session bundle: `anyplot-session-<the session id's
 * first 8 characters>.json`, those reduced to `[A-Za-z0-9_-]`.
 */
export function bundleFilename(sid: string): string {
  const short = sid.slice(0, 8).replace(/[^A-Za-z0-9_-]/g, '');
  return `anyplot-session-${short || 'session'}.json`;
}

/** The quoted `filename` of an `attachment` disposition, when it is a plain `.json` name. */
export function attachmentFilename(header: string | null): string | null {
  const match = header?.match(/^attachment;\s*filename="([A-Za-z0-9_.-]{1,100})"$/);
  return match && match[1].endsWith('.json') ? match[1] : null;
}

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
   * again) and keeps every row of it (no lines left out as notes or totals), while the
   * pre-filter, the judge and the store run as usual.
   * Text that asks for a formula (`sin(x) von -pi bis pi`) answers `422 formula` and
   * stores nothing: the chat's `generate_data` computes such a table. Code that
   * generates data (Python, JavaScript, R) answers `422 code` the same way: the
   * chat's `run_data_code` runs it.
   * `source` is the name of the file the text was read from (a drop, `.open()`,
   * a pasted file): it travels beside the text, which stays as in the file; the
   * server screens it and answers it as `file_name`, never as a note.
   */
  uploadDataset: (token: string, sid: string, text: string, confirmed = false, source?: string) =>
    agentJson<DatasetAnswer>(
      `${sessionPath(sid)}/dataset`,
      token,
      post({
        text,
        ...(confirmed ? { confirmed: true } : {}),
        ...(source ? { source } : {}),
      })
    ),
  putBindings: (token: string, sid: string, bindings: Binding[]) =>
    agentJson<BindingsApplied>(`${sessionPath(sid)}/bindings`, token, {
      method: 'PUT',
      body: JSON.stringify(bindings),
    }),
  /**
   * The chat header's chip: the session language with the source `chosen`, which
   * detection never overrides. Answers the stored form (`English` comes back as
   * `en`); an answer the page cannot read falls back to the value as sent.
   * `409 run_active` while a turn or a render runs, `422 invalid` for a value
   * outside `LANGUAGE_PATTERN`.
   */
  setLanguage: async (token: string, sid: string, language: string): Promise<PlotLanguage> => {
    const answer = await agentJson<unknown>(`${sessionPath(sid)}/language`, token, {
      method: 'PUT',
      body: JSON.stringify({ language }),
    });
    return plotLanguage(answer) ?? { language, source: 'chosen' };
  },
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

  /**
   * `.to_long()`: the service applies its own wide-table suggestion, without a
   * model call, as the next data version (the undo route's shape plus
   * `changes`). `422 no_suggestion` when the table is not wide for this spec.
   */
  datasetToLong: async (token: string, sid: string): Promise<DatasetChanged> => {
    const body = await agentJson<unknown>(`${sessionPath(sid)}/dataset/to_long`, token, post());
    // Typed like a `done` dataset: a malformed answer puts no table on screen.
    const dataset = datasetChanged(body);
    if (!dataset) throw new AgentApiError(502, 'upstream');
    return dataset;
  },
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
  /**
   * `.save()`: the session's feedback case as a JSON file (`GET .../bundle`): the
   * conversation, every version's code, plan, result and PNGs, the data profile,
   * the bindings and the config stamp; each version's `data.csv` with
   * `includeData`. The file name is the BFF's (`Content-Disposition`), or the same
   * name built here where a cross-origin page cannot read that header (dev).
   */
  fetchBundle: async (token: string, sid: string, includeData: boolean) => {
    const response = await agentFetch(
      `${sessionPath(sid)}/bundle?include_data=${includeData ? 'true' : 'false'}`,
      token
    );
    const filename =
      attachmentFilename(response.headers.get('Content-Disposition')) ?? bundleFilename(sid);
    return { blob: await response.blob(), filename };
  },
  /**
   * Quick feedback on a result version (`POST .../feedback`): the BFF stores the
   * version's case (conversation, code, PNGs, config, `data.csv` with
   * `include_data`) in the private case bucket, indexes it in the triage table
   * and answers `201 {case_id, stored}`. A later call for the same version
   * stores a new case, which names the earlier one in `replaces`. `502 storage`
   * when the bucket refused the case; `502 row_missing` with the stored
   * `case_id` (`AgentApiError.caseId`) when the files are stored but the row is
   * not; upstream errors as for `.save()`.
   */
  sendFeedback: (token: string, sid: string, body: FeedbackBody) =>
    agentJson<FeedbackStored>(`${sessionPath(sid)}/feedback`, token, post(body)),
  /**
   * The feedback cases, newest first (`GET /cases`). An answer without an
   * `items` list reads as an empty page.
   */
  listCases: async (token: string, query: CaseListQuery): Promise<AgentCasePage> => {
    const page = await agentJson<Partial<AgentCasePage> | null>(
      `/cases${caseListQuery(query)}`,
      token
    );
    return {
      items: Array.isArray(page?.items) ? page.items : [],
      has_more: page?.has_more === true,
    };
  },
  /** One case with what its manifest adds (`404 not_found` without a row, `502 storage`). */
  getCase: (token: string, id: string) =>
    agentJson<AgentCaseDetail>(`/cases/${encodeURIComponent(id)}`, token),
  /** One file of a case through the BFF's proxy; the bucket is private. */
  caseFile: async (token: string, id: string, name: CaseFileName) => {
    const response = await agentFetch(`/cases/${encodeURIComponent(id)}/files/${name}`, token);
    return response.blob();
  },
  /**
   * Change a case's triage state; answers the whole row. `422 no_data` promotes
   * a case without its `data.csv`, `422 expected_required` a bug or idea
   * without an expected outcome.
   */
  patchCase: (token: string, id: string, patch: CasePatch) =>
    agentJson<AgentCase>(`/cases/${encodeURIComponent(id)}`, token, {
      method: 'PATCH',
      body: JSON.stringify(patch),
    }),
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
  | {
      type: 'step';
      step: PipelineStep;
      attempt: number | null;
      /** On `repairing`: how the round before it ended. */
      previous: Round | null;
    }
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
       * The data version the turn made (the assistant's `prepare_data` or
       * `generate_data`), which replaces the page's preview or is its first
       * data; `null` when the data did not change.
       */
      dataset: DatasetChanged | null;
      /**
       * The session language after the run (the first typed message or the
       * assistant's `set_language` may have set it); `null` when the server sent
       * none (a refused turn, a gone session, an older server).
       */
      language: PlotLanguage | null;
    };

const isInt = (value: unknown): value is number =>
  typeof value === 'number' && Number.isInteger(value) && value >= 0;

/** One round from the stream, or `null` when its attempt, outcome or count is not one the server sends. */
function toRound(value: unknown): Round | null {
  if (!value || typeof value !== 'object') return null;
  const { attempt, outcome, findings, step, shipped } = value as Record<string, unknown>;
  if (!isInt(attempt) || attempt < 1 || !isInt(findings)) return null;
  if (!ROUND_OUTCOMES.includes(outcome as RoundOutcome)) return null;
  // Absent stays absent (an older server); a value of the wrong kind refuses the round.
  if (shipped !== undefined && typeof shipped !== 'boolean') return null;
  if (step !== undefined && step !== null && !PIPELINE_STEPS.includes(step as PipelineStep)) {
    return null;
  }
  const round: Round = { attempt, outcome: outcome as RoundOutcome, findings };
  if (typeof step === 'string') round.step = step as PipelineStep;
  if (shipped !== undefined) round.shipped = shipped;
  return round;
}

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

const LANGUAGE_SOURCES = new Set<string>(['default', 'pasted', 'detected', 'chosen']);

/**
 * The session language of a `done` event, the dataset route's or the language
 * route's answer, or `null`: an object whose `language` matches
 * `LANGUAGE_PATTERN` and whose `source` is one of the four. The chip shows it
 * as it comes, so anything else is dropped whole.
 */
export function plotLanguage(value: unknown): PlotLanguage | null {
  if (!isRecord(value)) return null;
  const { language, source } = value;
  if (typeof language !== 'string' || !LANGUAGE_PATTERN.test(language)) return null;
  if (typeof source !== 'string' || !LANGUAGE_SOURCES.has(source)) return null;
  return { language, source: source as LanguageSource };
}
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
 * The spec roles of a `done` dataset, at most `MAX_DONE_ROLES`, or `undefined`
 * when the field is absent or any entry lacks a name: the page then keeps the
 * roles it has, as against an older server.
 */
function roleList(value: unknown): RoleSpec[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const roles: RoleSpec[] = [];
  for (const entry of value.slice(0, MAX_DONE_ROLES)) {
    if (!isRecord(entry) || typeof entry.name !== 'string' || !entry.name) return undefined;
    roles.push({
      name: entry.name,
      kinds: strings(entry.kinds),
      required: entry.required === true,
      variadic: entry.variadic === true,
      description: typeof entry.description === 'string' ? entry.description : '',
      non_negative: entry.non_negative === true,
      computed: entry.computed === true,
    });
  }
  return roles;
}

/**
 * The data version of a `done` event, or `null`. It replaces the page's
 * preview, bindings and step as a whole, so anything malformed drops all of it
 * rather than putting a table on screen that is not the server's. Version 1 is
 * a generated first dataset (`generate_data` in a session without data).
 */
function datasetChanged(value: unknown): DatasetChanged | null {
  if (!isRecord(value) || !isInt(value.version) || value.version < 1) return null;
  const profile = datasetProfile(value.profile);
  const bindings = bindingList(value.bindings);
  if (!profile || !bindings) return null;
  if (!Array.isArray(value.preview) || !value.preview.every(isRow)) return null;
  const roles = roleList(value.roles);
  return {
    preview: value.preview,
    profile,
    bindings,
    warnings: strings(value.warnings),
    context_lines: strings(value.context_lines),
    ...(typeof value.file_name === 'string' && value.file_name
      ? { file_name: value.file_name }
      : {}),
    ...(roles ? { roles } : {}),
    ...(typeof value.code === 'string' && value.code ? { code: value.code } : {}),
    suggestion: longSuggestion(value.suggestion),
    changes: strings(value.changes),
    version: value.version,
  };
}

/** A wide-table offer as the service sends it, or `null` for anything else. */
export function longSuggestion(value: unknown): LongSuggestion | null {
  if (!isRecord(value) || value.kind !== 'to_long') return null;
  const columns = strings(value.columns);
  if (columns.length < 2 || typeof value.names_to !== 'string' || !value.names_to) return null;
  if (typeof value.values_to !== 'string' || !value.values_to || !isInt(value.rows)) return null;
  return {
    kind: 'to_long',
    columns,
    names_to: value.names_to,
    values_to: value.values_to,
    keys: strings(value.keys),
    rows: value.rows,
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
        previous:
          isInt(d.attempt) && d.attempt > 1
            ? toRound({ attempt: d.attempt - 1, outcome: d.outcome, findings: d.findings })
            : null,
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
          rounds: Array.isArray(d.rounds)
            ? d.rounds.map(toRound).filter((round): round is Round => round !== null)
            : [],
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
        language: plotLanguage(d.language),
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
  if (bytes <= 200 * 1024) return '50_200kb';
  if (bytes <= MAX_DATASET_BYTES) return '200kb_1mb';
  return 'over_1mb';
}

/** Low-cardinality count bucket for analytics (`1`, `2`, `3+`); below 1 reads as `1`. */
export function countBucket(count: number): '1' | '2' | '3+' {
  if (count <= 1) return '1';
  return count === 2 ? '2' : '3+';
}

export function utf8Bytes(text: string): number {
  return new TextEncoder().encode(text).length;
}
