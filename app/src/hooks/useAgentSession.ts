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
 * Versions: the `plot` event carries no version number. The agents service
 * numbers the versions of a session from 1 in the order it stores them, and it
 * stores exactly the results that ship a render (`ok`, `needs_attention`), so
 * the client numbers those plot events the same way and uses the number for
 * the artifact (`?v=`) and theme toggle routes.
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
  sizeBucket,
  type Theme,
  utf8Bytes,
} from 'src/lib/agent';
import { readSseEvents } from 'src/lib/sse';

// ============================================================================
// State
// ============================================================================

export type SessionPhase = 'opening' | 'ready' | 'unauthorized' | 'ineligible' | 'error';

export interface Failure {
  code: string;
  ref: string | null;
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

export interface AgentSessionState {
  phase: SessionPhase;
  failure: Failure | null;
  sessionId: string | null;
  library: string;
  eligibility: Eligibility | null;
  dataset: DatasetState | null;
  parsing: boolean;
  datasetError: Failure | null;
  /** Every role the UI shows a dropdown for: the server's defaults, then the missing roles. */
  roles: string[];
  bindings: Record<string, string | null>;
  bindingsComplete: boolean;
  missingRoles: string[];
  bindingsBusy: boolean;
  bindingsError: Failure | null;
  libraryBusy: boolean;
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
  | { type: 'bindings_start'; bindings: Record<string, string | null> }
  | {
      type: 'bindings_done';
      bindings: Record<string, string | null>;
      complete: boolean;
      missingRoles: string[];
    }
  | { type: 'bindings_failed'; bindings: Record<string, string | null>; failure: Failure }
  | { type: 'library_start' }
  | { type: 'library_done'; library: string; eligibility: Eligibility }
  | { type: 'library_failed'; failure: Failure }
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
    items: [],
    versions: {},
    run: null,
  };
}

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
      return { ...state, phase: action.phase, failure: action.failure };
    case 'unauthorized':
      return { ...state, phase: 'unauthorized', run: null };
    case 'parse_start':
      return { ...state, parsing: true, datasetError: null };
    case 'parse_done': {
      const bindings: Record<string, string | null> = {};
      for (const binding of action.parsed.bindings) bindings[binding.role] = binding.column;
      return {
        ...state,
        parsing: false,
        dataset: { parsed: action.parsed, bytes: action.bytes },
        roles: action.parsed.bindings.map(binding => binding.role),
        bindings,
        bindingsComplete: false,
        missingRoles: [],
        bindingsError: null,
      };
    }
    case 'parse_failed':
      return { ...state, parsing: false, datasetError: action.failure };
    case 'bindings_start':
      return { ...state, bindingsBusy: true, bindingsError: null, bindings: action.bindings };
    case 'bindings_done': {
      const roles = [...state.roles];
      for (const role of action.missingRoles) if (!roles.includes(role)) roles.push(role);
      return {
        ...state,
        bindingsBusy: false,
        roles,
        bindings: { ...Object.fromEntries(roles.map(role => [role, null])), ...action.bindings },
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
  if (err instanceof AgentApiError) return { code: err.code, ref: err.ref };
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

  // Open the session for the page's spec; the library is the URL's at mount
  // time, later switches go through `switchLibrary`. The page remounts this
  // hook (a `key`) for another spec or token, so the state starts fresh.
  const initialLibrary = useRef(library);
  useEffect(() => {
    mounted.current = true;
    let cancelled = false;
    let opened: string | null = null;
    const urls = blobUrls.current;
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
        } else {
          safeDispatch({ type: 'open_failed', phase: 'error', failure });
        }
      });
    return () => {
      cancelled = true;
      mounted.current = false;
      abortRef.current?.abort();
      // Purge the session, its dataset and its renders on the server.
      if (opened) void agentApi.deleteSession(token, opened).catch(() => undefined);
      for (const url of urls) URL.revokeObjectURL(url);
      urls.clear();
    };
  }, [specId, locale, token, safeDispatch]);

  // ---------------------------------------------------------------- dataset

  const applyBindings = useCallback(
    async (next: Record<string, string | null>, previous: Record<string, string | null>) => {
      const sid = stateRef.current.sessionId;
      if (!sid) return;
      safeDispatch({ type: 'bindings_start', bindings: next });
      const payload: Binding[] = Object.entries(next)
        .filter(([, column]) => column)
        .map(([role, column]) => ({ role, column }));
      try {
        const applied = await agentApi.putBindings(token, sid, payload);
        const bound: Record<string, string | null> = {};
        for (const binding of applied.bindings) bound[binding.role] = binding.column;
        safeDispatch({
          type: 'bindings_done',
          bindings: bound,
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
      if (!sid || !text.trim()) return;
      const bytes = utf8Bytes(text);
      const bucket = sizeBucket(bytes);
      if (bytes > MAX_DATASET_BYTES) {
        safeDispatch({ type: 'parse_failed', failure: { code: 'too_long', ref: null } });
        trackEvent('agent_data_parsed', { status: 'too_long', size_bucket: bucket });
        return;
      }
      safeDispatch({ type: 'parse_start' });
      try {
        const parsed = await agentApi.uploadDataset(token, sid, text);
        safeDispatch({ type: 'parse_done', parsed, bytes });
        trackEvent('agent_data_parsed', { status: 'ok', size_bucket: bucket });
        const defaults: Record<string, string | null> = {};
        for (const binding of parsed.bindings) defaults[binding.role] = binding.column;
        // Learn which required roles the defaults leave open (and store them,
        // which the parse already did: the PUT is idempotent).
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
      }
    },
    [token, safeDispatch, handleFailure, trackEvent, applyBindings]
  );

  const setBinding = useCallback(
    (role: string, column: string | null) => {
      const current = stateRef.current.bindings;
      const next: Record<string, string | null> = { ...current };
      // A column belongs to one role: taking it frees the role that held it.
      if (column) {
        for (const [other, held] of Object.entries(next)) {
          if (other !== role && held === column) next[other] = null;
        }
      }
      next[role] = column;
      void applyBindings(next, current);
    },
    [applyBindings]
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
          image: { state: 'failed', ...failure },
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

  /** The light and dark switch: render the other theme of a version (no model call), then show it. */
  const requestTheme = useCallback(
    async (number: number, theme: Theme) => {
      const sid = stateRef.current.sessionId;
      const version = stateRef.current.versions[number];
      if (!sid || !version) return;
      const current = version.images[theme];
      if (current && current.state !== 'failed') return;
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
        safeDispatch({
          type: 'version_image',
          number,
          theme,
          image: { state: 'failed', ...handleFailure(err) },
        });
      }
    },
    [token, safeDispatch, handleFailure, loadImage]
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
      const number = ++versionCounter.current;
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
      if (!sid || current.run || abortRef.current) return;
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
        if (!finished) {
          // The BFF always ends a turn with `done`; a stream without it was cut.
          addItem({ kind: 'error', code: 'upstream', ref: null });
        }
      } catch (err) {
        if (stoppedRef.current || isAbort(err)) {
          if (stoppedRef.current) addItem({ kind: 'notice', text: 'stopped' });
        } else {
          addItem({ kind: 'error', ...handleFailure(err) });
        }
      } finally {
        if (abortRef.current === controller) abortRef.current = null;
        safeDispatch({ type: 'run_end' });
      }
    },
    [token, safeDispatch, addItem, onEvent, handleFailure]
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

  /** Stop: the cancel route takes a waiting run out of the queue; the abort closes the stream. */
  const stop = useCallback(async () => {
    const sid = stateRef.current.sessionId;
    const controller = abortRef.current;
    if (!sid || !controller) return;
    stoppedRef.current = true;
    safeDispatch({ type: 'run_stopping' });
    try {
      await agentApi.cancel(token, sid);
    } catch {
      /* the abort below still ends the turn in this tab */
    }
    controller.abort();
  }, [token, safeDispatch]);

  // ---------------------------------------------------------------- library

  const switchLibrary = useCallback(
    async (next: string): Promise<boolean> => {
      const current = stateRef.current;
      const sid = current.sessionId;
      if (!sid || current.run || current.libraryBusy || next === current.library) return false;
      safeDispatch({ type: 'library_start' });
      try {
        const result = await agentApi.switchLibrary(token, sid, specId, next);
        safeDispatch({ type: 'library_done', library: next, eligibility: result.eligibility });
        return true;
      } catch (err) {
        const failure = handleFailure(err);
        safeDispatch({ type: 'library_failed', failure });
        addItem({ kind: 'error', ...failure });
        return false;
      }
    },
    [token, specId, safeDispatch, addItem, handleFailure]
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
