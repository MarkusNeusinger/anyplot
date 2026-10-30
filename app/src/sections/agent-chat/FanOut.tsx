/**
 * The admin fan-out, `.plot_all()`: the confirmed table plotted in every library
 * of the page at once, for testing.
 *
 * The page hands over the upload its session stored (`DatasetState.upload`) and
 * the bindings the admin confirmed. `FanOut` opens a session per library (a
 * `FanOutRun` with its own `useAgentSession`), stores the same upload there with
 * the same bindings and confirms it (`replayData`, without the summary turn of
 * a paste), and starts `create_plot` in at most `maxRuns` sessions at a time
 * (`grantSlots`): the server's `AGENT_USER_MAX_RUNS`, which refuses one run
 * more with `run_limit`. Each run goes through the agents service's run queue
 * like any other, and each session is deleted when the panel closes or the page
 * goes, like the page's own.
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
  type FanOutSlot,
  grantSlots,
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
  upload: DatasetUpload;
  bindings: BindingMap;
  slot: FanOutSlot;
  onReady: (library: string) => void;
  onDone: (library: string) => void;
}

function FanOutRun({
  specId,
  library,
  locale,
  token,
  upload,
  bindings,
  slot,
  onReady,
  onDone,
}: FanOutRunProps) {
  const { state, replayData, createPlot, stop } = useAgentSession({
    specId,
    library,
    locale,
    token,
    fanout: true,
  });
  const [dataFailure, setDataFailure] = useState<Failure | null>(null);
  const replayed = useRef(false);
  const started = useRef(false);

  // The session opened: store the table, bind it and confirm it. A session that
  // could not open (not eligible, an error) gives its place up at once.
  useEffect(() => {
    if (state.phase === 'opening' || replayed.current) return;
    replayed.current = true;
    if (state.phase !== 'ready') {
      onDone(library);
      return;
    }
    void replayData(upload, bindings).then(failure => {
      if (failure) {
        setDataFailure(failure);
        onDone(library);
      } else {
        onReady(library);
      }
    });
  }, [state.phase, replayData, upload, bindings, library, onReady, onDone]);

  // Given a place: one `create_plot`, whose end frees the place, whatever it brought.
  useEffect(() => {
    if (slot !== 'running' || started.current) return;
    started.current = true;
    void createPlot().finally(() => onDone(library));
  }, [slot, createPlot, library, onDone]);

  const status = runStatus(state, slot, dataFailure);
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
  upload: DatasetUpload;
  bindings: BindingMap;
  /** How many plots run at once (`AGENT_USER_MAX_RUNS`). */
  maxRuns: number;
  onClose: () => void;
}

export function FanOut({
  specId,
  libraries,
  locale,
  token,
  upload,
  bindings,
  maxRuns,
  onClose,
}: FanOutProps) {
  const [slots, setSlots] = useState<Record<string, FanOutSlot>>(() =>
    Object.fromEntries(libraries.map(library => [library, 'data' as FanOutSlot]))
  );
  const move = useCallback(
    (library: string, slot: 'waiting' | 'done') =>
      setSlots(current =>
        current[library] === 'done'
          ? current
          : grantSlots({ ...current, [library]: slot }, libraries, maxRuns)
      ),
    [libraries, maxRuns]
  );
  const onReady = useCallback((library: string) => move(library, 'waiting'), [move]);
  const onDone = useCallback((library: string) => move(library, 'done'), [move]);
  const done = libraries.filter(library => slots[library] === 'done').length;

  return (
    <Box
      component="section"
      aria-label="All libraries"
      sx={{ ...panelSx, mt: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}
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
            upload={upload}
            bindings={bindings}
            slot={slots[library]}
            onReady={onReady}
            onDone={onDone}
          />
        ))}
      </Box>
    </Box>
  );
}
