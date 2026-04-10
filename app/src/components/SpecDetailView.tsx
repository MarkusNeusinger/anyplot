/**
 * SpecDetailView component - Single implementation detail view.
 *
 * Shows large image with library carousel and action buttons.
 */

import { useState, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Skeleton from '@mui/material/Skeleton';
import DownloadIcon from '@mui/icons-material/Download';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';

import type { Implementation } from '../types';
import { colors, fontSize, typography } from '../theme';
import { buildDetailSrcSet, DETAIL_SIZES } from '../utils/responsiveImage';

interface SpecDetailViewProps {
  specId: string;
  specTitle: string;
  selectedLibrary: string;
  currentImpl: Implementation | null;
  implementations: Implementation[];
  imageLoaded: boolean;
  codeCopied: string | null;
  downloadDone: string | null;
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
  onImageLoad,
  onCopyCode,
  onDownload,
  onTrackEvent,
}: SpecDetailViewProps) {
  // Sort implementations alphabetically for the counter
  const sortedImpls = [...implementations].sort((a, b) => a.library_id.localeCompare(b.library_id));
  const currentIndex = sortedImpls.findIndex((impl) => impl.library_id === selectedLibrary);

  // In-place zoom + pan
  const containerRef = useRef<HTMLDivElement>(null);
  const [zoomed, setZoomed] = useState(false);
  const [origin, setOrigin] = useState({ x: 50, y: 50 });
  const [animating, setAnimating] = useState(false);
  const prevLibRef = useRef(selectedLibrary);

  // Reset zoom when library changes (no effect needed)
  if (prevLibRef.current !== selectedLibrary) {
    prevLibRef.current = selectedLibrary;
    setZoomed(false);
    setOrigin({ x: 50, y: 50 });
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
      setZoomed((z) => !z);
      setTimeout(() => setAnimating(false), 300);
    },
    [zoomed],
  );

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

  return (
    <Box
      sx={{
        maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 },
        mx: 'auto',
      }}
    >
      <Box
        ref={containerRef}
        onClick={handleZoomToggle}
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
          '&:hover .impl-counter': {
            opacity: 1,
          },
        }}
      >
        {!imageLoaded && (
          <Skeleton
            variant="rectangular"
            sx={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
            }}
          />
        )}
        {currentImpl?.preview_url && (
          <Box
            component="picture"
            sx={{
              display: imageLoaded ? 'contents' : 'none',
            }}
          >
            <source
              type="image/webp"
              srcSet={buildDetailSrcSet(currentImpl.preview_url, 'webp')}
              sizes={DETAIL_SIZES}
            />
            <source
              type="image/png"
              srcSet={buildDetailSrcSet(currentImpl.preview_url, 'png')}
              sizes={DETAIL_SIZES}
            />
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

        {/* Copied/Downloaded confirmation overlay */}
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
            {codeCopied === currentImpl.library_id ? '>>> copied' : '>>> downloaded'}
          </Box>
        )}

        {/* Action Buttons (top-right) - stop propagation */}
        <Box
          onClick={(e) => e.stopPropagation()}
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            display: zoomed ? 'none' : 'flex',
            gap: 0.5,
          }}
        >
          {currentImpl && (
            <Tooltip title="Copy Code" disableFocusListener>
              <IconButton
                onClick={(e: React.MouseEvent) => { (e.currentTarget as HTMLElement).blur(); onCopyCode(currentImpl); }}
                aria-label="Copy code"
                sx={{
                  bgcolor: 'rgba(255,255,255,0.9)',
                  '&:hover': { bgcolor: '#fff', color: colors.primary },
                }}
                size="medium"
              >
                <ContentCopyIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {currentImpl && (
            <Tooltip title="Download PNG" disableFocusListener>
              <IconButton
                onClick={(e: React.MouseEvent) => { (e.currentTarget as HTMLElement).blur(); onDownload(currentImpl); }}
                aria-label="Download PNG"
                sx={{
                  bgcolor: 'rgba(255,255,255,0.9)',
                  '&:hover': { bgcolor: '#fff', color: colors.primary },
                }}
                size="medium"
              >
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {currentImpl?.preview_html && (
            <Tooltip title="Open Interactive" disableFocusListener>
              <IconButton
                component={Link}
                to={`/interactive/${specId}/${selectedLibrary}`}
                aria-label="Open interactive"
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onTrackEvent('open_interactive', { spec: specId, library: selectedLibrary });
                }}
                sx={{
                  bgcolor: 'rgba(255,255,255,0.9)',
                  '&:hover': { bgcolor: '#fff', color: colors.primary },
                }}
                size="medium"
              >
                <OpenInNewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* Implementation counter (hover) */}
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
    </Box>
  );
}
