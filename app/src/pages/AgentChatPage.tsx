/**
 * "Use with my data": the admin-only agent chat at `/debug/agent?spec=&library=&language=`,
 * plus `&all=1` while the library menu's `all` is pressed. The query follows the
 * session: a library switch writes `library` and its `language`.
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
 * `.start_over()`: a new plot from the catalogue plot with this data, the way
 * out of code that went wrong, which keeps the remembered decisions (owner
 * decision of 2026-11-02); every shipped version gets a result card with the image,
 * the code and the downloads. A line above the column names the current step. The header
 * carries the library menu (`LibraryChip`, since 2026-11-02 in place of a pill
 * per library: the libraries grouped by language, `all` for the admin) and,
 * next to it, the session language chip (`LanguageChip`): the language of the
 * replies and of the text in the plot, English until the first typed message
 * or a choice sets another. The page talks only to the BFF under
 * `/debug/agent/*` (`src/lib/agent.ts`, `src/hooks/useAgentSession.ts`).
 *
 * A library switch keeps the data, the bindings, their confirmation, the
 * language and the plot memory. When its answer offers it, the composer's
 * create action becomes "plot in seaborn with your 3 decisions" (`carry_plot`):
 * the plot in the new library from its catalogue code, with the decisions the
 * user made so far; picking a library from the menu runs nothing, so browsing
 * costs nothing. `.create_plot()` (or `.start_over()` once the library has a
 * plot) stays beside it as the quiet plot from the catalogue code, which keeps
 * the decisions too but not the switch's carry (the theme asked for before),
 * and text typed into the box goes as a normal turn, which the server also
 * gives the decisions. The offer ends once a plot in that library ships, or
 * with a switch whose answer has none. The decisions themselves stand above the
 * composer as the remembered list (`Remembered`), each with `.forget()`, and
 * `.forget_all()` for a blank start: nothing else clears them.
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
 * The library menu's `all`, after the libraries, is the admin's test run.
 * While it is pressed, the composer's create action is `.plot_all()`: the
 * confirmed data, with the confirmed bindings, plotted in every library of the
 * header at once (`FanOut`), a session per library into which the server copies
 * this session's confirmed version, whatever its origin (pasted, opened,
 * computed or changed by the assistant), at most `AGENT_USER_MAX_RUNS` plots
 * running, each through the normal run queue. This session stays the data
 * session; in step 2 the message box waits (typed text would not go along) and
 * a line above it says so, while in step 1 the chat about the data goes on as
 * without `all`. Any library picked in the menu turns `all` off again (the
 * library in use only that); while the panel is open, neither the menu nor the
 * data card change anything, so every library copies the same confirmed data.
 * `all` is in the URL as `&all=1`, so a reload presses it again once the
 * libraries are known.
 *
 * The session itself is not in the URL and nothing restores it: while it holds
 * data, a plot or work in flight, a reload, a closed tab or a link off the page
 * asks first (`useLeaveWarning`: the browser's `beforeunload` dialog, and for a
 * link inside the site or the back button the router's blocker with a
 * `confirm`). The page's own query edits pass, and so do the reload links
 * after an expired session or no answer (`ReloadHint`), which the user clicked
 * on purpose.
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
  carryDecisions,
  type DatasetUpload,
  sessionBusy,
  sessionHoldsWork,
  useAgentSession,
} from 'src/hooks/useAgentSession';
import { useAnalytics } from 'src/hooks/useAnalytics';
import { useTheme } from 'src/hooks/useLayoutContext';
import { useLeaveWarning } from 'src/hooks/useLeaveWarning';
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
import { LibraryChip } from 'src/sections/agent-chat/LibraryChip';
import {
  carryActionText,
  ERROR_TEXT,
  LEAVE_TEXT,
  servicePausedText,
} from 'src/sections/agent-chat/messages';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { Remembered } from 'src/sections/agent-chat/Remembered';
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
/**
 * What `.start_over()` does, unlike `.send()` beside it (the owner could not tell the two apart),
 * and the quiet `.create_plot()` beside the offer after a switch: the catalogue code again, with the
 * remembered decisions, which only the user clears (owner decision of 2026-11-02).
 */
const START_OVER_HELP = 'new from the catalogue plot; keeps your remembered decisions';
const START_OVER_HELP_ID = 'agent-start-over-help';

/** The first of these controls that can take the focus now, in order of preference. */
function firstEnabled(...controls: (HTMLButtonElement | HTMLTextAreaElement | null)[]) {
  return controls.find(control => control && !control.disabled) ?? null;
}

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
  const allInUrl = params.get('all') === '1';

  // Every edit of the query starts from the latest one, also an edit made after an await (a
  // library switch), so one edit never brings back what another removed (`all`).
  const paramsRef = useRef(params);
  paramsRef.current = params;
  const editParams = useCallback(
    (edit: (next: URLSearchParams) => void) => {
      const next = new URLSearchParams(paramsRef.current);
      edit(next);
      if (next.toString() === paramsRef.current.toString()) return;
      paramsRef.current = next;
      setParams(next, { replace: true });
    },
    [setParams]
  );
  const onLibraryChange = useCallback(
    (next: string) =>
      editParams(query => {
        query.set('library', next);
        query.set('language', LIB_TO_LANG[next] ?? 'python');
      }),
    [editParams]
  );
  const onAllChange = useCallback(
    (pressed: boolean) =>
      editParams(query => (pressed ? query.set('all', '1') : query.delete('all'))),
    [editParams]
  );

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
      allInUrl={allInUrl}
      onLibraryChange={onLibraryChange}
      onAllChange={onAllChange}
    />
  );
}

interface AgentChatProps {
  specId: string;
  library: string;
  language: string;
  token: string;
  /** `&all=1` at the mount: the menu's `all` starts pressed, once the libraries are known. */
  allInUrl: boolean;
  onLibraryChange: (library: string) => void;
  /** The menu's `all` as it is now, for the URL. */
  onAllChange: (pressed: boolean) => void;
}

function AgentChat({
  specId,
  library,
  language,
  token,
  allInUrl,
  onLibraryChange,
  onAllChange,
}: AgentChatProps) {
  const { trackEvent } = useAnalytics();
  const { isDark } = useTheme();
  const locale = useMemo(() => browserLocale(), []);
  const session = useAgentSession({ specId, library, locale, token });
  const { state } = session;
  const [draft, setDraft] = useState('');
  const [title, setTitle] = useState<string | null>(null);
  const [libraries, setLibraries] = useState<string[]>([...DEFAULT_AGENT_LIBRARIES]);
  // `.plot_all()`: the caller's own run cap (`user_max_runs`, 5 for an admin), and the session whose
  // confirmed data the open fan-out copies.
  const [maxRuns, setMaxRuns] = useState(DEFAULT_USER_MAX_RUNS);
  // Both answers below are in (or failed): before that, the libraries and the limit are fallbacks.
  const [listsSettled, setListsSettled] = useState(false);
  // The service's day budget is spent: until when (ISO), for the note above the composer.
  const [pausedUntil, setPausedUntil] = useState<string | null>(null);
  const [fanOut, setFanOut] = useState<{
    sourceSession: string;
    upload?: DatasetUpload;
    bindings: BindingMap;
    libraries: string[];
  } | null>(null);
  // The library menu's `all`, in the URL as `&all=1` (`onAllChange`). Pressed from the URL, it
  // takes effect only once `offerAll` holds (`plotAll`), when the libraries are the server's.
  const [allPressed, setAllPressed] = useState(allInUrl);
  // The library menu's chip, which holds `all` since 2026-11-02.
  const libraryRef = useRef<HTMLButtonElement>(null);
  const fanOutRef = useRef<HTMLElement>(null);
  // Set by a key press on `.plot_all()`: the panel it opens takes the focus, once.
  const fanOutFocus = useRef(false);
  // Set by the panel's `.close()`, which takes its focused button away: the focus returns, once.
  const fanOutReturn = useRef(false);
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
        if (
          status.paused === true &&
          typeof status.resets_at === 'string' &&
          Date.parse(status.resets_at) > Date.now()
        ) {
          setPausedUntil(status.resets_at);
        }
      })
      .catch(() => undefined)
      .finally(settle);
    return () => controller.abort();
  }, [specId, token]);

  // The pause ends with the service's new day: the note goes at that moment, without a reload.
  useEffect(() => {
    if (!pausedUntil) return;
    const timer = window.setTimeout(
      () => setPausedUntil(null),
      Math.max(0, Date.parse(pausedUntil) - Date.now())
    );
    return () => window.clearTimeout(timer);
  }, [pausedUntil]);

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

  // Data, a plot or work in flight: a reload, a closed tab or a link off the page asks first,
  // since nothing restores the session. The fan-out's panel opens only on this session's
  // confirmed data, so its sessions are covered too.
  useLeaveWarning(sessionHoldsWork(state), LEAVE_TEXT);

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
  // The server files a version under its (spec, library) pair; the spec cannot
  // change in a session yet, so the library alone tells the pair.
  const hasPlot = Object.values(state.versions).some(version => version.library === state.library);
  const firstPlot = step2 && !hasPlot;
  // `all` in the menu only once the libraries and the limit are the server's: a snapshot of the
  // fallbacks would leave libraries out or start more runs than the server takes (`run_limit`).
  const offerAll = listsSettled && libraries.length > 1 && !reopen;
  const plotAll = allPressed && offerAll;
  // The chat waits only where `.plot_all()` is the action, in step 2: the fan-out takes no
  // text. Before it, with or without data, the box talks about the data as without `all`.
  const chatLocked = plotAll && step2;
  // After a switch whose answer offered it: the plot in this library with the remembered
  // decisions (`carry_plot`), the composer's create action. Not while `all` is pressed, whose
  // fan-out makes fresh plots everywhere.
  const carry =
    state.carryOffer?.target.library === state.library && state.dataset && !plotAll
      ? state.carryOffer
      : null;
  const carryText = carry
    ? carryActionText(carry.target.library, carryDecisions(carry, state.memory))
    : '';

  // `&all=1` follows `all`, so a reload presses it again. Only from the lists' answers on:
  // before them `all` is not offered yet, and one pressed from the URL waits for them.
  useEffect(() => {
    if (listsSettled) onAllChange(plotAll);
  }, [listsSettled, plotAll, onAllChange]);
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

  // The panel's `.close()` went with the panel: the focus returns to `.plot_all()`, which
  // opened it, or, while that waits, to the library menu or the message box.
  useEffect(() => {
    if (fanOut || !fanOutReturn.current) return;
    fanOutReturn.current = false;
    firstEnabled(createRef.current, libraryRef.current, messageRef.current)?.focus();
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
   * (`create_plot`), or, after a switch that offered it, with the remembered
   * decisions (`carry_plot`); text goes as the user's turn, and the assistant
   * makes the plot with that change (the server gives it the decisions too).
   * Otherwise the text is a turn about the data or the plot. While `all` is
   * pressed in step 2 nothing goes: the fan-out takes no text.
   */
  const handleSend = useCallback(
    (event?: React.FormEvent) => {
      event?.preventDefault();
      const text = draft.trim();
      if (busy || chatLocked) return;
      if (firstPlot && !text) {
        if (canCreate) void (carry ? session.carryPlot() : session.createPlot());
        return;
      }
      if (!text || (firstPlot && !canCreate)) return;
      void session.sendMessage(text);
      setDraft('');
    },
    [draft, busy, chatLocked, firstPlot, canCreate, carry, session]
  );

  /**
   * A library picked in the menu. While `all` is pressed, any pick turns it
   * off: the library in use only that; another library switches as it would
   * without it. The URL follows a switch the server took; a refused one
   * rejects, and the menu shows why under its chip.
   */
  const handlePick = useCallback(
    async (next: string) => {
      if (plotAll) {
        setAllPressed(false);
        if (next === state.library) return;
      }
      if (await session.switchLibrary(next)) onLibraryChange(next);
    },
    [plotAll, state.library, session, onLibraryChange]
  );

  // A switch the user asked for in the chat ("make it in seaborn", `done.switch`): once the turn
  // is over the page switches as the menu does, and with `plot` makes the plot there at once
  // with the user's decisions (`carry_plot`), without a second click (owner decision of
  // 2026-11-02). The intent is noted before the switch, so the render that brings the new
  // library finds it; the carry runs only on confirmed data, else the composer offers it.
  const carryNext = useRef<string | null>(null);
  useEffect(() => {
    const request = state.chatSwitch;
    if (!request || running || busy) return;
    if (request.plot) carryNext.current = request.library;
    void session.followChatSwitch().then(switched => {
      if (switched) onLibraryChange(switched.library);
      else if (carryNext.current === request.library) carryNext.current = null;
    });
  }, [state.chatSwitch, running, busy, session, onLibraryChange]);
  useEffect(() => {
    if (carryNext.current === null || state.library !== carryNext.current || running || busy)
      return;
    carryNext.current = null;
    if (canCreate) void session.carryPlot();
  }, [state.library, running, busy, canCreate, session]);

  /**
   * `.plot_all()`, the composer's action while `all` is pressed: the confirmed
   * data with its bindings, in every library of the header at once; the server
   * copies this session's confirmed version into each library's session. The
   * upload and the bindings go along only for a server without the copy.
   * Before the confirmation it calls nothing and shows the notice, as the quiet
   * `.create_plot()` does.
   */
  const handlePlotAll = (event: React.MouseEvent) => {
    if (!step2) {
      setGateShown(true);
      return;
    }
    if (!state.sessionId) return;
    const upload = state.dataset?.upload;
    fanOutFocus.current = event.detail === 0;
    setFanOut({
      sourceSession: state.sessionId,
      ...(upload ? { upload } : {}),
      bindings: state.bindings,
      libraries: [...libraries],
    });
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
   * The offer after a switch, beside `.send()` once the library has a plot (the
   * first plot's offer submits the form instead, `handleSend`). Before the
   * confirmation it calls nothing and shows the notice, as `.create_plot()` does.
   */
  const handleCarry = (event: React.MouseEvent) => {
    if (!step2) {
      setGateShown(true);
      return;
    }
    keepKeyboardFocus(event);
    void session.carryPlot();
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
  // The composer's create action while `all` is pressed, for every library at once: the CTA
  // before the first plot, the quiet button otherwise, and before the confirmation a click
  // shows the notice. It waits while the panel is open.
  const plotAllButton = (
    <Box
      key="plot-all"
      component="button"
      type="button"
      ref={createRef}
      onClick={handlePlotAll}
      disabled={!!fanOut || (step2 ? !canCreate : state.phase !== 'ready' || busy)}
      aria-label="Plot in all libraries"
      aria-describedby={
        [
          step2 ? DATA_SUMMARY_ID : gate ? 'agent-create-gate' : null,
          chatLocked ? 'agent-create-line' : null,
        ]
          .filter(Boolean)
          .join(' ') || undefined
      }
      sx={firstPlot ? ctaButtonSx : actionButtonSx}
    >
      .plot_all()
    </Box>
  );
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
        <LibraryChip
          library={state.library}
          libraries={libraries}
          offerAll={offerAll}
          allPressed={plotAll}
          // No session to switch: another library opens the page anew, with its own
          // session (a full navigation, like the `.adapt()` button).
          hrefFor={
            reopen ? lib => paths.agentChat(specId, lib, LIB_TO_LANG[lib] ?? 'python') : undefined
          }
          // Not during a run (the server refuses a switch then) or while the fan-out's panel
          // is open: its sessions run on this one's data.
          disabled={!reopen && (busy || !!fanOut || state.phase !== 'ready')}
          onPick={handlePick}
          onAllChange={setAllPressed}
          buttonRef={libraryRef}
        />
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
            // Not while the fan-out's panel is open: its sessions copy this session's confirmed data.
            locked={!!fanOut}
            onLoadData={session.fetchDataCsv}
            // A look at the session's data, not at a result: version 0.
            onDataViewShown={() => session.reportOutcome('opened_data_view', 0)}
          />

          {state.items.length === 0 && !state.run && (
            <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
              paste your data above, or ask here for example data or a curve: &quot;y = sin(x), x
              from{' '}
              <Box component="span" sx={{ whiteSpace: 'nowrap' }}>
                -pi
              </Box>{' '}
              to pi&quot;, and the assistant makes the table. it sums your data up here, and you can
              ask it to fix the data in plain words, such as &quot;read Anteil as numbers&quot; or
              &quot;sum per month&quot;. check the preview and the bindings, confirm, then{' '}
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

            {/* The decisions every next plot takes over, right above the composer that asks for
                it and whose offer after a switch counts them; nothing while there are none. */}
            <Remembered
              memory={state.memory}
              disabled={busy || state.phase !== 'ready'}
              onForget={session.forgetMemory}
              onForgetAll={session.forgetAllMemory}
              fallbackFocusRef={messageRef}
            />

            {/* While the chat waits for `all`, the line says so in the ink of the text, and the
                message box names it as its description. */}
            {(firstPlot || chatLocked) && (
              <Box
                id="agent-create-line"
                sx={{ ...labelSx, color: chatLocked ? 'var(--ink)' : 'var(--ink-soft)', mb: -1 }}
              >
                {chatLocked
                  ? `# ${firstPlot ? 'step 2 — ' : ''}plot the table as it is in all ${libraries.length} libraries at once · turn all off to chat`
                  : carry
                    ? `# step 2 — ${carryText}, or say first what it should do differently`
                    : '# step 2 — create the plot as it is, or say first what it should do differently'}
              </Box>
            )}
            {/* Told before the user types: every turn would get `service_paused` until then. */}
            {pausedUntil && (
              <Box
                role="note"
                data-testid="service-paused"
                sx={{
                  ...labelSx,
                  color: 'var(--ink)',
                  borderLeft: `3px solid ${colors.warning}`,
                  pl: 1.5,
                  lineHeight: 1.6,
                }}
              >
                # {servicePausedText(pausedUntil)}
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
                  // data, the chat is the other way to get some: example data or a
                  // formula. While `all` is pressed in step 2 the box waits: the
                  // fan-out takes no text.
                  chatLocked
                    ? 'all libraries: the table goes as it is · turn all off to chat'
                    : !state.dataset
                      ? 'ask for example data or a curve: "y = sin(x), x from -pi to pi"'
                      : !step2
                        ? 'ask about your data, or for a fix: "sum per month"'
                        : firstPlot
                          ? 'optional: what the first plot should do differently'
                          : 'ask about this plot, or ask for a change'
                }
                value={draft}
                maxLength={MAX_MESSAGE_CHARS}
                rows={2}
                disabled={state.phase !== 'ready' || chatLocked}
                aria-describedby={chatLocked ? 'agent-create-line' : undefined}
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
              ) : firstPlot && plotAll ? (
                plotAllButton
              ) : firstPlot && !carry ? (
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
                  {/* After a switch that offered it: the plot in this library with the remembered
                      decisions, the step's action. Before the library's first plot it submits
                      the form, so typed text goes as the turn, as `.create_plot()` does. */}
                  {carry && (
                    <Box
                      key="carry"
                      component="button"
                      type={firstPlot ? 'submit' : 'button'}
                      ref={createRef}
                      data-testid="carry-plot"
                      onClick={firstPlot ? keepKeyboardFocus : handleCarry}
                      disabled={step2 ? !canCreate : state.phase !== 'ready' || busy}
                      aria-describedby={
                        step2
                          ? `${DATA_SUMMARY_ID}${firstPlot ? ' agent-create-line' : ''}`
                          : gate
                            ? 'agent-create-gate'
                            : undefined
                      }
                      // The library's name and the count make it long: it wraps at phone width.
                      sx={{
                        ...(step2 ? ctaButtonSx : actionButtonSx),
                        whiteSpace: 'normal',
                        textAlign: 'left',
                        maxWidth: '100%',
                      }}
                    >
                      {carryText}
                    </Box>
                  )}
                  {/* Step 2 after a plot: start over from the catalogue plot with this data.
                      Beside the offer: the plot from the catalogue code, without the carry. Step 1: the step is
                      visible from the foot too, and a click says what comes first instead of
                      calling the server. With `all`, `.plot_all()`. */}
                  {state.dataset && plotAll && plotAllButton}
                  {state.dataset && !plotAll && (
                    <Box
                      component="button"
                      type="button"
                      ref={carry ? undefined : createRef}
                      onClick={handleCreate}
                      disabled={step2 ? !canCreate : state.phase !== 'ready' || busy}
                      // Once this library has a plot, the button starts over from the
                      // catalogue plot; `.send()` beside it changes the latest version.
                      aria-label={hasPlot ? 'Start over' : 'Create plot'}
                      title={hasPlot || carry ? START_OVER_HELP : undefined}
                      aria-describedby={
                        [
                          hasPlot || carry ? START_OVER_HELP_ID : null,
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
                  {state.dataset && (hasPlot || carry) && !plotAll && (
                    <Box component="span" id={START_OVER_HELP_ID} sx={visuallyHiddenSx}>
                      {START_OVER_HELP}
                    </Box>
                  )}
                  {/* Before the library's first plot the offer submits text; no `.send()` then. */}
                  {!firstPlot && (
                    <Box
                      component="button"
                      type="submit"
                      onClick={keepKeyboardFocus}
                      disabled={chatLocked || !draft.trim() || state.phase !== 'ready' || busy}
                      aria-describedby={chatLocked ? 'agent-create-line' : undefined}
                      sx={ghostButtonSx}
                    >
                      .send()
                    </Box>
                  )}
                </>
              )}
            </Box>
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
            sourceSession={fanOut.sourceSession}
            upload={fanOut.upload}
            bindings={fanOut.bindings}
            maxRuns={maxRuns}
            onClose={() => {
              fanOutReturn.current = true;
              setFanOut(null);
            }}
          />
        )}
      </Box>
    </>
  );
}
