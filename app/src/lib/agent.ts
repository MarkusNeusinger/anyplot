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

export interface ColumnProfile {
  name: string;
  dtype: ColumnDtype;
  missing: number;
  unique: number;
  min?: number | string | null;
  max?: number | string | null;
  top?: string[];
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

export interface DatasetParsed {
  /** Up to 20 data rows (the header is `profile.columns[].name`). */
  preview: string[][];
  profile: DatasetProfile;
  /** The server's default bindings; roles it could not match are absent. */
  bindings: Binding[];
  warnings: string[];
}

export interface BindingsApplied {
  bindings: Binding[];
  complete: boolean;
  /** Required roles without a column. */
  missing_roles: string[];
}

export type PlotStatus = 'ok' | 'needs_attention' | 'failed' | 'not_ready';

export interface PlotResult {
  status: PlotStatus;
  reason?: string | null;
  attempts: number;
  artifacts: ArtifactName[];
  changes: string[];
  residual_defects: string[];
}

export interface ThemeRendered {
  status: 'ok' | 'needs_attention' | 'failed';
  reason?: string | null;
  artifacts: ArtifactName[];
}

// ============================================================================
// Errors
// ============================================================================

export class AgentApiError extends Error {
  readonly status: number;
  /** The BFF's code (`run_active`, `too_long`, ...), or `network` when nothing answered. */
  readonly code: string;
  /** The request id to quote, when the BFF minted one. */
  readonly ref: string | null;

  constructor(status: number, code: string, ref: string | null = null) {
    super(`agent request failed: ${status} ${code}`);
    this.name = 'AgentApiError';
    this.status = status;
    this.code = code;
    this.ref = ref;
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
  try {
    const body: unknown = await response.json();
    if (body && typeof body === 'object') {
      const record = body as Record<string, unknown>;
      if (typeof record.detail === 'string') code = record.detail;
      if (typeof record.ref === 'string') ref = record.ref;
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
    ref
  );
}

// ============================================================================
// Requests
// ============================================================================

export function agentUrl(path: string): string {
  return `${DEBUG_API_URL}/debug/agent${path}`;
}

/** A raw BFF call with the CSRF header; throws `AgentApiError` on a non-2xx status. */
export async function agentFetch(path: string, token: string, init: RequestInit = {}) {
  let response: Response;
  try {
    response = await fetchWithAuth(agentUrl(path), token, {
      ...init,
      headers: { ...AGENT_CLIENT_HEADERS, ...((init.headers as Record<string, string>) || {}) },
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err;
    throw new AgentApiError(0, 'network');
  }
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
  uploadDataset: (token: string, sid: string, text: string) =>
    agentJson<DatasetParsed>(`${sessionPath(sid)}/dataset`, token, post({ text })),
  putBindings: (token: string, sid: string, bindings: Binding[]) =>
    agentJson<BindingsApplied>(`${sessionPath(sid)}/bindings`, token, {
      method: 'PUT',
      body: JSON.stringify(bindings),
    }),
  /** Opens the chat turn's SSE stream; the caller reads it with `readSseEvents`. */
  postMessage: (
    token: string,
    sid: string,
    body: { text: string } | { action: 'create_plot' },
    signal: AbortSignal
  ) =>
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
  deleteSession: async (token: string, sid: string) => {
    await agentFetch(sessionPath(sid), token, { method: 'DELETE' });
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
  | { type: 'done'; llmCalls: number | null; tokens: number | null };

const isInt = (value: unknown): value is number =>
  typeof value === 'number' && Number.isInteger(value) && value >= 0;
const strings = (value: unknown): string[] =>
  Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
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

export function utf8Bytes(text: string): number {
  return new TextEncoder().encode(text).length;
}
