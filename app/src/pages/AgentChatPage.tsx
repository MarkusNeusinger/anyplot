/**
 * "Use with my data": the agent chat, for admins at `/debug/agent?spec=&library=&language=`
 * (plus `&all=1` while the library menu's `all` is pressed) and for everyone at
 * `/agent?spec=&library=&language=` while the public lane is open (`PublicAgentChatPage`,
 * experimental). The site's `.use_my_data()` entries open `/agent` for an admin too while the
 * public lane is open, so the owner tests what a visitor gets; `/debug/agent` is the admin's
 * page for its tools, typed or bookmarked, and the entries' target only while the public lane
 * is closed (`useAgentEligibility`). The query follows the session: a library switch writes
 * `library` and its `language`.
 *
 * One column, chat first, two steps, data first. The data card is the first
 * turn of the thread: paste data (or ask in the chat for a curve, whose table
 * the assistant computes; while the session has no data, `.example_data()` on
 * the line above the composer asks it for a made-up table to try the plot),
 * read the assistant's summary of it in the next
 * turn, fix it in plain words if needed (each change updates the card in
 * place, with `.undo()`), check the preview and the role bindings, and press
 * `.create_plot()` at the composer's end, which takes the data and the bindings
 * as shown (it confirms them on the server first, the end of step 1) and starts
 * the plot (step 2): with an empty box the plot as it is, with text the text
 * goes as a turn and the assistant makes the first plot with that change. The
 * card collapses into a pinned header at the top of the thread with that click,
 * `.show()` opens it again, and any change to the data takes the page back to
 * step 1 with the card open; the header then stays as `! check again` and leads
 * back to the card, and the thread names what dropped the confirmation. Once the
 * library has a plot, the composer refines in plain
 * words (`.send()`, on the latest version), and the same button becomes
 * `.start_over()`: a new plot from the catalogue plot with this data, the way
 * out of code that went wrong, which keeps the remembered decisions (owner
 * decision of 2026-11-02); every shipped version gets a result card with the image,
 * the code and the downloads. A line above the column names the current step. The header
 * shows the catalogue plot being adapted as a thumbnail beside the spec's title, in the
 * library in use and the site theme (`CataloguePreview`; a click opens it large), with the
 * columns it expects behind the ⓘ after the title (the spec's roles as the session's open
 * names them, the spec's `data` bullets without them), and carries the library menu
 * (`LibraryChip`, since 2026-11-02 in place of a pill
 * per library: the libraries grouped by language, `all` for the admin) and,
 * next to it, the session language chip (`LanguageChip`): the language of the
 * replies and of the text in the plot, English until the first typed message
 * or a choice sets another. On the admin lane, the "⋯" menu (`SessionMenu`) at the
 * header's end holds `.save()` with its `# include data.csv` box (out of the header row
 * since 2026-11-02, owner: less text); the public lane has neither. The page talks only to the BFF under
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
 * The composer holds one filled call to action at its right end (`Composer.tsx`)
 * from the moment data is stored: `.create_plot()`, while the data is not
 * confirmed (also when the library has a plot: the click makes a new version
 * from the changed data, with the remembered decisions) and while it is
 * confirmed and the library has no plot yet. In step 1 the line above the box,
 * its description, names what it waits for (a table read from text to decide
 * on, a required role without a column) or what to check. Enter and `.send()`
 * send a turn and never confirm; `.send()` shows only while the box holds text.
 * The server's `data_unconfirmed` stays the backstop.
 *
 * Work in flight is never silent: a turn without pipeline steps holds an
 * in-progress line in the thread (`ChatThread`), the progress timeline below
 * it shows only what the line does not (a `create_plot` run, a queue position,
 * pipeline steps), and the data card says why its controls wait.
 *
 * The library menu's `all`, after the libraries, is the admin's test run.
 * While it is pressed, the composer's create action is `.plot_all()`: the
 * data with its bindings, confirmed first as `.create_plot()` does, plotted in
 * every library of the header at once (`FanOut`), a session per library into which the server copies
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
 * 2. The admin lane: the admin hint (`src/utils/adminAuth.ts`), or local
 *    development; without it the page asks for a sign-in on `/debug` first. The
 *    BFF's admin gate is the real check; a 401 or 403 from it clears the hint
 *    and shows the same notice.
 *    The public lane: the API's `GET /agent/lane` (`useAgentLaneOpen`); closed,
 *    the page says so. It talks to `/agent/*` with `PUBLIC_LANE` in place of the
 *    admin token, shows the experimental notice above the first input (one line, the
 *    details behind its ⓘ button: `ExperimentalNotice`), offers no `all` and no
 *    `.save()` (a visitor cannot resume a saved session, and the feedback form
 *    covers "something went wrong"), and leaves the feedback
 *    form's data box unticked (`sections/agent-chat/lane.ts`).
 *
 * Design: docs/concepts/agent-network.md ("Frontend", "Request flow").
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Link as RouterLink, useSearchParams } from 'react-router-dom';

import Box from '@mui/material/Box';

import { LoaderSpinner } from 'src/components/LoaderSpinner';
import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_TO_LANG, LIBRARIES } from 'src/constants';
import { CONFIG } from 'src/global-config';
import { useAgentLaneOpen } from 'src/hooks/useAgentLaneOpen';
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
import {
  agentApi,
  type AgentLane,
  browserLocale,
  DEFAULT_AGENT_LIBRARIES,
  MAX_MESSAGE_CHARS,
  PUBLIC_LANE,
} from 'src/lib/agent';
import { apiGet, endpoints } from 'src/lib/api';
import { NotFoundPage } from 'src/pages/NotFoundPage';
import { paths, specPath } from 'src/routes/paths';
import { attachmentSummary } from 'src/sections/agent-chat/attachmentText';
import { CataloguePreview } from 'src/sections/agent-chat/CataloguePreview';
import { ChatFeedback } from 'src/sections/agent-chat/ChatFeedback';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { Composer } from 'src/sections/agent-chat/Composer';
import { DataPanel } from 'src/sections/agent-chat/DataPanel';
import { ExperimentalNotice } from 'src/sections/agent-chat/ExperimentalNotice';
import { FanOut } from 'src/sections/agent-chat/FanOut';
import { DEFAULT_USER_MAX_RUNS } from 'src/sections/agent-chat/fanoutRules';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import { AgentLaneContext } from 'src/sections/agent-chat/lane';
import { LanguageChip } from 'src/sections/agent-chat/LanguageChip';
import { LibraryChip } from 'src/sections/agent-chat/LibraryChip';
import {
  carryActionText,
  DATA_HOWTO,
  describeDataFailure,
  DROP_HINT_TEXT,
  ERROR_TEXT,
  LEAVE_TEXT,
} from 'src/sections/agent-chat/messages';
import { PinnedHeader } from 'src/sections/agent-chat/PinnedData';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { Remembered } from 'src/sections/agent-chat/Remembered';
import { SessionMenu } from 'src/sections/agent-chat/SessionMenu';
import { columnLines, previewsByLibrary } from 'src/sections/agent-chat/specReference';
import { StepHeader } from 'src/sections/agent-chat/StepHeader';
import { inStep2, showsTimeline, stepOneLine } from 'src/sections/agent-chat/steps';
import {
  bodyTextSx,
  CHAT_SECTION_GAP,
  labelSx,
  panelSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { type Attachment, useChatAttachment } from 'src/sections/agent-chat/useChatAttachment';
import { useDataCardView } from 'src/sections/agent-chat/useDataCardView';
import { parseInlineCode } from 'src/sections/spec-detail/SpecTabs/utils';
import { colors, fontSize, proseLinkStyle, typography } from 'src/theme';
import { readAdminHint, readAdminToken, setAdminHint } from 'src/utils/adminAuth';
import type { ThemedPreviewSource } from 'src/utils/themedPreview';

const SPEC_PATTERN = /^[a-z0-9-]{1,100}$/;
/** Where `agent_open` says the visitor came from: the plot page, the landing page, the spec hub. */
const OPEN_SOURCES = new Set(['plot_page', 'landing', 'spec_hub', 'plot_of_the_day']);
/**
 * The chat column's width: it grows with the window up to this (960 until 2026-11-02; owner:
 * use the room of a wide screen), so the data card with its grid, the plot cards and the code
 * take the full width, while the thread's text keeps a readable line (`CHAT_TEXT_MAX` in
 * `styles.ts`). Below about 1100 px the window, not this cap, sets the width, as before.
 */
const COLUMN_MAX_WIDTH = 1360;

/** The first of these controls that can take the focus now, in order of preference. */
function firstEnabled(...controls: (HTMLButtonElement | HTMLTextAreaElement | null)[]) {
  return controls.find(control => control && !control.disabled) ?? null;
}

/**
 * The page is a tool on one catalogue pair, never a page to index: every branch (a notice, the door
 * still being asked, the session opening or failing, the chat) carries `noindex, nofollow`.
 */
function NoIndex() {
  return <meta name="robots" content="noindex, nofollow" />;
}

function Notice({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Box sx={{ py: 4, maxWidth: 560, mx: 'auto' }}>
      <NoIndex />
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

/** The chat's Highcharts note, shown while the session plots in Highcharts (the legal page says the same). */
export const HIGHCHARTS_NOTE =
  'highcharts is free for non-commercial use; a commercial use needs a licence from Highsoft.';

/** The public lane's page while the lane is closed (`GET /agent/lane` answered no). */
function LaneClosed() {
  return (
    <Notice title="use with my data · experimental">
      the assistant is closed right now. please try again later; the{' '}
      <Box component={RouterLink} to={paths.plots} sx={proseLinkStyle}>
        catalogue
      </Box>{' '}
      stays open.
    </Notice>
  );
}

/**
 * The public chat at `/agent`: the same page on the public lane (`PUBLIC_LANE`), open to
 * everyone while the API's public lane is (`useAgentLaneOpen`), labelled experimental, with
 * the admin-only parts left out (the fan-out's `all`, `.save()` and its "⋯" menu) and the
 * feedback form's data box unticked.
 */
export function PublicAgentChatPage() {
  return <AgentChatPage lane="public" />;
}

export function AgentChatPage({ lane = 'admin' }: { lane?: AgentLane } = {}) {
  const [params, setParams] = useSearchParams();
  const { trackPageview, trackEvent } = useAnalytics();
  const laneOpen = useAgentLaneOpen();
  const allowed =
    CONFIG.features.agentChat &&
    (lane === 'public' ? laneOpen === true : CONFIG.isDev || readAdminHint());

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
    trackPageview(lane === 'public' ? paths.agent : '/debug/agent');
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
  }, [allowed, valid, params, setParams, library, spec, trackEvent, trackPageview, lane]);

  if (!CONFIG.features.agentChat) return <NotFoundPage />;
  if (lane === 'public' && laneOpen === null) return <NoIndex />;
  if (!allowed) return lane === 'public' ? <LaneClosed /> : <AdminRequired />;
  const chatPath = lane === 'public' ? paths.publicAgentChat : paths.agentChat;
  if (!valid) {
    return (
      <Notice title="use with my data">
        open it from a plot&apos;s <code>.use_my_data()</code>, or start with{' '}
        <Box
          component={RouterLink}
          to={chatPath('scatter-basic', 'matplotlib', 'python')}
          sx={proseLinkStyle}
        >
          scatter-basic in matplotlib
        </Box>
        .
      </Notice>
    );
  }
  const token = lane === 'public' ? PUBLIC_LANE : readAdminToken();
  return (
    <AgentLaneContext.Provider value={lane}>
      <AgentChat
        key={`${spec}|${token}`}
        specId={spec}
        library={library}
        language={language}
        token={token}
        lane={lane}
        allInUrl={lane === 'admin' && allInUrl}
        onLibraryChange={onLibraryChange}
        onAllChange={onAllChange}
      />
    </AgentLaneContext.Provider>
  );
}

interface AgentChatProps {
  specId: string;
  library: string;
  language: string;
  /** The admin token, or `PUBLIC_LANE` on the public lane. */
  token: string;
  /** The lane the page runs on: the public one offers no `all` and says it is experimental. */
  lane: AgentLane;
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
  lane,
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
  // The catalogue plot beside the title: its preview per library, and the spec's `data` bullets,
  // the columns ⓘ's fallback while the session's open names no roles.
  const [reference, setReference] = useState<{
    previews: Record<string, ThemedPreviewSource>;
    data: string[];
  } | null>(null);
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

  // The spec's title, implemented libraries, previews and data bullets come from the public
  // catalogue API; the enabled libraries from the agents service. Both are best effort.
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
    apiGet<{
      title: string;
      data?: string[];
      implementations: (ThemedPreviewSource & { library_id: string })[];
    }>(endpoints.spec(specId), {
      signal: controller.signal,
    })
      .then(spec => {
        if (controller.signal.aborted) return;
        setTitle(spec.title);
        setReference({ previews: previewsByLibrary(spec.implementations), data: spec.data ?? [] });
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

  // A refused admin token ends the admin hint; a refusal on the public lane says nothing about
  // it, and an admin uses the public lane too while it is open.
  useEffect(() => {
    if (lane === 'admin' && state.phase === 'unauthorized') setAdminHint(false);
  }, [lane, state.phase]);

  // The progress and the replies arrive at the foot of the thread, below the
  // data card: bring the foot into view when a turn starts.
  const running = !!state.run;
  useEffect(() => {
    if (running) tailRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
  }, [running]);

  // The data card in the thread and the pinned header above it share where the card is in view.
  const dataView = useDataCardView(state);
  // The first reply after a card follows the user into view only while they are at the composer.
  const followReply = useCallback(() => !!tailRef.current?.contains(document.activeElement), []);

  // A turn, a theme render, a parse, an undo or a binding change in flight: the
  // server runs one at a time and would refuse or race a second.
  const busy = sessionBusy(state);
  // The table or file waiting in the message box for Enter (`useChatAttachment`).
  const attach = useChatAttachment({
    ready: state.phase === 'ready' && !!state.sessionId,
    working: busy,
    locked: !!fanOut,
    onConvert: session.convertFile,
    onTrack: trackEvent,
  });
  const attachment = attach.attachment;

  // Data, a plot or work in flight, and typed text or an attachment not sent yet: a reload, a
  // closed tab or a link off the page asks first, since nothing restores the session or the box.
  // The fan-out's panel opens only on this session's confirmed data, so its sessions are covered.
  useLeaveWarning(
    sessionHoldsWork(state) || draft.trim() !== '' || attachment !== null,
    LEAVE_TEXT
  );
  // The session could not open for this pair: other libraries are links instead.
  const reopen = state.phase === 'ineligible' || state.phase === 'error';
  // Step 2: the data and its bindings are confirmed, and no table read from text waits.
  const step2 = inStep2(state);
  // A plot button may start once there is data with every required role bound and nothing in
  // flight: on unconfirmed data its click confirms the data as shown first (`startPlot`). While
  // an attachment waits it would plot the data before it, or none: Enter reads it first.
  const canCreate =
    state.phase === 'ready' &&
    !!state.dataset &&
    state.bindingsComplete &&
    !state.transcription &&
    !attachment &&
    !busy;
  // The server files a version under its (spec, library) pair; the spec cannot change in a
  // session yet, so the library alone tells the pair.
  const hasPlot = Object.values(state.versions).some(version => version.library === state.library);
  // The composer's one filled CTA is a plot button from the moment data is stored: while the
  // data is unconfirmed (also with a plot here, whose next version takes the changed data), and
  // while it is confirmed and this library has no plot yet. Confirmed with a plot, the composer
  // refines with `.send()` and keeps a quiet `.start_over()`.
  const ctaPlot = !!state.dataset && !(step2 && hasPlot);
  // `all` in the menu only once the libraries and the limit are the server's: a snapshot of the
  // fallbacks would leave libraries out or start more runs than the server takes (`run_limit`).
  // `.plot_all()` is the admin's test run: never on the public lane, whose BFF has no copy route.
  const offerAll = lane === 'admin' && listsSettled && libraries.length > 1 && !reopen;
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
  // The columns ⓘ after the title: the spec's roles as the session's open named them, else the
  // spec's `data` bullets (an older server, or no session: ineligible, an error).
  const expectedLines = columnLines(state.specRoles, reference?.data);
  // Without data, `.example_data()` above the composer: the other way to data besides a paste.
  // A table read from text that waits for its decision is data at hand, so the line waits too.
  // A table or a file waiting in the box is data at hand as well.
  const exampleOffer =
    state.phase === 'ready' && !state.dataset && !state.transcription && !attachment;
  const exampleWorking = exampleOffer && state.run?.kind === 'example_data';
  // Step 1's line above the composer, the plot button's description: what it waits for (a
  // pending table read from text, a required role without a column), else what to check.
  const stepLine = stepOneLine(state, plotAll ? '.plot_all()' : undefined);

  // `&all=1` follows `all`, so a reload presses it again. Only from the lists' answers on:
  // before them `all` is not offered yet, and one pressed from the URL waits for them.
  useEffect(() => {
    if (listsSettled) onAllChange(plotAll);
  }, [listsSettled, plotAll, onAllChange]);

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
   * The form's submit, Enter in the box and `.send()`: the text goes as a turn about the data
   * or the plot, never as a confirmation. In step 1 a plot wish in it is kept for the next
   * `.create_plot()` (the assistant's `keep_plot_request`); in step 2 before the first plot the
   * assistant makes that plot with it. While `all` is pressed in step 2 nothing goes: the
   * fan-out takes no text.
   */
  const handleSend = (event?: React.FormEvent) => {
    event?.preventDefault();
    if (attachment) {
      void sendAttachment(attachment);
      return;
    }
    const text = draft.trim();
    // Text over the cap is never cut: the counter is red and nothing goes until it fits.
    if (!text || text.length > MAX_MESSAGE_CHARS || busy || chatLocked) return;
    void session.sendMessage(text);
    setDraft('');
  };

  /** Text back into the box, before anything typed since, with a blank line between them. */
  const restoreText = (text: string) =>
    setDraft(current => (current.trim() ? `${text}\n\n${current}` : text));

  // The attachment a table was read from, while that table waits for `.use()` or `.discard()`:
  // a discard gives it back for another try.
  const transcribedFrom = useRef<Attachment | null>(null);

  /**
   * `.discard()`: the table read from text goes, and what it came from comes back. Short pasted
   * text goes into the box, to edit and send as a message; a file's text, or text the box could
   * not send, waits as the attachment again, unless the user attached something since.
   */
  const handleDiscard = () => {
    session.discardTranscription();
    const sent = transcribedFrom.current;
    transcribedFrom.current = null;
    if (!sent) return;
    if (sent.via === 'paste' && sent.text.length <= MAX_MESSAGE_CHARS) restoreText(sent.text);
    else if (!attachment) attach.reattach(sent);
  };

  /**
   * Enter or `.send()` with an attachment: the dataset route reads it, and the typed text goes
   * along as its note, the first turn once the data is stored. The field lets go of the note at
   * once; when nothing was stored (a table read from text to decide on, text that went to the
   * chat, a refusal, nothing started), the note goes back into it, before anything typed since.
   * A refused attachment stays red with the reason, for Enter to try again or × to drop it.
   */
  const sendAttachment = async (sent: Attachment) => {
    if (busy || (sent.status !== 'ready' && sent.status !== 'failed')) return;
    // While `all` holds the box in step 2 it takes no text: the attachment goes alone.
    const note = chatLocked ? '' : draft.trim();
    if (note.length > MAX_MESSAGE_CHARS) return;
    if (note) setDraft(current => (current.trim() === note ? '' : current));
    attach.settle(sent.id, 'sending');
    const result = await session.parseData(sent.text, false, sent.source, undefined, {
      note,
      file: sent.converted,
      // The thread names the paste as the chip did, and its card follows it there.
      chip: attachmentSummary(sent),
      // Stored, or sent to the chat as the user's turn: the attachment goes before that turn
      // runs, and a note the forward did not take goes back into the box.
      onStored: () => attach.settle(sent.id, 'cleared'),
      onForward: () => {
        attach.settle(sent.id, 'cleared');
        if (note) restoreText(note);
      },
    });
    if (result.outcome === 'failed') {
      const failure = result.failure;
      attach.settle(sent.id, {
        error: failure
          ? describeDataFailure(failure.code, failure.ref, failure.cause ?? null)
          : describeDataFailure('internal', null),
      });
    } else if (result.outcome === 'skipped' || result.outcome === 'transcribed') {
      attach.settle(sent.id, result.outcome === 'skipped' ? 'ready' : 'cleared');
    }
    transcribedFrom.current = result.outcome === 'transcribed' ? sent : null;
    // Nothing was stored and nothing went to the chat: the note waits in the box again.
    const kept = result.outcome === 'stored' || result.outcome === 'forwarded';
    if (note && !kept) restoreText(note);
  };

  /**
   * A plot button's click (`.create_plot()`, `.start_over()`, the carry): the data and the
   * bindings as the card shows them are what the plot takes, so data that is not confirmed yet
   * is confirmed first; a refusal stops here and shows under the composer, and nothing is
   * plotted. Then the plot starts: the box's text, when the button takes it (`withText`, the
   * filled CTA), goes as the turn that makes the plot with that request, else the catalogue
   * plot (`create_plot`) or the switch's offer (`carry_plot`). The confirmation's busy state and
   * the session's own guards hold back a second click, also one before the state caught up.
   */
  const startPlot = async (
    event: React.MouseEvent,
    kind: 'create' | 'carry',
    withText: boolean
  ) => {
    keepKeyboardFocus(event);
    if (!canCreate) return;
    const text = withText ? draft.trim() : '';
    if (!state.dataConfirmed && !(await session.confirmData())) return;
    if (text) {
      // Only the text that went: an edit made while the confirmation ran stays in the box. The
      // turn puts the text in the thread before its request goes, so a turn refused at once
      // (a limit, the capacity, the network) shows it there with the error: nothing is lost.
      setDraft(current => (current.trim() === text ? '' : current));
      void session.sendMessage(text);
    } else {
      void (kind === 'carry' ? session.carryPlot() : session.createPlot());
    }
  };

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
  // with the user's decisions (`carry_plot`), without a second click. The intent is noted
  // before the switch, so the render that brings the new library finds it; the carry runs
  // only on confirmed data, never confirming by itself: on data the user has not taken yet,
  // the composer offers it and the click confirms.
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
    if (canCreate && step2) void session.carryPlot();
  }, [state.library, running, busy, canCreate, step2, session]);

  /**
   * `.plot_all()`, the action while `all` is pressed: the data with its bindings, in every
   * library of the header at once; the server copies this session's confirmed version into each
   * library's session, so data that is not confirmed yet is confirmed first, as for
   * `.create_plot()`, and a refusal opens no panel. The upload and the bindings go along only
   * for a server without the copy.
   */
  const handlePlotAll = async (event: React.MouseEvent) => {
    const sourceSession = state.sessionId;
    if (!canCreate || !sourceSession) return;
    const keyboard = event.detail === 0;
    if (!state.dataConfirmed && !(await session.confirmData())) return;
    const upload = state.dataset?.upload;
    fanOutFocus.current = keyboard;
    setFanOut({
      sourceSession,
      ...(upload ? { upload } : {}),
      bindings: state.bindings,
      libraries: [...libraries],
    });
  };

  /**
   * The quiet `.create_plot()` beside the offer after a switch, or `.start_over()` once the
   * library has a plot: the fresh plot from the catalogue code, with the remembered decisions;
   * text in the box stays there for `.send()`.
   */
  const handleCreate = (event: React.MouseEvent) => void startPlot(event, 'create', false);

  /**
   * The offer after a switch: the plot in this library with the remembered decisions. While it
   * is the filled CTA (data unconfirmed, or no plot here yet) the box's text goes along as the
   * turn that makes it; beside `.send()` once the confirmed data has a plot, it takes none.
   */
  const handleCarry = (event: React.MouseEvent) => void startPlot(event, 'carry', ctaPlot);

  /** The filled `.create_plot()`: the plot, with the box's text as its request. */
  const handlePlot = (event: React.MouseEvent) => void startPlot(event, 'create', true);

  if (state.phase === 'unauthorized') return lane === 'public' ? <LaneClosed /> : <AdminRequired />;
  const chatPath = lane === 'public' ? paths.publicAgentChat : paths.agentChat;

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
        {/* The catalogue plot and its title stay together when the row wraps at phone width; the
            columns it expects are behind the ⓘ, closed by default. */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, minWidth: 0 }}>
          <CataloguePreview
            title={title ?? specId}
            library={state.library}
            preview={reference?.previews[state.library] ?? null}
          />
          <Box sx={{ minWidth: 0 }}>
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
            {expectedLines.length > 0 && (
              <InfoPopover
                label="Columns the plot expects"
                heading="# the plot expects"
                testId="expected-columns"
                lines={expectedLines.map(line => parseInlineCode(line))}
              />
            )}
          </Box>
        </Box>
        <LibraryChip
          library={state.library}
          libraries={libraries}
          offerAll={offerAll}
          allPressed={plotAll}
          // No session to switch: another library opens the page anew, with its own
          // session (a full navigation, like the plot page's `.use_my_data()`).
          hrefFor={reopen ? lib => chatPath(specId, lib, LIB_TO_LANG[lib] ?? 'python') : undefined}
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
        {/* The "⋯" menu holds `.save()`, the admin's debugging bundle, which downloads the
            session; without one (ineligible, error) there is nothing to save. The public lane
            has no `.save()` (a visitor cannot resume a saved session), so no menu either. */}
        {lane === 'admin' && !reopen && (
          <SessionMenu
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
        <NoIndex />
        {header}
        {state.phase === 'opening' ? (
          // The open can take seconds: on the public lane the bot check runs inside it first
          // (`withHumanCheck`), and a check that asks for a click shows at the window's foot.
          <Box
            role="status"
            data-testid="session-opening"
            sx={{ ...labelSx, display: 'flex', alignItems: 'center', gap: 1.5 }}
          >
            opening a session
            <LoaderSpinner size="inline" />
          </Box>
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
                  ? lane === 'public'
                    ? 'the assistant is closed right now. please try again later.'
                    : 'the agent chat is switched off on this server (AGENT_ENABLED).'
                  : (ERROR_TEXT[state.failure?.code ?? ''] ?? 'the session could not be opened.')}
              {state.phase === 'error' && <ReloadHint code={state.failure?.code} opening />}
            </Box>
          </Box>
        )}
      </Box>
    );
  }

  return (
    <>
      <>
        <title>{`agent · ${title ?? specId} | anyplot.ai`}</title>
        <NoIndex />
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
        {lane === 'public' && <ExperimentalNotice />}
        {state.library === 'highcharts' && (
          <Box role="note" data-testid="highcharts-licence" sx={{ ...labelSx, mb: 2 }}>
            # {HIGHCHARTS_NOTE}
          </Box>
        )}
        <StepHeader current={step2 ? 2 : 1} />
        {/* The whole chat takes a dropped file: it becomes the message box's attachment. */}
        <Box
          component="section"
          aria-label="Chat"
          onDragEnter={attach.handleDragEnter}
          onDragOver={attach.handleDragOver}
          onDragLeave={attach.handleDragLeave}
          onDrop={attach.handleDrop}
          sx={{ ...panelSx, display: 'flex', flexDirection: 'column', gap: CHAT_SECTION_GAP }}
        >
          {/* The how-to of the data that comes in through the message box sits beside the label,
              not in it, so it never joins the section's name. */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: -0.5 }}>
            <Box sx={labelSx}># chat</Box>
            <InfoPopover
              label="How the chat takes data"
              heading="# how it works"
              lines={DATA_HOWTO}
              testId="data-howto"
            />
          </Box>

          {/* Once the data was confirmed, the header that leads to its card. A sibling of the
              thread, so it sticks over all of it; the card stands in the thread after its paste. */}
          <PinnedHeader state={state} view={dataView} />

          <ChatThread
            state={state}
            specId={specId}
            language={language}
            onRequestTheme={(version, theme) => void session.requestTheme(version, theme)}
            onFetchArtifact={session.fetchArtifact}
            onTrack={trackEvent}
            onOutcome={session.reportOutcome}
            onSendFeedback={session.sendFeedback}
            renderData={part => (
              <DataPanel
                state={state}
                view={dataView}
                part={part}
                onParse={(text, source, table, file) =>
                  void session.parseData(text, false, source, table, { file })
                }
                onConfirmTranscription={() => {
                  transcribedFrom.current = null;
                  void session.confirmTranscription();
                }}
                onTrack={trackEvent}
                // The sheet picker's read holds the composer back until its parse starts.
                onConvert={session.readSheet}
                onDiscardTranscription={handleDiscard}
                onBind={session.setBinding}
                onUndo={() => void session.undoData()}
                onToLong={() => void session.toLongData()}
                // Not while the fan-out's panel is open: its sessions copy this session's data.
                locked={!!fanOut}
                onLoadData={session.fetchDataCsv}
                // A look at the session's data, not at a result: version 0.
                onDataViewShown={() => session.reportOutcome('opened_data_view', 0)}
              />
            )}
            followReply={followReply}
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

            <Composer
              draft={draft}
              onDraftChange={event => {
                // A paste the browser inserted itself, when its event hid the text: routed now.
                if (!attach.handleInput(event, draft)) setDraft(event.target.value);
              }}
              onPaste={event => void attach.handlePaste(event)}
              attachment={attachment}
              attachmentNotice={attach.notice}
              onRemoveAttachment={attach.remove}
              dropHint={
                attach.dragOver
                  ? {
                      ready: attach.dropReady,
                      text: attach.dropReady
                        ? DROP_HINT_TEXT.ready
                        : attachment?.status === 'reading'
                          ? DROP_HINT_TEXT.reading
                          : fanOut && !busy
                            ? DROP_HINT_TEXT.locked
                            : DROP_HINT_TEXT.working,
                    }
                  : null
              }
              canOpen={attach.dropReady}
              fileInputRef={attach.fileInputRef}
              onFileChosen={attach.handleChosen}
              onSubmit={handleSend}
              messageRef={messageRef}
              createRef={createRef}
              ready={state.phase === 'ready'}
              busy={busy}
              running={running}
              stopping={!!state.run?.stopping}
              hasData={!!state.dataset}
              step2={step2}
              hasPlot={hasPlot}
              ctaPlot={ctaPlot}
              canCreate={canCreate}
              plotAll={plotAll}
              chatLocked={chatLocked}
              libraryCount={libraries.length}
              fanOutOpen={!!fanOut}
              carryText={carry ? carryText : null}
              stepLine={stepLine}
              confirming={state.confirmBusy}
              confirmError={state.confirmError}
              pausedUntil={pausedUntil}
              exampleOffer={exampleOffer}
              exampleWorking={exampleWorking}
              onExampleData={event => {
                keepKeyboardFocus(event);
                void session.exampleData();
              }}
              onStop={event => {
                keepKeyboardFocus(event);
                void session.stop();
              }}
              onPlot={handlePlot}
              onCreate={handleCreate}
              onCarry={handleCarry}
              onPlotAll={event => void handlePlotAll(event)}
              keepKeyboardFocus={keepKeyboardFocus}
            />
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
