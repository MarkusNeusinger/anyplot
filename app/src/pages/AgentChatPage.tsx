/**
 * "Use with my data": the agent chat at `/agent?spec=&library=&language=`, one page for everyone
 * (owner, 2026-11-06): the admin's chat looks and behaves exactly like a visitor's and runs the
 * same code, so the owner never misses what a visitor meets. The page detects an admin at runtime
 * (`useAgentAdmin`: the admin hint from `/debug` plus a successful admin call) and then talks to
 * the admin API (`/debug/agent/*`), else to the public API with its bot check. The only other
 * differences are the limits, which the server enforces per tier, and the fan-out to every
 * library; every admin extra sits behind one element, the admin menu (`AdminMenu`). The old
 * address `/debug/agent` only redirects here (`AgentChatRedirect`). The query follows the
 * session: a library switch writes `library` and its `language`.
 *
 * One column, chat first, two steps, data first, in one terminal-style frame (`ChatFrame`,
 * since the v4 design of 2026-11-06): the tab label `~/anyplot.ai/agent` on its top border, the
 * header row inside it, and at its foot the status line, `>>> step 1 of 2 · …`, which names the
 * step and what the plot button waits for. The thread opens with the start item (`StartItem`,
 * since 2026-11-07): "You came from **<the spec's title>**. It needs", the spec's roles as chips
 * in plain words (`x · numbers`, `y · numbers, one or more`), the catalogue plot being adapted
 * as a thumbnail in the library in use and the site theme (`CataloguePreview`; a click opens it
 * large), the columns it expects behind an ⓘ after the chips (the spec's roles as the session's
 * open names them, the spec's `data` bullets without them), a pointer to the box below and the
 * how-to of the data behind an ⓘ; it repeats none of the composer's controls, stays first and
 * scrolls up with the talk. The data card is the first
 * turn after it: paste data (or ask in the chat for a curve, whose table
 * the assistant computes; while the session has no data, `.example_data()` in
 * the highlighted line above the message box asks it for a made-up table to try the plot),
 * read the assistant's summary of it in the next
 * turn, fix it in plain words if needed (each change is a new version: the card moves below the
 * turn, and the version before folds to its label, `▸ data v1 · pasted · 2 rows × 2 cols`), check
 * the preview and the role bindings, and press
 * `.create_plot() →` at the composer's end, which takes the data and the bindings
 * as shown (it confirms them on the server first, the end of step 1) and starts
 * the plot (step 2): with an empty box the plot as it is, with text the text
 * goes as a turn and the assistant makes the first plot with that change. The
 * thread reads in chapters (`# data`, `# plot`, `threadModel.ts`), and the live data card stays
 * open in both steps (the v4 design; the pinned header with `.show()` and `.hide()` went
 * 2026-11-07): a change to the data after a plot opens a new `# data` chapter with the card
 * (after the request that made it, before its reply, or at the thread's end for a version of the
 * card's own controls), and the status line names what dropped the confirmation. Once the
 * library has a plot, the same button reads `.update_plot() →` and sends the
 * box's text, a change in plain words on the latest version (as Enter does), and
 * `.start_over()` at the end of the status line makes a new plot from the
 * catalogue plot with this data, the way out of code that went wrong, which
 * keeps the remembered decisions (owner decision of 2026-11-02); every shipped
 * version gets a result card with the image,
 * the code and the downloads. The header row, in plain words, shows the spec's title, the link
 * back, and carries the library menu (`LibraryChip`, `seaborn ▾`, since
 * 2026-11-02 in place of a pill per library: the libraries grouped by language), next to it the
 * session language chip (`LanguageChip`, `English ▾`): the language of the replies and of the
 * text in the plot, English until the first typed message or a choice sets another (the
 * thumbnail and both ⓘ stood in the row until the start item took them). For an admin, the
 * admin menu stands at the row's end (since
 * 2026-11-06, where the "⋯" menu with `.save()` stood): the fan-out toggle, `.save()` with its
 * `# include data.csv` box, "view as visitor" and the admin's diagnostics. The page talks only to
 * the BFF (`src/lib/agent.ts`, `src/hooks/useAgentSession.ts`).
 *
 * A library switch keeps the data, the bindings, their confirmation, the
 * language and the plot memory. When its answer offers it, the plot button's
 * click with an empty box makes the plot in the new library from its catalogue
 * code with the decisions the user made so far (`carry_plot`); the button keeps
 * its name, and the status line names the decisions it keeps. Picking a library
 * from the menu runs nothing, so browsing costs nothing. `.start_over()` stays
 * the plot from the catalogue code, which keeps the decisions too but not the
 * switch's carry (the theme asked for before), and text typed into the box goes
 * as a normal turn, which the server also gives the decisions. The offer ends
 * once a plot in that library ships, or with a switch whose answer has none. The
 * decisions themselves stand on the latest `# plot` chapter line, `3 decisions ▾`
 * (before the first plot on the latest chapter line), which unfolds their list under
 * the line (`Remembered`), each with `.forget()`, and `.forget_all()` for a blank
 * start: nothing else clears them. An open plot card names the decisions it kept
 * and added (`kept: … · new: …`); its label names the request it answered. A typed turn that
 * changed nothing, by the server's word and by what the page saw, reads as a question:
 * a `?` beside its bubble, `? answer · nothing changed` over its reply, and a count on
 * its chapter line that jumps to the chapter's questions in turn.
 *
 * The composer is one row in two fixed places (`Composer.tsx`, since the v4
 * composer row), the message box and the plot button, under one quiet line of
 * links that is never gone: `# no data at hand? .example_data() · .open() a
 * file`, highlighted until the first data arrives, then muted, `# other data?
 * .open() · .example_data()`. Nothing comes or goes, so nothing moves and a
 * focused control keeps the focus: a state changes only how the line reads,
 * whether the plot button is filled (from the moment data is stored) and which
 * controls are inert (`.example_data()` once there is data). The plot
 * button reads `.create_plot() →` until the library has a plot, while the data
 * is unconfirmed its click confirms it as shown first, and the status line at
 * the frame's foot, its description, names what it waits for (a table read from
 * text to decide on, a required role without a column) or what to check. Enter,
 * and on a touch screen the `↵` in the box, sends a turn and never confirms. The
 * server's `data_unconfirmed` stays the backstop. With data in the box (a file, a
 * pasted or typed table), the plot button sends it as Enter would, with the typed
 * text as its note, and once the reading comes back clean goes on by itself with
 * the confirmation and the plot; else it stops at the data card, where the
 * status line says what to look at (`plotChain.ts`, owner decision of 2026-11-08). At the status line's end stand
 * `.stop()` while a run is in progress, `.start_over()` once the library has a
 * plot, and `.feedback()` before the first plot.
 *
 * Work in flight is never silent: one working line at the thread's foot says
 * what the turn does now (`WorkingLine`: `drawing your plot · second try · 0:42`,
 * `waiting · you are 3rd`, `summarizing your data`), for every turn and on both
 * lanes; the status line at the frame's foot counts the same clock beside
 * `usually 1–3 min`, and a shipped plot's card keeps it as `ready in 1:12`. The
 * frame's tab says how the service is (`LoadMood`: `● quiet`, `● busy`, `●
 * resting until 01:00`), from the one reader of `/status` (`useAgentStatus`),
 * which reads again after each run and while the tab is visible. The run's
 * progress grid and the admin meters are sections of the admin menu, and the
 * data card says why its controls wait.
 *
 * The admin menu's `all 15 libraries` is the admin's test run, the fan-out (in the library
 * menu as `all` until 2026-11-06). While it is on, the library chip reads `all 15 libraries ▾`
 * and the composer's plot button is `.plot_all()`: the
 * data with its bindings, confirmed first as `.create_plot()` does, plotted in
 * every library of the header at once (`FanOut`), a session per library into which the server copies
 * this session's confirmed version, whatever its origin (pasted, opened,
 * computed or changed by the assistant), at most `AGENT_USER_MAX_RUNS` plots
 * running, each through the normal run queue. This session stays the data
 * session; in step 2 the message box waits (typed text would not go along) and
 * the status line says so, while in step 1 the chat about the data goes on as
 * without the fan-out. Any library picked in the library menu turns it off again
 * (the library in use only that); while the panel is open, neither the menu nor
 * the data card change anything, so every library copies the same confirmed
 * data. The toggle is not in the URL (`&all=1` until 2026-11-06): a reload opens
 * a new session anyway, and the toggle is one click.
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
 * 2. The lane. A browser without the admin hint (`src/utils/adminAuth.ts`) or local
 *    development is a visitor's: it sends no request to the debug API, and runs on the
 *    public lane while the API's `GET /agent/lane` is open (`useAgentLaneOpen`); closed,
 *    the page says so. A browser with the hint asks the admin lane's `GET /status` first
 *    (`useAgentAdmin`), and the page waits for the answer, which picks the lane: the admin
 *    lane, also while the public door is closed; or, after a refusal or no answer (an
 *    expired Cloudflare Access session), the public lane, while the admin menu says the
 *    admin session expired and links to `/debug`. A refusal later in the session does the
 *    same. "View as visitor" in the admin menu runs the public lane for this tab, exactly
 *    as a visitor's. The BFF's admin gate is the real check; the page only picks the API.
 *    On both lanes the experimental notice stands above the frame (`ExperimentalNotice`),
 *    the feedback form's data box starts unticked with the consent line under it, and an
 *    error reads the same; the admin's diagnostics are in the admin menu.
 * 3. Analytics: while the page serves an admin (either lane), it sends no pageview and no
 *    event (`src/analytics/mute.ts`), so the admin's own use never counts as a visitor's.
 *
 * Design: docs/concepts/agent-network.md ("Frontend", "Request flow").
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Link as RouterLink, useSearchParams } from 'react-router-dom';

import Box from '@mui/material/Box';
import GlobalStyles from '@mui/material/GlobalStyles';

import { setAnalyticsMuted } from 'src/analytics/mute';
import { LoaderSpinner } from 'src/components/LoaderSpinner';
import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_TO_LANG, LIBRARIES } from 'src/constants';
import { CONFIG } from 'src/global-config';
import { useAgentAdmin } from 'src/hooks/useAgentAdmin';
import { useAgentLaneOpen } from 'src/hooks/useAgentLaneOpen';
import {
  type AgentSessionState,
  type BindingMap,
  carryDecisions,
  type DatasetUpload,
  type ParseResult,
  sessionBusy,
  sessionHoldsWork,
  useAgentSession,
} from 'src/hooks/useAgentSession';
import { loadMood, useAgentStatus } from 'src/hooks/useAgentStatus';
import { useAnalytics } from 'src/hooks/useAnalytics';
import { useTheme } from 'src/hooks/useLayoutContext';
import { useLeaveWarning } from 'src/hooks/useLeaveWarning';
import {
  agentApi,
  type AgentLane,
  type AgentStatus,
  browserLocale,
  budgetShare,
  DEFAULT_AGENT_LIBRARIES,
  MAX_MESSAGE_CHARS,
  PUBLIC_LANE,
} from 'src/lib/agent';
import { apiGet, endpoints } from 'src/lib/api';
import { NotFoundPage } from 'src/pages/NotFoundPage';
import { paths, specPath } from 'src/routes/paths';
import {
  AdminMenu,
  AdminMeters,
  type AdminMode,
  AdminSection,
} from 'src/sections/agent-chat/AdminMenu';
import { attachmentSummary } from 'src/sections/agent-chat/attachmentText';
import { ChatFeedback } from 'src/sections/agent-chat/ChatFeedback';
import { ChatFrame, FrameRule, StatusLine } from 'src/sections/agent-chat/ChatFrame';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { Composer } from 'src/sections/agent-chat/Composer';
import { DataPanel } from 'src/sections/agent-chat/DataPanel';
import { ExperimentalNotice } from 'src/sections/agent-chat/ExperimentalNotice';
import { FanOut } from 'src/sections/agent-chat/FanOut';
import { DEFAULT_USER_MAX_RUNS } from 'src/sections/agent-chat/fanoutRules';
import { LanguageChip } from 'src/sections/agent-chat/LanguageChip';
import { LibraryChip } from 'src/sections/agent-chat/LibraryChip';
import { LoadMood } from 'src/sections/agent-chat/LoadMood';
import {
  attachmentWaitLine,
  CHAIN_READING_TEXT,
  chainStopText,
  describeDataFailure,
  DROP_HINT_TEXT,
  ERROR_TEXT,
  LEAVE_TEXT,
  VIEW_SWITCH_TEXT,
} from 'src/sections/agent-chat/messages';
import {
  boxData,
  type ChainStep,
  chainStep,
  type ChainStop,
  sameStopMark,
  type StopMark,
  stopMark,
} from 'src/sections/agent-chat/plotChain';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { previewsByLibrary } from 'src/sections/agent-chat/specReference';
import { StartItem } from 'src/sections/agent-chat/StartItem';
import {
  hasPlotHere,
  inStep2,
  plotButtonKind,
  plotButtonLabel,
  runView,
  statusLine,
} from 'src/sections/agent-chat/steps';
import {
  bodyTextSx,
  labelSx,
  MASTHEAD_CLEARANCE,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { type Attachment, useChatAttachment } from 'src/sections/agent-chat/useChatAttachment';
import { colors, fontSize, proseLinkStyle, typography } from 'src/theme';
import { readAdminToken, readViewAsVisitor, setViewAsVisitor } from 'src/utils/adminAuth';
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

/**
 * The first of these controls that can take the focus now, in order of preference. An inert
 * button (`aria-disabled`) takes it too: it keeps its place and says why it waits.
 */
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

/** The chat's Highcharts note, shown while the session plots in Highcharts (the legal page says the same). */
export const HIGHCHARTS_NOTE =
  'highcharts is free for non-commercial use; a commercial use needs a licence from Highsoft.';

/**
 * The page while the public lane is closed (`GET /agent/lane` answered no) and the page does not
 * run on the admin lane. An admin's browser keeps the admin menu below the text: "view as visitor"
 * to switch back, or the line about an expired admin session.
 */
function LaneClosed({ adminMenu = null }: { adminMenu?: React.ReactNode }) {
  return (
    <Notice title="use with my data · experimental">
      the assistant is closed right now. please try again later; the{' '}
      <Box component={RouterLink} to={paths.plots} sx={proseLinkStyle}>
        catalogue
      </Box>{' '}
      stays open.
      {/* Its row is the admin menu's too (`admin-menu…`), so the parity test leaves it out. */}
      {adminMenu && (
        <Box data-testid="admin-menu-row" sx={{ display: 'flex', mt: 2 }}>
          {adminMenu}
        </Box>
      )}
    </Notice>
  );
}

/** What the page hands the chat for the admin menu, in an admin's browser only. */
interface AdminView {
  mode: AdminMode;
  /** The code the failed admin check answered with. */
  failure: string | null;
  onViewAsVisitor: (on: boolean) => void;
}

export function AgentChatPage() {
  const [params, setParams] = useSearchParams();
  const { trackPageview, trackEvent } = useAnalytics();
  const laneOpen = useAgentLaneOpen();
  const adminCheck = useAgentAdmin();
  const { admin } = adminCheck;
  // "View as visitor", the admin menu's switch, for this tab: the public lane exactly.
  const [asVisitor, setAsVisitor] = useState(readViewAsVisitor);
  const adminLane = admin === 'admin' && !asVisitor;
  const lane: AgentLane = adminLane ? 'admin' : 'public';
  // The page waits for the answer that picks the lane: the admin check while it may lead to the
  // admin lane, else the public lane's door.
  const deciding = !adminLane && ((admin === 'checking' && !asVisitor) || laneOpen === null);
  const allowed = CONFIG.features.agentChat && !deciding && (adminLane || laneOpen === true);
  // An admin's browser, on either lane: the admin's own use counts as no visitor's.
  const muted = admin !== 'none';
  // The admin menu, in an admin's browser only; none while the check that may lead to the admin
  // lane is out, since the page waits for it then.
  const adminMode: AdminMode | null =
    admin === 'expired'
      ? 'expired'
      : admin === 'none'
        ? null
        : asVisitor
          ? 'visitor'
          : admin === 'admin'
            ? 'admin'
            : null;
  const onViewAsVisitor = useCallback((on: boolean) => {
    setViewAsVisitor(on);
    setAsVisitor(on);
  }, []);

  const spec = params.get('spec') ?? '';
  const library = params.get('library') ?? '';
  // The language follows the library (the catalogue's pairing), never the query:
  // `?library=matplotlib&language=javascript` would otherwise pick the wrong
  // highlighter and a back link to a page that does not exist.
  const language = LIB_TO_LANG[library] ?? 'python';
  const valid = SPEC_PATTERN.test(spec) && (LIBRARIES as readonly string[]).includes(library);

  // Declared before the open's effect below, so the switch is on before the page records anything.
  useEffect(() => {
    if (!muted) return;
    setAnalyticsMuted(true);
    return () => setAnalyticsMuted(false);
  }, [muted]);

  // Every edit of the query starts from the latest one, also an edit made after an await (a
  // library switch), so one edit never brings back what another removed (`source`).
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

  // `source` only says where the visitor came from; it is read once for
  // `agent_open` and dropped, so a reload counts as a direct open. An admin's
  // open is no visitor's: the page records nothing for it (`muted`).
  const openTracked = useRef(false);
  useEffect(() => {
    if (!allowed || !valid || openTracked.current) return;
    openTracked.current = true;
    const source = params.get('source');
    if (!muted) {
      trackPageview(paths.agent);
      trackEvent('agent_open', {
        library,
        source: source && OPEN_SOURCES.has(source) ? source : 'direct',
        spec,
      });
    }
    if (source) {
      const next = new URLSearchParams(params);
      next.delete('source');
      setParams(next, { replace: true });
    }
  }, [allowed, valid, params, setParams, library, spec, trackEvent, trackPageview, muted]);

  if (!CONFIG.features.agentChat) return <NotFoundPage />;
  if (deciding) return <NoIndex />;
  const adminView: AdminView | null = adminMode
    ? { mode: adminMode, failure: adminCheck.failure, onViewAsVisitor }
    : null;
  if (!allowed) {
    return (
      <LaneClosed
        adminMenu={
          adminView && (
            <AdminMenu
              mode={adminView.mode}
              failure={adminView.failure}
              onViewAsVisitor={onViewAsVisitor}
            />
          )
        }
      />
    );
  }
  if (!valid) {
    return (
      <Notice title="use with my data">
        open it from a plot&apos;s <code>.use_my_data()</code>, or start with{' '}
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
  const token = adminLane ? readAdminToken() : PUBLIC_LANE;
  return (
    <AgentChat
      key={`${spec}|${token}`}
      specId={spec}
      library={library}
      language={language}
      token={token}
      lane={lane}
      admin={adminView}
      onAdminRefused={adminCheck.refused}
      takeAdminStatus={adminCheck.takeStatus}
      onLibraryChange={onLibraryChange}
    />
  );
}

interface AgentChatProps {
  specId: string;
  library: string;
  language: string;
  /** The admin token, or `PUBLIC_LANE` on the public lane. */
  token: string;
  /** The API the page calls: it changes nothing the page shows outside the admin menu. */
  lane: AgentLane;
  /** The admin menu's state, in an admin's browser; null for a visitor. */
  admin: AdminView | null;
  /** The admin lane refused a call (401 or 403): the page falls back to the public lane. */
  onAdminRefused: () => void;
  /** The admin check's status answer, once (`useAgentAdmin`): the admin lane asks no second time. */
  takeAdminStatus: () => AgentStatus | null;
  onLibraryChange: (library: string) => void;
}

function AgentChat({
  specId,
  library,
  language,
  token,
  lane,
  admin,
  onAdminRefused,
  takeAdminStatus,
  onLibraryChange,
}: AgentChatProps) {
  const { trackEvent } = useAnalytics();
  const { isDark } = useTheme();
  const locale = useMemo(() => browserLocale(), []);
  const session = useAgentSession({ specId, library, locale, token });
  const { state } = session;
  const [draft, setDraft] = useState('');
  const [title, setTitle] = useState<string | null>(null);
  // The catalogue plot of the start item: its preview per library, and the spec's `data` bullets,
  // the columns ⓘ's fallback while the session's open names no roles.
  const [reference, setReference] = useState<{
    previews: Record<string, ThemedPreviewSource>;
    data: string[];
  } | null>(null);
  // The libraries the catalogue implements the spec in (null before its answer, or after it failed),
  // and whether that answer is in.
  const [implemented, setImplemented] = useState<string[] | null>(null);
  const [specSettled, setSpecSettled] = useState(false);
  // The lane's `/status`, its one reader (`useAgentStatus`): the enabled libraries and the run cap
  // of its first answer, and the load the frame's tab shows as its mood, read again while the tab
  // is visible and after each run.
  const agentStatus = useAgentStatus({ token, lane, takeAdminStatus, running: !!state.run });
  const libraries = useMemo(() => {
    const base = agentStatus.libraries ?? [...DEFAULT_AGENT_LIBRARIES];
    return implemented ? base.filter(lib => implemented.includes(lib)) : base;
  }, [agentStatus.libraries, implemented]);
  // `.plot_all()`: the caller's own run cap (`user_max_runs`, 5 for an admin).
  const maxRuns = agentStatus.userMaxRuns ?? DEFAULT_USER_MAX_RUNS;
  // Both answers are in (or failed): before that, the libraries and the limit are fallbacks.
  const listsSettled = specSettled && agentStatus.settled;
  // The admin meters' share of the day budget (`/budget`), read as the admin menu opens.
  const [budgetPercent, setBudgetPercent] = useState<number | null>(null);
  // The session whose confirmed data the open fan-out copies.
  const [fanOut, setFanOut] = useState<{
    sourceSession: string;
    upload?: DatasetUpload;
    bindings: BindingMap;
    libraries: string[];
  } | null>(null);
  // The admin menu's fan-out toggle (`all 15 libraries`); it takes effect only while `offerAll`
  // holds (`plotAll`), when the libraries are the server's.
  const [allPressed, setAllPressed] = useState(false);
  // The library menu's chip, where the focus returns after the fan-out's panel.
  const libraryRef = useRef<HTMLButtonElement>(null);
  const fanOutRef = useRef<HTMLElement>(null);
  // Set by a key press on `.plot_all()`: the panel it opens takes the focus, once.
  const fanOutFocus = useRef(false);
  // Set by the panel's `.close()`, which takes its focused button away: the focus returns, once.
  const fanOutReturn = useRef(false);
  const tailRef = useRef<HTMLDivElement>(null);
  const messageRef = useRef<HTMLTextAreaElement>(null);
  const plotRef = useRef<HTMLButtonElement>(null);
  // What the last removal from the remembered decisions did, which the footer's status region says;
  // numbered, so the same words a second time (a second `.forget_all()`) are a new text to read.
  const [memoryNote, setMemoryNote] = useState({ text: '', n: 0 });
  const announceMemory = useCallback(
    (text: string) => setMemoryNote(note => ({ text, n: note.n + 1 })),
    []
  );
  // `.feedback()` at the status line's end opened the chat's own feedback form above it; the
  // form takes the focus once, as it opens from that click.
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const feedbackFocus = useRef(false);
  const openFeedback = useCallback(() => {
    feedbackFocus.current = true;
    setFeedbackOpen(true);
  }, []);
  const takeFeedbackFocus = useCallback(() => {
    const take = feedbackFocus.current;
    feedbackFocus.current = false;
    return take;
  }, []);
  // The plot button's one click on data in the box (`plotChain.ts`): the chain in flight (its
  // number, which a newer chain or the user's next step replaces), and for the status line that
  // it reads, or where it stopped at the card and on which state.
  const chainRef = useRef<number | null>(null);
  const chainSeq = useRef(0);
  const [chainView, setChainView] = useState<
    { kind: 'reading' } | { kind: 'stopped'; stop: ChainStop; mark: StopMark } | null
  >(null);
  // The page as it last rendered, which the chain reads after its awaits: the session, what the
  // page adds, and the plot click on the data as it is then.
  const chainPage = useRef<{
    state: AgentSessionState;
    plotAll: boolean;
    attachment: boolean;
    plot: () => void;
  } | null>(null);
  // The chain waits for the next commit while the session settles: every commit lets it read on.
  const commitWaiters = useRef<(() => void)[]>([]);
  useEffect(() => {
    if (commitWaiters.current.length === 0) return;
    const waiting = commitWaiters.current;
    commitWaiters.current = [];
    for (const resolve of waiting) resolve();
  });
  // A page that goes ends its chain: a waiting one reads on once more, finds it ended, and stops.
  useEffect(
    () => () => {
      chainRef.current = null;
      const waiting = commitWaiters.current;
      commitWaiters.current = [];
      for (const resolve of waiting) resolve();
    },
    []
  );

  // The spec's title, implemented libraries, previews and data bullets come from the public
  // catalogue API, best effort; the enabled libraries from the agents service (`useAgentStatus`).
  useEffect(() => {
    const controller = new AbortController();
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
        setImplemented(spec.implementations.map(impl => impl.library_id));
      })
      .catch(() => undefined)
      .finally(() => {
        if (!controller.signal.aborted) setSpecSettled(true);
      });
    return () => controller.abort();
  }, [specId]);

  // A `service_paused` refusal says the day budget is spent: the tab rests at once, until the
  // reset the refusal names, without waiting for the next read. A data call's `429` does not:
  // its own line says the same with the time, and the next read brings the mood.
  const { markPaused } = agentStatus;
  const pausedSeen = useRef(0);
  useEffect(() => {
    for (let index = state.items.length - 1; index >= 0; index -= 1) {
      const item = state.items[index];
      if (item.id <= pausedSeen.current) break;
      if (item.kind === 'refusal' && item.code === 'service_paused' && item.until) {
        pausedSeen.current = item.id;
        markPaused(item.until);
        break;
      }
    }
  }, [state.items, markPaused]);

  // The admin meters, as the admin menu opens on the admin lane: the runs in flight through the
  // one status reader (also during a run, when its answer feeds the meters alone), and the day
  // budget's share. The public lane has no `/budget`, and neither has "view as visitor".
  const { refresh: refreshStatus } = agentStatus;
  const readMeters = useCallback(() => {
    void refreshStatus();
    agentApi
      .budget(token)
      .then(budget => setBudgetPercent(budgetShare(budget)))
      .catch(() => undefined);
  }, [refreshStatus, token]);

  // A refused admin call ends the admin hint, and the page falls back to the public lane with a
  // new session (`useAgentAdmin`); a refusal on the public lane says nothing about the admin.
  useEffect(() => {
    if (lane === 'admin' && state.phase === 'unauthorized') onAdminRefused();
  }, [lane, state.phase, onAdminRefused]);

  // The progress and the replies arrive at the foot of the thread, below the
  // data card: bring the foot into view when a turn starts.
  const running = !!state.run;
  useEffect(() => {
    if (running) tailRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'nearest' });
  }, [running]);

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
  // A plot button may start on stored data once every required role is bound and nothing is in
  // flight: on unconfirmed data its click confirms the data as shown first (`startPlot`). Data
  // waiting in the box goes first instead (`sendsFirst`), never the data before it.
  const canCreate =
    state.phase === 'ready' &&
    !!state.dataset &&
    state.bindingsComplete &&
    !state.transcription &&
    !attachment &&
    !busy;
  // The server files a version under its (spec, library) pair; the spec cannot change in a
  // session yet, so the library alone tells the pair.
  const hasPlot = hasPlotHere(state);
  // The fan-out's toggle in the admin menu only once the libraries and the limit are the
  // server's: a snapshot of the fallbacks would leave libraries out or start more runs than the
  // server takes (`run_limit`). `.plot_all()` is the admin's test run: never on the public lane,
  // whose BFF has no copy route, so "view as visitor" has none either.
  const offerAll = lane === 'admin' && listsSettled && libraries.length > 1 && !reopen;
  const plotAll = allPressed && offerAll;
  // The chat waits only where `.plot_all()` is the action, in step 2: the fan-out takes no
  // text. Before it, with or without data, the box talks about the data as without `all`.
  const chatLocked = plotAll && step2;
  // After a switch whose answer offered it: the plot in this library with the remembered
  // decisions (`carry_plot`), which the plot button's click runs while the box is empty. Not
  // while `all` is pressed, whose fan-out makes fresh plots everywhere. The button keeps its
  // name; the status line names the decisions, when there are any to take along.
  const carry =
    state.carryOffer?.target.library === state.library && state.dataset && !plotAll
      ? state.carryOffer
      : null;
  const carryCount = carry ? carryDecisions(carry, state.memory) : 0;
  // `.example_data()` in the data line above the box: the other way to data besides a paste,
  // inert once there is data, which it would replace. A table read from text that waits for its
  // decision is data at hand, and so is a table or a file waiting in the box: it waits then, as
  // while anything is in flight.
  const exampleActive =
    state.phase === 'ready' && !state.dataset && !state.transcription && !attachment && !busy;
  // What the box holds that the plot button sends before it plots (`plotChain.ts`): an
  // attachment, or a table typed into the box. Not with the admin's fan-out, whose `.plot_all()`
  // copies data already stored.
  const boxSends = useMemo(() => boxData(attachment, draft), [attachment, draft]);
  // New data in the box, or on its way after the click: the button names the plot it makes.
  const boxHoldsData = !!attachment || boxSends === 'typed' || chainView?.kind === 'reading';
  // The plot button in its fixed place: what it is, and the label the status line, the card's
  // own step-1 line and the thread name it by.
  const plotKind = plotButtonKind(state, plotAll, boxHoldsData);
  const plotAction = plotAll ? '.plot_all()' : plotButtonLabel(state, boxHoldsData);
  // One click sends the box's data as Enter would, then plots once the reading comes back clean
  // (owner decision of 2026-11-08), whenever nothing runs.
  const sendsFirst =
    boxSends !== null &&
    plotKind !== 'all' &&
    state.phase === 'ready' &&
    !!state.sessionId &&
    !busy &&
    !fanOut;
  // `.update_plot() →` on confirmed data whose plot is current sends the box's text, a change of
  // the latest version: with an empty box there is nothing to update. On data or bindings
  // changed since, and with a switch's offer, it plots with an empty box too.
  const plotNeedsText = plotKind === 'update' && step2 && !carry;
  const plotText = draft.trim();
  // Text over the cap is never cut and never goes, also not as a plot's request.
  const plotActive =
    plotKind === 'all'
      ? canCreate && !fanOut
      : sendsFirst ||
        (canCreate && plotText.length <= MAX_MESSAGE_CHARS && (!plotNeedsText || plotText !== ''));
  // The click starts from the catalogue plot although the library has one: data or bindings
  // changed since, or new data in the box, so the plot is made anew, with the remembered decisions.
  const plotFresh = hasPlot && (!step2 || boxHoldsData) && plotKind !== 'all';
  // The status line at the frame's foot, the plot button's description: the step, then what the
  // button waits for (an attachment, a pending table read from text, a required role without a
  // column, a run), what to check, or what the click does.
  const status = statusLine(state, {
    action: plotAction,
    // With data, the line says the attachment replaces it; it names the plot button that takes
    // it along, unless only Enter sends it.
    attachmentLine: attachment
      ? attachmentWaitLine(
          state.dataset ? state.dataset.parsed.profile.rows : null,
          boxSends === 'attachment' && plotKind !== 'all' ? plotAction : null
        )
      : null,
    readingLine: chainView?.kind === 'reading' ? CHAIN_READING_TEXT : null,
    // Where the one click stopped, while nothing changed since.
    stopLine:
      chainView?.kind === 'stopped' && sameStopMark(chainView.mark, state)
        ? chainStopText(chainView.stop, plotAction)
        : null,
    carry: carry ? { library: carry.target.library, decisions: carryCount } : null,
    lockedLibraries: chatLocked ? libraries.length : null,
  });
  // `.start_over()` at the status line's end: once the confirmed data has a plot here, and after
  // a switch's offer, the plot from the catalogue code without the carry.
  const startOverShown = !plotAll && ((step2 && hasPlot) || carryCount > 0);
  // The chat's own feedback before the first plot: `.feedback()` at the status line's end opens
  // its form above the line. Not while a turn runs, which may still bring the plot; a sent
  // record stays in view. A library switch alone is no conversation to report.
  const feedbackOffer =
    state.items.some(item => item.kind !== 'switch') &&
    !state.run &&
    Object.keys(state.versions).length === 0;
  const feedbackShown = !!state.chatFeedback || (feedbackOpen && feedbackOffer);
  // While a plot is drawn, what the run sends into the thread waits for its card, so the user's
  // prompt and the working line below it stay in view (`runView`).
  const view = runView(state);
  // The service's mood on the frame's tab (`LoadMood`), from the last read, busy also while the
  // own turn waits in the queue (where it stands is the working line's); none before an answer.
  const ownQueued = state.run?.steps[state.run.steps.length - 1]?.step === 'queued';
  const mood = loadMood(agentStatus.load, ownQueued);
  // The session's own state while nothing waits, so the thread's state changes only with it.
  const threadState = useMemo(
    () => (view.items === state.items ? state : { ...state, items: view.items }),
    [state, view.items]
  );

  // A key press on `.plot_all()` continues in the panel it opened: the button waits while
  // the panel is open, and the panel is where the plots come in.
  useEffect(() => {
    if (!fanOut || !fanOutFocus.current) return;
    fanOutFocus.current = false;
    fanOutRef.current?.focus();
  }, [fanOut]);

  // The panel's `.close()` went with the panel: the focus returns to `.plot_all()`, which
  // opened it, or, without it, to the library menu or the message box.
  useEffect(() => {
    if (fanOut || !fanOutReturn.current) return;
    fanOutReturn.current = false;
    firstEnabled(plotRef.current, libraryRef.current, messageRef.current)?.focus();
  }, [fanOut]);

  /**
   * The form's submit, Enter in the box, the `↵` on a touch screen and `.update_plot() →` on a
   * current plot: the text goes as a turn about the data or the plot, never as a confirmation.
   * In step 1 a plot wish in it is kept for the next `.create_plot()` (the assistant's
   * `keep_plot_request`); in step 2 before the first plot the assistant makes that plot with
   * it. While `all` is pressed in step 2 nothing goes: the fan-out takes no text.
   */
  const handleSend = (event?: React.FormEvent) => {
    event?.preventDefault();
    cancelChain();
    if (attachment) {
      void sendAttachment(attachment);
      return;
    }
    const text = draft.trim();
    // Text over the cap is never cut: the counter is red and nothing goes until it fits.
    if (!text || text.length > MAX_MESSAGE_CHARS || busy || chatLocked) return;
    // A table in the box is data, as its paste would have been: the assistant reads no data from
    // a message. It goes without a note, because the parser keeps the lines around it as notes.
    const typed = attach.attachTyped(text);
    setDraft('');
    if (typed) {
      void sendAttachment(typed, '');
      return;
    }
    void session.sendMessage(text);
  };

  /** Text back into the box, before anything typed since, with a blank line between them. */
  const restoreText = (text: string) =>
    setDraft(current => (current.trim() ? `${text}\n\n${current}` : text));

  // The attachment a table was read from, while that table waits for `.use()` or `.discard()`:
  // a discard gives it back for another try.
  const transcribedFrom = useRef<Attachment | null>(null);

  /**
   * `.discard()`: the table read from text goes, and what it came from comes back. Short pasted
   * or typed text goes into the box, to edit and send as a message; a file's text, or text the
   * box could not send, waits as the attachment again, unless the user attached something since.
   */
  const handleDiscard = () => {
    session.discardTranscription();
    const sent = transcribedFrom.current;
    transcribedFrom.current = null;
    if (!sent) return;
    if (sent.via !== 'file' && sent.text.length <= MAX_MESSAGE_CHARS) restoreText(sent.text);
    else if (!attachment) attach.reattach(sent);
  };

  /** ×: the attachment goes; a typed table goes back into the box, since nothing else holds it. */
  const handleRemoveAttachment = () => {
    cancelChain();
    if (attachment?.via === 'typed') restoreText(attachment.text);
    attach.remove();
  };

  /**
   * Enter with an attachment: the dataset route reads it, and the typed text goes
   * along as its note, the first turn once the data is stored. The field lets go of the note at
   * once; when nothing was stored (a table read from text to decide on, text that went to the
   * chat, a refusal, nothing started), the note goes back into it, before anything typed since.
   * A refused attachment stays red with the reason, for Enter to try again or × to drop it.
   * `ownNote` replaces the box's text as the note: a typed table was that text, and goes alone.
   * Resolves to how the parse and its turn ended (the plot button's one click reads on from it),
   * or null when nothing started.
   */
  const sendAttachment = async (
    sent: Attachment,
    ownNote?: string
  ): Promise<ParseResult | null> => {
    if (busy || (sent.status !== 'ready' && sent.status !== 'failed')) return null;
    // Also while `all` holds the box in step 2: an attachment opens the box for its note, since
    // the new data takes the session back to step 1, where the chat about the data goes on.
    const note = ownNote ?? draft.trim();
    if (note.length > MAX_MESSAGE_CHARS) return null;
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
    return result;
  };

  /** The user's own next step (typing, a paste, Enter, a click) ends the one click's chain. */
  const cancelChain = () => {
    if (chainRef.current === null) return;
    chainRef.current = null;
    setChainView(null);
  };

  /**
   * The plot button's click on data in the box (`plotChain.ts`): it goes as Enter sends it, with
   * the box's text as its note (`sendAttachment`). Once the reading ends, the chain reads the page
   * after each render (`chainPage`) until `chainStep` decides, then acts once: it plots as a click
   * on the plot button would on that data, or keeps where it stopped for the status line. A chain
   * the user's next step ended (`cancelChain`), or a newer one, does nothing more; the page never
   * restores a chain, so a reload or a closed tab ends it with the session.
   */
  const plotChain = async (sent: Attachment, ownNote?: string) => {
    chainSeq.current += 1;
    const id = chainSeq.current;
    chainRef.current = id;
    // The reading's items come after these; the state at the click is the one not to decide on.
    const since = state.nextItemId;
    let seen: AgentSessionState = state;
    setChainView({ kind: 'reading' });
    try {
      const result = await sendAttachment(sent, ownNote);
      let rechecked = false;
      while (chainRef.current === id) {
        const page = chainPage.current;
        // Until the page rendered after the last await, it shows what the chain already decided
        // on. A send that stored nothing ends the chain at once: it may have changed no session
        // state.
        const step: ChainStep =
          !result || !page || result.outcome !== 'stored'
            ? { kind: 'stop', stop: null }
            : page.state === seen
              ? { kind: 'wait' }
              : chainStep(page.state, { result, since, rechecked }, page);
        if (step.kind === 'wait') {
          await new Promise<void>(resolve => commitWaiters.current.push(resolve));
          continue;
        }
        if (step.kind === 'recheck' && page) {
          rechecked = true;
          seen = page.state;
          if (await session.checkBindings()) continue;
        }
        chainRef.current = null;
        if (step.kind === 'plot' && page) {
          setChainView(null);
          page.plot();
        } else if (step.kind === 'stop' && step.stop && page) {
          setChainView({ kind: 'stopped', stop: step.stop, mark: stopMark(page.state) });
        } else {
          setChainView(null);
        }
        return;
      }
    } finally {
      // A failure on the way the session did not catch itself: the chain ends, and the status
      // line no longer says that it reads.
      if (chainRef.current === id) {
        chainRef.current = null;
        setChainView(null);
      }
    }
  };

  /** The plot button with data in the box: the attachment, or the table typed there, goes first. */
  const sendAndPlot = () => {
    if (attachment) {
      void plotChain(attachment);
      return;
    }
    const typed = attach.attachTyped(draft.trim());
    if (!typed) return;
    setDraft('');
    void plotChain(typed, '');
  };

  /**
   * A plot click (the plot button, `.start_over()`): the data and the bindings as the card shows
   * them are what the plot takes, so data that is not confirmed yet is confirmed first; a
   * refusal stops here and shows under the composer, and nothing is plotted. Then the plot
   * starts: the box's text, when the button takes it (`withText`, the plot button), goes as the
   * turn that makes the plot with that request, else the catalogue plot (`create_plot`) or the
   * switch's offer (`carry_plot`), under `label`, the button as it read, which the thread shows
   * for the turn. The confirmation's busy state and the session's own guards hold back a second
   * click, also one before the state caught up. The button stays where it is, inert while the
   * plot runs, so the focus stays on it. A table typed into the box never comes here: it is data,
   * which the click reads first (`sendAndPlot`).
   */
  const startPlot = async (kind: 'create' | 'carry', withText: boolean, label: string) => {
    if (!canCreate) return;
    const text = withText ? draft.trim() : '';
    // The turn would refuse it after the box let go of it: nothing confirms, nothing is lost.
    if (text.length > MAX_MESSAGE_CHARS) return;
    if (!state.dataConfirmed && !(await session.confirmData())) return;
    if (text) {
      // Only the text that went: an edit made while the confirmation ran stays in the box. The
      // turn puts the text in the thread before its request goes, so a turn refused at once
      // (a limit, the capacity, the network) shows it there with the error: nothing is lost.
      setDraft(current => (current.trim() === text ? '' : current));
      void session.sendMessage(text);
    } else {
      void (kind === 'carry' ? session.carryPlot(label) : session.createPlot(label));
    }
  };
  // The one click's chain reads the page from here after its awaits: its plot is this render's
  // click on the plot button with an empty box, the switch's offer when there is one.
  chainPage.current = {
    state,
    plotAll,
    attachment: !!attachment,
    plot: () => void startPlot(carry ? 'carry' : 'create', false, plotButtonLabel(state)),
  };

  /**
   * A library picked in the menu. While the fan-out is on, any pick turns it
   * off: the library in use only that; another library switches as it would
   * without it. The URL follows a switch the server took; a refused one
   * rejects, and the menu shows why under its chip.
   */
  const handlePick = useCallback(
    async (next: string) => {
      // The user's own step: the one click's chain plots nothing after it.
      if (chainRef.current !== null) {
        chainRef.current = null;
        setChainView(null);
      }
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
   * `.plot_all()`, the action while the fan-out is on: the data with its bindings, in every
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
   * `.start_over()` at the status line's end: the fresh plot from the catalogue code, with the
   * remembered decisions, without a switch's carry; text in the box stays there.
   */
  const handleStartOver = () => {
    cancelChain();
    void startPlot('create', false, '.start_over()');
  };

  /**
   * The plot button. `.plot_all()` opens the fan-out; with data in the box the click reads it and
   * plots it once it reads clean (`sendAndPlot`); `.update_plot() →` on a current plot sends the
   * box's text as Enter does; every other click plots, with the box's text as the request: the
   * switch's offer with the remembered decisions when there is one (`carry_plot`), else the
   * catalogue plot. The thread names the turn as the button read.
   */
  const handlePlot = (event: React.MouseEvent) => {
    cancelChain();
    if (plotKind === 'all') {
      void handlePlotAll(event);
      return;
    }
    if (sendsFirst) {
      sendAndPlot();
      return;
    }
    if (plotNeedsText) {
      handleSend();
      return;
    }
    void startPlot(carry ? 'carry' : 'create', true, plotButtonLabel(state));
  };

  /**
   * "View as visitor" in the admin menu: the other lane opens a session of its own, so one that
   * holds work asks first, as leaving the page does.
   */
  const handleViewAsVisitor = (on: boolean) => {
    if (sessionHoldsWork(state) && !window.confirm(VIEW_SWITCH_TEXT)) return;
    admin?.onViewAsVisitor(on);
  };

  // The admin menu, the one admin-only element, at the header row's right end. Its fan-out toggle
  // and `.save()` exist on the admin lane only (the public BFF has neither route), the diagnostics
  // say what a visitor reads as "closed".
  const adminMenu = admin && (
    <AdminMenu
      mode={admin.mode}
      failure={admin.failure}
      onViewAsVisitor={handleViewAsVisitor}
      fanOut={
        offerAll
          ? {
              libraries: libraries.length,
              pressed: plotAll,
              // As the library chip: not during a run or while the fan-out's panel is open.
              disabled: busy || !!fanOut || state.phase !== 'ready',
              onChange: setAllPressed,
            }
          : null
      }
      save={
        lane === 'admin' && !reopen
          ? {
              disabled: state.phase !== 'ready' || !state.sessionId || busy,
              onSave: session.saveSession,
            }
          : null
      }
      diagnostics={
        state.phase === 'error' && state.failure?.code === 'not_enabled'
          ? [
              lane === 'admin'
                ? 'not_enabled · the agent chat is switched off on this server (AGENT_ENABLED)'
                : 'not_enabled · the public lane is closed on this server (AGENT_PUBLIC_ENABLED, or AGENT_ENABLED)',
            ]
          : []
      }
      onOpen={admin.mode === 'admin' ? readMeters : undefined}
    >
      {/* The running turn's progress grid, the working line's detail, in the admin's and the
          visitor's view alike; not after an expired admin session, whose menu says only that. */}
      {admin.mode !== 'expired' && state.run && (
        <AdminSection heading="progress of this turn">
          <ProgressTimeline run={state.run} />
        </AdminSection>
      )}
      {/* The meters on the admin lane only: the public lane has no `/budget`. */}
      {admin.mode === 'admin' && (
        <AdminSection heading="load · runs in flight, today's budget">
          <AdminMeters runs={agentStatus.inFlight} share={budgetPercent} />
        </AdminSection>
      )}
    </AdminMenu>
  );

  // A refusal on the admin lane falls back to the public lane (the effect above); in between,
  // nothing. On the public lane it reads as the closed door.
  if (state.phase === 'unauthorized') {
    return lane === 'public' ? <LaneClosed adminMenu={adminMenu} /> : <NoIndex />;
  }

  const backHref = specPath(specId, language, state.library);
  // Above the frame: the page's heading and the experimental notice, which stands above the first
  // input in every state of the session, on both lanes.
  const masthead = (
    <>
      <SectionHeader
        prompt="❯"
        title={
          <>
            agent · <em>use with my data</em>
          </>
        }
      />
      <ExperimentalNotice />
    </>
  );
  // The frame's header row, in plain words: the spec's title (the link back), the library and the
  // reply language as dropdowns, and in an admin's browser the admin menu. The catalogue plot,
  // the columns it expects and the how-to of the data are the start item's, the thread's first
  // item. At phone width the title takes the first line and the controls wrap below it.
  const headerRow = (
    <Box>
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          columnGap: { xs: 1, sm: 1.75 },
          rowGap: 1.25,
        }}
      >
        {/* A line of its own at phone width; the link is only as wide as the title. */}
        <Box sx={{ minWidth: 0, flexBasis: { xs: '100%', sm: 'auto' } }}>
          <Box
            component={RouterLink}
            to={backHref}
            sx={{
              fontFamily: typography.mono,
              fontSize: fontSize.md,
              color: 'var(--ink)',
              textDecoration: 'none',
              '&:hover': { color: colors.primary, textDecoration: 'underline' },
              overflowWrap: 'anywhere',
            }}
          >
            {title ?? specId}
          </Box>
        </Box>
        <LibraryChip
          library={state.library}
          libraries={libraries}
          allPressed={plotAll}
          // No session to switch: another library opens the page anew, with its own
          // session (a full navigation).
          hrefFor={
            reopen ? lib => paths.agentChat(specId, lib, LIB_TO_LANG[lib] ?? 'python') : undefined
          }
          // Not during a run (the server refuses a switch then) or while the fan-out's panel
          // is open: its sessions run on this one's data.
          disabled={!reopen && (busy || !!fanOut || state.phase !== 'ready')}
          onPick={handlePick}
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
        {adminMenu}
      </Box>
      {state.phase === 'ready' && state.library === 'highcharts' && (
        <Box role="note" data-testid="highcharts-licence" sx={{ ...labelSx, mt: 1.25 }}>
          # {HIGHCHARTS_NOTE}
        </Box>
      )}
    </Box>
  );

  // Until the session is open, or when it could not open, the frame holds the wait or the reason
  // below its header row, where the chat will stand.
  const ready = state.phase === 'ready';
  const notOpen =
    state.phase === 'opening' ? (
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
              ? // The same words on both lanes; the admin menu names the switch.
                'the assistant is closed right now. please try again later.'
              : (ERROR_TEXT[state.failure?.code ?? ''] ?? 'the session could not be opened.')}
          {state.phase === 'error' && <ReloadHint code={state.failure?.code} opening />}
        </Box>
      </Box>
    );

  // One tree in every phase: the tab's title, the heading, the notice, the frame and its header
  // row stay mounted when the session opens, so nothing above the thread flashes or loses its
  // state, and the tab names this page also while the session opens or after it failed.
  return (
    <>
      <title>{`agent · ${title ?? specId} | anyplot.ai`}</title>
      <NoIndex />
      {/* The focus, a jump to a chapter and the card the focus follows land below the site's
          sticky masthead, never under it (WCAG 2.4.11; `MASTHEAD_CLEARANCE`). */}
      <GlobalStyles styles={{ html: { scrollPaddingTop: MASTHEAD_CLEARANCE } }} />
      {/* `colorScheme` gives the native controls (scrollbars, select menus) the site theme. */}
      <Box
        sx={{
          py: 2,
          maxWidth: COLUMN_MAX_WIDTH,
          mx: 'auto',
          colorScheme: isDark ? 'dark' : 'light',
        }}
      >
        {masthead}
        {/* The whole chat takes a dropped file once the session is open: it becomes the message
            box's attachment. */}
        <ChatFrame
          header={headerRow}
          mood={mood && <LoadMood mood={mood} />}
          onDragEnter={ready ? attach.handleDragEnter : undefined}
          onDragOver={ready ? attach.handleDragOver : undefined}
          onDragLeave={ready ? attach.handleDragLeave : undefined}
          onDrop={ready ? attach.handleDrop : undefined}
        >
          {!ready ? (
            notOpen
          ) : (
            <>
              <ChatThread
                state={threadState}
                specId={specId}
                language={language}
                onRequestTheme={(version, theme) => void session.requestTheme(version, theme)}
                onFetchArtifact={session.fetchArtifact}
                onTrack={trackEvent}
                onOutcome={session.reportOutcome}
                onSendFeedback={session.sendFeedback}
                start={
                  <StartItem
                    title={title ?? specId}
                    library={state.library}
                    preview={reference?.previews[state.library] ?? null}
                    roles={state.specRoles}
                    bullets={reference?.data}
                  />
                }
                renderData={(part, version) => (
                  <DataPanel
                    state={state}
                    part={part}
                    version={version}
                    // Every control of the card is the user's own step: the one click's chain
                    // plots nothing after it (`cancelChain`).
                    onParse={(text, source, table, file) => {
                      cancelChain();
                      void session.parseData(text, false, source, table, { file });
                    }}
                    onConfirmTranscription={() => {
                      cancelChain();
                      transcribedFrom.current = null;
                      void session.confirmTranscription();
                    }}
                    onTrack={trackEvent}
                    // The sheet picker's read holds the composer back until its parse starts.
                    onConvert={(dataBase64, sheet) => {
                      cancelChain();
                      return session.readSheet(dataBase64, sheet);
                    }}
                    onDiscardTranscription={() => {
                      cancelChain();
                      handleDiscard();
                    }}
                    onBind={(name, column) => {
                      cancelChain();
                      session.setBinding(name, column);
                    }}
                    onUndo={() => {
                      cancelChain();
                      void session.undoData();
                    }}
                    onToLong={() => {
                      cancelChain();
                      void session.toLongData();
                    }}
                    // A look at the data (`.change()`, `.view_all()`) ends the chain too: the
                    // plot never starts while the user checks the card.
                    onLook={cancelChain}
                    // Not while the fan-out's panel is open: its sessions copy this session's data.
                    locked={!!fanOut}
                    onLoadData={session.fetchDataCsv}
                    // A look at the session's data, not at a result: version 0.
                    onDataViewShown={() => session.reportOutcome('opened_data_view', 0)}
                  />
                )}
                followReply={followReply}
                decisions={{
                  disabled: busy || state.phase !== 'ready',
                  onForget: session.forgetMemory,
                  onForgetAll: session.forgetAllMemory,
                  fallbackFocusRef: messageRef,
                  onAnnounce: announceMemory,
                }}
              />

              <Box
                ref={tailRef}
                sx={{ display: 'flex', flexDirection: 'column', gap: 2, scrollMarginBottom: 16 }}
              >
                {/* The frame's second dashed rule: the thread above, the composer below. The thread
                    is never empty, since the start item stands first in it. */}
                <FrameRule />

                {/* What a removal from the remembered decisions did, for a screen reader: the list
                    stands on a chapter line inside the thread's log, which would not read a
                    removal out, and comes and goes with the memory; this region stays. */}
                <Box role="status" data-testid="memory-status" sx={visuallyHiddenSx}>
                  <span key={memoryNote.n}>{memoryNote.text}</span>
                </Box>

                <Composer
                  draft={draft}
                  onDraftChange={event => {
                    // Typed while the one click reads: it plots nothing after that.
                    cancelChain();
                    // A paste the browser inserted itself, when its event hid the text: routed now.
                    if (!attach.handleInput(event, draft)) setDraft(event.target.value);
                  }}
                  onPaste={event => {
                    cancelChain();
                    void attach.handlePaste(event);
                  }}
                  attachment={attachment}
                  attachmentNotice={attach.notice}
                  onRemoveAttachment={handleRemoveAttachment}
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
                  onFileChosen={event => {
                    attach.handleChosen(event);
                    // The chooser hands the focus back to `.open()`, where Enter would only open it
                    // again: the box takes it, so Enter sends the file with its note.
                    messageRef.current?.focus();
                  }}
                  onSubmit={handleSend}
                  messageRef={messageRef}
                  plotRef={plotRef}
                  ready={state.phase === 'ready'}
                  busy={busy}
                  hasData={!!state.dataset}
                  step2={step2}
                  hasPlot={hasPlot}
                  chatLocked={chatLocked}
                  plot={{
                    kind: plotKind,
                    active: plotActive,
                    confirming: state.confirmBusy,
                    fresh: plotFresh,
                  }}
                  example={{ active: exampleActive }}
                  confirmError={state.confirmError}
                  onExampleData={() => void session.exampleData()}
                  onPlot={handlePlot}
                />
                {/* A chat without a plot has no result card to report on: its own form, opened
                    from `.feedback()` at the status line's end, right above that line. */}
                {feedbackShown && (
                  <ChatFeedback
                    sent={state.chatFeedback}
                    dataAvailable={!!state.dataset}
                    onSend={session.sendFeedback}
                    takeFocus={takeFeedbackFocus}
                  />
                )}
                {/* The frame's foot, in the tail, so a turn's start brings it into view with the box. */}
                <StatusLine
                  state={state}
                  line={status}
                  stop={
                    running
                      ? { stopping: !!state.run?.stopping, onStop: () => void session.stop() }
                      : null
                  }
                  startOver={
                    startOverShown ? { inert: !canCreate, onStartOver: handleStartOver } : null
                  }
                  onFeedback={feedbackOffer && !feedbackShown ? openFeedback : null}
                  focusAfterStop={messageRef}
                />
              </Box>
            </>
          )}
        </ChatFrame>
        {/* The admin's fan-out stays below the frame: its sessions are not this chat's. */}
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
