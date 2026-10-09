/**
 * "Use with my data": the admin-only agent chat at `/debug/agent?spec=&library=&language=`.
 *
 * Paste data, check the preview and the role bindings, `.create_plot()`, then
 * refine in plain words; every shipped version gets a result card with the
 * image, the code and the downloads. The page talks only to the BFF under
 * `/debug/agent/*` (`src/lib/agent.ts`, `src/hooks/useAgentSession.ts`).
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

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useSearchParams } from 'react-router-dom';

import Box from '@mui/material/Box';

import { SectionHeader } from 'src/components/SectionHeader';
import { LIBRARIES } from 'src/constants';
import { CONFIG } from 'src/global-config';
import { useAgentSession } from 'src/hooks/useAgentSession';
import { useAnalytics } from 'src/hooks/useAnalytics';
import { useTheme } from 'src/hooks/useLayoutContext';
import { agentApi, browserLocale, DEFAULT_AGENT_LIBRARIES, MAX_MESSAGE_CHARS } from 'src/lib/agent';
import { apiGet, endpoints } from 'src/lib/api';
import { NotFoundPage } from 'src/pages/NotFoundPage';
import { paths, specPath } from 'src/routes/paths';
import { ChatThread } from 'src/sections/agent-chat/ChatThread';
import { DataPanel } from 'src/sections/agent-chat/DataPanel';
import { ERROR_TEXT } from 'src/sections/agent-chat/messages';
import { ProgressTimeline } from 'src/sections/agent-chat/ProgressTimeline';
import {
  actionButtonSx,
  bodyTextSx,
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
  const language = (params.get('language') ?? 'python').toLowerCase();
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
  const chatRef = useRef<HTMLDivElement>(null);

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

  // On a phone the chat sits below the data panel: bring it into view when a
  // turn starts, so the progress is visible.
  const running = !!state.run;
  useEffect(() => {
    if (running) chatRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
  }, [running]);

  const handleSend = useCallback(
    (event?: React.FormEvent) => {
      event?.preventDefault();
      const text = draft.trim();
      if (!text || running) return;
      void session.sendMessage(text);
      setDraft('');
    },
    [draft, running, session]
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
            return (
              <Box
                key={lib}
                component="button"
                type="button"
                aria-pressed={active}
                disabled={active || running || state.libraryBusy || state.phase !== 'ready'}
                onClick={() => void handleLibrary(lib)}
                sx={{
                  ...actionButtonSx,
                  border: '1px solid',
                  borderColor: active ? 'var(--ink-muted)' : 'var(--rule)',
                  color: active ? 'var(--ink)' : 'var(--ink-soft)',
                  bgcolor: active ? 'var(--bg-elevated)' : 'transparent',
                  '&:disabled': { cursor: 'default', opacity: active ? 1 : 0.45 },
                }}
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
      <Box sx={{ py: 2 }}>
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
                ? 'this plot cannot be adapted in this library yet.'
                : state.failure?.code === 'not_enabled'
                  ? 'the agent chat is switched off on this server (AGENT_ENABLED).'
                  : (ERROR_TEXT[state.failure?.code ?? ''] ?? 'the session could not be opened.')}
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
      <Box sx={{ py: 2, maxWidth: 1480, mx: 'auto', colorScheme: isDark ? 'dark' : 'light' }}>
        {header}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: 'minmax(0, 5fr) minmax(0, 7fr)' },
            gap: { xs: 2, md: 3 },
            alignItems: 'start',
          }}
        >
          <DataPanel
            state={state}
            onParse={text => void session.parseData(text)}
            onBind={session.setBinding}
            onCreatePlot={() => void session.createPlot()}
          />

          <Box
            component="section"
            aria-label="Chat"
            ref={chatRef}
            sx={{
              ...panelSx,
              display: 'flex',
              flexDirection: 'column',
              gap: 2,
              scrollMarginTop: 16,
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minHeight: 28 }}>
              <Box sx={labelSx}># chat</Box>
              {state.run?.queue && (
                <Box
                  role="status"
                  data-testid="queue-counter"
                  aria-label={`Queued: position ${state.run.queue.position}, ${state.run.queue.waiting} waiting`}
                  sx={{
                    ml: 'auto',
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
            </Box>

            {state.items.length === 0 && !state.run && (
              <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>
                paste your data, check the bindings, then <code>.create_plot()</code>. afterwards,
                ask for changes in plain words: &quot;log scale on y&quot;, &quot;dark
                version&quot;, &quot;label the outliers&quot;.
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

            {state.run && <ProgressTimeline run={state.run} />}

            <Box
              component="form"
              onSubmit={handleSend}
              sx={{ display: 'flex', gap: 1, alignItems: 'flex-end', flexWrap: 'wrap' }}
            >
              <Box
                component="textarea"
                aria-label="Message"
                placeholder="ask about this plot, or ask for a change"
                value={draft}
                maxLength={MAX_MESSAGE_CHARS}
                rows={2}
                disabled={state.phase !== 'ready'}
                onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setDraft(event.target.value)
                }
                onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    handleSend();
                  }
                }}
                sx={{ ...nativeControlSx, flex: '1 1 240px', resize: 'vertical' }}
              />
              {running ? (
                <Box
                  component="button"
                  type="button"
                  onClick={() => void session.stop()}
                  disabled={state.run?.stopping}
                  aria-label="Stop"
                  sx={{
                    ...ghostButtonSx,
                    color: colors.error,
                    '&:hover:not(:disabled)': { color: colors.error, borderColor: colors.error },
                  }}
                >
                  .stop()
                </Box>
              ) : (
                <Box
                  component="button"
                  type="submit"
                  disabled={!draft.trim() || state.phase !== 'ready'}
                  sx={ghostButtonSx}
                >
                  .send()
                </Box>
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
