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
 * header then stays as `! confirm again` and leads back to the card. In step
 * 2 the composer's action is `.create_plot()`: with an empty box it starts the
 * first plot as it is, with text the text goes as a turn and the assistant
 * makes the first plot with that change. Once the library has a plot, the
 * composer refines in plain words; every shipped version gets a result card
 * with the image, the code and the downloads. A line above the column names
 * the current step. The page talks only to the BFF under `/debug/agent/*`
 * (`src/lib/agent.ts`, `src/hooks/useAgentSession.ts`).
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

import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';

import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { LIB_TO_LANG, LIBRARIES } from 'src/constants';
import { CONFIG } from 'src/global-config';
import { sessionBusy, useAgentSession } from 'src/hooks/useAgentSession';
import { useAnalytics } from 'src/hooks/useAnalytics';
import { useTheme } from 'src/hooks/useLayoutContext';
import { agentApi, browserLocale, DEFAULT_AGENT_LIBRARIES, MAX_MESSAGE_CHARS } from 'src/lib/agent';
import { apiGet, endpoints } from 'src/lib/api';
import { NotFoundPage } from 'src/pages/NotFoundPage';
import { paths, specPath } from 'src/routes/paths';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { DATA_SUMMARY_ID, DataPanel } from 'src/sections/agent-chat/DataPanel';
import { ERROR_TEXT } from 'src/sections/agent-chat/messages';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import { ReloadHint } from 'src/sections/agent-chat/ReloadHint';
import { StepHeader } from 'src/sections/agent-chat/StepHeader';
import { inStep2 } from 'src/sections/agent-chat/steps';
import {
  actionButtonSx,
  bodyTextSx,
  ctaButtonSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  panelSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { colors, fontSize, proseLinkStyle, typography } from 'src/theme';
import { readAdminHint, readAdminToken, setAdminHint } from 'src/utils/adminAuth';

const SPEC_PATTERN = /^[a-z0-9-]{1,100}$/;
const OPEN_SOURCES = new Set(['plot_page']);
/** The chat column's width: a thread to read, and a plot that fits the screen with its composer. */
const COLUMN_MAX_WIDTH = 960;

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
  const tailRef = useRef<HTMLDivElement>(null);
  const messageRef = useRef<HTMLTextAreaElement>(null);
  const createRef = useRef<HTMLButtonElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  // Set by the user's own `.confirm()`: the step change it brings moves the focus, once.
  const confirmFocus = useRef(false);

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
    apiGet<{ title: string; implementations: { library_id: string }[] }>(endpoints.spec(specId), {
      signal: controller.signal,
    })
      .then(spec => {
        if (controller.signal.aborted) return;
        setTitle(spec.title);
        implemented = spec.implementations.map(impl => impl.library_id);
        publish();
      })
      .catch(() => undefined);
    agentApi
      .status(token)
      .then(status => {
        if (Array.isArray(status.libraries) && status.libraries.length) {
          enabled = status.libraries;
          publish();
        }
      })
      .catch(() => undefined);
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
  const firstPlot =
    step2 && !Object.values(state.versions).some(version => version.library === state.library);

  // The user's own `.confirm()` collapsed the card and took its focused button
  // away. Before the first plot the keyboard continues at `.create_plot()`, the
  // step's next action (a button, so a phone opens no keyboard); after it at the
  // pinned header's toggle, since a fresh run must not be one key press away by
  // accident; it is in view where it sticks, so the focus scrolls nothing. Only
  // for that confirmation, and only while nothing else holds the focus: a step 2
  // that a turn's sync brings back never takes it from the composer. A layout
  // effect, so the focus has moved by the time the button shows.
  useLayoutEffect(() => {
    if (!confirmFocus.current || state.confirmBusy) return;
    confirmFocus.current = false;
    const active = document.activeElement;
    if (!step2 || (active && active !== document.body)) return;
    if (firstPlot) createRef.current?.focus();
    else toggleRef.current?.focus({ preventScroll: true });
  }, [state.confirmBusy, step2, firstPlot]);

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
   */
  const handleSend = useCallback(
    (event?: React.FormEvent) => {
      event?.preventDefault();
      const text = draft.trim();
      if (busy) return;
      if (firstPlot && !text) {
        if (canCreate) void session.createPlot();
        return;
      }
      if (!text || (firstPlot && !canCreate)) return;
      void session.sendMessage(text);
      setDraft('');
    },
    [draft, busy, firstPlot, canCreate, session]
  );

  const handleLibrary = useCallback(
    async (next: string) => {
      if (await session.switchLibrary(next)) onLibraryChange(next);
    },
    [session, onLibraryChange]
  );

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
            const pillSx = {
              ...actionButtonSx,
              border: '1px solid',
              borderColor: active ? 'var(--ink-muted)' : 'var(--rule)',
              color: active ? 'var(--ink)' : 'var(--ink-soft)',
              bgcolor: active ? 'var(--bg-elevated)' : 'transparent',
              '&:disabled': { cursor: 'default', opacity: active ? 1 : 0.45 },
            };
            // No session to switch: another library opens the page anew, with
            // its own session (a full navigation, like the `.adapt()` button).
            if (!active && reopen) {
              return (
                <Box
                  key={lib}
                  component="a"
                  href={paths.agentChat(specId, lib, language)}
                  sx={{ ...pillSx, textDecoration: 'none' }}
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
                aria-pressed={active}
                disabled={active || busy || state.phase !== 'ready'}
                onClick={() => void handleLibrary(lib)}
                sx={pillSx}
              >
                {lib}
              </Box>
            );
          })}
        </Box>
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
      <Helmet>
        <title>{`agent · ${specId} | anyplot.ai`}</title>
        <meta name="robots" content="noindex, nofollow" />
      </Helmet>
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
            onParse={text => void session.parseData(text)}
            onConfirmTranscription={() => void session.confirmTranscription()}
            onDiscardTranscription={session.discardTranscription}
            onSendFormula={() => void session.sendFormula()}
            onBind={session.setBinding}
            onConfirmData={() => {
              confirmFocus.current = true;
              void session.confirmData();
            }}
            onUndo={() => void session.undoData()}
            toggleRef={toggleRef}
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
            onRefine={text => void session.sendMessage(text)}
            onTrack={trackEvent}
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
            {state.run && <ProgressTimeline run={state.run} />}

            {firstPlot && (
              <Box id="agent-create-line" sx={{ ...labelSx, color: 'var(--ink-soft)', mb: -1 }}>
                # step 2 — create the plot as it is, or say first what it should do differently
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
                  // data, the chat is the other way to get some: a formula.
                  !state.dataset
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
                disabled={state.phase !== 'ready'}
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
              ) : firstPlot ? (
                <Box
                  key="create"
                  component="button"
                  type="submit"
                  ref={createRef}
                  onClick={keepKeyboardFocus}
                  disabled={!canCreate}
                  aria-describedby={`${DATA_SUMMARY_ID} agent-create-line`}
                  sx={ctaButtonSx}
                >
                  .create_plot()
                </Box>
              ) : (
                <>
                  {/* Step 2 after a plot: start over from the catalogue plot with this data. */}
                  {step2 && (
                    <Box
                      component="button"
                      type="button"
                      ref={createRef}
                      onClick={(event: React.MouseEvent) => {
                        keepKeyboardFocus(event);
                        void session.createPlot();
                      }}
                      disabled={!canCreate}
                      aria-describedby={DATA_SUMMARY_ID}
                      sx={actionButtonSx}
                    >
                      .create_plot()
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
            {draft.length > MAX_MESSAGE_CHARS * 0.9 && (
              <Box sx={{ ...labelSx, mt: -1 }}>
                {draft.length} / {MAX_MESSAGE_CHARS}
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    </>
  );
}
