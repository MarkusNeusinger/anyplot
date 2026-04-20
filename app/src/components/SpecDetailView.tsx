/**
 * SpecDetailView component - Single implementation detail view.
 *
 * Shows large image with library carousel and action buttons.
 * Toggles between static preview (PNG) and interactive HTML iframe.
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Skeleton from '@mui/material/Skeleton';
import DownloadIcon from '@mui/icons-material/Download';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ImageOutlinedIcon from '@mui/icons-material/ImageOutlined';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

import type { Implementation } from '../types';
import { API_URL } from '../constants';
import { colors, fontSize, typography } from '../theme';
import { buildDetailSrcSet, DETAIL_SIZES } from '../utils/responsiveImage';

const INITIAL_WIDTH = 1600;
const INITIAL_HEIGHT = 900;

interface SpecDetailViewProps {
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
  const currentIndex = sortedImpls.findIndex((impl) => impl.library_id === selectedLibrary);

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

  // Reset interactive size when switching library
  useEffect(() => {
    setSizeReady(false);
    setContentWidth(INITIAL_WIDTH);
    setContentHeight(INITIAL_HEIGHT);
  }, [selectedLibrary]);

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
      setZoomed((z) => !z);
      if (animTimerRef.current) clearTimeout(animTimerRef.current);
      animTimerRef.current = setTimeout(() => setAnimating(false), 300);
    },
    [zoomed],
  );

  useEffect(() => {
    return () => { if (animTimerRef.current) clearTimeout(animTimerRef.current); };
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
    [zoomed, animating],
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
    [zoomed, animating],
  );

  const interactiveAvailable = !!currentImpl?.preview_html;
  const proxyUrl = (url: string) =>
    `${API_URL}/proxy/html?url=${encodeURIComponent(url)}&origin=${encodeURIComponent(window.location.origin)}`;

  return (
    <Box sx={{ maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 }, mx: 'auto' }}>
      {viewMode === 'interactive' && interactiveAvailable && currentImpl?.preview_html ? (
        <Box
          ref={interactiveContainerRef}
          sx={{
            position: 'relative',
            borderRadius: 2,
            overflow: 'hidden',
            bgcolor: '#fff',
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
              bgcolor: '#fff',
              overflow: 'hidden',
              width: contentWidth * scale,
              height: contentHeight * scale,
              opacity: sizeReady ? 1 : 0,
              transition: 'opacity 0.2s ease-in-out',
            }}
          >
            <iframe
              src={proxyUrl(currentImpl.preview_html)}
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

          <Box sx={{ position: 'absolute', top: 8, right: 8, display: 'flex', gap: 0.5 }}>
            <Tooltip title=".preview()" disableFocusListener>
              <IconButton
                onClick={() => {
                  onViewModeChange('preview');
                  onTrackEvent('view_mode_change', { mode: 'preview', library: selectedLibrary });
                }}
                aria-label=".preview()"
                sx={{ bgcolor: 'rgba(255,255,255,0.9)', '&:hover': { bgcolor: '#fff', color: colors.primary } }}
                size="medium"
              >
                <ImageOutlinedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title=".raw()" disableFocusListener>
              <IconButton
                onClick={() => window.open(currentImpl.preview_html, '_blank', 'noopener,noreferrer')}
                aria-label=".raw()"
                sx={{ bgcolor: 'rgba(255,255,255,0.9)', '&:hover': { bgcolor: '#fff', color: colors.primary } }}
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
          aria-label={zoomed ? '.zoom(-)' : '.zoom(+)'}
          onClick={handleZoomToggle}
          onKeyDown={(e: React.KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleZoomToggle(e as unknown as React.MouseEvent); } }}
          onMouseMove={handleMouseMove}
          onTouchMove={handleTouchMove}
          sx={{
            position: 'relative',
            borderRadius: 2,
            overflow: 'hidden',
            bgcolor: '#fff',
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
          {currentImpl?.preview_url && (
            <Box component="picture" sx={{ display: imageLoaded ? 'contents' : 'none' }}>
              <source type="image/webp" srcSet={buildDetailSrcSet(currentImpl.preview_url, 'webp')} sizes={DETAIL_SIZES} />
              <source type="image/png" srcSet={buildDetailSrcSet(currentImpl.preview_url, 'png')} sizes={DETAIL_SIZES} />
              <Box
                component="img"
                src={`${currentImpl.preview_url.replace(/\.png$/, '')}_1200.png`}
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
                    target.closest('picture')?.querySelectorAll('source').forEach(s => s.remove());
                    target.removeAttribute('srcset');
                    target.src = currentImpl.preview_url!;
                  }
                }}
              />
            </Box>
          )}

          {currentImpl && (codeCopied === currentImpl.library_id || downloadDone === currentImpl.library_id) && (
            <Box sx={{
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
            }}>
              {codeCopied === currentImpl.library_id ? '>>> .copied' : '>>> .downloaded'}
            </Box>
          )}

          <Box
            onClick={(e) => e.stopPropagation()}
            sx={{ position: 'absolute', top: 8, right: 8, display: zoomed ? 'none' : 'flex', gap: 0.5 }}
          >
            {currentImpl && (
              <Tooltip title=".copy()" disableFocusListener>
                <IconButton
                  onClick={(e: React.MouseEvent) => { (e.currentTarget as HTMLElement).blur(); onCopyCode(currentImpl); }}
                  aria-label=".copy()"
                  sx={{ bgcolor: 'rgba(255,255,255,0.9)', '&:hover': { bgcolor: '#fff', color: colors.primary } }}
                  size="medium"
                >
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            {currentImpl && (
              <Tooltip title=".download()" disableFocusListener>
                <IconButton
                  onClick={(e: React.MouseEvent) => { (e.currentTarget as HTMLElement).blur(); onDownload(currentImpl); }}
                  aria-label=".download()"
                  sx={{ bgcolor: 'rgba(255,255,255,0.9)', '&:hover': { bgcolor: '#fff', color: colors.primary } }}
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
                    onTrackEvent('view_mode_change', { mode: 'interactive', library: selectedLibrary });
                  }}
                  aria-label=".open()"
                  sx={{ bgcolor: 'rgba(255,255,255,0.9)', '&:hover': { bgcolor: '#fff', color: colors.primary } }}
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
