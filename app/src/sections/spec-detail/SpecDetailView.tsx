/**
 * SpecDetailView component - Single implementation detail view.
 *
 * Shows large image with library carousel and action buttons.
 * Toggles between static preview (PNG) and interactive HTML iframe.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DownloadIcon from '@mui/icons-material/Download';
import ImageOutlinedIcon from '@mui/icons-material/ImageOutlined';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ThumbDownIcon from '@mui/icons-material/ThumbDown';
import ThumbDownOutlinedIcon from '@mui/icons-material/ThumbDownOutlined';
import ThumbUpIcon from '@mui/icons-material/ThumbUp';
import ThumbUpOutlinedIcon from '@mui/icons-material/ThumbUpOutlined';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Skeleton from '@mui/material/Skeleton';
import Tooltip from '@mui/material/Tooltip';

import { API_URL } from 'src/constants';
import { useTheme } from 'src/hooks/useLayoutContext';
import { useLocalStorage } from 'src/hooks/useLocalStorage';
import { useQuickReaction } from 'src/hooks/useQuickReaction';
import { colors, fontSize, overlayButtonSx, typography } from 'src/theme';
import type { Implementation } from 'src/types';
import { PLOT_VOTES_KEY, type QuickReaction, voteKey, type VoteTarget } from 'src/utils/feedback';
import { buildDetailSrcSet, DETAIL_SIZES } from 'src/utils/responsiveImage';
import { selectPreviewHtml, selectPreviewUrl } from 'src/utils/themedPreview';

const INITIAL_WIDTH = 1600;
const INITIAL_HEIGHT = 900;
const VOTE_TOAST_MS = 1200;

interface SpecDetailViewProps {
  specId: string;
  specTitle: string;
  selectedLibrary: string;
  currentImpl: Implementation | null;
  implementations: Implementation[];
  imageLoaded: boolean;
  codeCopied: string | null;
  downloadDone: string | null;
  viewMode: 'preview' | 'interactive';
  onViewModeChange: (mode: 'preview' | 'interactive') => void;
  onImageLoad: () => void;
  onCopyCode: (impl: Implementation) => void;
  onDownload: (impl: Implementation) => void;
  onTrackEvent: (event: string, props?: Record<string, string | undefined>) => void;
}

export function SpecDetailView({
  specId,
  specTitle,
  selectedLibrary,
  currentImpl,
  implementations,
  imageLoaded,
  codeCopied,
  downloadDone,
  viewMode,
  onViewModeChange,
  onImageLoad,
  onCopyCode,
  onDownload,
  onTrackEvent,
}: SpecDetailViewProps) {
  const sortedImpls = [...implementations].sort((a, b) => a.library_id.localeCompare(b.library_id));
  const currentIndex = sortedImpls.findIndex(impl => impl.library_id === selectedLibrary);

  // Static preview zoom + pan
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoomed, setZoomed] = useState(false);
  const [origin, setOrigin] = useState({ x: 50, y: 50 });
  const [animating, setAnimating] = useState(false);
  const animTimerRef = useRef<ReturnType<typeof setTimeout>>(null);
  const prevLibRef = useRef(selectedLibrary);

  // Reset zoom when library changes
  useEffect(() => {
    if (prevLibRef.current !== selectedLibrary) {
      prevLibRef.current = selectedLibrary;
      setZoomed(false);
      setOrigin({ x: 50, y: 50 });
    }
  }, [selectedLibrary]);

  // 👍 / 👎 on the plot — one tap rates THIS implementation, once: the vote is
  // final for the session, so nobody can flip up/down at will (the server
  // drops repeat votes from the same session for the same image as well).
  // The visitor's own vote is kept per spec/language/library in localStorage
  // so the thumb stays inked when they come back or flip through the carousel;
  // the server row is what gets counted (FeedbackRepository.reaction_counts).
  const submitReaction = useQuickReaction();
  const [votes, setVotes] = useLocalStorage<Record<string, QuickReaction>>(PLOT_VOTES_KEY, {});
  const voteTarget = useMemo<VoteTarget | null>(
    () =>
      currentImpl
        ? { specId, language: currentImpl.language, libraryId: currentImpl.library_id }
        : null,
    [specId, currentImpl]
  );
  const vote = voteTarget ? (votes[voteKey(voteTarget)] ?? null) : null;
  const [voteToast, setVoteToast] = useState<QuickReaction | null>(null);
  const voteToastTimerRef = useRef<ReturnType<typeof setTimeout>>(null);
  const handleVote = useCallback(
    (reaction: QuickReaction) => {
      if (!voteTarget || vote) return;
      const key = voteKey(voteTarget);
      // Optimistic: ink the thumb now, roll back only if the server refused.
      setVotes(prev => ({ ...prev, [key]: reaction }));
      setVoteToast(reaction);
      if (voteToastTimerRef.current) clearTimeout(voteToastTimerRef.current);
      voteToastTimerRef.current = setTimeout(() => setVoteToast(null), VOTE_TOAST_MS);
      void submitReaction(reaction, voteTarget).then(ok => {
        if (ok) return;
        setVotes(prev => {
          const next = { ...prev };
          delete next[key];
          return next;
        });
        setVoteToast(null);
      });
    },
    [voteTarget, vote, setVotes, submitReaction]
  );
  useEffect(() => {
    return () => {
      if (voteToastTimerRef.current) clearTimeout(voteToastTimerRef.current);
    };
  }, []);

  // Interactive iframe state — scaled to fit container
  const interactiveContainerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [contentWidth, setContentWidth] = useState(INITIAL_WIDTH);
  const [contentHeight, setContentHeight] = useState(INITIAL_HEIGHT);
  const [sizeReady, setSizeReady] = useState(false);

  const updateScale = useCallback(() => {
    if (!interactiveContainerRef.current) return;
    const padding = 24;
    const cw = interactiveContainerRef.current.clientWidth - padding;
    const ch = interactiveContainerRef.current.clientHeight - padding;
    const sx = cw / contentWidth;
    const sy = ch / contentHeight;
    setScale(Math.min(sx, sy) * 0.98);
  }, [contentWidth, contentHeight]);

  useEffect(() => {
    if (viewMode !== 'interactive') return;
    const handleMessage = (event: MessageEvent) => {
      const allowedOrigins = [
        window.location.origin,
        'https://anyplot.ai',
        'https://api.anyplot.ai',
        'http://localhost:8000',
      ];
      if (!allowedOrigins.includes(event.origin)) return;
      if (event.data?.type === 'anyplot-size') {
        const { width, height } = event.data;
        if (typeof width === 'number' && typeof height === 'number' && width > 0 && height > 0) {
          setContentWidth(width);
          setContentHeight(height);
          setSizeReady(true);
        }
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [viewMode]);

  useEffect(() => {
    if (viewMode !== 'interactive') return;
    const timer = setTimeout(updateScale, 100);
    window.addEventListener('resize', updateScale);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', updateScale);
    };
  }, [viewMode, updateScale]);

  // Reset interactive size when switching library — React 19 "adjust state on prop change".
  const [prevLibrary, setPrevLibrary] = useState(selectedLibrary);
  if (prevLibrary !== selectedLibrary) {
    setPrevLibrary(selectedLibrary);
    setSizeReady(false);
    setContentWidth(INITIAL_WIDTH);
    setContentHeight(INITIAL_HEIGHT);
  }

  const handleZoomToggle = useCallback(
    (e: React.MouseEvent) => {
      if (!containerRef.current) return;
      if (!zoomed) {
        const rect = containerRef.current.getBoundingClientRect();
        setOrigin({
          x: ((e.clientX - rect.left) / rect.width) * 100,
          y: ((e.clientY - rect.top) / rect.height) * 100,
        });
      }
      setAnimating(true);
      setZoomed(z => !z);
      if (animTimerRef.current) clearTimeout(animTimerRef.current);
      animTimerRef.current = setTimeout(() => setAnimating(false), 300);
    },
    [zoomed]
  );

  useEffect(() => {
    return () => {
      if (animTimerRef.current) clearTimeout(animTimerRef.current);
    };
  }, []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!zoomed || animating || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      setOrigin({
        x: ((e.clientX - rect.left) / rect.width) * 100,
        y: ((e.clientY - rect.top) / rect.height) * 100,
      });
    },
    [zoomed, animating]
  );

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!zoomed || animating || !containerRef.current) return;
      const touch = e.touches[0];
      const rect = containerRef.current.getBoundingClientRect();
      setOrigin({
        x: ((touch.clientX - rect.left) / rect.width) * 100,
        y: ((touch.clientY - rect.top) / rect.height) * 100,
      });
    },
    [zoomed, animating]
  );

  const { isDark } = useTheme();
  const previewUrl = selectPreviewUrl(currentImpl, isDark);
  const previewHtml = selectPreviewHtml(currentImpl, isDark);
  const interactiveAvailable = !!previewHtml;

  // Overlay action buttons (vote/copy/download/open/preview/raw) sit on top
  // of the preview image — shared theme-aware style, see src/theme/tokens.ts.
  const overlayBtnSx = overlayButtonSx(isDark);
  const proxyUrl = (url: string) =>
    `${API_URL}/proxy/html?url=${encodeURIComponent(url)}&origin=${encodeURIComponent(window.location.origin)}`;

  // 👍 sits top-left, 👎 bottom-left — the two corners the plot content
  // rarely uses — so rating an image is one obvious tap without covering the
  // title or the legend. The chosen thumb stays inked (green / matte red) so
  // the choice reads as committed, not merely hovered, and the other thumb
  // fades out once a vote is in. The same elements are rendered on both the
  // static and the interactive surface.
  const thumbSx = (active: boolean, locked: boolean, activeColor: string) => {
    if (active) {
      return {
        ...overlayBtnSx,
        color: activeColor,
        '&:hover': { ...overlayBtnSx['&:hover'], color: activeColor },
      };
    }
    if (locked) {
      // Keep the overlay surface under the disabled thumb; MUI would drop it.
      return {
        ...overlayBtnSx,
        '&.Mui-disabled': { bgcolor: overlayBtnSx.bgcolor, opacity: 0.45 },
      };
    }
    return overlayBtnSx;
  };
  const thumbButton = (
    reaction: QuickReaction,
    label: string,
    verb: string,
    activeColor: string,
    Outlined: typeof ThumbUpOutlinedIcon,
    Filled: typeof ThumbUpIcon
  ) => {
    if (!currentImpl) return null;
    const active = vote === reaction;
    const locked = !!vote && !active;
    return (
      // A natively disabled button emits no pointer events, so the tooltip
      // listens on a wrapping span (MUI's documented pattern for this case).
      <Tooltip title={locked ? '.rated()' : verb} disableFocusListener>
        <span style={{ display: 'inline-flex' }}>
          <IconButton
            onClick={(e: React.MouseEvent) => {
              (e.currentTarget as HTMLElement).blur();
              handleVote(reaction);
            }}
            aria-label={label}
            aria-pressed={active}
            disabled={locked}
            sx={thumbSx(active, locked, activeColor)}
            size="medium"
          >
            {active ? <Filled fontSize="small" /> : <Outlined fontSize="small" />}
          </IconButton>
        </span>
      </Tooltip>
    );
  };
  const thumbUpButton = thumbButton(
    'thumbs_up',
    'Thumbs up',
    '.like()',
    colors.primary,
    ThumbUpOutlinedIcon,
    ThumbUpIcon
  );
  const thumbDownButton = thumbButton(
    'thumbs_down',
    'Thumbs down',
    '.dislike()',
    colors.error,
    ThumbDownOutlinedIcon,
    ThumbDownIcon
  );
  // Centre toast, same shape as the `.copied` / `.downloaded` confirmations.
  const toastText = voteToast
    ? voteToast === 'thumbs_up'
      ? '>>> .liked'
      : '>>> .disliked'
    : currentImpl && codeCopied === currentImpl.library_id
      ? '>>> .copied'
      : currentImpl && downloadDone === currentImpl.library_id
        ? '>>> .downloaded'
        : null;
  const toast = toastText && (
    <Box
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
        fontSize: fontSize.sm,
        pointerEvents: 'none',
        zIndex: 2,
      }}
    >
      {toastText}
    </Box>
  );

  return (
    <Box sx={{ maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 }, mx: 'auto' }}>
      {viewMode === 'interactive' && interactiveAvailable && previewHtml ? (
        <Box
          ref={interactiveContainerRef}
          sx={{
            position: 'relative',
            borderRadius: 2,
            overflow: 'hidden',
            bgcolor: 'var(--bg-surface)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            aspectRatio: '16/9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            p: 1.5,
          }}
        >
          <Box
            sx={{
              bgcolor: 'var(--bg-surface)',
              overflow: 'hidden',
              width: contentWidth * scale,
              height: contentHeight * scale,
              opacity: sizeReady ? 1 : 0,
              transition: 'opacity 0.2s ease-in-out',
            }}
          >
            <iframe
              src={proxyUrl(previewHtml)}
              width={contentWidth}
              height={contentHeight}
              style={{
                width: contentWidth,
                height: contentHeight,
                border: 'none',
                transform: `scale(${scale})`,
                transformOrigin: 'top left',
              }}
              title={`${specTitle} - ${selectedLibrary} interactive`}
            />
          </Box>

          {toast}

          <Box sx={{ position: 'absolute', top: 8, left: 8, display: 'flex', gap: 0.5 }}>
            {thumbUpButton}
          </Box>
          <Box sx={{ position: 'absolute', bottom: 8, left: 8, display: 'flex', gap: 0.5 }}>
            {thumbDownButton}
          </Box>

          <Box sx={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 0.5 }}>
            <Tooltip title=".preview()" disableFocusListener>
              <IconButton
                onClick={() => {
                  onViewModeChange('preview');
                  onTrackEvent('view_mode_change', { mode: 'preview', library: selectedLibrary });
                }}
                aria-label="Show static preview"
                sx={overlayBtnSx}
                size="medium"
              >
                <ImageOutlinedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title=".raw()" disableFocusListener>
              <IconButton
                onClick={() =>
                  previewHtml && window.open(previewHtml, '_blank', 'noopener,noreferrer')
                }
                aria-label="Open raw HTML"
                sx={overlayBtnSx}
                size="medium"
              >
                <OpenInNewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      ) : (
        <Box
          ref={containerRef}
          role="button"
          tabIndex={0}
          aria-label={zoomed ? 'Zoom out' : 'Zoom in'}
          onClick={handleZoomToggle}
          onKeyDown={(e: React.KeyboardEvent) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              handleZoomToggle(e as unknown as React.MouseEvent);
            }
          }}
          onMouseMove={handleMouseMove}
          onTouchMove={handleTouchMove}
          sx={{
            position: 'relative',
            borderRadius: 2,
            overflow: 'hidden',
            bgcolor: 'var(--bg-surface)',
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            aspectRatio: '16/9',
            cursor: zoomed ? 'zoom-out' : 'zoom-in',
            touchAction: zoomed ? 'none' : 'auto',
            outline: 'none',
            '&:focus-visible': { boxShadow: `0 0 0 2px ${colors.primary}` },
            '&:hover .impl-counter': { opacity: 1 },
          }}
        >
          {!imageLoaded && (
            <Skeleton
              variant="rectangular"
              sx={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
            />
          )}
          {previewUrl && (
            <Box
              component="picture"
              key={previewUrl}
              sx={{ display: imageLoaded ? 'contents' : 'none' }}
            >
              <source
                type="image/webp"
                srcSet={buildDetailSrcSet(previewUrl, 'webp')}
                sizes={DETAIL_SIZES}
              />
              <source
                type="image/png"
                srcSet={buildDetailSrcSet(previewUrl, 'png')}
                sizes={DETAIL_SIZES}
              />
              <Box
                component="img"
                src={`${previewUrl.replace(/\.png$/, '')}_1200.png`}
                alt={`${specTitle} - ${selectedLibrary}`}
                onLoad={onImageLoad}
                sx={{
                  display: 'block',
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  transform: zoomed ? 'scale(2.5)' : 'scale(1)',
                  transformOrigin: `${origin.x}% ${origin.y}%`,
                  transition: animating ? 'transform 0.3s ease' : 'none',
                }}
                onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                  const target = e.target as HTMLImageElement;
                  if (!target.dataset.fallback) {
                    target.dataset.fallback = '1';
                    target
                      .closest('picture')
                      ?.querySelectorAll('source')
                      .forEach(s => s.remove());
                    target.removeAttribute('srcset');
                    target.src = previewUrl;
                  }
                }}
              />
            </Box>
          )}

          {toast}

          <Box
            onClick={e => e.stopPropagation()}
            sx={{
              position: 'absolute',
              top: 8,
              left: 8,
              display: zoomed ? 'none' : 'flex',
              gap: 0.5,
            }}
          >
            {thumbUpButton}
          </Box>
          <Box
            onClick={e => e.stopPropagation()}
            sx={{
              position: 'absolute',
              bottom: 8,
              left: 8,
              display: zoomed ? 'none' : 'flex',
              gap: 0.5,
            }}
          >
            {thumbDownButton}
          </Box>

          <Box
            onClick={e => e.stopPropagation()}
            sx={{
              position: 'absolute',
              top: 8,
              right: 8,
              display: zoomed ? 'none' : 'flex',
              gap: 0.5,
            }}
          >
            {currentImpl && (
              <Tooltip title=".copy()" disableFocusListener>
                <IconButton
                  onClick={(e: React.MouseEvent) => {
                    (e.currentTarget as HTMLElement).blur();
                    onCopyCode(currentImpl);
                  }}
                  aria-label="Copy code"
                  sx={overlayBtnSx}
                  size="medium"
                >
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {currentImpl && (
              <Tooltip title=".download()" disableFocusListener>
                <IconButton
                  onClick={(e: React.MouseEvent) => {
                    (e.currentTarget as HTMLElement).blur();
                    onDownload(currentImpl);
                  }}
                  aria-label="Download PNG"
                  sx={overlayBtnSx}
                  size="medium"
                >
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {interactiveAvailable && (
              <Tooltip title=".open()" disableFocusListener>
                <IconButton
                  onClick={() => {
                    onViewModeChange('interactive');
                    onTrackEvent('view_mode_change', {
                      mode: 'interactive',
                      library: selectedLibrary,
                    });
                  }}
                  aria-label="Show interactive"
                  sx={overlayBtnSx}
                  size="medium"
                >
                  <PlayArrowIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </Box>

          {implementations.length > 1 && !zoomed && (
            <Box
              className="impl-counter"
              sx={{
                position: 'absolute',
                bottom: 8,
                right: 8,
                px: 1,
                py: 0.25,
                bgcolor: 'rgba(0,0,0,0.6)',
                borderRadius: 1,
                fontSize: '0.75rem',
                fontFamily: typography.fontFamily,
                color: '#fff',
                opacity: 0,
                transition: 'opacity 0.2s',
              }}
            >
              {currentIndex + 1}/{implementations.length}
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
}
