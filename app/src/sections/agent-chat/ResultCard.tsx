/**
 * One plot version of the agent chat: the rendered image with its actions,
 * the adapted code with its downloads, what changed, residual notes, and a
 * composer for refinements.
 *
 * - The image is the blob URL of the theme the run rendered. The light and
 *   dark switch shows the other theme, rendering it first through the theme
 *   toggle route when the version does not have it yet (no model call).
 * - The served PNG carries the service's footer strip ("made with any.plot()",
 *   "anyplot.ai/<spec>"), so it is taller than the 16:9 render; the image box
 *   takes the loaded PNG's own aspect instead of a fixed one.
 * - Copy image puts the PNG on the clipboard (`ClipboardItem`), or downloads
 *   it where the browser cannot; Download PNG and Open full size work on the
 *   theme on screen.
 * - The code is the exported `plot.py`, byte-identical to what rendered; it
 *   runs unchanged next to `data.csv`, so both download under those names.
 * - `feedbackSlot` is where the quick-feedback control goes (a later change).
 *
 * The card is self-contained, so the public phase can reuse it unchanged.
 */

import { lazy, type ReactNode, Suspense, useCallback, useEffect, useRef, useState } from 'react';

import CheckIcon from '@mui/icons-material/Check';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import ImageOutlinedIcon from '@mui/icons-material/ImageOutlined';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Skeleton from '@mui/material/Skeleton';
import Tooltip from '@mui/material/Tooltip';

import type { PlotVersion } from 'src/hooks/useAgentSession';
import { useCopyCode } from 'src/hooks/useCopyCode';
import { useTheme } from 'src/hooks/useLayoutContext';
import { type ArtifactName, MAX_MESSAGE_CHARS, type Theme } from 'src/lib/agent';
import { copyImage, downloadBlob } from 'src/sections/agent-chat/files';
import { IMAGE_FAILURE } from 'src/sections/agent-chat/messages';
import {
  actionButtonSx,
  bodyTextSx,
  ghostButtonSx,
  labelSx,
  nativeControlSx,
  smallText,
} from 'src/sections/agent-chat/styles';
import { colors, fontSize, overlayButtonSx, typography } from 'src/theme';

const CodeHighlighter = lazy(() => import('src/components/CodeHighlighter'));

const TOAST_MS = 1500;
/**
 * The image box's aspect before the PNG has loaded: a 3200x1800 render plus the
 * 64 px footer strip the agents service appends. Once loaded, the box takes the
 * PNG's own aspect, so the square format (2400x2448) fits without a band.
 */
const PLACEHOLDER_ASPECT = '3200/1864';

const STATUS_LABEL: Record<string, string> = {
  ok: 'ok',
  needs_attention: 'needs attention',
};

export interface ResultCardProps {
  version: PlotVersion;
  specId: string;
  language: string;
  /** Whether this is the newest version: only it is expanded and gets the composer. */
  latest: boolean;
  /**
   * A turn, a theme render, a parse or a binding change is in flight: a
   * refinement and a theme that still has to render wait for it, since the
   * server runs one at a time. A theme the version already has stays one click away.
   */
  busy: boolean;
  onRequestTheme: (version: number, theme: Theme) => void;
  onFetchArtifact: (version: number, name: ArtifactName) => Promise<Blob>;
  onRefine: (text: string) => void;
  onTrack: (event: string, props?: Record<string, string | undefined>) => void;
  /** The quick-feedback control, once it exists. */
  feedbackSlot?: ReactNode;
}

export function ResultCard({
  version,
  specId,
  language,
  latest,
  busy,
  onRequestTheme,
  onFetchArtifact,
  onRefine,
  onTrack,
  feedbackSlot,
}: ResultCardProps) {
  const { isDark } = useTheme();
  const [expanded, setExpanded] = useState(latest);
  const [shownTheme, setShownTheme] = useState<Theme>(version.theme);
  const [toast, setToast] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [aspect, setAspect] = useState(PLACEHOLDER_ASPECT);
  const toastTimer = useRef<ReturnType<typeof setTimeout>>(null);

  // A newer version collapses this one; it stays one click away in the thread.
  const [wasLatest, setWasLatest] = useState(latest);
  if (wasLatest !== latest) {
    setWasLatest(latest);
    setExpanded(latest);
  }

  useEffect(
    () => () => {
      if (toastTimer.current) clearTimeout(toastTimer.current);
    },
    []
  );

  const showToast = useCallback((text: string) => {
    setToast(text);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), TOAST_MS);
  }, []);

  const { library, number, result } = version;
  const image = version.images[shownTheme];
  const readyImage = image?.state === 'ready' ? image : null;
  const pngName = `${specId}-${library}-v${number}-${shownTheme}.png`;

  const { copied, copyToClipboard } = useCopyCode({
    onCopy: () =>
      onTrack('copy_code', { spec: specId, library, method: 'agent', page: 'agent_chat' }),
  });

  /** Whether showing `theme` needs a render on the server first. */
  const needsRender = (theme: Theme) => {
    const current = version.images[theme];
    return !current || current.state === 'failed';
  };

  const handleTheme = (theme: Theme) => {
    if (needsRender(theme)) {
      if (busy) return;
      onRequestTheme(number, theme);
    }
    setShownTheme(theme);
  };

  const handleCopyImage = async () => {
    if (!readyImage) return;
    const outcome = await copyImage(readyImage.blob, pngName);
    showToast(outcome === 'copied' ? '>>> .copied' : '>>> .downloaded');
  };

  const handleDownloadPng = () => {
    if (!readyImage) return;
    downloadBlob(readyImage.blob, pngName);
    showToast('>>> .downloaded');
  };

  const handleOpen = () => {
    if (readyImage) window.open(readyImage.url, '_blank', 'noopener,noreferrer');
  };

  /** Size the box to the loaded PNG, so the strip's page colour never meets a letterbox band. */
  const handleImageLoad = (event: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = event.currentTarget;
    if (naturalWidth > 0 && naturalHeight > 0) setAspect(`${naturalWidth}/${naturalHeight}`);
  };

  const handleDownloadFile = async (name: 'plot.py' | 'data.csv') => {
    setFileError(null);
    try {
      const blob =
        name === 'plot.py' && version.code.state === 'ready'
          ? new Blob([version.code.text], { type: 'text/x-python' })
          : await onFetchArtifact(number, name);
      // The exported code reads `data.csv` from its own directory, so the pair
      // keeps exactly these names.
      downloadBlob(blob, name);
    } catch {
      setFileError(`could not download ${name}`);
    }
  };

  const handleRefine = (event: React.FormEvent) => {
    event.preventDefault();
    const text = draft.trim();
    if (!text || busy) return;
    onRefine(text);
    setDraft('');
  };

  const overlayBtnSx = overlayButtonSx(isDark);
  const attempts = `${result.attempts} attempt${result.attempts === 1 ? '' : 's'}`;
  const header = (
    <Box
      component="button"
      type="button"
      onClick={() => setExpanded(open => !open)}
      aria-expanded={expanded}
      aria-label={`Version ${number}, ${STATUS_LABEL[result.status] ?? result.status}`}
      sx={{
        all: 'unset',
        boxSizing: 'border-box',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'baseline',
        columnGap: 1,
        rowGap: 0.25,
        width: '100%',
        cursor: 'pointer',
        fontFamily: typography.mono,
        fontSize: fontSize.md,
        color: 'var(--ink-soft)',
        '&:focus-visible': { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
      }}
    >
      <Box component="span" sx={{ color: 'var(--ink)', fontWeight: 600 }}>
        v{number}
      </Box>
      <span>{library}</span>
      <Box
        component="span"
        sx={{
          color: 'var(--ink)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.5,
          '&::before': {
            content: '""',
            width: 7,
            height: 7,
            borderRadius: '50%',
            bgcolor: result.status === 'ok' ? colors.primary : colors.warning,
          },
        }}
        data-testid="result-status"
      >
        {STATUS_LABEL[result.status] ?? result.status}
      </Box>
      <Box component="span" sx={{ color: 'var(--ink-muted)' }}>
        {attempts}
      </Box>
      <Box component="span" sx={{ ml: 'auto', color: 'var(--ink-muted)' }}>
        {expanded ? '.collapse()' : '.expand()'}
      </Box>
    </Box>
  );

  return (
    <Box
      component="article"
      aria-label={`Plot version ${number}`}
      sx={{
        border: '1px solid var(--rule)',
        borderRadius: 2,
        bgcolor: 'var(--bg-page)',
        p: { xs: 1.25, sm: 2 },
        minWidth: 0,
      }}
    >
      {header}
      {expanded && (
        <Box sx={{ mt: 1.5, display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
          {/* Image with the overlay actions of the plot page. */}
          <Box
            sx={{
              position: 'relative',
              borderRadius: 2,
              overflow: 'hidden',
              bgcolor: 'var(--bg-surface)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              aspectRatio: aspect,
            }}
            data-testid="result-image-box"
          >
            {readyImage ? (
              <Box
                component="img"
                src={readyImage.url}
                alt={`Adapted plot, version ${number}, ${shownTheme} theme`}
                onLoad={handleImageLoad}
                sx={{ display: 'block', width: '100%', height: '100%', objectFit: 'contain' }}
              />
            ) : image?.state === 'failed' ? (
              <Box
                role="alert"
                sx={{
                  position: 'absolute',
                  inset: 0,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  p: 2,
                  textAlign: 'center',
                  ...bodyTextSx,
                  color: 'var(--ink-soft)',
                }}
              >
                {IMAGE_FAILURE[image.code] ?? `could not load the ${shownTheme} plot`}
                {image.ref ? ` (ref ${image.ref})` : ''}
              </Box>
            ) : (
              <>
                <Skeleton
                  variant="rectangular"
                  sx={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
                />
                <Box
                  sx={{
                    position: 'absolute',
                    inset: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    ...labelSx,
                  }}
                >
                  {shownTheme === version.theme
                    ? 'loading plot…'
                    : `rendering ${shownTheme} theme…`}
                </Box>
              </>
            )}

            {toast && (
              <Box
                role="status"
                sx={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  bgcolor: 'rgba(0,0,0,0.7)',
                  color: '#fff',
                  px: 1.5,
                  py: 0.5,
                  borderRadius: 1,
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.md,
                  pointerEvents: 'none',
                }}
              >
                {toast}
              </Box>
            )}

            <Box sx={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 0.5 }}>
              <Tooltip title=".copy_png()" disableFocusListener>
                <span style={{ display: 'inline-flex' }}>
                  <IconButton
                    onClick={handleCopyImage}
                    aria-label="Copy image"
                    disabled={!readyImage}
                    sx={overlayBtnSx}
                    size="medium"
                  >
                    <ImageOutlinedIcon fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
              <Tooltip title=".download()" disableFocusListener>
                <span style={{ display: 'inline-flex' }}>
                  <IconButton
                    onClick={handleDownloadPng}
                    aria-label="Download PNG"
                    disabled={!readyImage}
                    sx={overlayBtnSx}
                    size="medium"
                  >
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
              <Tooltip title=".open()" disableFocusListener>
                <span style={{ display: 'inline-flex' }}>
                  <IconButton
                    onClick={handleOpen}
                    aria-label="Open full size"
                    disabled={!readyImage}
                    sx={overlayBtnSx}
                    size="medium"
                  >
                    <OpenInNewIcon fontSize="small" />
                  </IconButton>
                </span>
              </Tooltip>
            </Box>
          </Box>

          {/* Theme switch: the run rendered one theme; the other renders on demand. */}
          <Box
            role="group"
            aria-label="Plot theme"
            sx={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 0.5 }}
          >
            <Box component="span" sx={{ ...labelSx, mr: 0.5 }}>
              theme
            </Box>
            {(['light', 'dark'] as const).map(theme => {
              const active = theme === shownTheme;
              const state = version.images[theme]?.state;
              return (
                <Box
                  key={theme}
                  component="button"
                  type="button"
                  aria-pressed={active}
                  disabled={!active && busy && needsRender(theme)}
                  onClick={() => handleTheme(theme)}
                  sx={{
                    ...actionButtonSx,
                    color: active ? 'var(--ink)' : 'var(--ink-soft)',
                    bgcolor: active ? 'var(--bg-elevated)' : 'transparent',
                    border: '1px solid',
                    borderColor: active ? 'var(--ink-muted)' : 'var(--rule)',
                  }}
                >
                  {theme}
                  {state === 'loading' && theme !== shownTheme ? ' …' : ''}
                </Box>
              );
            })}
            {readyImage?.status === 'needs_attention' && shownTheme !== version.theme && (
              <Box component="span" sx={{ ...labelSx, ml: 1 }}>
                padded onto the canvas
              </Box>
            )}
          </Box>

          {result.changes.length > 0 && (
            <Box>
              <Box sx={labelSx}># what changed</Box>
              <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2.5, ...bodyTextSx }}>
                {result.changes.map((change, index) => (
                  <li key={index}>{change}</li>
                ))}
              </Box>
            </Box>
          )}

          {result.residual_defects.length > 0 && (
            <Box
              sx={{
                borderLeft: `3px solid ${colors.warning}`,
                pl: 1.5,
                py: 0.25,
              }}
            >
              <Box sx={labelSx}># notes — still worth a look</Box>
              <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2.5, ...bodyTextSx }}>
                {result.residual_defects.map((note, index) => (
                  <li key={index}>{note}</li>
                ))}
              </Box>
            </Box>
          )}

          {/* The adapted code: copy it, or download it with its data. */}
          <Box sx={{ minWidth: 0 }}>
            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                gap: 0.5,
                mb: 1,
              }}
            >
              <Box component="span" sx={{ ...labelSx, mr: 'auto' }}>
                # plot.py runs next to data.csv
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, ml: -1.25 }}>
                <Box
                  component="button"
                  type="button"
                  onClick={() => handleDownloadFile('plot.py')}
                  aria-label="Download plot.py"
                  sx={actionButtonSx}
                >
                  .download(&apos;plot.py&apos;)
                </Box>
                <Box
                  component="button"
                  type="button"
                  onClick={() => handleDownloadFile('data.csv')}
                  aria-label="Download data.csv"
                  sx={actionButtonSx}
                >
                  .download(&apos;data.csv&apos;)
                </Box>
              </Box>
            </Box>
            {fileError && (
              <Box role="alert" sx={{ ...labelSx, color: colors.error, mb: 1 }}>
                {fileError}
              </Box>
            )}
            <Box sx={{ position: 'relative', minWidth: 0 }}>
              {version.code.state === 'ready' ? (
                <>
                  <Tooltip title={copied ? '.copied' : '.copy()'}>
                    <IconButton
                      onClick={() =>
                        version.code.state === 'ready' && copyToClipboard(version.code.text)
                      }
                      aria-label="Copy code"
                      size="small"
                      sx={{
                        position: 'absolute',
                        top: 10,
                        right: 10,
                        zIndex: 1,
                        bgcolor: 'var(--bg-elevated)',
                        border: '1px solid var(--code-border)',
                        '&:hover': { bgcolor: 'var(--bg-surface)' },
                      }}
                    >
                      {copied ? (
                        <CheckIcon color="success" fontSize="small" />
                      ) : (
                        <ContentCopyIcon fontSize="small" />
                      )}
                    </IconButton>
                  </Tooltip>
                  <Box sx={{ maxHeight: 420, overflow: 'auto', borderRadius: '8px', minWidth: 0 }}>
                    <Suspense
                      fallback={
                        <Box component="pre" sx={{ ...bodyTextSx, m: 0, fontSize: smallText }}>
                          {version.code.text}
                        </Box>
                      }
                    >
                      <CodeHighlighter
                        code={version.code.text}
                        language={language}
                        library={library}
                      />
                    </Suspense>
                  </Box>
                </>
              ) : version.code.state === 'failed' ? (
                <Box role="alert" sx={{ ...labelSx, color: colors.error }}>
                  could not load plot.py
                </Box>
              ) : (
                <Skeleton variant="rounded" height={120} />
              )}
            </Box>
          </Box>

          {/* The quick-feedback control lands here (a later change). */}
          <Box data-testid="result-feedback-slot" sx={{ '&:empty': { display: 'none' } }}>
            {feedbackSlot}
          </Box>

          {latest && (
            <Box
              component="form"
              onSubmit={handleRefine}
              sx={{ display: 'flex', gap: 1, alignItems: 'flex-end', flexWrap: 'wrap' }}
            >
              <Box
                component="textarea"
                aria-label="Refine this plot"
                placeholder="refine: e.g. log scale on y, larger markers"
                value={draft}
                maxLength={MAX_MESSAGE_CHARS}
                rows={2}
                onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setDraft(event.target.value)
                }
                onKeyDown={(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    handleRefine(event);
                  }
                }}
                sx={{ ...nativeControlSx, flex: '1 1 220px', resize: 'vertical' }}
              />
              <Box
                component="button"
                type="submit"
                disabled={busy || !draft.trim()}
                sx={ghostButtonSx}
              >
                .refine()
              </Box>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}
