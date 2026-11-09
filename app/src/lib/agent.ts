/**
 * Client for the agent chat BFF: the admin lane (`/debug/agent/*`,
 * api/routers/agent.py) and the public lane (`/agent/*`,
 * api/routers/agent_public.py), which take the same requests.
 *
 * The contract is documented in docs/reference/api.md ("Agent chat"); the
 * design in docs/concepts/agent-network.md. On the admin lane every call goes
 * through `fetchWithAuth` (Cloudflare Access cookie or the admin token)
 * against the debug API base; on the public lane it goes to the API base
 * without a cookie, with the tab's anonymous id and the session id as headers
 * (`PUBLIC_LANE`, `publicRoute`). Every state-changing call carries the CSRF
 * header `X-Anyplot-Client: agent-chat/1`. Errors arrive as
 * `{"detail": "<code>", "ref": "<request id>"}` and become `AgentApiError`.
 */

import { API_URL, DEBUG_API_URL, LIBRARIES } from 'src/constants';
import { fetchWithAuth } from 'src/lib/api';
import type { SseEvent } from 'src/lib/sse';
import {
  type TurnstileAction,
  TurnstileError,
  turnstileHeaders,
  turnstileSiteKey,
} from 'src/lib/turnstile';

export const AGENT_CLIENT_HEADERS = { 'X-Anyplot-Client': 'agent-chat/1' } as const;
/** The BFF's limit on pasted data: 1 MB of UTF-8. */
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
/** The exported code's download name: its language's (`plot.py` for Python, `plot.R`, `plot.jl`, `plot.js`, `plot.tsx`). */
export type CodeArtifact = 'plot.py' | 'plot.R' | 'plot.jl' | 'plot.js' | 'plot.tsx';
/**
 * A JavaScript plot's self-contained interactive page: built by the server on
 * demand in the theme asked for, downloaded as it is, and shown in the card
 * through the preview relay (`PREVIEW_RELAY_URL`).
 */
export const PAGE_ARTIFACT = 'plot.html';
/**
 * The API's static relay page of the interactive preview (`api/preview_relay.py`,
 * JS-4b-2): the card frames it sandboxed and posts the version's `plot.html`
 * into it, which it shows in a sandboxed frame of its own. It sits outside
 * `/debug/*`, takes no token and reads no cookie. It follows `API_URL`, while
 * the chat's own requests follow `DEBUG_API_URL`.
 */
export const PREVIEW_RELAY_URL = `${API_URL}/preview/relay`;
/**
 * The relay's only message, a signal without content once it listens
 * (`READY_MESSAGE` in `api/preview_relay.py`, pinned by a test): the card posts
 * the page only on this signal from the relay frame's own window, so a page
 * that stands in at the relay's URL (an error page of the edge) never gets it.
 */
export const PREVIEW_RELAY_READY = 'anyplot-relay-ready';
/**
 * The wrapper's frame at scale 1, the first rule of this form in its style
 * (`sizing_css` in `agents/anyplot/render/page.py`, pinned by a test): the
 * canvas in CSS pixels, 1600x900 or 1200x1200.
 */
export const PAGE_FRAME_PATTERN = /\.frame \{ width: (\d+)px; height: (\d+)px; \}/;
/** The wrapper's margin around its frame (`MARGIN_PX` in `render/page.py`). */
export const PAGE_MARGIN_PX = 16;
/** The frame of a page without the rule: the landscape canvas, which the wrapper then scales to fit. */
export const PAGE_FRAME_FALLBACK = { width: 1600, height: 900 };

/**
 * The wrapper's own size at scale 1, read from the page itself so the card's
 * frame and the wrapper never disagree (a square plot whose PNG has not loaded
 * is still framed square): the frame and the margin around it, just past the
 * wrapper's first media query, so it shows the plot at scale 1 and the card
 * scales the whole relay frame to its width.
 */
export function pageFrameSize(page: string): { width: number; height: number } {
  const match = PAGE_FRAME_PATTERN.exec(page);
  const width = match ? Number(match[1]) : PAGE_FRAME_FALLBACK.width;
  const height = match ? Number(match[2]) : PAGE_FRAME_FALLBACK.height;
  return { width: width + 2 * PAGE_MARGIN_PX, height: height + 2 * PAGE_MARGIN_PX };
}
export type ArtifactName =
  'plot-light.png' | 'plot-dark.png' | CodeArtifact | typeof PAGE_ARTIFACT | 'data.csv';
export const PNG_ARTIFACT: Record<Theme, ArtifactName> = {
  light: 'plot-light.png',
  dark: 'plot-dark.png',
};
export const CODE_ARTIFACTS: readonly CodeArtifact[] = [
  'plot.py',
  'plot.R',
  'plot.jl',
  'plot.js',
  'plot.tsx',
];
/** The media type of a downloaded code file, by its name. */
export const CODE_MEDIA_TYPES: Record<CodeArtifact, string> = {
  'plot.py': 'text/x-python',
  'plot.R': 'text/plain',
  'plot.jl': 'text/plain',
  'plot.js': 'text/javascript',
  'plot.tsx': 'text/plain',
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
  /**
   * The caller's own cap of sandbox runs queued or running at once: `AGENT_USER_MAX_RUNS`, or
   * `AGENT_ADMIN_USER_MAX_RUNS` for an admin; absent from an older server.
   */
  user_max_runs?: number;
  /** The tier the agents service served the request as (`X-Anyplot-Tier`); absent from an older server. */
  tier?: 'admin' | 'public';
  /** The service's day budget is spent: every turn gets `service_paused` until `resets_at`. */
  paused?: boolean;
  /** The next 00:00 UTC, when the day budget starts again (ISO 8601). */
  resets_at?: string;
  enabled: boolean;
}

/** The day caps the agents service counts users at (`ledger.LIMIT_KINDS`). */
export const LIMIT_KINDS = [
  'tokens',
  'runs',
  'data_runs',
  'messages',
  'pastes',
  'conversions',
  'locked_out',
] as const;

/**
 * The answer of the admin lane's `GET /budget`, the agents service's usage book of the day:
 * counts and times only. The debug page's "today" line and the chat's admin meters read it.
 */
export interface AgentBudget {
  since: string;
  started_at: string;
  resets_at: string;
  paused: boolean;
  tokens: number;
  budget_tokens: number;
  usd: number | null;
  budget_usd: number | null;
  users: number;
  users_at_limit: number;
  limits: Record<string, number>;
}

const count = (value: unknown): number =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;

const amount = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;

const instant = (value: unknown): string | null =>
  typeof value === 'string' && !Number.isNaN(Date.parse(value)) ? value : null;

/** A record of counts under `keys`, 0 for a key it lacks or holds no count under. */
export const countsOf = (value: unknown, keys: readonly string[]): Record<string, number> => {
  const record = value && typeof value === 'object' ? (value as Record<string, unknown>) : {};
  return Object.fromEntries(keys.map(key => [key, count(record[key])]));
};

/** `/budget`'s answer as the page reads it; `null` for one without its times. */
export function readBudget(body: unknown): AgentBudget | null {
  if (!body || typeof body !== 'object') return null;
  const record = body as Record<string, unknown>;
  const since = instant(record.since);
  const started = instant(record.started_at);
  const resets = instant(record.resets_at);
  if (!since || !started || !resets) return null;
  return {
    since,
    started_at: started,
    resets_at: resets,
    paused: record.paused === true,
    tokens: count(record.tokens),
    budget_tokens: count(record.budget_tokens),
    usd: amount(record.usd),
    budget_usd: amount(record.budget_usd),
    users: count(record.users),
    users_at_limit: count(record.users_at_limit),
    limits: countsOf(record.limits, LIMIT_KINDS),
  };
}

/**
 * The share of the day budget spent, in whole percent: the weighted tokens against their budget,
 * which the service's day pause is measured on (`ledger.py`). `null` without a budget. The one
 * share both the debug page and the chat's admin meter show, so they never disagree.
 */
export function budgetShare(budget: AgentBudget): number | null {
  return budget.budget_tokens > 0 ? Math.round((budget.tokens / budget.budget_tokens) * 100) : null;
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

/**
 * `POST /sessions`'s answer: the session and the spec's roles, which the page header lists as the
 * columns the plot expects before any data. `roles` is `null` from a server without the field or
 * with a malformed one; the header then falls back to the spec's own `data` bullets.
 */
export interface SessionStarted extends SessionOpened {
  roles: RoleSpec[] | null;
}

/**
 * What a session adapts: a (spec, library) pair. Today only the library
 * switches (`POST .../library` refuses another spec with `422 invalid`); the
 * later plot-type switch changes the spec through the same pair.
 */
export interface PlotTarget {
  spec_id: string;
  library: string;
}

/**
 * The switch answer's `carry`: how much a plot in the new library would take
 * over, and whether the page should offer it (the `carry_plot` action).
 * `decisions` counts the plot memory's entries (or, with an empty memory, the
 * source plot's requests), `newer` the entries written after the new
 * library's own latest plot; `offer` is true when something carries and the
 * library has no plot yet or its plot misses newer decisions.
 */
export interface SwitchCarry {
  decisions: number;
  newer: number;
  target_has_plot: boolean;
  from_plot: boolean;
  offer: boolean;
}

/**
 * `POST .../library`'s answer. `target` and `carry` come from a server with the
 * plot memory; an older one answers neither, read as `null`:
 * no offer, the page behaves as before.
 */
export interface LibrarySwitched extends SessionOpened {
  target: PlotTarget | null;
  carry: SwitchCarry | null;
}

/** Where a decision of the plot memory applies: an axis, the colour, the series, the whole plot, or unnamed. */
export type MemoryTarget = 'x' | 'y' | 'color' | 'series' | 'plot';
const MEMORY_TARGETS = new Set<string>(['x', 'y', 'color', 'series', 'plot']);

/**
 * One decision the plot memory keeps (`agents/anyplot/memory.py`): `kind` is
 * one of the server's closed set (`axis_label`, `reference_line`, ...), `text`
 * the decision in plain words (at most 200 characters), `expect` the text it
 * puts in the plot verbatim, and `turn` the user turn it came in.
 */
export interface MemoryEntry {
  id: string;
  kind: string;
  target: MemoryTarget | null;
  text: string;
  expect: string | null;
  turn: number;
}

/** The plot memory as `GET .../memory` answers it, oldest first; the DELETE answers the same after the removal. */
export interface PlotMemory {
  entries: MemoryEntry[];
  max_entries: number;
  /**
   * The memory ever held a decision: from then on its entries alone (also
   * none) are what a plot in another library takes over, so the offer counts
   * them. `false` from a server that names none.
   */
  written: boolean;
}

/** An entry id as the BFF takes it in the DELETE path (`MEMORY_ENTRY_ID_PATTERN`). */
export const MEMORY_ENTRY_ID = /^m[0-9]{1,6}$/;

/**
 * The plot memory a stored version stands on, by entry id (`plot.memory`): `kept`, the decisions
 * from before the run that it kept, and `added`, the ones the run added, each in the memory's
 * order. A decision the run replaced is in neither list. The server settles them with the version,
 * so they hold also when the turn fails later. Ids are numbered once per session and never reused:
 * an id names one decision for the session's life.
 */
export interface VersionMemory {
  kept: string[];
  added: string[];
}

/**
 * What a turn changed (`done.turn`, the agents service's `stream.turn_outcome`, read from its own
 * record of the assistant's tool calls, never from the reply): the data or its bindings (`data`),
 * the plot pipeline ran, shipped or not (`plot`), the library (`switch`), the language the user
 * asked for (`language`), a wish kept for the first plot or a decision the memory read after the
 * turn found added (`kept`), a decision removed from the plot memory (`memory`), or nothing
 * (`answer`: the turn answered a question). A turn that changed several things names the first of
 * them in this order.
 */
export const TURN_OUTCOMES = [
  'data',
  'plot',
  'switch',
  'language',
  'kept',
  'memory',
  'answer',
] as const;
export type TurnOutcome = (typeof TURN_OUTCOMES)[number];
/** The service's cap of entries (`memory.MAX_ENTRIES`), for an answer that names none. */
const DEFAULT_MAX_MEMORY_ENTRIES = 30;
/** The service's cap of an entry's text (`memory.MAX_TEXT_CHARS`); a longer one is cut, never shown whole. */
const MAX_MEMORY_TEXT_CHARS = 200;

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
 * The language route's answer: the session language, and on a session with
 * data the `.to_long()` offer recomputed in it (`null` for none; absent
 * without data or from an older server).
 */
export interface LanguageAnswer extends PlotLanguage {
  suggestion?: LongSuggestion | null;
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
 * (`keys`, date columns or a matrix's row labels, stay), `rows` long.
 */
export interface LongSuggestion {
  kind: 'to_long';
  columns: string[];
  names_to: string;
  values_to: string;
  keys: string[];
  rows: number;
  /**
   * The columns a role that takes labels should not be bound to (the server's
   * `bindings.label_siblings`): `columns` without years or parts of a date. Empty
   * from an older server.
   */
  siblings: string[];
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
   * The paste's answer only, when the text held two or more tables, each under
   * its own header after a blank line: one label per table (its header names
   * and its row count). Read it through `tableChoice`.
   */
  tables?: unknown;
  /** The table read, 1-based, beside `tables`. */
  table?: unknown;
  /**
   * The version's number in the session, the `3` of `data v3`: the server numbers every
   * version it stores once (a paste, a pick, a change, `.to_long()`, a copy) and never gives
   * a number twice; an undo makes the version it restores current under its own number.
   * Whether `.undo()` can go is `can_undo`'s, never this number's.
   */
  version: number;
  /**
   * Whether `.undo()` has a version to restore (the server's history holds one); absent from
   * an older server, which the page reads as nothing to undo.
   */
  can_undo?: boolean;
  /**
   * The number of the current data's first version (its paste, file, copy or the table
   * computed without data), from which the page counts how far an undo went back; absent
   * from an older server.
   */
  original_version?: number;
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
  /** The version's number in the session (`DatasetParsed.version`). */
  version: number;
  /**
   * Whether `.undo()` has a version to restore: false when `generate_data` made the
   * session's first data; absent from an older server.
   */
  can_undo?: boolean;
  /** The number of the current data's first version (`DatasetParsed.original_version`). */
  original_version?: number;
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

/**
 * The answer of `POST .../dataset/copy`, the admin fan-out's copy of the page
 * session's confirmed data into a fan-out session: the dataset route's shape
 * (the session's first version), already bound and confirmed on the server.
 */
export interface DatasetCopied extends DatasetParsed {
  confirmed: true;
  /** Whether every required role has a column (the server's binding check). */
  complete: boolean;
  missing_roles: string[];
  /** The page session's data version the copy was taken from. */
  copied_from: number;
  /**
   * What the copy took over of the page session's tuned plot (its plot memory and a carry for this library):
   * with `offer`, the fan-out plots with `carry_plot` instead of `create_plot`. Absent from an older server.
   */
  carry?: SwitchCarry | null;
}

/** The tables of one paste the page may choose from (the service's `MAX_TABLES`). */
export const MAX_DATASET_TABLES = 10;

/**
 * The tables a paste held and the one read, or `null` for a paste of one
 * table, a data version the assistant made, or a malformed answer.
 */
export function tableChoice(
  parsed: DatasetParsed | DatasetChanged
): { tables: string[]; table: number } | null {
  if (!('tables' in parsed) || !Array.isArray(parsed.tables)) return null;
  const tables = parsed.tables.filter((label): label is string => typeof label === 'string');
  if (tables.length < 2 || tables.length !== parsed.tables.length) return null;
  const listed = tables.slice(0, MAX_DATASET_TABLES);
  const table = parsed.table;
  if (!isInt(table) || table < 1 || table > listed.length) return null;
  return { tables: listed, table };
}

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
  /** The rubric ids the round passed on to the repair (`VQ-05`), which the grid names in words. */
  defects?: string[];
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
  /**
   * The decisions the stored version kept and added (`VersionMemory`). Absent when the server
   * named none, for a plot without a stored version or from an older server: the version's memory
   * is unknown then, never empty. A session without memory sends two empty lists.
   */
  memory?: VersionMemory;
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

/**
 * What the user did with a result, for the content-free usage telemetry (`POST
 * .../outcome`, `api/routers/agent.py`): a closed set, never a name or a text.
 */
export const OUTCOME_ACTIONS = [
  'copied_code',
  'copied_image',
  'downloaded_png',
  'downloaded_code',
  // A JavaScript plot's interactive `plot.html` (since JS-4b).
  'downloaded_page',
  // The same page shown in the card (since JS-4b-2); a look, not a keep.
  'opened_preview',
  // The data panel's view of every row (`.view_all()`, version 0); a look at the data, not a keep.
  'opened_data_view',
  'downloaded_data',
  'saved_session',
  'feedback',
] as const;
export type OutcomeAction = (typeof OUTCOME_ACTIONS)[number];

/**
 * The body of `POST .../outcome`: the action, the result version it was on (0
 * for the session itself: `saved_session`, feedback on the chat) and, only with
 * `feedback`, the reaction. Nothing else ever travels.
 */
export type OutcomeBody =
  | { action: Exclude<OutcomeAction, 'feedback'>; version: number }
  | { action: 'feedback'; version: number; reaction: FeedbackReaction };

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

/** One pipeline round as a case keeps it: closed codes and counts only. */
export interface AgentCaseRound {
  attempt: number;
  /** The page's outcome name: `render_failed`, `measured`, `review`, `ok`, ... */
  outcome: string;
  findings: number;
  step: string | null;
  shipped: boolean;
  /** The rubric ids the round passed on (`VQ-05`). */
  defects: string[];
  /** The host gates any render of the round failed or reported on (`R1`, `R3`, `G8`). */
  gates_failed: string[];
  /** The closed class of each render that failed in the sandbox (`key`, `timeout`). */
  sandbox_failures: string[];
}

/** How the session's latest plot run ended when the case was sent. */
export interface AgentCaseLastRun {
  status: string;
  reason: string | null;
  /** The version the run stored; `null` for a run that stored none. */
  version: number | null;
  /** The session's user turn the run ran in. */
  turn: number | null;
  rounds: AgentCaseRound[];
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
  /** The rounds of the case's version; empty for the chat's case and older cases, absent from an older API. */
  rounds?: AgentCaseRound[];
  /** How many versions the session held; `null` for an older case, absent from an older API. */
  session_versions?: number | null;
  /** How the session's latest plot run ended; `null` before any run and for an older case. */
  last_run?: AgentCaseLastRun | null;
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
 * summary of the stored data, `example_data` for example data to try the plot
 * (`.example_data()`, before any data), `create_plot` starts step 2 (the fresh
 * plot from the catalogue code, also `.start_over()`), and `carry_plot` makes
 * the plot in the library the user switched to, with the plot memory's
 * decisions. None of them passes the scope judge, so none sets the session
 * language, which the first typed message does: `.example_data()` as typed
 * words would keep a German visitor in English.
 */
export type TurnAction = 'create_plot' | 'carry_plot' | 'summarize_data' | 'example_data';

/** Whether a turn of this kind is a plot run from the start: its path shows up front, it has no in-progress line. */
export const isPlotAction = (kind: string): boolean =>
  kind === 'create_plot' || kind === 'carry_plot';

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
  /** A refused file conversion's measured value and cap (`422 file_too_many_rows` and kin); null otherwise. */
  readonly measured: number | null;
  readonly limit: number | null;
  /**
   * What a refused paste fails on, in the agents service's words (`422 unparseable`,
   * `413 too_long`): "the header has 3 fields, but line 3 has 4"; null otherwise.
   */
  readonly cause: string | null;
  /** Which part of a damaged file is broken (`422 file_corrupt`): one of `CONVERT_DAMAGES`; null otherwise. */
  readonly damage: ConvertDamage | null;

  constructor(
    status: number,
    code: string,
    ref: string | null = null,
    errors: string[] = [],
    caseId: string | null = null,
    measure: { measured?: number | null; limit?: number | null } = {},
    cause: string | null = null,
    damage: ConvertDamage | null = null
  ) {
    super(`agent request failed: ${status} ${code}`);
    this.name = 'AgentApiError';
    this.status = status;
    this.code = code;
    this.ref = ref;
    this.errors = errors;
    this.caseId = caseId;
    this.measured = measure.measured ?? null;
    this.limit = measure.limit ?? null;
    this.cause = cause;
    this.damage = damage;
  }

  /** 401 and 403 from the admin gate: the browser is not (or no longer) signed in as an admin. */
  get unauthorized(): boolean {
    return this.status === 401 || (this.status === 403 && this.code === 'forbidden');
  }

  /**
   * The request id the page shows beside the error: only for a fault of the server or the
   * connection (a 5xx, or no answer), where a report needs it to find the request. A 4xx is a
   * refusal whose text names its cause (a column that does not fit, a paste the parser cannot
   * read, a limit), which the visitor acts on without quoting an id.
   */
  get shownRef(): string | null {
    return this.status === 0 || this.status >= 500 ? this.ref : null;
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
  const measure: { measured?: number; limit?: number } = {};
  let cause: string | null = null;
  let damage: ConvertDamage | null = null;
  try {
    const body: unknown = await response.json();
    if (body && typeof body === 'object') {
      const record = body as Record<string, unknown>;
      if (typeof record.detail === 'string') code = record.detail;
      if (typeof record.ref === 'string') ref = record.ref;
      errors = strings(record.errors).slice(0, MAX_BINDING_ERRORS);
      if (typeof record.case_id === 'string') caseId = record.case_id;
      if (isCount(record.measured)) measure.measured = record.measured;
      if (isCount(record.limit)) measure.limit = record.limit;
      if (typeof record.cause === 'string') {
        cause = record.cause.split(/\s+/).join(' ').trim().slice(0, MAX_CAUSE_CHARS) || null;
      }
      if ((CONVERT_DAMAGES as readonly unknown[]).includes(record.damage)) {
        damage = record.damage as ConvertDamage;
      }
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
    caseId,
    measure,
    cause,
    damage
  );
}

/** The longest cause the page shows, as the BFF caps it (`api/routers/agent.py` `_MAX_CAUSE_CHARS`). */
const MAX_CAUSE_CHARS = 300;

/** The broken part of a damaged file (`agents/renderer/wire.py` `ConvertDamage`, `api/routers/agent.py`). */
export const CONVERT_DAMAGES = [
  'zip',
  'workbook',
  'sheet',
  'parquet',
  'arrow',
  'npy_header',
  'npy_data',
] as const;
export type ConvertDamage = (typeof CONVERT_DAMAGES)[number];

function isCount(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0;
}

/** The raw file cap of a conversion: 5 MB, as the BFF and the agents service count it. */
export const MAX_CONVERT_BYTES = 5 * 1024 * 1024;

/** What the server counted while it read a file (`agents/renderer/wire.py` `ConvertWarning`). */
export interface ConvertWarnings {
  formulas_without_value?: number;
  hidden_sheets?: number;
  dropped_columns?: number;
  list_columns?: number;
  utc_timestamps?: number;
  renamed_columns?: number;
}

/** A converted file: the text for the box, what kind of file it was, the sheet read and the others. */
export interface ConvertAnswer {
  text: string;
  /** `json` for a table with list columns: records the parser expands into long format. */
  format: 'csv' | 'json';
  kind: string;
  rows: number;
  columns: number;
  sheet: string | null;
  sheets: string[];
  sheet_count: number;
  warnings: ConvertWarnings;
  /** The names of the columns left out (at most 20); `warnings.dropped_columns` counts all of them. */
  dropped: string[];
}

const WARNING_KEYS = [
  'formulas_without_value',
  'hidden_sheets',
  'dropped_columns',
  'list_columns',
  'utc_timestamps',
  'renamed_columns',
] as const;

/** The conversion route's answer, checked field by field; null when it is not that shape. */
export function convertAnswer(value: unknown): ConvertAnswer | null {
  if (!value || typeof value !== 'object') return null;
  const record = value as Record<string, unknown>;
  if (typeof record.text !== 'string' || typeof record.kind !== 'string') return null;
  const warnings: ConvertWarnings = {};
  const raw = record.warnings;
  if (raw && typeof raw === 'object') {
    for (const key of WARNING_KEYS) {
      const count = (raw as Record<string, unknown>)[key];
      if (isCount(count) && count > 0) warnings[key] = count;
    }
  }
  return {
    text: record.text,
    format: record.format === 'json' ? 'json' : 'csv',
    kind: record.kind,
    rows: isCount(record.rows) ? record.rows : 0,
    columns: isCount(record.columns) ? record.columns : 0,
    sheet: typeof record.sheet === 'string' ? record.sheet : null,
    sheets: strings(record.sheets).slice(0, 10),
    sheet_count: isCount(record.sheet_count) ? record.sheet_count : 0,
    warnings,
    dropped: strings(record.dropped).slice(0, 20),
  };
}

/** Base64 of a file's bytes, in chunks, so a 5 MB file never builds one huge argument list. */
export function toBase64(bytes: Uint8Array): string {
  let binary = '';
  const chunk = 0x8000;
  for (let index = 0; index < bytes.length; index += chunk) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunk));
  }
  return btoa(binary);
}

/** The BFF passes at most this many binding check lines. */
const MAX_BINDING_ERRORS = 20;

// ============================================================================
// Requests
// ============================================================================

/**
 * Which BFF the chat talks to: the admin lane (`/debug/agent/*` behind the
 * admin gate, `api/routers/agent.py`) or the public lane (`/agent/*`,
 * anonymous, `api/routers/agent_public.py`). The two take the same requests;
 * the public one takes the session id in the `X-Anyplot-Session` header
 * instead of the path, and the page's tab id in `X-Anyplot-Anon`.
 */
export type AgentLane = 'admin' | 'public';

/**
 * The credential of the public lane, passed where an admin passes the admin
 * token (`agentApi.*(token, ...)`): a call with it goes to `/agent/*` without a
 * cookie, with the tab's anonymous id. It holds a NUL character, which no
 * header can carry, so no admin token is ever mistaken for it and it is never
 * sent anywhere itself.
 */
export const PUBLIC_LANE = '\u0000public';

/** The lane a credential calls: the public one for `PUBLIC_LANE`, else the admin one. */
export function laneOf(token: string): AgentLane {
  return token === PUBLIC_LANE ? 'public' : 'admin';
}

/** sessionStorage key of the public lane's tab id. */
export const ANONYMOUS_ID_KEY = 'anyplot.agentTab';
let fallbackAnonymousId: string | null = null;

function randomId(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes, byte => byte.toString(16).padStart(2, '0')).join('');
}

/**
 * The public lane's anonymous id: random, one per browser tab
 * (sessionStorage), sent only to the public BFF as `X-Anyplot-Anon`. The
 * agents service salts it with a per-process salt before it keys the
 * per-user limits on it, so it ties nothing to a person. Where storage is
 * unavailable it lives as long as the page.
 */
export function anonymousId(): string {
  try {
    const stored = sessionStorage.getItem(ANONYMOUS_ID_KEY);
    if (stored && /^[A-Za-z0-9_-]{22,64}$/.test(stored)) return stored;
    const fresh = randomId();
    sessionStorage.setItem(ANONYMOUS_ID_KEY, fresh);
    return fresh;
  } catch {
    fallbackAnonymousId ??= randomId();
    return fallbackAnonymousId;
  }
}

const SESSION_ROUTE = /^\/sessions\/([^/?]+)(.*)$/;

/**
 * A request path of the admin lane as the public lane takes it: the session
 * id leaves the path for the `X-Anyplot-Session` header (Cloud Run logs every
 * URL with the client's address), so `/sessions/<sid>/dataset` becomes
 * `/session/dataset`. Paths without a session stay as they are.
 */
export function publicRoute(path: string): { path: string; session: string | null } {
  const match = SESSION_ROUTE.exec(path);
  if (!match) return { path, session: null };
  return { path: `/session${match[2]}`, session: decodeURIComponent(match[1]) };
}

export function agentUrl(path: string, lane: AgentLane = 'admin'): string {
  if (lane === 'public') return `${API_URL}/agent${publicRoute(path).path}`;
  return `${DEBUG_API_URL}/debug/agent${path}`;
}

/** The public lane's request: no cookie and no admin token, the tab id and the session id as headers. */
function publicFetch(path: string, init: RequestInit): Promise<Response> {
  const route = publicRoute(path);
  const headers: Record<string, string> = {
    ...AGENT_CLIENT_HEADERS,
    'X-Anyplot-Anon': anonymousId(),
    ...(route.session ? { 'X-Anyplot-Session': route.session } : {}),
    ...((init.headers as Record<string, string>) || {}),
  };
  if (init.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  return fetch(agentUrl(path, 'public'), { ...init, credentials: 'omit', headers });
}

/**
 * A raw BFF call with the CSRF header; throws `AgentApiError` on a non-2xx status.
 * `token` is the admin token, or `PUBLIC_LANE` for the public lane (`laneOf`).
 *
 * A request that gets no readable answer becomes code `unreachable`. On the
 * admin lane in production that is usually an expired Cloudflare Access
 * session: the API answers with a cross-origin redirect to the Access login,
 * which `fetch` cannot follow and reports as a `TypeError`, exactly like a
 * dropped connection. The chat page is not behind Access, so it cannot sign
 * the admin in again itself: its admin check falls back to the public lane
 * and links to `/debug` (`useAgentAdmin`).
 */
export async function agentFetch(path: string, token: string, init: RequestInit = {}) {
  const lane = laneOf(token);
  let response: Response;
  try {
    response =
      lane === 'public'
        ? await publicFetch(path, init)
        : await fetchWithAuth(agentUrl(path, 'admin'), token, {
            ...init,
            headers: {
              ...AGENT_CLIENT_HEADERS,
              ...((init.headers as Record<string, string>) || {}),
            },
          });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new AgentApiError(0, 'unreachable');
  }
  if (!response.ok) throw await toAgentApiError(response);
  return response;
}

/**
 * Whether the public lane is open (`GET /agent/lane`): one plain request with
 * no identity, which the API lets browsers cache for a minute. Any failure
 * reads as closed.
 */
export async function publicLaneOpen(signal?: AbortSignal): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/agent/lane`, { credentials: 'omit', signal });
    if (!response.ok) return false;
    const body: unknown = await response.json();
    return isRecord(body) && body.open === true;
  } catch {
    return false;
  }
}

async function agentJson<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await agentFetch(path, token, init);
  return (await response.json()) as T;
}

/**
 * Run a call that opens or stores something with the bot check's header on the
 * public lane (`src/lib/turnstile.ts`). The admin lane, and a build without a
 * site key, have no check: the call starts at once, as before. A check that
 * fails in the browser is the same `bot_check_failed` or `bot_check_unavailable`
 * the API answers, so the page has one message for both.
 */
function withHumanCheck<T>(
  token: string,
  action: TurnstileAction,
  call: (headers: Record<string, string>) => Promise<T>
): Promise<T> {
  if (laneOf(token) !== 'public' || !turnstileSiteKey()) return call({});
  return turnstileHeaders(action).then(call, (err: unknown) => {
    throw new AgentApiError(0, err instanceof TurnstileError ? err.code : 'bot_check_failed');
  });
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
  /**
   * The day's usage book (`GET /budget`), the admin meters' share; the admin lane only, since the
   * public lane has no such route: a call with `PUBLIC_LANE` rejects without a request. An answer
   * without its times rejects too.
   */
  budget: async (token: string): Promise<AgentBudget> => {
    if (laneOf(token) === 'public') throw new AgentApiError(404, 'not_found');
    const budget = readBudget(await agentJson<unknown>('/budget', token));
    if (!budget) throw new AgentApiError(502, 'upstream');
    return budget;
  },
  eligibility: (token: string, spec: string, library: string, signal?: AbortSignal) =>
    agentJson<Eligibility>(
      `/eligibility?spec=${encodeURIComponent(spec)}&library=${encodeURIComponent(library)}`,
      token,
      { signal }
    ),
  /**
   * `fanout` marks a session the admin's `.plot_all()` opens: the server files
   * its usage telemetry under the source `fanout` instead of `live`. Sent only
   * when set. On the public lane the call carries a fresh Turnstile token.
   */
  openSession: (
    token: string,
    specId: string,
    library: string,
    locale: string,
    fanout = false
  ): Promise<SessionStarted> =>
    withHumanCheck(token, 'agent_session', async headers => {
      const answer = await agentJson<SessionOpened & Record<string, unknown>>('/sessions', token, {
        ...post({ spec_id: specId, library, locale, ...(fanout ? { source: 'fanout' } : {}) }),
        headers,
      });
      return {
        session_id: answer.session_id,
        eligibility: answer.eligibility,
        roles: roleList(answer.roles) ?? null,
      };
    }),
  /**
   * The library switch (the header's library menu). The body leaves `source`
   * out, which the BFF reads as `menu`, so a page deployed before the API is no
   * `422`. The answer's `target` and `carry` are checked field by field: an
   * older server, or anything malformed, reads as `null`, which offers nothing.
   */
  switchLibrary: async (
    token: string,
    sid: string,
    specId: string,
    library: string,
    source: SwitchSource = 'menu'
  ): Promise<LibrarySwitched> => {
    // The menu, the default, is left out: a BFF from before the field refuses unknown body keys.
    const body =
      source === 'menu' ? { spec_id: specId, library } : { spec_id: specId, library, source };
    const answer = await agentJson<SessionOpened & Record<string, unknown>>(
      `${sessionPath(sid)}/library`,
      token,
      post(body)
    );
    return {
      session_id: answer.session_id,
      eligibility: answer.eligibility,
      target: plotTarget(answer.target),
      carry: switchCarry(answer.carry),
    };
  },
  /**
   * The plot memory, oldest first (`GET .../memory`). An answer that is not
   * that shape is `502 upstream`; a server without the route answers `404
   * not_found`.
   */
  memory: async (token: string, sid: string, signal?: AbortSignal): Promise<PlotMemory> => {
    const memory = plotMemory(
      await agentJson<unknown>(`${sessionPath(sid)}/memory`, token, { signal })
    );
    if (!memory) throw new AgentApiError(502, 'upstream');
    return memory;
  },
  /**
   * Remove one decision from the plot memory (the remembered list's
   * `.forget()`): the answer is the memory after it. The plot itself does not
   * change; the next plot no longer takes the decision over. `404 not_found`
   * for an id the memory does not hold, `409 run_active` while a turn runs. An
   * id outside the BFF's pattern is refused here, before any request.
   */
  forgetMemory: async (token: string, sid: string, entryId: string): Promise<PlotMemory> => {
    if (!MEMORY_ENTRY_ID.test(entryId)) throw new AgentApiError(0, 'invalid');
    const memory = plotMemory(
      await agentJson<unknown>(`${sessionPath(sid)}/memory/${entryId}`, token, {
        method: 'DELETE',
      })
    );
    if (!memory) throw new AgentApiError(502, 'upstream');
    return memory;
  },
  /**
   * Forget every decision of the plot memory (the remembered list's
   * `.forget_all()`, a blank start): the answer is the memory after it. Only
   * the user clears the memory; `.start_over()` keeps it. `409 run_active`
   * while a turn runs.
   */
  forgetAllMemory: async (token: string, sid: string): Promise<PlotMemory> => {
    const memory = plotMemory(
      await agentJson<unknown>(`${sessionPath(sid)}/memory`, token, { method: 'DELETE' })
    );
    if (!memory) throw new AgentApiError(502, 'upstream');
    return memory;
  },
  /**
   * A stored dataset, or a transcription of free text to confirm first (`isTranscribed`).
   * `confirmed` marks the table the user accepted with `.use()`: the server then never
   * hands the text to its transcriber again (a one-column table would otherwise be read
   * again) and keeps every row of it (no lines left out as notes or totals), while the
   * pre-filter, the judge and the store run as usual.
   * Text that asks for a formula (`sin(x) von -pi bis pi`) answers `422 formula` and
   * stores nothing: the chat's `generate_data` computes such a table. Code that
   * generates data (Python, JavaScript, R) answers `422 code` the same way: the
   * chat's `run_data_code` runs it. Text that asks for data instead of holding
   * it ("Beispieldaten") answers `422 data_request`: the hook sends it to the
   * chat as the user's turn, where the assistant generates example data.
   * `source` is the name of the file the text was read from (a drop, `.open()`,
   * a pasted file): it travels beside the text, which stays as in the file; the
   * server screens it and answers it as `file_name`, never as a note.
   * `table` reads another of the tables the previous answer's `tables` named
   * (1-based), when the text holds several.
   */
  uploadDataset: (
    token: string,
    sid: string,
    text: string,
    confirmed = false,
    source?: string,
    table?: number
  ) =>
    agentJson<DatasetAnswer>(
      `${sessionPath(sid)}/dataset`,
      token,
      post({
        text,
        ...(confirmed ? { confirmed: true } : {}),
        ...(source ? { source } : {}),
        ...(table ? { table } : {}),
      })
    ),
  /**
   * A dropped binary data file (Excel, OpenDocument, Parquet, Feather, Arrow,
   * NumPy) read on the server, in the renderer's sandbox, into the text the
   * message box's attachment holds. Nothing is stored: the page attaches `text`, and
   * Enter sends it through `uploadDataset`. `sheet` asks for
   * another sheet (or `.npz` array) of the same file, by a name of `sheets`.
   * An answer the page cannot read is `422 invalid`.
   */
  convertFile: async (
    token: string,
    sid: string,
    dataBase64: string,
    sheet?: string
  ): Promise<ConvertAnswer> => {
    const answer = await agentJson<unknown>(
      `${sessionPath(sid)}/dataset/convert`,
      token,
      post({ data_base64: dataBase64, ...(sheet ? { sheet } : {}) })
    );
    const parsed = convertAnswer(answer);
    if (!parsed) throw new AgentApiError(422, 'invalid');
    return parsed;
  },
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
   * outside `LANGUAGE_PATTERN`. On a session with data the answer also carries
   * `suggestion`, the `.to_long()` offer with its new column names in the new
   * language (or `null`), so the data panel's card follows the language.
   */
  setLanguage: async (token: string, sid: string, language: string): Promise<LanguageAnswer> => {
    const answer = await agentJson<unknown>(`${sessionPath(sid)}/language`, token, {
      method: 'PUT',
      body: JSON.stringify({ language }),
    });
    const applied = plotLanguage(answer) ?? { language, source: 'chosen' as const };
    return isRecord(answer) && 'suggestion' in answer
      ? { ...applied, suggestion: longSuggestion(answer.suggestion) }
      : applied;
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
   * The admin fan-out: the server copies the confirmed current data of
   * `fromSession` (the page's own session), byte for byte with its bindings and
   * their confirmation, into the fan-out session `sid`. Both must be this
   * admin's. `422 unconfirmed` / `no_dataset` for a source without confirmed
   * data, `409 has_dataset` for a target with data; a server without the route
   * answers `404 not_found`.
   */
  copyDataset: (token: string, sid: string, fromSession: string) =>
    agentJson<DatasetCopied>(
      `${sessionPath(sid)}/dataset/copy`,
      token,
      post({ from_session: fromSession })
    ),
  /**
   * `.view_all()`: the current data version's canonical `data.csv` as the server
   * stores it, at most 4 MiB, for the data panel's full view. Read-only; `422
   * no_dataset` before any data.
   */
  datasetCsv: async (token: string, sid: string, signal?: AbortSignal): Promise<string> => {
    const response = await agentFetch(`${sessionPath(sid)}/dataset/data.csv`, token, { signal });
    return response.text();
  },

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
  /**
   * Opens the chat turn's SSE stream; the caller reads it with `readSseEvents`.
   * `siteTheme`, the theme the site shows, is the theme a plot of the turn
   * renders in unless the user asks for one in the chat. It travels in the
   * query, not the strict body, so a page deployed before the API is no `422`.
   */
  postMessage: (
    token: string,
    sid: string,
    body: TurnBody,
    signal: AbortSignal,
    siteTheme?: Theme
  ) =>
    agentFetch(`${sessionPath(sid)}/messages${siteTheme ? `?theme=${siteTheme}` : ''}`, token, {
      ...post(body),
      headers: { Accept: 'text/event-stream' },
      signal,
    }),
  /**
   * The rest of the session's latest turn after its stream was cut (`GET .../turn`): the
   * events after `lastEventId`, the last SSE id the page read (`<run_id>.<n>`), then the
   * turn live until it ends; read with `readSseEvents` like the turn's own stream. The
   * server runs a turn whose stream the edge lost on to its end, so the page reads its
   * result here instead of asking for it again. `404 not_found` when another turn is the
   * latest; `502 upstream` or `503 capacity` when it cannot be read right now.
   */
  resumeTurn: (token: string, sid: string, lastEventId: string, signal: AbortSignal) =>
    agentFetch(`${sessionPath(sid)}/turn`, token, {
      headers: { Accept: 'text/event-stream', 'Last-Event-ID': lastEventId },
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
  /** One file of a version; `theme` picks the theme of `plot.html`, which the server builds on demand. */
  artifact: async (
    token: string,
    sid: string,
    name: ArtifactName,
    version: number,
    theme?: Theme
  ) => {
    const query = theme ? `?v=${version}&theme=${theme}` : `?v=${version}`;
    const response = await agentFetch(`${sessionPath(sid)}/artifacts/${name}${query}`, token);
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
   * not; upstream errors as for `.save()`. On the public lane the call carries
   * a fresh Turnstile token.
   */
  sendFeedback: (token: string, sid: string, body: FeedbackBody) =>
    withHumanCheck(token, 'agent_feedback', headers =>
      agentJson<FeedbackStored>(`${sessionPath(sid)}/feedback`, token, { ...post(body), headers })
    ),
  /**
   * The usage beacon (`POST .../outcome`, `204`): fire and forget. The body is
   * rebuilt from its three fields, so nothing else can ride along; `keepalive`
   * lets it outlive a page that closes right after a download. Every failure
   * (a refused body, `429`, an expired session, no network) is swallowed: the
   * beacon never shows an error and never blocks the page.
   */
  reportOutcome: async (token: string, sid: string, body: OutcomeBody): Promise<void> => {
    const payload =
      body.action === 'feedback'
        ? { action: body.action, version: body.version, reaction: body.reaction }
        : { action: body.action, version: body.version };
    try {
      await agentFetch(`${sessionPath(sid)}/outcome`, token, { ...post(payload), keepalive: true });
    } catch {
      /* best effort: telemetry never surfaces */
    }
  },
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
  // The user already has their cap of sandbox runs (`user_max_runs`) queued or running in other windows.
  'run_limit',
  'deadline',
  'guard_unavailable',
  // The assistant wrote no reply, also when the service asked it once more.
  'no_reply',
  'upstream',
  'internal',
] as const;
export type StreamErrorCode = (typeof STREAM_ERROR_CODES)[number];

export type AgentEvent =
  | { type: 'ready'; runId: string | null }
  | { type: 'queued'; position: number; waiting: number }
  /** A run that waited in the queue holds its slot now: the wait is over. */
  | { type: 'started' }
  | {
      type: 'step';
      step: PipelineStep;
      attempt: number | null;
      /**
       * The most rounds the run may make (`max_attempts`, the service's `AGENT_MAX_ATTEMPTS`), so
       * the page counts `try 2 of 2` from the server; `null` from a server without it.
       */
      maxAttempts: number | null;
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
      /**
       * The `.to_long()` offer after the run, its new column names in the
       * session language, which the turn may have changed: `null` for none,
       * `undefined` when the server sent no `suggestion` (no data, an older
       * server), which leaves the page's card as it is.
       */
      suggestion?: LongSuggestion | null;
      /**
       * The library switch the user asked for in the chat (the assistant's
       * `switch_plot`), which the page carries out with the
       * switch route and, with `plot`, the carry run; `null` without one.
       */
      switch: ChatSwitch | null;
      /**
       * What the turn changed, in the server's word (`TurnOutcome`). Absent when the server sent
       * none: a refused, failed or stopped turn, or an older server. `unknown` for a value this
       * page does not know (a newer server), which the page reads as a change, never as a question.
       */
      turn?: TurnOutcome | 'unknown';
    };

/** Where a switch came from, for the server's telemetry only: the library menu, or the chat (`done.switch`). */
export type SwitchSource = 'menu' | 'chat';

/** A library switch asked for in the chat (`done.switch`): the library, and whether to plot there at once. */
export interface ChatSwitch {
  library: string;
  plot: boolean;
}

/** `done.switch` as the page can carry it out: a supported library id, else `null`. */
export function chatSwitch(value: unknown): ChatSwitch | null {
  if (!value || typeof value !== 'object') return null;
  const { library, plot } = value as Record<string, unknown>;
  if (typeof library !== 'string' || !LIBRARIES.includes(library)) return null;
  return { library, plot: plot !== false };
}

const isInt = (value: unknown): value is number =>
  typeof value === 'number' && Number.isInteger(value) && value >= 0;

/** One round from the stream, or `null` when its attempt, outcome or count is not one the server sends. */
function toRound(value: unknown): Round | null {
  if (!value || typeof value !== 'object') return null;
  const { attempt, outcome, findings, step, shipped, defects } = value as Record<string, unknown>;
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
  // Closed rubric ids only; anything else is left out, never shown.
  const ids = strings(defects).filter(id => RUBRIC_ID.test(id));
  if (ids.length) round.defects = ids;
  return round;
}

const RUBRIC_ID = /^[A-Z]{2}-[0-9]{2}$/;

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

/** A switch answer's `target`, or `null` for anything but two non-empty strings. */
export function plotTarget(value: unknown): PlotTarget | null {
  if (!isRecord(value)) return null;
  const { spec_id, library } = value;
  if (typeof spec_id !== 'string' || !spec_id || typeof library !== 'string' || !library) {
    return null;
  }
  return { spec_id, library };
}

/**
 * A switch answer's `carry`, or `null`: two counts and three flags, else
 * nothing. An offer is a button the page shows, so a half-read one offers
 * nothing rather than a count that is not the server's.
 */
export function switchCarry(value: unknown): SwitchCarry | null {
  if (!isRecord(value)) return null;
  const { decisions, newer, target_has_plot, from_plot, offer } = value;
  if (!isInt(decisions) || decisions < 0 || !isInt(newer) || newer < 0) return null;
  if (typeof target_has_plot !== 'boolean' || typeof from_plot !== 'boolean') return null;
  if (typeof offer !== 'boolean') return null;
  return { decisions, newer, target_has_plot, from_plot, offer };
}

/** One entry of the plot memory, its documented fields only; `null` without an id, a kind or a text. */
function memoryEntry(value: unknown): MemoryEntry | null {
  if (!isRecord(value)) return null;
  const { id, kind, target, text, expect, turn } = value;
  if (typeof id !== 'string' || !MEMORY_ENTRY_ID.test(id)) return null;
  if (typeof kind !== 'string' || !kind || typeof text !== 'string' || !text.trim()) return null;
  return {
    id,
    kind,
    target:
      typeof target === 'string' && MEMORY_TARGETS.has(target) ? (target as MemoryTarget) : null,
    text: text.slice(0, MAX_MEMORY_TEXT_CHARS),
    expect: typeof expect === 'string' && expect ? expect : null,
    turn: isInt(turn) ? turn : 0,
  };
}

/**
 * The memory route's answer, or `null` when it is not `{entries: [...]}`. The
 * list is shown with a remove control per entry, so an entry the page cannot
 * read is left out rather than shown half (the server's own validation makes
 * that a case that does not happen).
 */
export function plotMemory(value: unknown): PlotMemory | null {
  if (!isRecord(value) || !Array.isArray(value.entries)) return null;
  const entries = value.entries
    .map(memoryEntry)
    .filter((entry): entry is MemoryEntry => entry !== null);
  const max = value.max_entries;
  return {
    entries,
    max_entries: isInt(max) && max > 0 ? max : DEFAULT_MAX_MEMORY_ENTRIES,
    written: value.written === true,
  };
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
 * rather than putting a table on screen that is not the server's. A generated
 * first dataset (`generate_data` in a session without data) has nothing to undo.
 * `can_undo` and `original_version` pass only as the server types them.
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
    ...(typeof value.can_undo === 'boolean' ? { can_undo: value.can_undo } : {}),
    ...(isInt(value.original_version) && value.original_version >= 1
      ? { original_version: value.original_version }
      : {}),
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
    siblings: strings(value.siblings),
  };
}

/**
 * A version's `memory` as the server sends it: both lists, each id in the memory's pattern (an
 * entry that is no id is dropped, never the list); `null` for anything else, which reads as no
 * field, so a malformed value never shows as an empty memory.
 */
function versionMemory(value: unknown): VersionMemory | null {
  if (!isRecord(value) || !Array.isArray(value.kept) || !Array.isArray(value.added)) return null;
  const ids = (items: unknown[]) =>
    items.filter((id): id is string => typeof id === 'string' && MEMORY_ENTRY_ID.test(id));
  return { kept: ids(value.kept), added: ids(value.added) };
}

/** `done.turn` as the page reads it: a known outcome, or `unknown` for any other value. */
function turnOf(value: unknown): TurnOutcome | 'unknown' {
  return TURN_OUTCOMES.includes(value as TurnOutcome) ? (value as TurnOutcome) : 'unknown';
}

const ARTIFACT_NAMES = new Set<string>([
  'plot-light.png',
  'plot-dark.png',
  ...CODE_ARTIFACTS,
  PAGE_ARTIFACT,
  'data.csv',
]);
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
      if (d.step === 'started') return { type: 'started' };
      if (!PIPELINE_STEPS.includes(d.step as PipelineStep)) return null;
      return {
        type: 'step',
        step: d.step as PipelineStep,
        attempt: isInt(d.attempt) ? d.attempt : null,
        maxAttempts: isInt(d.max_attempts) && d.max_attempts >= 1 ? d.max_attempts : null,
        previous:
          isInt(d.attempt) && d.attempt > 1
            ? toRound({
                attempt: d.attempt - 1,
                outcome: d.outcome,
                findings: d.findings,
                defects: d.defects,
              })
            : null,
      };
    case 'message':
      return typeof d.text === 'string' ? { type: 'message', text: d.text } : null;
    case 'plot': {
      if (typeof d.status !== 'string' || !PLOT_STATUSES.has(d.status)) return null;
      const memory = versionMemory(d.memory);
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
          ...(memory ? { memory } : {}),
        },
      };
    }
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
        ...('suggestion' in d ? { suggestion: longSuggestion(d.suggestion) } : {}),
        switch: chatSwitch(d.switch),
        ...(d.turn !== undefined && d.turn !== null ? { turn: turnOf(d.turn) } : {}),
      };
    default:
      return null;
  }
}

/** The theme a version rendered: the PNG among its artifacts (light wins a tie). */
export function renderedThemes(artifacts: readonly string[]): Theme[] {
  return (['light', 'dark'] as const).filter(theme => artifacts.includes(PNG_ARTIFACT[theme]));
}

/** The name a version's exported code downloads under: the code artifact among its artifacts, `plot.py` without one. */
export function codeArtifact(artifacts: readonly string[]): CodeArtifact {
  return CODE_ARTIFACTS.find(name => artifacts.includes(name)) ?? 'plot.py';
}

/** Whether a version offers the interactive page: a JavaScript plot, whose code runs only in it. */
export function hasPage(artifacts: readonly string[]): boolean {
  return artifacts.includes(PAGE_ARTIFACT);
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
