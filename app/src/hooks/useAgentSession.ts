/**
 * State machine of one "Use with my data" chat session (`/debug/agent`).
 *
 * Owns everything the chat page shows and every call it makes to the BFF
 * (`src/lib/agent.ts`): opening the session, the pasted dataset and its
 * bindings, the turns and their `anyplot/1` stream, the plot versions with
 * their images and code, the theme toggle, the library switch and Stop.
 *
 * Phases: `opening` → `ready` (or `unauthorized`, `ineligible`, `error`). At
 * most one turn runs at a time; while it runs, `run` holds its timeline and
 * queue position.
 *
 * Versions: the `plot` event carries `version`, the number the agents service
 * stored the result under, which the artifact (`?v=`) and theme toggle routes
 * take. Against a server without that field the hook counts the shipped plot
 * events instead (the server numbers them in the same order), which drifts
 * only when a stored version's event never arrives.
 *
 * Bindings: the dataset answer lists the spec's roles. A single role binds
 * under its own name, a variadic family `y` under its members `y1`, `y2`, ...;
 * the hook keeps the members contiguous (`compactFamilies`), so clearing `y2`
 * of three moves `y3` up. Every change replaces the whole set on the server.
 *
 * One thing at a time: the agents service runs one turn or theme render per
 * user and answers anything else with `409 run_active`, and a parse or a
 * binding change rewrites the data a turn reads. So the hook starts none of
 * these while another is in flight, and Stop keeps the stream open until the
 * server's `done` confirms the run ended (at most `STOP_GRACE_MS`), so the
 * next action does not race the stopped run.
 *
 * Session lifetime: the session, with the pasted data and its renders, is
 * deleted when the page unmounts and on `pagehide` (a reload or a closed tab,
 * sent with `keepalive`); the server's idle sweep is the backstop.
 *
 * Analytics carry enum properties only, never text or data:
 * `agent_data_parsed{status, size_bucket}`,
 * `agent_plot_rendered{library, status, repaired, spec}` and
 * `agent_guardrail_block{reason}`.
 */

import { useCallback, useEffect, useReducer, useRef } from 'react';

import { useAnalytics } from 'src/hooks/useAnalytics';
import {
  agentApi,
  AgentApiError,
  type AgentEvent,
  type ArtifactName,
  type Binding,
  type DatasetParsed,
  type Eligibility,
  MAX_DATASET_BYTES,
  MAX_MESSAGE_CHARS,
  parseAgentEvent,
  type PipelineStep,
  type PlotResult,
  PNG_ARTIFACT,
  renderedThemes,
  type RoleSpec,
  sizeBucket,
  type Theme,
  utf8Bytes,
} from 'src/lib/agent';
import { readSseEvents } from 'src/lib/sse';
import { reloadOnceForAccess } from 'src/utils/adminAuth';

/** How long Stop waits for the server's `done` before it lets go of the stream. */
export const STOP_GRACE_MS = 30_000;

// ============================================================================
// State
// ============================================================================

export type SessionPhase = 'opening' | 'ready' | 'unauthorized' | 'ineligible' | 'error';

export interface Failure {
  code: string;
  ref: string | null;
  /** The binding check's lines of a refused binding set. */
  errors?: string[];
}

export type TimelineStep = 'queued' | PipelineStep;

export interface RunState {
  kind: 'create_plot' | 'message';
  /** Steps in arrival order; the last one is in progress. */
  steps: { step: TimelineStep; attempt: number | null }[];
  /** Set while the turn waits in the run queue: `position` 1 runs next. */
  queue: { position: number; waiting: number } | null;
  stopping: boolean;
}

export type ThemeImage =
  | { state: 'loading' }
  | { state: 'ready'; url: string; blob: Blob; status: 'ok' | 'needs_attention' }
  | { state: 'failed'; code: string; ref: string | null };

export type CodeText =
  { state: 'loading' } | { state: 'ready'; text: string } | { state: 'failed' };

export interface PlotVersion {
  /** The agents service's version number (1-based within the session). */
  number: number;
  library: string;
  result: PlotResult;
  /** The theme the run rendered; the other one renders on demand. */
  theme: Theme;
  images: Partial<Record<Theme, ThemeImage>>;
  code: CodeText;
}

export type ChatItem =
  | { id: number; kind: 'user'; text: string }
  | { id: number; kind: 'action'; action: 'create_plot'; library: string }
  | { id: number; kind: 'assistant'; text: string }
  | { id: number; kind: 'refusal'; code: string; text: string }
  | { id: number; kind: 'error'; code: string; ref: string | null }
  | { id: number; kind: 'plot'; version: number }
  | { id: number; kind: 'plot_failed'; result: PlotResult }
  | { id: number; kind: 'notice'; text: string };

/** Distributes `Omit` over the union, so each member keeps its own fields. */
type WithoutId<T> = T extends unknown ? Omit<T, 'id'> : never;
type NewChatItem = WithoutId<ChatItem>;

export interface DatasetState {
  parsed: DatasetParsed;
  bytes: number;
}

/** Binding name (`x`, `y1`) to column; only bound names are present. */
export type BindingMap = Record<string, string>;

export interface AgentSessionState {
  phase: SessionPhase;
  failure: Failure | null;
  sessionId: string | null;
  library: string;
  eligibility: Eligibility | null;
  dataset: DatasetState | null;
  parsing: boolean;
  datasetError: Failure | null;
  /** The spec's roles, in spec order; the data panel shows a column choice for each. */
  roles: RoleSpec[];
  bindings: BindingMap;
  bindingsComplete: boolean;
  /** Required roles without a column; a variadic family by its name. */
  missingRoles: string[];
  bindingsBusy: boolean;
  bindingsError: Failure | null;
  libraryBusy: boolean;
  /** A theme toggle render is in flight. */
  themeBusy: boolean;
  items: ChatItem[];
  versions: Record<number, PlotVersion>;
  run: RunState | null;
}

type Action =
  | { type: 'opened'; sessionId: string; eligibility: Eligibility }
  | { type: 'open_failed'; phase: SessionPhase; failure: Failure | null }
  | { type: 'unauthorized' }
  | { type: 'parse_start' }
  | { type: 'parse_done'; parsed: DatasetParsed; bytes: number }
  | { type: 'parse_failed'; failure: Failure }
  | { type: 'bindings_start'; bindings: BindingMap }
  | { type: 'bindings_done'; bindings: BindingMap; complete: boolean; missingRoles: string[] }
  | { type: 'bindings_failed'; bindings: BindingMap; failure: Failure }
  | { type: 'library_start' }
  | { type: 'library_done'; library: string; eligibility: Eligibility }
  | { type: 'library_failed'; failure: Failure }
  | { type: 'theme_busy'; busy: boolean }
  | { type: 'item'; item: ChatItem }
  | { type: 'run_start'; kind: RunState['kind'] }
  | { type: 'run_queued'; position: number; waiting: number }
  | { type: 'run_step'; step: PipelineStep; attempt: number | null }
  | { type: 'run_stopping' }
  | { type: 'run_end' }
  | { type: 'version_add'; version: PlotVersion }
  | { type: 'version_image'; number: number; theme: Theme; image: ThemeImage }
  | { type: 'version_code'; number: number; code: CodeText };

export function initialAgentState(library: string): AgentSessionState {
  return {
    phase: 'opening',
    failure: null,
    sessionId: null,
    library,
    eligibility: null,
    dataset: null,
    parsing: false,
    datasetError: null,
    roles: [],
    bindings: {},
    bindingsComplete: false,
    missingRoles: [],
    bindingsBusy: false,
    bindingsError: null,
    libraryBusy: false,
    themeBusy: false,
    items: [],
    versions: {},
    run: null,
  };
}

// ============================================================================
// Roles and bindings
// ============================================================================

/** A role the server named but did not describe (an older server, or a missing role). */
function bareRole(name: string, required: boolean): RoleSpec {
  return { name, kinds: [], required, variadic: false, description: '' };
}

/**
 * The variadic family a binding name belongs to (`y3` → `y`), as the agents
 * service resolves it: an exact single role wins, then the family with the
 * longest name whose `<name><digits>` matches.
 */
export function familyOf(name: string, roles: readonly RoleSpec[]): RoleSpec | null {
  if (roles.some(role => !role.variadic && role.name === name)) return null;
  let best: RoleSpec | null = null;
  for (const role of roles) {
    if (!role.variadic || !name.startsWith(role.name)) continue;
    if (!/^\d+$/.test(name.slice(role.name.length))) continue;
    if (!best || role.name.length > best.name.length) best = role;
  }
  return best;
}

/** A family's bound members in member order: `[[y1, col], [y2, col], ...]`. */
export function familyMembers(
  bindings: BindingMap,
  family: RoleSpec,
  roles: readonly RoleSpec[]
): [string, string][] {
  return Object.entries(bindings)
    .filter(([name]) => familyOf(name, roles)?.name === family.name)
    .sort(([a], [b]) => Number(a.slice(family.name.length)) - Number(b.slice(family.name.length)));
}

/**
 * The binding name of a family's `n`-th member (1-based). A name a single role
 * of the spec owns (a family `y` next to a role `y2`) is skipped, because the
 * server would read it as that role.
 */
export function nthMember(family: RoleSpec, n: number, roles: readonly RoleSpec[]): string {
  const singles = new Set(roles.filter(role => !role.variadic).map(role => role.name));
  let index = 0;
  let name = family.name;
  for (let found = 0; found < n;) {
    index += 1;
    name = `${family.name}${index}`;
    if (!singles.has(name)) found += 1;
  }
  return name;
}

/** Renumber every family's bound members in their order, so the members stay contiguous. */
export function compactFamilies(
  bindings: Record<string, string | null>,
  roles: readonly RoleSpec[]
): BindingMap {
  const bound: BindingMap = {};
  for (const [name, column] of Object.entries(bindings)) if (column) bound[name] = column;
  const result: BindingMap = {};
  for (const [name, column] of Object.entries(bound)) {
    if (!familyOf(name, roles)) result[name] = column;
  }
  for (const family of roles.filter(role => role.variadic)) {
    familyMembers(bound, family, roles).forEach(([, column], index) => {
      result[nthMember(family, index + 1, roles)] = column;
    });
  }
  return result;
}

function toMap(bindings: readonly Binding[]): BindingMap {
  const map: BindingMap = {};
  for (const binding of bindings) if (binding.column) map[binding.role] = binding.column;
  return map;
}

// ============================================================================
// Reducer
// ============================================================================

function patchVersion(
  state: AgentSessionState,
  number: number,
  patch: (version: PlotVersion) => PlotVersion
): AgentSessionState {
  const version = state.versions[number];
  if (!version) return state;
  return { ...state, versions: { ...state.versions, [number]: patch(version) } };
}

export function agentReducer(state: AgentSessionState, action: Action): AgentSessionState {
  switch (action.type) {
    case 'opened':
      return {
        ...state,
        phase: 'ready',
        sessionId: action.sessionId,
        eligibility: action.eligibility,
      };
    case 'open_failed':
      return { ...state, phase: action.phase, failure: action.failure, run: null };
    case 'unauthorized':
      return { ...state, phase: 'unauthorized', run: null };
    case 'parse_start':
      return { ...state, parsing: true, datasetError: null };
    case 'parse_done':
      return {
        ...state,
        parsing: false,
        dataset: { parsed: action.parsed, bytes: action.bytes },
        // An older server names no roles: the default bindings stand in for them.
        roles:
          action.parsed.roles ??
          action.parsed.bindings.map(binding => bareRole(binding.role, false)),
        bindings: toMap(action.parsed.bindings),
        bindingsComplete: false,
        missingRoles: [],
        bindingsError: null,
      };
    case 'parse_failed':
      return { ...state, parsing: false, datasetError: action.failure };
    case 'bindings_start':
      return { ...state, bindingsBusy: true, bindingsError: null, bindings: action.bindings };
    case 'bindings_done': {
      const known = new Set(state.roles.map(role => role.name));
      const missing = action.missingRoles.filter(name => !known.has(name));
      return {
        ...state,
        bindingsBusy: false,
        roles: [...state.roles, ...missing.map(name => bareRole(name, true))],
        bindings: action.bindings,
        bindingsComplete: action.complete,
        missingRoles: action.missingRoles,
      };
    }
    case 'bindings_failed':
      return {
        ...state,
        bindingsBusy: false,
        bindings: action.bindings,
        bindingsError: action.failure,
      };
    case 'library_start':
      return { ...state, libraryBusy: true };
    case 'library_done':
      return {
        ...state,
        libraryBusy: false,
        library: action.library,
        eligibility: action.eligibility,
      };
    case 'library_failed':
      return { ...state, libraryBusy: false };
    case 'theme_busy':
      return { ...state, themeBusy: action.busy };
    case 'item':
      return { ...state, items: [...state.items, action.item] };
    case 'run_start':
      return { ...state, run: { kind: action.kind, steps: [], queue: null, stopping: false } };
    case 'run_queued': {
      if (!state.run) return state;
      const steps = state.run.steps;
      const last = steps[steps.length - 1];
      return {
        ...state,
        run: {
          ...state.run,
          steps: last?.step === 'queued' ? steps : [...steps, { step: 'queued', attempt: null }],
          queue: { position: action.position, waiting: action.waiting },
        },
      };
    }
    case 'run_step':
      if (!state.run) return state;
      return {
        ...state,
        run: {
          ...state.run,
          queue: null,
          steps: [...state.run.steps, { step: action.step, attempt: action.attempt }],
        },
      };
    case 'run_stopping':
      return state.run ? { ...state, run: { ...state.run, stopping: true } } : state;
    case 'run_end':
      return { ...state, run: null };
    case 'version_add':
      return {
        ...state,
        versions: { ...state.versions, [action.version.number]: action.version },
      };
    case 'version_image':
      return patchVersion(state, action.number, version => ({
        ...version,
        images: { ...version.images, [action.theme]: action.image },
      }));
    case 'version_code':
      return patchVersion(state, action.number, version => ({ ...version, code: action.code }));
    default:
      return state;
  }
}

// ============================================================================
// Hook
// ============================================================================

export interface UseAgentSessionOptions {
  specId: string;
  library: string;
  locale: string;
  token: string;
}

const GUARDRAIL_REASONS = new Set(['out_of_scope', 'budget', 'unsupported_content']);

function failureOf(err: unknown): Failure {
  if (err instanceof AgentApiError) {
    return err.errors.length
      ? { code: err.code, ref: err.ref, errors: err.errors }
      : { code: err.code, ref: err.ref };
  }
  return { code: 'network', ref: null };
}

const isAbort = (err: unknown) => err instanceof DOMException && err.name === 'AbortError';

export function useAgentSession({ specId, library, locale, token }: UseAgentSessionOptions) {
  const [state, dispatch] = useReducer(agentReducer, library, initialAgentState);
  const { trackEvent } = useAnalytics();

  // Values async callbacks read after an await; refs, so a stale closure never
  // acts on a previous session.
  const stateRef = useRef(state);
  stateRef.current = state;
  const abortRef = useRef<AbortController | null>(null);
  const stoppedRef = useRef(false);
  const stopTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Set synchronously, before the state catches up, so a double click starts nothing twice.
  const themeRef = useRef(false);
  const parseRef = useRef(false);
  const versionCounter = useRef(0);
  const blobUrls = useRef<Set<string>>(new Set());
  const mounted = useRef(true);

  const itemId = useRef(0);

  const safeDispatch = useCallback((action: Action) => {
    if (mounted.current) dispatch(action);
  }, []);

  /** Append a thread item; ids are assigned here so the reducer stays pure. */
  const addItem = useCallback(
    (item: NewChatItem) => {
      itemId.current += 1;
      safeDispatch({ type: 'item', item: { ...item, id: itemId.current } as ChatItem });
    },
    [safeDispatch]
  );

  const handleFailure = useCallback(
    (err: unknown): Failure => {
      if (err instanceof AgentApiError && err.unauthorized) safeDispatch({ type: 'unauthorized' });
      return failureOf(err);
    },
    [safeDispatch]
  );

  /** Whether a turn, a theme render, a parse, a binding change or a library switch is in flight. */
  const busy = useCallback(() => {
    const current = stateRef.current;
    return (
      !!abortRef.current ||
      themeRef.current ||
      parseRef.current ||
      current.bindingsBusy ||
      current.libraryBusy
    );
  }, []);

  // Open the session for the page's spec; the library is the URL's at mount
  // time, later switches go through `switchLibrary`. The page remounts this
  // hook (a `key`) for another spec or token, so the state starts fresh.
  const initialLibrary = useRef(library);
  useEffect(() => {
    mounted.current = true;
    let cancelled = false;
    let opened: string | null = null;
    let purged = false;
    const urls = blobUrls.current;

    /** Delete the server session once: its dataset and renders go with it. */
    const purge = (keepalive: boolean) => {
      if (!opened || purged) return;
      purged = true;
      void agentApi.deleteSession(token, opened, { keepalive }).catch(() => undefined);
    };
    // A reload or a closed tab runs no effect cleanup; `pagehide` does fire.
    const onPageHide = () => purge(true);
    // Back from the back-forward cache, the page holds a session that is gone.
    const onPageShow = (event: PageTransitionEvent) => {
      if (event.persisted && purged) {
        safeDispatch({
          type: 'open_failed',
          phase: 'error',
          failure: { code: 'session_expired', ref: null },
        });
      }
    };
    window.addEventListener('pagehide', onPageHide);
    window.addEventListener('pageshow', onPageShow);

    agentApi
      .openSession(token, specId, initialLibrary.current, locale)
      .then(result => {
        if (cancelled) {
          void agentApi.deleteSession(token, result.session_id).catch(() => undefined);
          return;
        }
        opened = result.session_id;
        safeDispatch({
          type: 'opened',
          sessionId: result.session_id,
          eligibility: result.eligibility,
        });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const failure = failureOf(err);
        if (err instanceof AgentApiError && err.unauthorized) {
          safeDispatch({ type: 'unauthorized' });
        } else if (failure.code === 'not_eligible') {
          safeDispatch({ type: 'open_failed', phase: 'ineligible', failure });
        } else if (failure.code === 'unreachable' && reloadOnceForAccess()) {
          // An expired Access session: the reload lets Access sign the admin in.
        } else {
          safeDispatch({ type: 'open_failed', phase: 'error', failure });
        }
      });
    return () => {
      cancelled = true;
      mounted.current = false;
      window.removeEventListener('pagehide', onPageHide);
      window.removeEventListener('pageshow', onPageShow);
      if (stopTimer.current) clearTimeout(stopTimer.current);
      abortRef.current?.abort();
      purge(false);
      for (const url of urls) URL.revokeObjectURL(url);
      urls.clear();
    };
  }, [specId, locale, token, safeDispatch]);

  // ---------------------------------------------------------------- dataset

  const applyBindings = useCallback(
    async (next: BindingMap, previous: BindingMap) => {
      const sid = stateRef.current.sessionId;
      if (!sid) return;
      safeDispatch({ type: 'bindings_start', bindings: next });
      const payload: Binding[] = Object.entries(next).map(([role, column]) => ({ role, column }));
      try {
        const applied = await agentApi.putBindings(token, sid, payload);
        safeDispatch({
          type: 'bindings_done',
          bindings: toMap(applied.bindings),
          complete: applied.complete,
          missingRoles: applied.missing_roles,
        });
      } catch (err) {
        safeDispatch({ type: 'bindings_failed', bindings: previous, failure: handleFailure(err) });
      }
    },
    [token, safeDispatch, handleFailure]
  );

  const parseData = useCallback(
    async (text: string) => {
      const sid = stateRef.current.sessionId;
      if (!sid || !text.trim() || busy()) return;
      const bytes = utf8Bytes(text);
      const bucket = sizeBucket(bytes);
      if (bytes > MAX_DATASET_BYTES) {
        safeDispatch({ type: 'parse_failed', failure: { code: 'too_long', ref: null } });
        trackEvent('agent_data_parsed', { status: 'too_long', size_bucket: bucket });
        return;
      }
      parseRef.current = true;
      safeDispatch({ type: 'parse_start' });
      try {
        const parsed = await agentApi.uploadDataset(token, sid, text);
        safeDispatch({ type: 'parse_done', parsed, bytes });
        trackEvent('agent_data_parsed', { status: 'ok', size_bucket: bucket });
        const defaults = toMap(parsed.bindings);
        // Learn whether the defaults are complete and which required roles
        // they leave open (the parse stored them already: the PUT is idempotent).
        await applyBindings(defaults, defaults);
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'parse_failed', failure });
        const status = ['too_long', 'unparseable', 'data_refused'].includes(failure.code)
          ? failure.code
          : 'error';
        trackEvent('agent_data_parsed', { status, size_bucket: bucket });
        if (failure.code === 'data_refused') {
          trackEvent('agent_guardrail_block', { reason: 'data_refused' });
        }
      } finally {
        parseRef.current = false;
      }
    },
    [token, safeDispatch, handleFailure, trackEvent, applyBindings, busy]
  );

  /** Bind `name` (a single role or a family member such as `y2`) to `column`, or clear it with `null`. */
  const setBinding = useCallback(
    (name: string, column: string | null) => {
      if (busy()) return;
      const { bindings: current, roles } = stateRef.current;
      const next: Record<string, string | null> = { ...current };
      // A column belongs to one role: taking it frees the role that held it.
      if (column) {
        for (const [other, held] of Object.entries(next)) {
          if (other !== name && held === column) next[other] = null;
        }
      }
      next[name] = column;
      void applyBindings(compactFamilies(next, roles), current);
    },
    [applyBindings, busy]
  );

  // ---------------------------------------------------------------- versions

  const fetchArtifact = useCallback(
    async (number: number, name: ArtifactName): Promise<Blob> => {
      const sid = stateRef.current.sessionId;
      if (!sid) throw new AgentApiError(0, 'no_session');
      return agentApi.artifact(token, sid, name, number);
    },
    [token]
  );

  const loadImage = useCallback(
    async (number: number, theme: Theme, status: 'ok' | 'needs_attention') => {
      safeDispatch({ type: 'version_image', number, theme, image: { state: 'loading' } });
      try {
        const blob = await fetchArtifact(number, PNG_ARTIFACT[theme]);
        if (!mounted.current) return;
        const url = URL.createObjectURL(blob);
        blobUrls.current.add(url);
        safeDispatch({
          type: 'version_image',
          number,
          theme,
          image: { state: 'ready', url, blob, status },
        });
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({
          type: 'version_image',
          number,
          theme,
          image: { state: 'failed', code: failure.code, ref: failure.ref },
        });
      }
    },
    [fetchArtifact, safeDispatch, handleFailure]
  );

  const loadCode = useCallback(
    async (number: number) => {
      safeDispatch({ type: 'version_code', number, code: { state: 'loading' } });
      try {
        const text = await (await fetchArtifact(number, 'plot.py')).text();
        safeDispatch({ type: 'version_code', number, code: { state: 'ready', text } });
      } catch (err) {
        handleFailure(err);
        safeDispatch({ type: 'version_code', number, code: { state: 'failed' } });
      }
    },
    [fetchArtifact, safeDispatch, handleFailure]
  );

  /**
   * The light and dark switch: render the other theme of a version (no model
   * call), then show it. Nothing starts while a turn or another render runs,
   * which the server would refuse with `409 run_active`.
   */
  const requestTheme = useCallback(
    async (number: number, theme: Theme) => {
      const sid = stateRef.current.sessionId;
      const version = stateRef.current.versions[number];
      if (!sid || !version || busy()) return;
      const current = version.images[theme];
      if (current && current.state !== 'failed') return;
      themeRef.current = true;
      safeDispatch({ type: 'theme_busy', busy: true });
      safeDispatch({ type: 'version_image', number, theme, image: { state: 'loading' } });
      try {
        const rendered = await agentApi.renderTheme(token, sid, number, theme);
        if (rendered.status === 'failed' || !rendered.artifacts.includes(PNG_ARTIFACT[theme])) {
          safeDispatch({
            type: 'version_image',
            number,
            theme,
            image: { state: 'failed', code: rendered.reason || 'render', ref: null },
          });
          return;
        }
        await loadImage(number, theme, rendered.status);
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({
          type: 'version_image',
          number,
          theme,
          image: { state: 'failed', code: failure.code, ref: failure.ref },
        });
      } finally {
        themeRef.current = false;
        safeDispatch({ type: 'theme_busy', busy: false });
      }
    },
    [token, safeDispatch, handleFailure, loadImage, busy]
  );

  // ---------------------------------------------------------------- turns

  const onPlot = useCallback(
    (result: PlotResult) => {
      const current = stateRef.current;
      trackEvent('agent_plot_rendered', {
        library: current.library,
        status: result.status,
        repaired: result.attempts > 1 ? 'yes' : 'no',
        spec: specId,
      });
      if (result.status !== 'ok' && result.status !== 'needs_attention') {
        addItem({ kind: 'plot_failed', result });
        return;
      }
      // The server's number; counting is the fallback for a server without it.
      const number = result.version ?? versionCounter.current + 1;
      versionCounter.current = Math.max(versionCounter.current, number);
      const theme = renderedThemes(result.artifacts)[0] ?? 'light';
      safeDispatch({
        type: 'version_add',
        version: {
          number,
          library: current.library,
          result,
          theme,
          images: {},
          code: { state: 'loading' },
        },
      });
      addItem({ kind: 'plot', version: number });
      void loadImage(number, theme, result.status);
      void loadCode(number);
    },
    [specId, trackEvent, safeDispatch, addItem, loadImage, loadCode]
  );

  const onEvent = useCallback(
    (event: AgentEvent) => {
      switch (event.type) {
        case 'queued':
          safeDispatch({ type: 'run_queued', position: event.position, waiting: event.waiting });
          break;
        case 'step':
          safeDispatch({ type: 'run_step', step: event.step, attempt: event.attempt });
          break;
        case 'message':
          addItem({ kind: 'assistant', text: event.text });
          break;
        case 'plot':
          onPlot(event.result);
          break;
        case 'refusal':
          addItem({ kind: 'refusal', code: event.code, text: event.text });
          trackEvent('agent_guardrail_block', {
            reason: GUARDRAIL_REASONS.has(event.code) ? event.code : 'other',
          });
          break;
        case 'error':
          addItem({ kind: 'error', code: event.code, ref: event.ref });
          if (event.code === 'guard_unavailable') {
            trackEvent('agent_guardrail_block', { reason: 'guard_unavailable' });
          }
          break;
        default:
          break;
      }
    },
    [safeDispatch, addItem, onPlot, trackEvent]
  );

  const runTurn = useCallback(
    async (body: { text: string } | { action: 'create_plot' }) => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy()) return;
      const controller = new AbortController();
      abortRef.current = controller;
      stoppedRef.current = false;
      safeDispatch({ type: 'run_start', kind: 'text' in body ? 'message' : 'create_plot' });
      addItem(
        'text' in body
          ? { kind: 'user', text: body.text }
          : { kind: 'action', action: 'create_plot', library: current.library }
      );
      let finished = false;
      try {
        const response = await agentApi.postMessage(token, sid, body, controller.signal);
        if (!response.body) throw new AgentApiError(502, 'upstream');
        for await (const raw of readSseEvents(response.body, controller.signal)) {
          const event = parseAgentEvent(raw);
          if (!event) continue;
          onEvent(event);
          if (event.type === 'done') {
            finished = true;
            break;
          }
        }
        if (!finished && !stoppedRef.current) {
          // The BFF always ends a turn with `done`; a stream without it was cut.
          addItem({ kind: 'error', code: 'upstream', ref: null });
        }
      } catch (err) {
        if (!stoppedRef.current && !isAbort(err)) {
          const failure = handleFailure(err);
          addItem({ kind: 'error', code: failure.code, ref: failure.ref });
        }
      } finally {
        if (stopTimer.current) clearTimeout(stopTimer.current);
        stopTimer.current = null;
        if (stoppedRef.current) addItem({ kind: 'notice', text: 'stopped' });
        if (abortRef.current === controller) abortRef.current = null;
        safeDispatch({ type: 'run_end' });
      }
    },
    [token, safeDispatch, addItem, onEvent, handleFailure, busy]
  );

  const createPlot = useCallback(() => runTurn({ action: 'create_plot' }), [runTurn]);

  const sendMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || trimmed.length > MAX_MESSAGE_CHARS) return Promise.resolve();
      return runTurn({ text: trimmed });
    },
    [runTurn]
  );

  /**
   * Stop: the cancel route takes a waiting run out of the queue at once and
   * aborts a running one at its next step boundary. The stream stays open
   * until the server's `done` says the run is over, so the next action does
   * not meet `409 run_active`, and a result stored just before the stop still
   * arrives. After `STOP_GRACE_MS`, or when the cancel call fails, the stream
   * is closed here.
   */
  const stop = useCallback(async () => {
    const sid = stateRef.current.sessionId;
    const controller = abortRef.current;
    if (!sid || !controller || stoppedRef.current) return;
    stoppedRef.current = true;
    safeDispatch({ type: 'run_stopping' });
    stopTimer.current = setTimeout(() => controller.abort(), STOP_GRACE_MS);
    try {
      await agentApi.cancel(token, sid);
    } catch {
      controller.abort(); // the server may not have heard the cancel: end the turn in this tab
    }
  }, [token, safeDispatch]);

  // ---------------------------------------------------------------- library

  const switchLibrary = useCallback(
    async (next: string): Promise<boolean> => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || busy() || next === current.library) return false;
      safeDispatch({ type: 'library_start' });
      try {
        const result = await agentApi.switchLibrary(token, sid, specId, next);
        safeDispatch({ type: 'library_done', library: next, eligibility: result.eligibility });
        return true;
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'library_failed', failure });
        addItem({ kind: 'error', code: failure.code, ref: failure.ref });
        return false;
      }
    },
    [token, specId, safeDispatch, addItem, handleFailure, busy]
  );

  return {
    state,
    parseData,
    setBinding,
    createPlot,
    sendMessage,
    stop,
    switchLibrary,
    requestTheme,
    fetchArtifact,
  };
}

export type AgentSession = ReturnType<typeof useAgentSession>;

/** Whether the page should hold back actions the server would refuse or race (see the module notes). */
export function sessionBusy(state: AgentSessionState): boolean {
  return !!state.run || state.parsing || state.bindingsBusy || state.libraryBusy || state.themeBusy;
}
