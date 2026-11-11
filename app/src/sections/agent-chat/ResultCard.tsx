/**
 * One plot version of the agent chat: the rendered image with its actions,
 * the adapted code with its downloads, what changed, residual notes, and the
 * quick-feedback control. The card has no composer of its own: a change
 * request or a question goes through the thread's one composer below it,
 * which the assistant reads either way (since 2026-10-12).
 *
 * - The card's frame carries its label on the border (`CardFrame.tsx`, v4
 *   design): `plot v2 · matplotlib · title in German`, the version, its library
 *   and what it answered. The label is the card's toggle: a click folds the
 *   card to that one line (`▸ plot v2 · …`), and a newer version folds the one
 *   before it. The version's status (`ok`, `needs attention`) stands in the
 *   theme row, before the run's line.
 * - What the version kept and added of the remembered decisions
 *   (`PlotVersion.decisions`): `kept: y = 7 line · x label · new: log scale on
 *   y`, each decision cut to 40 characters, in full for a screen reader; from
 *   `sm` up the open card's first line, on a phone under the image, above the
 *   card's action line. The label does not count them, so a phone shows both
 *   parts too. No line when both are empty or the server named none.
 * - Folded by default since 2026-11-02 (owner: less text, the details behind
 *   a toggle rather than removed): the image, its toolbar and the theme switch
 *   show; the run's rounds and its "what changed" list sit behind one status
 *   line (`ready in 1:12 · second try · 5 changes ⓘ`: how long the plot took
 *   by the working line's clock, when the page timed it), and the code behind `.show_code()`,
 *   while `.copy()` and the downloads stay in view. Each card keeps its own
 *   choice while the session lives, also across a fold of the whole card;
 *   a new version's card starts folded. The residual notes stay in view: they
 *   are what still needs the user's eye. They read in plain words, one line
 *   per issue (`residualNotes.ts`); the review's lines in full, with their
 *   rubric ids and measurements, sit behind the notes' ⓘ.
 * - The image's actions (`.copy_png()`, `.download()` for the PNG, `.open()`,
 *   and `.interactive()` or `.preview()`) are icons over its top right corner
 *   from `sm` up, their names on hover; at phone width, where that corner holds
 *   the plot's title, they stand by their names on the card's action line right
 *   under the image. The code's downloads stand in the code's line further down.
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
 * - The code is the export, byte-identical to what rendered, under its
 *   language's name (`plot.py`, `plot.R`, `plot.js`, ...: the code artifact
 *   among the version's artifacts); it runs unchanged next to `data.csv`, so
 *   both download under those names. A JavaScript plot's code runs only in
 *   its page: such a version also offers `plot.html`, the self-contained
 *   interactive page, which the server builds in the theme on screen when it
 *   is asked for (so the button waits while the session is busy, like a theme
 *   that still has to render).
 * - `.interactive()` shows that page in place of the image (`InteractivePreview`,
 *   through the API's sandboxed relay), only when the user asks for it; a theme
 *   switch shows the other theme's page, `.preview()` the image again. The pages
 *   of an open preview are kept, so switching back or downloading the page
 *   builds nothing twice; closing the preview or collapsing the card (also
 *   when a newer version arrives) drops them, and a build still under way is
 *   ignored when it ends. The frame takes the wrapper's size from the page.
 * - A copy or a download that succeeded calls `onOutcome` with the action and
 *   the version, the content-free usage beacon; nothing else travels.
 * - Below the code, the quick-feedback control (`ResultFeedback`) stores the
 *   version as a feedback case; it shows when the page passes `onSendFeedback`.
 *
 * The card is self-contained, so the public phase can reuse it unchanged.
 */

import { lazy, Suspense, useCallback, useEffect, useId, useRef, useState } from 'react';

import DownloadIcon from '@mui/icons-material/Download';
import ImageOutlinedIcon from '@mui/icons-material/ImageOutlined';
import InfoIcon from '@mui/icons-material/Info';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Skeleton from '@mui/material/Skeleton';
import Tooltip from '@mui/material/Tooltip';
import useMediaQuery from '@mui/material/useMediaQuery';

import { LIB_TO_LANG } from 'src/constants';
import type { FeedbackInput, PlotVersion } from 'src/hooks/useAgentSession';
import type { TrackEvent } from 'src/hooks/useAnalytics';
import { useCopyCode } from 'src/hooks/useCopyCode';
import { useTheme } from 'src/hooks/useLayoutContext';
import {
  type ArtifactName,
  CODE_MEDIA_TYPES,
  type CodeArtifact,
  codeArtifact,
  hasPage,
  type OutcomeAction,
  PAGE_ARTIFACT,
  pageFrameSize,
  type Theme,
} from 'src/lib/agent';
import { CardFrame } from 'src/sections/agent-chat/CardFrame';
import { decisionsText, plotCardLabel } from 'src/sections/agent-chat/cardLabels';
import { copyImage, downloadBlob } from 'src/sections/agent-chat/files';
import { InfoPopover } from 'src/sections/agent-chat/InfoPopover';
import { InteractivePreview } from 'src/sections/agent-chat/InteractivePreview';
import { elapsedClock, IMAGE_FAILURE } from 'src/sections/agent-chat/messages';
import { plainNotes } from 'src/sections/agent-chat/residualNotes';
import { ResultFeedback } from 'src/sections/agent-chat/ResultFeedback';
import { RoundGrid } from 'src/sections/agent-chat/RoundGrid';
import {
  actionButtonSx,
  bodyTextSx,
  cardActionSx,
  labelSx,
  PHONE_QUERY,
  readableSx,
  smallText,
  visuallyHiddenSx,
} from 'src/sections/agent-chat/styles';
import { gridRows, triesText } from 'src/sections/agent-chat/timeline';
import { colors, fontSize, overlayButtonSx, typography } from 'src/theme';

const CodeHighlighter = lazy(() => import('src/components/CodeHighlighter'));

const TOAST_MS = 1500;
/** `.copy()` for a while after the browser refused the clipboard; the code opens beside it. */
const COPY_FAILED_TEXT = '.copy() failed · select the code';
/** The code download button's label per code artifact; literal, so the root prompt's control list can name them. */
const DOWNLOAD_CODE_LABELS: Record<CodeArtifact, string> = {
  'plot.py': ".download('plot.py')",
  'plot.R': ".download('plot.R')",
  'plot.jl': ".download('plot.jl')",
  'plot.js': ".download('plot.js')",
  'plot.tsx': ".download('plot.tsx')",
};
/**
 * The image box's aspect before the PNG has loaded: a 3200x1800 render plus the
 * 64 px footer strip the agents service appends. Once loaded, the box takes the
 * PNG's own aspect, so the square format (2400x2448) fits without a band.
 */
const PLACEHOLDER_ASPECT = '3200/1864';

/** The beacon actions a card reports; the save and the feedback report themselves. */
export type CardOutcome = Exclude<OutcomeAction, 'saved_session' | 'feedback'>;

const STATUS_LABEL: Record<string, string> = {
  ok: 'ok',
  needs_attention: 'needs attention',
};

const plural = (count: number, noun: string) => `${count} ${noun}${count === 1 ? '' : 's'}`;

export interface ResultCardProps {
  version: PlotVersion;
  specId: string;
  /** The page's language; the code is highlighted in its version's library's language when the app knows it. */
  language: string;
  /** Whether this is the newest version: only it starts expanded. */
  latest: boolean;
  /**
   * What the version answered, for its label: the request before it, cut to 40 characters, or
   * `first plot` or `.start_over()` (`plotSummaries` in `threadModel.ts`); none without either.
   */
  summary?: string | null;
  /**
   * A turn, a theme render, a parse or a binding change is in flight: a theme
   * that still has to render waits for it, since the server runs one at a
   * time. A theme the version already has stays one click away.
   */
  busy: boolean;
  onRequestTheme: (version: number, theme: Theme) => void;
  /** One file of the version; `theme` picks the theme of `plot.html`, which the server builds on demand. */
  onFetchArtifact: (version: number, name: ArtifactName, theme?: Theme) => Promise<Blob>;
  onTrack: TrackEvent;
  /**
   * The usage beacon, called once a copy or a download succeeded, with the
   * action and this card's version only; fire and forget.
   */
  onOutcome?: (action: CardOutcome, version: number) => void;
  /**
   * Store the version as a feedback case (`.send()` in the quick-feedback
   * control); without it the card shows no control. Never held back by `busy`.
   */
  onSendFeedback?: (version: number, input: FeedbackInput) => Promise<void>;
}

export function ResultCard({
  version,
  specId,
  language,
  latest,
  summary: request = null,
  busy,
  onRequestTheme,
  onFetchArtifact,
  onTrack,
  onOutcome,
  onSendFeedback,
}: ResultCardProps) {
  const { isDark } = useTheme();
  // Read at the first render, so a phone never paints the actions over the image first.
  const narrow = useMediaQuery(PHONE_QUERY, { noSsr: true });
  const [expanded, setExpanded] = useState(latest);
  const [shownTheme, setShownTheme] = useState<Theme>(version.theme);
  const [toast, setToast] = useState<string | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [buildingPage, setBuildingPage] = useState(false);
  const [aspect, setAspect] = useState(PLACEHOLDER_ASPECT);
  // The interactive preview: shown in place of the image on request, with the pages fetched while it is open.
  const [interactive, setInteractive] = useState(false);
  const [pages, setPages] = useState<Partial<Record<Theme, string>>>({});
  // Per theme, so a failed build of one theme never covers the page of the other that is on screen meanwhile.
  const [previewErrors, setPreviewErrors] = useState<Partial<Record<Theme, string>>>({});
  // Bumped when the preview closes or the card unmounts, so a page that arrives afterwards is dropped; the beacon goes
  // once per opening.
  const previewRun = useRef(0);
  const previewReported = useRef(false);
  const toastTimer = useRef<ReturnType<typeof setTimeout>>(null);
  const [wasLatest, setWasLatest] = useState(latest);
  // The run's details (its rounds and what changed) and the code, folded until asked for. The
  // card's own state, outside the part a collapse unmounts, so the choice outlives a collapse.
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [codeOpen, setCodeOpen] = useState(false);
  const detailsId = useId();
  const codeId = useId();
  const bodyId = useId();

  useEffect(
    () => () => {
      if (toastTimer.current) clearTimeout(toastTimer.current);
      // A build still under way when the card goes keeps neither its page nor reports the opening.
      previewRun.current += 1;
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

  const {
    copied,
    failed: copyFailed,
    copyToClipboard,
  } = useCopyCode({
    onCopy: () => {
      onTrack('copy_code', { spec: specId, library, method: 'agent', page: 'agent_chat' });
      onOutcome?.('copied_code', number);
    },
    // The browser refused the clipboard: the code opens, so the user can select it by hand.
    onError: () => setCodeOpen(true),
  });

  /** Whether showing `theme` needs a render on the server first. */
  const needsRender = (theme: Theme) => {
    const current = version.images[theme];
    return !current || current.state === 'failed';
  };

  /** Whether showing `theme` in the open preview needs its page built first. */
  const needsPage = (theme: Theme) => pages[theme] === undefined;

  /** Set or clear (`undefined`) the preview's error for `theme`. */
  const setPreviewError = (theme: Theme, code: string | undefined) =>
    setPreviewErrors(current => ({ ...current, [theme]: code }));

  /**
   * Drop the preview: its pages (two wrappers of up to tens of MiB), its error,
   * and a build still under way, whose page is ignored when it comes.
   */
  const dropPreview = () => {
    previewRun.current += 1;
    setInteractive(false);
    setPages({});
    setPreviewErrors({});
  };

  /** Collapse the card; an open preview goes, and a theme it showed without a PNG gives way to the run's own. */
  const collapse = () => {
    if (interactive) {
      dropPreview();
      if (needsRender(shownTheme)) setShownTheme(version.theme);
    }
    setExpanded(false);
  };

  // A newer version collapses this one; it stays one click away in the thread.
  if (wasLatest !== latest) {
    setWasLatest(latest);
    if (latest) setExpanded(true);
    else collapse();
  }

  const handleTheme = (theme: Theme) => {
    if (interactive) {
      // The preview shows the other theme's page; the PNG renders when the image is back on screen.
      if (needsPage(theme) && busy) return;
      setShownTheme(theme);
      // A fresh relay for the theme, also after the last one did not answer.
      setPreviewError(theme, undefined);
      void showPage(theme);
      return;
    }
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
    // Where the browser cannot copy an image, the user got the PNG as a download.
    onOutcome?.(outcome === 'copied' ? 'copied_image' : 'downloaded_png', number);
  };

  const handleDownloadPng = () => {
    if (!readyImage) return;
    downloadBlob(readyImage.blob, pngName);
    showToast('>>> .downloaded');
    onOutcome?.('downloaded_png', number);
  };

  const handleOpen = () => {
    if (readyImage) window.open(readyImage.url, '_blank', 'noopener,noreferrer');
  };

  /** Size the box to the loaded PNG, so the strip's page colour never meets a letterbox band. */
  const handleImageLoad = (event: React.SyntheticEvent<HTMLImageElement>) => {
    const { naturalWidth, naturalHeight } = event.currentTarget;
    if (naturalWidth > 0 && naturalHeight > 0) setAspect(`${naturalWidth}/${naturalHeight}`);
  };

  // The exported code downloads under its language's name (`plot.py`, `plot.R`, `plot.js`, ...).
  const codeName = codeArtifact(version.result.artifacts);
  const downloadCodeLabel = DOWNLOAD_CODE_LABELS[codeName];
  // A JavaScript plot's code runs only in its page, which the version offers as `plot.html`.
  const page = hasPage(version.result.artifacts);
  // Highlighted in the version's own language: after a library switch the thread holds versions of several
  // languages (a matplotlib plot above a ggplot2 one), while `language` follows the page's library.
  const codeLanguage = LIB_TO_LANG[library] ?? language;

  const handleDownloadFile = async (name: ArtifactName) => {
    setFileError(null);
    try {
      const blob =
        name === codeName && version.code.state === 'ready'
          ? new Blob([version.code.text], { type: CODE_MEDIA_TYPES[codeName] })
          : await onFetchArtifact(number, name);
      // The exported code reads `data.csv` from its own directory, so the pair
      // keeps exactly these names.
      downloadBlob(blob, name);
      onOutcome?.(name === codeName ? 'downloaded_code' : 'downloaded_data', number);
    } catch {
      setFileError(`could not download ${name}`);
    }
  };

  /**
   * The interactive page in the theme on screen, built by the server now; the
   * session hook holds the whole session back while it builds (`pageBusy`),
   * and the beacon reports it as `downloaded_page`.
   */
  const handleDownloadPage = async () => {
    const shown = pages[shownTheme];
    if (shown === undefined && (busy || buildingPage)) return;
    setFileError(null);
    setBuildingPage(shown === undefined);
    try {
      // The open preview's page is the very file: no second build.
      const blob =
        shown !== undefined
          ? new Blob([shown], { type: 'text/html' })
          : await onFetchArtifact(number, PAGE_ARTIFACT, shownTheme);
      downloadBlob(blob, PAGE_ARTIFACT);
      onOutcome?.('downloaded_page', number);
    } catch {
      setFileError(`could not download ${PAGE_ARTIFACT}`);
    } finally {
      setBuildingPage(false);
    }
  };

  /** Fetch `theme`'s page for the open preview, unless it is there; the session waits while the server builds it. */
  const showPage = async (theme: Theme) => {
    if (!needsPage(theme) || busy || buildingPage) return;
    const run = previewRun.current;
    setPreviewError(theme, undefined);
    setBuildingPage(true);
    try {
      const text = await (await onFetchArtifact(number, PAGE_ARTIFACT, theme)).text();
      if (run !== previewRun.current) return; // closed meanwhile
      setPages(current => ({ ...current, [theme]: text }));
      if (!previewReported.current) {
        previewReported.current = true;
        onOutcome?.('opened_preview', number);
      }
    } catch (err) {
      if (run === previewRun.current) {
        const code = (err as { code?: unknown } | null)?.code;
        setPreviewError(theme, typeof code === 'string' ? code : 'internal');
      }
    } finally {
      setBuildingPage(false);
    }
  };

  const handleOpenPreview = () => {
    if (needsPage(shownTheme) && busy) return;
    previewReported.current = false;
    setInteractive(true);
    void showPage(shownTheme);
  };

  const handleClosePreview = () => {
    dropPreview();
    if (needsRender(shownTheme)) {
      // A theme the preview showed without its PNG: render it now, or go back to the run's own while busy.
      if (busy) setShownTheme(version.theme);
      else onRequestTheme(number, shownTheme);
    }
  };

  // The preview keeps the wrapper's own aspect, read from its page; the image box, and the preview while it
  // builds, take the PNG's.
  const shownPage = interactive ? pages[shownTheme] : undefined;
  const previewError = interactive ? previewErrors[shownTheme] : undefined;
  const pageFrame = shownPage !== undefined ? pageFrameSize(shownPage) : null;

  const overlayBtnSx = overlayButtonSx(isDark);
  // The image's actions stand over its top right corner as the plot page's icons, their names on
  // hover. On a phone that corner holds the plot's title and a hover never comes, so they stand
  // on the card's action line under the image instead, by their names (`.download()`).
  const imageActions = interactive ? (
    <Tooltip title=".preview()" disableFocusListener>
      <IconButton onClick={handleClosePreview} aria-label="Show image" sx={overlayBtnSx}>
        <ImageOutlinedIcon fontSize="small" />
      </IconButton>
    </Tooltip>
  ) : (
    <>
      {page && (
        <Tooltip title=".interactive()" disableFocusListener>
          <span style={{ display: 'inline-flex' }}>
            <IconButton
              onClick={handleOpenPreview}
              aria-label="Show interactive"
              disabled={busy || buildingPage}
              sx={overlayBtnSx}
            >
              <PlayArrowIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
      )}
      <Tooltip title=".copy_png()" disableFocusListener>
        <span style={{ display: 'inline-flex' }}>
          <IconButton
            onClick={handleCopyImage}
            aria-label="Copy image"
            disabled={!readyImage}
            sx={overlayBtnSx}
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
          >
            <OpenInNewIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
    </>
  );
  // The same actions on the phone's action line, the PNG's download first. Their names hold the
  // words on screen (`.copy_png()` is "Copy PNG image"), so a voice command finds them (WCAG 2.5.3).
  const phoneImageActions = interactive ? (
    <Box
      component="button"
      type="button"
      onClick={handleClosePreview}
      aria-label="Preview: show the image"
      sx={cardActionSx}
    >
      .preview()
    </Box>
  ) : (
    <>
      <Box
        component="button"
        type="button"
        onClick={handleDownloadPng}
        aria-label="Download PNG"
        disabled={!readyImage}
        sx={cardActionSx}
      >
        .download()
      </Box>
      <Box
        component="button"
        type="button"
        onClick={handleCopyImage}
        aria-label="Copy PNG image"
        disabled={!readyImage}
        sx={cardActionSx}
      >
        .copy_png()
      </Box>
      <Box
        component="button"
        type="button"
        onClick={handleOpen}
        aria-label="Open full size"
        disabled={!readyImage}
        sx={cardActionSx}
      >
        .open()
      </Box>
      {page && (
        <Box
          component="button"
          type="button"
          onClick={handleOpenPreview}
          aria-label="Show interactive"
          disabled={busy || buildingPage}
          sx={cardActionSx}
        >
          .interactive()
        </Box>
      )}
    </>
  );
  // Named the way the progress grid names its rounds, and which round shipped when an earlier one won.
  const attempts = triesText(result);
  const rounds = gridRows(result.rounds ?? [], [], result.status);
  // The status line: how long the plot took (the working line's clock, frozen as it shipped), the
  // tries and how many changes the run made, and the toggle of both lists. A version the page did
  // not time says no time, never a wrong one.
  const summary = [
    version.readyMs !== undefined ? `ready in ${elapsedClock(version.readyMs)}` : null,
    attempts,
    result.changes.length ? plural(result.changes.length, 'change') : null,
  ]
    .filter(Boolean)
    .join(' · ');
  const hasDetails = rounds.length > 0 || result.changes.length > 0;
  // The remembered decisions the version kept and the ones it added, as the server named them;
  // a version whose memory is unknown has neither.
  const decisions = version.decisions;
  const kept = decisions ? decisionsText('kept', decisions.kept) : null;
  const added = decisions ? decisionsText('new', decisions.added) : null;
  const label = plotCardLabel(number, library, request);
  // Both parts at every width: the label names the request, so this line is the card's only word
  // on what the version kept.
  const shown = [kept, added].filter(part => part !== null);
  const decisionsLine = shown.length ? (
    <Box
      data-testid="result-decisions"
      sx={{
        ...labelSx,
        color: 'var(--ink-soft)',
        lineHeight: 1.6,
        overflowWrap: 'anywhere',
        mt: narrow ? -1 : 0,
      }}
    >
      <span aria-hidden>{shown.map(part => part.text).join(' · ')}</span>
      <Box component="span" sx={visuallyHiddenSx}>
        {shown.map(part => part.spoken).join('; ')}
      </Box>
    </Box>
  ) : null;

  return (
    <CardFrame
      component="article"
      aria-label={`Plot version ${number}`}
      label={label.text}
      spokenLabel={label.spoken}
      labelTestId="result-label"
      toggle={{
        expanded,
        onToggle: () => (expanded ? collapse() : setExpanded(true)),
        bodyId,
      }}
    >
      {expanded && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, minWidth: 0 }}>
          {/* What the version kept and added, the card's first line from `sm` up (the v4 mock),
              its actions over the image's corner beside it. */}
          {!narrow && decisionsLine}
          {/* Image with the overlay actions of the plot page. */}
          <Box
            sx={{
              position: 'relative',
              borderRadius: 2,
              overflow: 'hidden',
              bgcolor: 'var(--bg-surface)',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              aspectRatio: pageFrame ? `${pageFrame.width}/${pageFrame.height}` : aspect,
            }}
            data-testid="result-image-box"
          >
            {interactive ? (
              previewError ? (
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
                  could not show the interactive plot ({previewError})
                </Box>
              ) : shownPage !== undefined ? (
                <InteractivePreview
                  key={shownTheme}
                  page={shownPage}
                  title={`Interactive plot, version ${number}, ${shownTheme} theme`}
                  onUnavailable={code => setPreviewError(shownTheme, code)}
                />
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
                    {`building the interactive ${shownTheme} plot…`}
                  </Box>
                </>
              )
            ) : readyImage ? (
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

            {!narrow && (
              <Box sx={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 0.5 }}>
                {imageActions}
              </Box>
            )}
          </Box>

          {/* On a phone the same line stands under the image, above the card's action line. */}
          {narrow && decisionsLine}

          {narrow && (
            <Box
              role="group"
              aria-label="Image actions"
              data-testid="result-image-actions"
              // The words line up with the card's text, the buttons' padding outside it.
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                columnGap: 1,
                rowGap: 0.5,
                ml: -1.25,
                mt: -1,
              }}
            >
              {phoneImageActions}
            </Box>
          )}

          {/* The theme switch and, at the row's end, the version's status and the run's line. */}
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              alignItems: 'center',
              columnGap: 2,
              rowGap: 0.5,
              minWidth: 0,
            }}
          >
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
                    disabled={
                      !active &&
                      (busy || buildingPage) &&
                      (interactive ? needsPage(theme) : needsRender(theme))
                    }
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
              {!interactive &&
                readyImage?.status === 'needs_attention' &&
                shownTheme !== version.theme && (
                  <Box component="span" sx={{ ...labelSx, ml: 1 }}>
                    padded onto the canvas
                  </Box>
                )}
            </Box>
            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                columnGap: 1.5,
                ml: 'auto',
                minWidth: 0,
              }}
            >
              {/* The version's status, which the card's header row had before its label moved
                  onto the border: a dot in the status colour beside the word. */}
              <Box
                component="span"
                data-testid="result-status"
                sx={{
                  ...labelSx,
                  color: 'var(--ink-soft)',
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
              >
                {STATUS_LABEL[result.status] ?? result.status}
              </Box>
              {/* The run in one line: its tries and the count of its changes. The ⓘ toggle opens
                  the rounds and the "what changed" list; a run with neither has a plain line. */}
              {hasDetails ? (
                <Box
                  component="button"
                  type="button"
                  data-testid="result-summary"
                  onClick={() => setDetailsOpen(open => !open)}
                  aria-expanded={detailsOpen}
                  aria-controls={detailsOpen ? detailsId : undefined}
                  // The visible line, with what it opens in front for a screen reader.
                  aria-label={`Run details: ${summary}`}
                  sx={{
                    ...actionButtonSx,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.5,
                    mr: -0.75,
                    px: 0.75,
                    whiteSpace: 'normal',
                    textAlign: 'left',
                  }}
                >
                  {summary}
                  {detailsOpen ? (
                    <InfoIcon aria-hidden sx={{ fontSize: 16 }} />
                  ) : (
                    <InfoOutlinedIcon aria-hidden sx={{ fontSize: 16 }} />
                  )}
                </Box>
              ) : (
                <Box component="span" data-testid="result-summary" sx={labelSx}>
                  {summary}
                </Box>
              )}
            </Box>
          </Box>

          {detailsOpen && hasDetails && (
            <Box
              id={detailsId}
              data-testid="result-details"
              sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, minWidth: 0 }}
            >
              {/* How each round of the run ended, as the progress grid showed it while it ran. */}
              {rounds.length > 0 && (
                <Box sx={{ minWidth: 0, overflowX: 'auto' }}>
                  <Box sx={{ ...labelSx, mb: 0.5 }}># rounds</Box>
                  <RoundGrid rows={rounds} label={`Rounds of version ${number}`} />
                </Box>
              )}

              {result.changes.length > 0 && (
                <Box>
                  <Box sx={labelSx}># what changed</Box>
                  <Box component="ul" sx={{ m: 0, mt: 0.5, pl: 2.5, ...bodyTextSx, ...readableSx }}>
                    {result.changes.map((change, index) => (
                      <li key={index}>{change}</li>
                    ))}
                  </Box>
                </Box>
              )}
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
              <Box sx={labelSx}>
                # notes — still worth a look
                <InfoPopover
                  label="The notes in full"
                  heading="# the review's notes, as the repair reads them"
                  lines={result.residual_defects}
                  testId="residual-details"
                />
              </Box>
              <Box
                component="ul"
                data-testid="residual-notes"
                sx={{ m: 0, mt: 0.5, pl: 2.5, ...bodyTextSx, ...readableSx }}
              >
                {plainNotes(result.residual_defects).map(note => (
                  <li key={note}>{note}</li>
                ))}
              </Box>
            </Box>
          )}

          {/* The adapted code: copy it, or download it with its data; the code itself on request. */}
          <Box sx={{ minWidth: 0, display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                alignItems: 'center',
                gap: 0.5,
              }}
            >
              <Box component="span" sx={{ ...labelSx, mr: 'auto' }}>
                {page
                  ? `# ${codeName} runs in ${PAGE_ARTIFACT}`
                  : `# ${codeName} runs next to data.csv`}
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, ml: -1.25 }}>
                <Box
                  component="button"
                  type="button"
                  onClick={() => setCodeOpen(open => !open)}
                  aria-expanded={codeOpen}
                  aria-controls={codeOpen ? codeId : undefined}
                  aria-label={codeOpen ? 'Hide code' : 'Show code'}
                  sx={actionButtonSx}
                >
                  {codeOpen ? '.hide_code()' : '.show_code()'}
                </Box>
                <Box
                  component="button"
                  type="button"
                  onClick={() =>
                    version.code.state === 'ready' && copyToClipboard(version.code.text)
                  }
                  disabled={version.code.state !== 'ready'}
                  aria-label="Copy code"
                  sx={copyFailed ? { ...actionButtonSx, color: colors.error } : actionButtonSx}
                >
                  {copied ? '.copied' : copyFailed ? COPY_FAILED_TEXT : '.copy()'}
                </Box>
                {/* The button's name stays "Copy code"; a screen reader hears the refusal here. */}
                <Box component="span" role="status" sx={visuallyHiddenSx}>
                  {copyFailed ? COPY_FAILED_TEXT : ''}
                </Box>
                <Box
                  component="button"
                  type="button"
                  onClick={() => handleDownloadFile(codeName)}
                  aria-label={`Download ${codeName}`}
                  sx={actionButtonSx}
                >
                  {downloadCodeLabel}
                </Box>
                {page && (
                  <Box
                    component="button"
                    type="button"
                    onClick={handleDownloadPage}
                    disabled={busy || buildingPage}
                    aria-label={`Download ${PAGE_ARTIFACT}, ${shownTheme} theme`}
                    aria-busy={buildingPage}
                    sx={actionButtonSx}
                  >
                    .download(&apos;plot.html&apos;){buildingPage ? ' …' : ''}
                  </Box>
                )}
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
              <Box role="alert" sx={{ ...labelSx, color: colors.error }}>
                {fileError}
              </Box>
            )}
            {/* In view also while the code is folded: it says why `.copy()` waits. */}
            {version.code.state === 'failed' && (
              <Box role="alert" sx={{ ...labelSx, color: colors.error }}>
                could not load {codeName}
              </Box>
            )}
            {/* The highlighter's chunk loads only once the code is asked for. */}
            {codeOpen && version.code.state !== 'failed' && (
              <Box id={codeId} data-testid="result-code" sx={{ minWidth: 0 }}>
                {version.code.state === 'ready' ? (
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
                        language={codeLanguage}
                        library={library}
                      />
                    </Suspense>
                  </Box>
                ) : (
                  <Skeleton variant="rounded" height={120} />
                )}
              </Box>
            )}
          </Box>

          {/* Quick feedback: this version as a case for tuning the assistant. */}
          <Box data-testid="result-feedback-slot" sx={{ '&:empty': { display: 'none' } }}>
            {onSendFeedback && (
              <ResultFeedback
                version={number}
                sent={version.feedback ?? null}
                onSend={onSendFeedback}
              />
            )}
          </Box>
        </Box>
      )}
    </CardFrame>
  );
}
