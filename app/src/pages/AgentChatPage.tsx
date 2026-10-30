/**
 * "Use with my data": the admin-only agent chat at `/debug/agent?spec=&library=&language=`.
 *
 * One column, chat first, two steps, data first. The data card is the first
 * turn of the thread: paste data (or ask in the chat for a curve, whose table
 * the assistant computes), read the assistant's summary of it in the next
 * turn, fix it in plain words if needed (each change updates the card in
 * place, with `.undo()`), check the preview and the role bindings and
 * `.confirm()` them at the card's foot (step 1). The card then collapses into
 * a pinned header at the top of the thread, `.show()` opens it again, and any
 * change to the data takes the page back to step 1 with the card open; the
 * header then stays as `! confirm again` and leads back to the card, and the
 * thread names what dropped the confirmation. In step 2 the composer's action
 * is `.create_plot()`: with an empty box it starts the first plot as it is,
 * with text the text goes as a turn and the assistant makes the first plot
 * with that change. Once the library has a plot, the composer refines in plain
 * words (`.send()`, on the latest version), and the same button becomes
 * `.start_over()`: a new plot from the catalogue plot with this data, without
 * the earlier changes; every shipped version gets a result card with the image,
 * the code and the downloads. A line above the column names the current step. The header
 * carries, next to the library pills, the session language chip
 * (`LanguageChip`): the language of the replies and of the text in the plot,
 * English until the first typed message or a choice sets another. The page
 * talks only to the BFF under `/debug/agent/*` (`src/lib/agent.ts`,
 * `src/hooks/useAgentSession.ts`).
 *
 * `.create_plot()` is in the composer as soon as there is data. Before the
 * confirmation it is the quiet button, and a click calls nothing: a notice
 * under the composer says to confirm the data first (or to decide on a table
 * read from text, whichever the data card asks for at the moment), with
 * `.show()`, which brings `.confirm()` (or `.use()`) into view and focuses it;
 * a hidden status region announces it. The notice clears once the data is
 * confirmed or a turn starts. The server's `data_unconfirmed` stays the
 * backstop.
 *
 * Work in flight is never silent: a turn without pipeline steps holds an
 * in-progress line in the thread (`ChatThread`), the progress timeline below
 * it shows only what the line does not (a `create_plot` run, a queue position,
 * pipeline steps), and the data card says why its controls wait.
 *
 * The header's `all` pill, after the library pills, is the admin's test run.
 * While it is pressed, the composer's create action is `.plot_all()`: the table
 * as it was pasted or opened, with the confirmed bindings, plotted in every
 * library of the header at once (`FanOut`), a session per library, at most
 * `AGENT_USER_MAX_RUNS` plots running, each through the normal run queue. This
 * session stays the data session, the message box waits (typed text would not
 * go along), and any library pill turns `all` off again. Data the assistant
 * changed or computed has no upload to replay, so `.plot_all()` waits for a
 * pasted or opened table and says so.
 *
 * Gates, outermost first:
 * 1. `CONFIG.features.agentChat` (build-time `VITE_ENABLE_AGENT_CHAT`): off, the
 *    route renders the 404 page and this chunk is not even built.
 * 2. The admin hint (`src/utils/adminAuth.ts`), or local development: without
 *    it the page asks for a sign-in on `/debug` first. The BFF's admin gate is
 *    the real check; a 401 or 403 from it clears the hint and shows the same
 *    notice.
 *
 * Design: docs/concepts/agent-network.md ("Frontend", "Request flow").
 */

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';

import { Link as RouterLink, useSearchParams } from 'react-router-dom';

import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_TO_LANG, LIBRARIES } from 'src/constants';
import { CONFIG } from 'src/global-config';
import {
  type BindingMap,
  type DatasetUpload,
  sessionBusy,
  useAgentSession,
} from 'src/hooks/useAgentSession';
import { useAnalytics } from 'src/hooks/useAnalytics';
import { useTheme } from 'src/hooks/useLayoutContext';
import { agentApi, browserLocale, DEFAULT_AGENT_LIBRARIES, MAX_MESSAGE_CHARS } from 'src/lib/agent';
import { apiGet, endpoints } from 'src/lib/api';
import { NotFoundPage } from 'src/pages/NotFoundPage';
import { paths, specPath } from 'src/routes/paths';
import { ChatFeedback } from 'src/sections/agent-chat/ChatFeedback';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { DATA_SUMMARY_ID, DataPanel } from 'src/sections/agent-chat/DataPanel';
import { FanOut } from 'src/sections/agent-chat/FanOut';
import { DEFAULT_USER_MAX_RUNS } from 'src/sections/agent-chat/fanoutRules';
import { LanguageChip } from 'src/sections/agent-chat/LanguageChip';
import { ERROR_TEXT } from 'src/sections/agent-chat/messages';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { SaveButton } from 'src/sections/agent-chat/SaveButton';
import { StepHeader } from 'src/sections/agent-chat/StepHeader';
import { inStep2, showsTimeline } from 'src/sections/agent-chat/steps';
import {
  actionButtonSx,
  bodyTextSx,
  ctaButtonSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  panelSx,
  smallText,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors, fontSize, proseLinkStyle, typography } from 'src/theme';
import { readAdminHint, readAdminToken, setAdminHint } from 'src/utils/adminAuth';

const SPEC_PATTERN = /^[a-z0-9-]{1,100}$/;
const OPEN_SOURCES = new Set(['plot_page']);
/** The chat column's width: a thread to read, and a plot that fits the screen with its composer. */
const COLUMN_MAX_WIDTH = 960;
/** What `.start_over()` does, unlike `.send()` beside it (the owner could not tell the two apart). */
const START_OVER_HELP = 'new from the catalogue plot, without your changes';
const START_OVER_HELP_ID = 'agent-start-over-help';
/** Why `.plot_all()` waits: the fan-out replays the upload, which only a paste or a file leaves. */
const PLOT_ALL_HINT =
  '.plot_all() takes a table as it was pasted or opened, not one the assistant changed or computed';
const PLOT_ALL_HINT_ID = 'agent-plot-all-hint';

/** A pill of the header's library group: a library, or `all` after them. */
const pillSx = (pressed: boolean) => ({
  ...actionButtonSx,
  border: '1px solid',
  borderColor: pressed ? 'var(--ink-muted)' : 'var(--rule)',
  color: pressed ? 'var(--ink)' : 'var(--ink-soft)',
  bgcolor: pressed ? 'var(--bg-elevated)' : 'transparent',
  '&:disabled': { cursor: 'default', opacity: pressed ? 1 : 0.45 },
});

/** What a click on `.create_plot()` before the confirmation asks for first. */
type CreateGate = 'confirm' | 'transcription';

/** The composer's notice after such a click, and where its `.show()` leads. */
const CREATE_GATE: Record<CreateGate, { text: string; action: string }> = {
  confirm: {
    text: 'confirm the data first · .confirm() sits at the foot of the data card',
    action: 'Go to the confirmation',
  },
  transcription: {
    text: 'decide on the table first · .use() or .discard() sit in the data card',
    action: 'Go to the table',
  },
};

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Box sx={{ py: 4, maxWidth: 560, mx: 'auto' }}>
      <SectionHeader prompt="❯" title={<em>{title}</em>} />
      <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>{children}</Box>
    </Box>
  );
}

function AdminRequired() {
  return (
    <Notice title="admin sign-in">
      this page is for admins. sign in on{' '}
      <Box component={RouterLink} to={paths.debug} sx={proseLinkStyle}>
        /debug
      </Box>{' '}
      first, then come back.
    </Notice>
  );
}

export function AgentChatPage() {
  const [params, setParams] = useSearchParams();
  const { trackPageview, trackEvent } = useAnalytics();
  const allowed = CONFIG.features.agentChat && (CONFIG.isDev || readAdminHint());

  const spec = params.get('spec') ?? '';
  const library = params.get('library') ?? '';
  // The language follows the library (the catalogue's pairing), never the query:
  // `?library=matplotlib&language=javascript` would otherwise pick the wrong
  // highlighter and a back link to a page that does not exist.
  const language = LIB_TO_LANG[library] ?? 'python';
  const valid = SPEC_PATTERN.test(spec) && (LIBRARIES as readonly string[]).includes(library);

  // `source` only says where the visitor came from; it is read once for
  // `agent_open` and dropped, so a reload counts as a direct open.
  const openTracked = useRef(false);
  useEffect(() => {
    if (!allowed || !valid || openTracked.current) return;
    openTracked.current = true;
    trackPageview('/debug/agent');
    const source = params.get('source');
    trackEvent('agent_open', {
      library,
      source: source && OPEN_SOURCES.has(source) ? source : 'direct',
      spec,
    });
    if (source) {
      const next = new URLSearchParams(params);
      next.delete('source');
      setParams(next, { replace: true });
    }
  }, [allowed, valid, params, setParams, library, spec, trackEvent, trackPageview]);

  if (!CONFIG.features.agentChat) return <NotFoundPage />;
  if (!allowed) return <AdminRequired />;
  if (!valid) {
    return (
      <Notice title="use with my data">
        open this page from a plot&apos;s <code>.adapt()</code> button: it needs a spec and a
        library, such as{' '}
        <Box
          component={RouterLink}
          to={paths.agentChat('scatter-basic', 'matplotlib', 'python')}
          sx={proseLinkStyle}
        >
          scatter-basic in matplotlib
        </Box>
        .
      </Notice>
    );
  }
  const token = readAdminToken();
  return (
    <AgentChat
      key={`${spec}|${token}`}
      specId={spec}
      library={library}
      language={language}
      token={token}
      onLibraryChange={next => {
        const nextParams = new URLSearchParams(params);
        nextParams.set('library', next);
        setParams(nextParams, { replace: true });
      }}
    />
  );
}

interface AgentChatProps {
  specId: string;
  library: string;
  language: string;
  token: string;
  onLibraryChange: (library: string) => void;
}

function AgentChat({ specId, library, language, token, onLibraryChange }: AgentChatProps) {
  const { trackEvent } = useAnalytics();
  const { isDark } = useTheme();
  const locale = useMemo(() => browserLocale(), []);
  const session = useAgentSession({ specId, library, locale, token });
  const { state } = session;
  const [draft, setDraft] = useState('');
  const [title, setTitle] = useState<string | null>(null);
  const [libraries, setLibraries] = useState<string[]>([...DEFAULT_AGENT_LIBRARIES]);
  // `.plot_all()`: the server's run limit, and what the open fan-out replays in every library.
  const [maxRuns, setMaxRuns] = useState(DEFAULT_USER_MAX_RUNS);
  // Both answers below are in (or failed): before that, the libraries and the limit are fallbacks.
  const [listsSettled, setListsSettled] = useState(false);
  const [fanOut, setFanOut] = useState<{
    upload: DatasetUpload;
    bindings: BindingMap;
    libraries: string[];
  } | null>(null);
  // The header's `all` pill: page state only, never in the URL.
  const [allPressed, setAllPressed] = useState(false);
  const allRef = useRef<HTMLButtonElement>(null);
  const fanOutRef = useRef<HTMLElement>(null);
  // Set by a key press on `.plot_all()`: the panel it opens takes the focus, once.
  const fanOutFocus = useRef(false);
  const tailRef = useRef<HTMLDivElement>(null);
  const messageRef = useRef<HTMLTextAreaElement>(null);
  const createRef = useRef<HTMLButtonElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  // The data card's `.confirm()` and a pending table's `.use()`, where the notice leads.
  const confirmRef = useRef<HTMLButtonElement>(null);
  const decisionRef = useRef<HTMLButtonElement>(null);
  // Set by the user's own `.confirm()`: the step change it brings moves the focus, once.
  const confirmFocus = useRef(false);
  // Whether the notice a click on `.create_plot()` before the confirmation opens
  // shows; what it asks for is read from the data card at render (`gate`).
  const [gateShown, setGateShown] = useState(false);

  // The spec's title and implemented libraries come from the public catalogue
  // API; the enabled libraries from the agents service. Both are best effort.
  useEffect(() => {
    const controller = new AbortController();
    let implemented: string[] | null = null;
    let enabled: string[] | null = null;
    const publish = () => {
      if (controller.signal.aborted) return;
      const base = enabled ?? [...DEFAULT_AGENT_LIBRARIES];
      setLibraries(implemented ? base.filter(lib => implemented!.includes(lib)) : base);
    };
    let pending = 2;
    const settle = () => {
      pending -= 1;
      if (pending === 0 && !controller.signal.aborted) setListsSettled(true);
    };
    apiGet<{ title: string; implementations: { library_id: string }[] }>(endpoints.spec(specId), {
      signal: controller.signal,
    })
      .then(spec => {
        if (controller.signal.aborted) return;
        setTitle(spec.title);
        implemented = spec.implementations.map(impl => impl.library_id);
        publish();
      })
      .catch(() => undefined)
      .finally(settle);
    agentApi
      .status(token)
      .then(status => {
        if (Array.isArray(status.libraries) && status.libraries.length) {
          enabled = status.libraries;
          publish();
        }
        if (typeof status.user_max_runs === 'number' && status.user_max_runs > 0) {
          setMaxRuns(status.user_max_runs);
        }
      })
      .catch(() => undefined)
      .finally(settle);
    return () => controller.abort();
  }, [specId, token]);

  useEffect(() => {
    if (state.phase === 'unauthorized') setAdminHint(false);
  }, [state.phase]);

  // The progress and the replies arrive at the foot of the thread, below the
  // data card: bring the foot into view when a turn starts.
  const running = !!state.run;
  useEffect(() => {
    if (running) tailRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
  }, [running]);

  // The notice before the confirmation opens under the composer, which a turn's
  // start leaves at the window's lower edge: bring it in, without moving the focus.
  // Only when it opens: a change of its wording follows a decision in the data
  // card, where the user is, and must not pull the window to the foot.
  const gateRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (gateShown) gateRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
  }, [gateShown]);

  // A turn, a theme render, a parse, an undo or a binding change in flight: the
  // server runs one at a time and would refuse or race a second.
  const busy = sessionBusy(state);
  // The session could not open for this pair: other libraries are links instead.
  const reopen = state.phase === 'ineligible' || state.phase === 'error';
  // Step 2: the data and its bindings are confirmed, and no table read from text waits.
  const step2 = inStep2(state);
  const canCreate =
    state.phase === 'ready' && step2 && state.bindingsComplete && !state.transcription && !busy;
  // Until this library has a plot, `.create_plot()` is the composer's action and
  // text in the box goes with it; the pipeline counts versions per library too.
  const hasPlot = Object.values(state.versions).some(version => version.library === state.library);
  const firstPlot = step2 && !hasPlot;
  // `.plot_all()`: the stored upload, as it was posted, plotted in every library at once. Data
  // the assistant changed or computed has no upload, so the fan-out never plots other data.
  const upload = state.dataset?.upload;
  // The `all` pill only once the libraries and the limit are the server's: a snapshot of the
  // fallbacks would leave libraries out or start more runs than the server takes (`run_limit`).
  const offerAll = listsSettled && libraries.length > 1 && !reopen;
  const plotAll = allPressed && offerAll;
  // The notice before the confirmation is done once the data is confirmed or a turn starts.
  // Adjusted while rendering, React's pattern for state that follows other state.
  if (gateShown && (step2 || running)) setGateShown(false);
  // What the notice asks for first, from the data card as it is now: a table read
  // from text waits for `.use()` or `.discard()`, anything else for `.confirm()`. A
  // table that arrives or is discarded after the click changes the text, the
  // announcement and the target of `.show()` with it, so none names a button
  // that is gone or waits.
  const gate: CreateGate | null = gateShown
    ? state.transcription
      ? 'transcription'
      : 'confirm'
    : null;

  // The user's own `.confirm()` collapsed the card and took its focused button
  // away. Before the first plot the keyboard continues at `.create_plot()` (or
  // `.plot_all()`), the step's next action (a button, so a phone opens no
  // keyboard), unless it waits; otherwise at the pinned header's toggle, since
  // a fresh run must not be one key press away by accident; it is in view where
  // it sticks, so the focus scrolls nothing. Only for that confirmation, and
  // only while nothing else holds the focus: a step 2 that a turn's sync brings
  // back never takes it from the composer. A layout effect, so the focus has
  // moved by the time the button shows.
  useLayoutEffect(() => {
    if (!confirmFocus.current || state.confirmBusy) return;
    confirmFocus.current = false;
    const active = document.activeElement;
    if (!step2 || (active && active !== document.body)) return;
    if (firstPlot && !createRef.current?.disabled) createRef.current?.focus();
    else toggleRef.current?.focus({ preventScroll: true });
  }, [state.confirmBusy, step2, firstPlot]);

  // A key press on `.plot_all()` continues in the panel it opened: the button waits while
  // the panel is open, and the panel is where the plots come in.
  useEffect(() => {
    if (!fanOut || !fanOutFocus.current) return;
    fanOutFocus.current = false;
    fanOutRef.current?.focus();
  }, [fanOut]);

  /**
   * A key press on a composer button that a run replaces with `.stop()` (Enter
   * and Space fire a click with `detail` 0): the focus continues in the message
   * box, where a second press sends nothing, and stays there when the run ends.
   * A pointer click moves no focus, so a phone opens no keyboard.
   */
  const keepKeyboardFocus = (event: React.MouseEvent) => {
    if (event.detail === 0) messageRef.current?.focus();
  };

  /**
   * The composer's action. The first plot: an empty box starts it as it is
   * (`create_plot`), text goes as the user's turn, and the assistant makes the
   * plot with that change. Otherwise the text is a turn about the data or the plot.
   * While `all` is pressed nothing goes: the fan-out takes no text.
   */
  const handleSend = useCallback(
    (event?: React.FormEvent) => {
      event?.preventDefault();
      const text = draft.trim();
      if (busy || plotAll) return;
      if (firstPlot && !text) {
        if (canCreate) void session.createPlot();
        return;
      }
      if (!text || (firstPlot && !canCreate)) return;
      void session.sendMessage(text);
      setDraft('');
    },
    [draft, busy, plotAll, firstPlot, canCreate, session]
  );

  const handleLibrary = useCallback(
    async (next: string) => {
      if (await session.switchLibrary(next)) onLibraryChange(next);
    },
    [session, onLibraryChange]
  );

  /**
   * A library pill. While `all` is pressed, any pill turns it off: the session's
   * own library only that, and the keyboard continues at `all`, since the pill
   * pressed now is disabled; another library switches as it would without it.
   */
  const handlePill = (next: string) => {
    if (plotAll) {
      setAllPressed(false);
      if (next === state.library) {
        allRef.current?.focus();
        return;
      }
    }
    void handleLibrary(next);
  };

  /**
   * `.plot_all()`, the composer's action while `all` is pressed: the stored
   * upload with the confirmed bindings, in every library of the header at once.
   * Before the confirmation it calls nothing and shows the notice, as the quiet
   * `.create_plot()` does.
   */
  const handlePlotAll = (event: React.MouseEvent) => {
    if (!step2) {
      setGateShown(true);
      return;
    }
    if (!upload) return;
    fanOutFocus.current = event.detail === 0;
    setFanOut({ upload, bindings: state.bindings, libraries: [...libraries] });
  };

  /**
   * The quiet `.create_plot()` before the confirmation: no call, the server
   * would answer `data_unconfirmed`; the notice under the composer says what
   * comes first. The click moves no focus.
   */
  const handleCreate = (event: React.MouseEvent) => {
    if (!step2) {
      setGateShown(true);
      return;
    }
    keepKeyboardFocus(event);
    void session.createPlot();
  };

  /**
   * The notice's `.show()`: bring the button the notice names into view, below
   * the pinned header (the page's scroll padding), and move the keyboard focus
   * to it. A disabled button (bindings incomplete, something in flight) cannot
   * take the focus, so it is only scrolled to.
   */
  const goToGate = () => {
    const target = (gate === 'transcription' ? decisionRef : confirmRef).current;
    target?.scrollIntoView?.({ behavior: 'smooth', block: 'center' });
    if (target && !target.disabled) target.focus({ preventScroll: true });
  };

  if (state.phase === 'unauthorized') return <AdminRequired />;

  const backHref = specPath(specId, language, state.library);
  const header = (
    <>
      <SectionHeader
        prompt="❯"
        title={
          <>
            agent · <em>use with my data</em>
          </>
        }
      />
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          columnGap: 2,
          rowGap: 1,
          mt: -2,
          mb: 3,
        }}
      >
        <Box
          component={RouterLink}
          to={backHref}
          sx={{
            fontFamily: typography.mono,
            fontSize: fontSize.md,
            color: 'var(--ink-soft)',
            textDecoration: 'none',
            '&:hover': { color: colors.primary },
            overflowWrap: 'anywhere',
          }}
        >
          ← {title ?? specId}
        </Box>
        <Box
          role="group"
          aria-label="Library"
          sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, alignItems: 'center' }}
        >
          <Box component="span" sx={{ ...labelSx, mr: 0.5 }}>
            {language} ·
          </Box>
          {libraries.map(lib => {
            const active = lib === state.library;
            // While `all` is pressed it shows as the pressed pill; the session stays this one's.
            const pressed = active && !plotAll;
            // No session to switch: another library opens the page anew, with
            // its own session (a full navigation, like the `.adapt()` button).
            if (!active && reopen) {
              return (
                <Box
                  key={lib}
                  component="a"
                  href={paths.agentChat(specId, lib, language)}
                  sx={{ ...pillSx(false), textDecoration: 'none' }}
                >
                  {lib}
                </Box>
              );
            }
            return (
              <Box
                key={lib}
                component="button"
                type="button"
                aria-pressed={pressed}
                disabled={pressed || busy || state.phase !== 'ready'}
                onClick={() => handlePill(lib)}
                sx={pillSx(pressed)}
              >
                {lib}
              </Box>
            );
          })}
          {offerAll && (
            <Box
              component="button"
              type="button"
              ref={allRef}
              aria-pressed={plotAll}
              aria-label="All libraries"
              disabled={busy || !!fanOut || state.phase !== 'ready'}
              onClick={() => setAllPressed(!plotAll)}
              sx={pillSx(plotAll)}
            >
              all
            </Box>
          )}
        </Box>
        {/* The session language of the replies and the plot text; without a session there is none. */}
        {!reopen && (
          <LanguageChip
            value={state.plotLanguage}
            disabled={state.phase !== 'ready' || !state.sessionId || busy}
            onSet={session.setLanguage}
          />
        )}
        {/* `.save()` downloads the session; without one (ineligible, error) there is nothing to save. */}
        {!reopen && (
          <SaveButton
            disabled={state.phase !== 'ready' || !state.sessionId || busy}
            onSave={session.saveSession}
          />
        )}
      </Box>
    </>
  );

  if (state.phase === 'opening' || state.phase === 'ineligible' || state.phase === 'error') {
    return (
      <Box sx={{ py: 2, maxWidth: COLUMN_MAX_WIDTH, mx: 'auto' }}>
        {header}
        {state.phase === 'opening' ? (
          <Box sx={labelSx}>opening a session…</Box>
        ) : (
          <Box role="alert" sx={{ borderLeft: `2px solid ${colors.error}`, pl: 1.5 }}>
            <Box sx={{ ...labelSx, color: colors.error }}>
              {state.phase === 'ineligible' ? 'not eligible' : `error · ${state.failure?.code}`}
              {state.failure?.ref ? ` · ref ${state.failure.ref}` : ''}
            </Box>
            <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
              {state.phase === 'ineligible'
                ? 'this plot cannot be adapted in this library yet; pick another library above.'
                : state.failure?.code === 'not_enabled'
                  ? 'the agent chat is switched off on this server (AGENT_ENABLED).'
                  : (ERROR_TEXT[state.failure?.code ?? ''] ?? 'the session could not be opened.')}
              {state.phase === 'error' && <ReloadHint code={state.failure?.code} />}
            </Box>
          </Box>
        )}
      </Box>
    );
  }

  return (
    <>
      <>
        <title>{`agent · ${specId} | anyplot.ai`}</title>
        <meta name="robots" content="noindex, nofollow" />
      </>
      {/* `colorScheme` gives the native controls (scrollbars, select menus) the site theme. */}
      <Box
        sx={{
          py: 2,
          maxWidth: COLUMN_MAX_WIDTH,
          mx: 'auto',
          colorScheme: isDark ? 'dark' : 'light',
        }}
      >
        {header}
        <StepHeader current={step2 ? 2 : 1} />
        <Box
          component="section"
          aria-label="Chat"
          sx={{ ...panelSx, display: 'flex', flexDirection: 'column', gap: 2 }}
        >
          <Box sx={{ ...labelSx, mb: -0.5 }}># chat</Box>

          {/* The first turn: the data card, once confirmed the pinned header. A sibling of
              the thread, so the header sticks over all of it. */}
          <DataPanel
            state={state}
            onParse={(text, source, table) => void session.parseData(text, false, source, table)}
            onConfirmTranscription={() => void session.confirmTranscription()}
            onTrack={trackEvent}
            onConvert={session.convertFile}
            onDiscardTranscription={session.discardTranscription}
            onSendFormula={() => void session.sendFormula()}
            onBind={session.setBinding}
            onConfirmData={() => {
              confirmFocus.current = true;
              void session.confirmData();
            }}
            onUndo={() => void session.undoData()}
            onToLong={() => void session.toLongData()}
            toggleRef={toggleRef}
            confirmRef={confirmRef}
            decisionRef={decisionRef}
          />

          {state.items.length === 0 && !state.run && (
            <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
              paste your data above, or ask here for a curve: &quot;y = sin(x), x from{' '}
              <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
                -pi
              </Box>{' '}
              to pi&quot;, and the assistant computes the table. it sums your data up here, and you
              can ask it to fix the data in plain words, such as &quot;read Anteil as numbers&quot;
              or &quot;sum per month&quot;. check the preview and the bindings, confirm, then{' '}
              <code>.create_plot()</code>, with a note first if the plot should do something
              differently. afterwards, ask for changes to the plot: &quot;log scale on y&quot;,
              &quot;dark version&quot;, &quot;label the outliers&quot;.
            </Box>
          )}

          <ChatThread
            state={state}
            specId={specId}
            language={language}
            onRequestTheme={(version, theme) => void session.requestTheme(version, theme)}
            onFetchArtifact={session.fetchArtifact}
            onTrack={trackEvent}
            onOutcome={session.reportOutcome}
            onSendFeedback={session.sendFeedback}
          />

          <Box
            ref={tailRef}
            sx={{ display: 'flex', flexDirection: 'column', gap: 2, scrollMarginBottom: 16 }}
          >
            {/* At the foot with the progress, where a long thread keeps it in view. */}
            {state.run?.queue && (
              <Box
                role="status"
                data-testid="queue-counter"
                aria-label={`Queued: position ${state.run.queue.position}, ${state.run.queue.waiting} waiting`}
                sx={{
                  alignSelf: 'flex-end',
                  mb: -1,
                  fontFamily: typography.mono,
                  fontSize: smallText,
                  color: 'var(--ink)',
                  bgcolor: 'var(--bg-elevated)',
                  border: '1px solid var(--rule)',
                  borderRadius: 1,
                  px: 1,
                  py: 0.25,
                  whiteSpace: 'nowrap',
                }}
              >
                queue {state.run.queue.position}/{state.run.queue.waiting}
              </Box>
            )}
            {/* A turn without pipeline steps has its in-progress line in the thread instead. */}
            {state.run && showsTimeline(state) && <ProgressTimeline run={state.run} />}

            {firstPlot && (
              <Box id="agent-create-line" sx={{ ...labelSx, color: 'var(--ink-soft)', mb: -1 }}>
                {plotAll
                  ? `# step 2 — plot the table as it is in all ${libraries.length} libraries at once`
                  : '# step 2 — create the plot as it is, or say first what it should do differently'}
              </Box>
            )}
            <Box
              component="form"
              onSubmit={handleSend}
              sx={{ display: 'flex', gap: 1, alignItems: 'flex-end', flexWrap: 'wrap' }}
            >
              <Box
                component="textarea"
                ref={messageRef}
                aria-label="Message"
                placeholder={
                  // Step 1 talks about the data, step 2 about the plot. Without
                  // data, the chat is the other way to get some: a formula. While
                  // `all` is pressed the box waits: the fan-out takes no text.
                  plotAll
                    ? 'all libraries: the table goes as it is · turn all off to chat'
                    : !state.dataset
                      ? 'ask for a curve: "y = sin(x), x from -pi to pi"'
                      : !step2
                        ? 'ask about your data, or for a fix: "sum per month"'
                        : firstPlot
                          ? 'optional: what the first plot should do differently'
                          : 'ask about this plot, or ask for a change'
                }
                value={draft}
                maxLength={MAX_MESSAGE_CHARS}
                rows={2}
                disabled={state.phase !== 'ready' || plotAll}
                onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setDraft(event.target.value)
                }
                onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
                  // Enter sends text; an empty box creates nothing by accident.
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    if (draft.trim()) handleSend();
                  }
                }}
                sx={{ ...nativeControlSx, flex: '1 1 240px', resize: 'vertical' }}
              />
              {/* Own keys: the button a run replaces never turns into `.stop()` in place,
                  with a focus that a second key press would spend on stopping the run. */}
              {running ? (
                <Box
                  key="stop"
                  component="button"
                  type="button"
                  onClick={(event: React.MouseEvent) => {
                    keepKeyboardFocus(event);
                    void session.stop();
                  }}
                  disabled={state.run?.stopping}
                  aria-label="Stop"
                  sx={{
                    ...ghostButtonSx,
                    color: colors.error,
                    '&:hover:not(:disabled)': { color: colors.error, borderColor: colors.error },
                  }}
                >
                  {state.run?.stopping ? '.stop() …' : '.stop()'}
                </Box>
              ) : plotAll ? (
                <>
                  {/* The create action of the branch below, for every library at once: the CTA
                      before the first plot, the quiet button otherwise, and before the
                      confirmation a click shows the notice. It waits while the panel is open. */}
                  {state.dataset && (
                    <Box
                      key="plot-all"
                      component="button"
                      type="button"
                      ref={createRef}
                      onClick={handlePlotAll}
                      disabled={
                        !upload ||
                        !!fanOut ||
                        (step2 ? !canCreate : state.phase !== 'ready' || busy)
                      }
                      aria-label="Plot in all libraries"
                      aria-describedby={
                        [
                          step2 ? DATA_SUMMARY_ID : gate ? 'agent-create-gate' : null,
                          firstPlot ? 'agent-create-line' : null,
                          upload ? null : PLOT_ALL_HINT_ID,
                        ]
                          .filter(Boolean)
                          .join(' ') || undefined
                      }
                      sx={firstPlot ? ctaButtonSx : actionButtonSx}
                    >
                      .plot_all()
                    </Box>
                  )}
                  {!firstPlot && (
                    <Box component="button" type="button" disabled sx={ghostButtonSx}>
                      .send()
                    </Box>
                  )}
                </>
              ) : firstPlot ? (
                <Box
                  key="create"
                  component="button"
                  type="submit"
                  ref={createRef}
                  onClick={keepKeyboardFocus}
                  disabled={!canCreate}
                  aria-label="Create plot"
                  aria-describedby={`${DATA_SUMMARY_ID} agent-create-line`}
                  sx={ctaButtonSx}
                >
                  .create_plot()
                </Box>
              ) : (
                <>
                  {/* Step 2 after a plot: start over from the catalogue plot with this data.
                      Step 1: the step is visible from the foot too, and a click says what
                      comes first instead of calling the server. */}
                  {state.dataset && (
                    <Box
                      component="button"
                      type="button"
                      ref={createRef}
                      onClick={handleCreate}
                      disabled={step2 ? !canCreate : state.phase !== 'ready' || busy}
                      // Once this library has a plot, the button starts over from the
                      // catalogue plot; `.send()` beside it changes the latest version.
                      aria-label={hasPlot ? 'Start over' : 'Create plot'}
                      title={hasPlot ? START_OVER_HELP : undefined}
                      aria-describedby={
                        [
                          hasPlot ? START_OVER_HELP_ID : null,
                          step2 ? DATA_SUMMARY_ID : gate ? 'agent-create-gate' : null,
                        ]
                          .filter(Boolean)
                          .join(' ') || undefined
                      }
                      sx={actionButtonSx}
                    >
                      {hasPlot ? '.start_over()' : '.create_plot()'}
                    </Box>
                  )}
                  {state.dataset && hasPlot && (
                    <Box component="span" id={START_OVER_HELP_ID} sx={visuallyHiddenSx}>
                      {START_OVER_HELP}
                    </Box>
                  )}
                  <Box
                    component="button"
                    type="submit"
                    onClick={keepKeyboardFocus}
                    disabled={!draft.trim() || state.phase !== 'ready' || busy}
                    sx={ghostButtonSx}
                  >
                    .send()
                  </Box>
                </>
              )}
            </Box>
            {plotAll && state.dataset && !upload && (
              <Box
                id={PLOT_ALL_HINT_ID}
                data-testid="plot-all-hint"
                sx={{ ...labelSx, color: 'var(--ink-soft)', mt: -1 }}
              >
                # {PLOT_ALL_HINT}
              </Box>
            )}
            {/* No role on the visible notice: the status box below speaks it, once. */}
            {gate && (
              <Box
                ref={gateRef}
                data-testid="create-gate"
                sx={{
                  mt: -1,
                  borderLeft: `3px solid ${colors.warning}`,
                  pl: 1.5,
                  display: 'flex',
                  flexWrap: 'wrap',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  columnGap: 1,
                  rowGap: 0.75,
                }}
              >
                <Box
                  id="agent-create-gate"
                  sx={{ ...labelSx, color: 'var(--ink)', flex: '1 1 220px', lineHeight: 1.6 }}
                >
                  # {CREATE_GATE[gate].text}
                </Box>
                <Box
                  component="button"
                  type="button"
                  onClick={goToGate}
                  aria-label={CREATE_GATE[gate].action}
                  sx={actionButtonSx}
                >
                  .show()
                </Box>
              </Box>
            )}
            <Box role="status" data-testid="composer-status" sx={visuallyHiddenSx}>
              {gate ? CREATE_GATE[gate].text : ''}
            </Box>
            {draft.length > MAX_MESSAGE_CHARS * 0.9 && (
              <Box sx={{ ...labelSx, mt: -1 }}>
                {draft.length} / {MAX_MESSAGE_CHARS}
              </Box>
            )}
            {/* A chat without a plot has no result card to report on: its own control. Not while a
                turn runs, which may still bring the plot; a sent record stays in view. */}
            {(state.chatFeedback ||
              (state.items.length > 0 &&
                !state.run &&
                Object.keys(state.versions).length === 0)) && (
              <ChatFeedback
                sent={state.chatFeedback}
                dataAvailable={!!state.dataset}
                onSend={session.sendFeedback}
              />
            )}
          </Box>
        </Box>
        {fanOut && (
          <FanOut
            panelRef={fanOutRef}
            specId={specId}
            libraries={fanOut.libraries}
            locale={locale}
            token={token}
            upload={fanOut.upload}
            bindings={fanOut.bindings}
            maxRuns={maxRuns}
            onClose={() => setFanOut(null)}
          />
        )}
      </Box>
    </>
  );
}
