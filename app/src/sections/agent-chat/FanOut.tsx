/**
 * The admin fan-out, `.plot_all()`: the confirmed table plotted in every library
 * of the page at once, for testing.
 *
 * The page hands over its own session's id, whose data the admin confirmed.
 * `FanOut` opens a session per library (a `FanOutRun` with its own
 * `useAgentSession`), has the server copy that session's confirmed current
 * version into it with its bindings and their confirmation (`copyData`, without
 * the summary turn of a paste), whatever the data's origin: pasted, opened,
 * computed or changed by the assistant. It then starts `create_plot` in at most
 * `maxRuns` sessions at a time (`grantSlots`): the caller's own cap, which
 * `/status` reports as `user_max_runs` (`AGENT_ADMIN_USER_MAX_RUNS`, 5, for the
 * admin since 2026-11-01) and which refuses one run more with `run_limit`. That
 * cap counts the admin's runs in every window, so a `run_limit` sends the library
 * back to waiting and holds the panel back until one of its runs ends or 15 s
 * pass (`nextFanOut`); three panels started at once thus share the five places
 * and finish every library. Each run goes through the agents service's run queue,
 * and each session is deleted when the panel closes or the page goes, like the
 * page's own.
 *
 * A server without the copy (the page deployed before the API or the agents
 * service) answers `404 not_found`: a library then posts the page's upload again
 * (`replayData`) with the bindings the page held at the click, where the data
 * came from a paste or a file, and otherwise stops with `copy_unavailable`.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';

import {
  type BindingMap,
  type DatasetUpload,
  type Failure,
  useAgentSession,
} from 'src/hooks/useAgentSession';
import {
  awaitsRetry,
  type FanOutEvent,
  type FanOutSlot,
  initialFanOut,
  nextFanOut,
  RUN_LIMIT_RETRY_MS,
  type RunLimitInfo,
  runStatus,
  type Tone,
} from 'src/sections/agent-chat/fanoutRules';
import {
  bodyTextSx,
  cardSx,
  ghostButtonSx,
  labelSx,
  panelSx,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { colors } from 'src/theme';

const TONE_COLOR: Record<Tone, string> = {
  ok: colors.primary,
  warning: colors.warning,
  error: colors.error,
  muted: 'var(--ink-muted)',
};

interface FanOutRunProps {
  specId: string;
  library: string;
  locale: string;
  token: string;
  sourceSession: string;
  upload?: DatasetUpload;
  bindings: BindingMap;
  slot: FanOutSlot;
  limit: RunLimitInfo | null;
  onReady: (library: string) => void;
  onDone: (library: string) => void;
  onLimited: (library: string) => void;
}

function FanOutRun({
  specId,
  library,
  locale,
  token,
  sourceSession,
  upload,
  bindings,
  slot,
  limit,
  onReady,
  onDone,
  onLimited,
}: FanOutRunProps) {
  const { state, copyData, replayData, plotTurn, stop } = useAgentSession({
    specId,
    library,
    locale,
    token,
    fanout: true,
  });
  const [dataFailure, setDataFailure] = useState<Failure | null>(null);
  const stored = useRef(false);
  const inFlight = useRef(false);

  // The session opened: the server copies the page session's confirmed data into it. A session
  // that could not open (not eligible, an error) gives its place up at once.
  useEffect(() => {
    if (state.phase === 'opening' || stored.current) return;
    stored.current = true;
    if (state.phase !== 'ready') {
      onDone(library);
      return;
    }
    void copyData(sourceSession)
      .then(failure => {
        // A server without the copy: the paste as it was posted, where the data came from one.
        if (failure?.code !== 'not_found') return failure;
        return upload
          ? replayData(upload, bindings)
          : { code: 'copy_unavailable', ref: failure.ref };
      })
      .then(failure => {
        if (failure) {
          setDataFailure(failure);
          onDone(library);
        } else {
          onReady(library);
        }
      });
  }, [
    state.phase,
    copyData,
    replayData,
    sourceSession,
    upload,
    bindings,
    library,
    onReady,
    onDone,
  ]);

  // Given a place: one `create_plot`, whose end frees the place. A `run_limit` (the admin's runs in other
  // windows hold every place) sends the library back to waiting for another place; anything else ends it.
  useEffect(() => {
    if (slot !== 'running' || inFlight.current) return;
    inFlight.current = true;
    void plotTurn()
      .then(code => {
        inFlight.current = false;
        if (code === 'run_limit') onLimited(library);
        else onDone(library);
      })
      .catch(() => {
        // The turn handles its own errors; this only keeps an unexpected rejection from holding the place.
        inFlight.current = false;
        onDone(library);
      });
  }, [slot, plotTurn, library, onDone, onLimited]);

  const status = runStatus(state, slot, dataFailure, limit);
  const versions = Object.values(state.versions).filter(version => version.library === library);
  const latest = versions[versions.length - 1];
  const image = latest?.images[latest.theme];

  return (
    <Box
      component="article"
      aria-label={library}
      sx={{ ...cardSx, display: 'flex', flexDirection: 'column', gap: 1 }}
    >
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          columnGap: 1,
        }}
      >
        <Box sx={{ ...labelSx, color: 'var(--ink)' }}>{library}</Box>
        {/* A polite live region of its own: the panel's line announces only the done count. */}
        <Box
          role="status"
          data-testid="fanout-status"
          sx={{ ...labelSx, color: TONE_COLOR[status.tone] }}
        >
          <Box component="span" sx={visuallyHiddenSx}>
            {library}:{' '}
          </Box>
          {status.text}
        </Box>
      </Box>
      {status.detail && <Box sx={{ ...bodyTextSx, color: 'var(--ink-soft)' }}>{status.detail}</Box>}
      {image?.state === 'ready' && (
        <Box
          component="a"
          href={image.url}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Open the ${library} plot full size`}
          sx={{ display: 'block', lineHeight: 0 }}
        >
          <Box
            component="img"
            src={image.url}
            alt={`${library} plot, version ${latest.number}, ${latest.theme} theme`}
            sx={{ width: '100%', height: 'auto', borderRadius: 1, border: '1px solid var(--rule)' }}
          />
        </Box>
      )}
      {image?.state === 'loading' && <Box sx={labelSx}>loading the image…</Box>}
      {image?.state === 'failed' && (
        <Box sx={{ ...labelSx, color: colors.error }}>image · {image.code}</Box>
      )}
      {state.run && (
        <Box
          component="button"
          type="button"
          onClick={() => void stop()}
          disabled={state.run.stopping}
          aria-label={`Stop the ${library} plot`}
          sx={{ ...ghostButtonSx, alignSelf: 'flex-start' }}
        >
          .stop()
        </Box>
      )}
    </Box>
  );
}

export interface FanOutProps {
  specId: string;
  /** The page's libraries when `.plot_all()` was pressed, in its order. */
  libraries: string[];
  locale: string;
  token: string;
  /** The page's own session, whose confirmed data every library's session copies. */
  sourceSession: string;
  /**
   * The page's upload and the bindings at the click, for a server without the copy only: the upload
   * is absent for data the assistant changed or computed.
   */
  upload?: DatasetUpload;
  bindings: BindingMap;
  /** How many plots run at once: the caller's own cap (`user_max_runs` of `/status`). */
  maxRuns: number;
  onClose: () => void;
  /** The panel, which takes the focus when a key press on `.plot_all()` opened it. */
  panelRef?: React.Ref<HTMLElement>;
}

export function FanOut({
  panelRef,
  specId,
  libraries,
  locale,
  token,
  sourceSession,
  upload,
  bindings,
  maxRuns,
  onClose,
}: FanOutProps) {
  const [fanOut, setFanOut] = useState(() => initialFanOut(libraries));
  const send = useCallback(
    (event: FanOutEvent) => setFanOut(current => nextFanOut(current, event, libraries, maxRuns)),
    [libraries, maxRuns]
  );
  const onReady = useCallback((library: string) => send({ type: 'ready', library }), [send]);
  const onDone = useCallback((library: string) => send({ type: 'ended', library }), [send]);
  const onLimited = useCallback(
    (library: string) => send({ type: 'run_limit', library, now: Date.now() }),
    [send]
  );
  // Held back by `run_limit`: try one library more every 15 s, until the server takes it again.
  const retrying = awaitsRetry(fanOut);
  useEffect(() => {
    if (!retrying) return;
    const timer = setInterval(() => send({ type: 'retry' }), RUN_LIMIT_RETRY_MS);
    return () => clearInterval(timer);
  }, [retrying, send]);
  const { slots } = fanOut;
  const done = libraries.filter(library => slots[library] === 'done').length;

  return (
    <Box
      component="section"
      ref={panelRef}
      tabIndex={-1}
      aria-label="All libraries"
      sx={{
        ...panelSx,
        mt: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
      }}
    >
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          columnGap: 1,
          rowGap: 0.75,
        }}
      >
        <Box aria-live="polite" sx={labelSx}>
          # all libraries · {done} of {libraries.length} done · at most {maxRuns} at a time
        </Box>
        <Box
          component="button"
          type="button"
          onClick={onClose}
          aria-label="Close all libraries"
          sx={ghostButtonSx}
        >
          .close()
        </Box>
      </Box>
      <Box
        sx={{
          display: 'grid',
          gap: 1.5,
          gridTemplateColumns: { xs: 'minmax(0, 1fr)', sm: 'repeat(2, minmax(0, 1fr))' },
        }}
      >
        {libraries.map(library => (
          <FanOutRun
            key={library}
            specId={specId}
            library={library}
            locale={locale}
            token={token}
            sourceSession={sourceSession}
            upload={upload}
            bindings={bindings}
            slot={slots[library]}
            limit={
              fanOut.limited[library]
                ? {
                    count: fanOut.limited[library].count,
                    gaveUp: fanOut.gaveUp.includes(library),
                  }
                : null
            }
            onReady={onReady}
            onDone={onDone}
            onLimited={onLimited}
          />
        ))}
      </Box>
    </Box>
  );
}
