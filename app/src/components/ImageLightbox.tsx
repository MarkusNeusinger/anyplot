/**
 * ImageLightbox component - Full-resolution plot image viewer.
 *
 * MUI Modal-based lightbox with library switching, keyboard navigation,
 * and action buttons (copy code, download, open interactive).
 */

import { useEffect, useMemo, useCallback } from 'react';
import Modal from '@mui/material/Modal';
import Fade from '@mui/material/Fade';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import CloseIcon from '@mui/icons-material/Close';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import DownloadIcon from '@mui/icons-material/Download';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';

import type { Implementation } from '../types';
import { fontSize } from '../theme';
import { buildDetailSrcSet, DETAIL_SIZES } from '../utils/responsiveImage';

interface ImageLightboxProps {
  open: boolean;
  specId: string;
  specTitle: string;
  currentImpl: Implementation | null;
  implementations: Implementation[];
  codeCopied: string | null;
  onClose: () => void;
  onSelectLibrary: (libraryId: string) => void;
  onCopyCode: (impl: Implementation) => void;
  onDownload: (impl: Implementation) => void;
  onTrackEvent: (event: string, props?: Record<string, string | undefined>) => void;
}

export function ImageLightbox({
  open,
  specId,
  specTitle,
  currentImpl,
  implementations,
  codeCopied,
  onClose,
  onSelectLibrary,
  onCopyCode,
  onDownload,
  onTrackEvent,
}: ImageLightboxProps) {
  // Sort implementations alphabetically for consistent ordering
  const sortedImpls = useMemo(
    () => [...implementations].sort((a, b) => a.library_id.localeCompare(b.library_id)),
    [implementations],
  );

  const currentIndex = useMemo(() => {
    if (!currentImpl) return 0;
    const idx = sortedImpls.findIndex((impl) => impl.library_id === currentImpl.library_id);
    return idx >= 0 ? idx : 0;
  }, [sortedImpls, currentImpl]);

  const navigatePrev = useCallback(() => {
    if (sortedImpls.length < 2) return;
    const prev = (currentIndex - 1 + sortedImpls.length) % sortedImpls.length;
    onSelectLibrary(sortedImpls[prev].library_id);
  }, [sortedImpls, currentIndex, onSelectLibrary]);

  const navigateNext = useCallback(() => {
    if (sortedImpls.length < 2) return;
    const next = (currentIndex + 1) % sortedImpls.length;
    onSelectLibrary(sortedImpls[next].library_id);
  }, [sortedImpls, currentIndex, onSelectLibrary]);

  // Keyboard navigation: left/right arrows switch libraries
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT') return;

      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        navigatePrev();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        navigateNext();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open, navigatePrev, navigateNext]);

  if (!currentImpl) return null;

  return (
    <Modal
      open={open}
      onClose={onClose}
      closeAfterTransition
      slotProps={{
        backdrop: {
          sx: { backgroundColor: 'rgba(0,0,0,0.85)' },
        },
      }}
    >
      <Fade in={open}>
        <Box
          sx={{
            position: 'fixed',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            outline: 'none',
          }}
        >
          {/* Close button (top-right) */}
          <IconButton
            onClick={onClose}
            aria-label="Close lightbox"
            sx={{
              position: 'absolute',
              top: 16,
              right: 16,
              color: '#fff',
              bgcolor: 'rgba(255,255,255,0.1)',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' },
              zIndex: 1,
            }}
          >
            <CloseIcon />
          </IconButton>

          {/* Left arrow */}
          {sortedImpls.length > 1 && (
            <IconButton
              onClick={navigatePrev}
              aria-label="Previous library"
              sx={{
                position: 'absolute',
                left: { xs: 8, md: 24 },
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#fff',
                bgcolor: 'rgba(255,255,255,0.1)',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' },
                zIndex: 1,
              }}
            >
              <ChevronLeftIcon fontSize="large" />
            </IconButton>
          )}

          {/* Right arrow */}
          {sortedImpls.length > 1 && (
            <IconButton
              onClick={navigateNext}
              aria-label="Next library"
              sx={{
                position: 'absolute',
                right: { xs: 8, md: 24 },
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#fff',
                bgcolor: 'rgba(255,255,255,0.1)',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' },
                zIndex: 1,
              }}
            >
              <ChevronRightIcon fontSize="large" />
            </IconButton>
          )}

          {/* Full-resolution image */}
          {currentImpl.preview_url && (
            <Box
              component="picture"
              sx={{ display: 'contents' }}
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
                alt={`${specTitle} - ${currentImpl.library_id}`}
                sx={{
                  maxHeight: '90vh',
                  maxWidth: '95vw',
                  objectFit: 'contain',
                  borderRadius: 1,
                }}
                onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                  const target = e.target as HTMLImageElement;
                  if (!target.dataset.fallback) {
                    target.dataset.fallback = '1';
                    target.closest('picture')?.querySelectorAll('source').forEach((s) => s.remove());
                    target.removeAttribute('srcset');
                    target.src = currentImpl.preview_url!;
                  }
                }}
              />
            </Box>
          )}

          {/* Bottom bar: library name + action buttons */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 24,
              left: '50%',
              transform: 'translateX(-50%)',
              display: 'flex',
              alignItems: 'center',
              gap: 2,
              px: 2.5,
              py: 1,
              bgcolor: 'rgba(0,0,0,0.6)',
              borderRadius: 2,
              backdropFilter: 'blur(8px)',
            }}
          >
            <Box
              sx={{
                fontFamily: '"MonoLisa", "MonoLisa Fallback", monospace',
                fontSize: fontSize.base,
                color: '#fff',
                whiteSpace: 'nowrap',
              }}
            >
              {currentImpl.library_id}
            </Box>

            <Box sx={{ display: 'flex', gap: 0.5 }}>
              {currentImpl.code && (
                <Tooltip title={codeCopied === currentImpl.library_id ? 'Copied!' : 'Copy Code'}>
                  <IconButton
                    onClick={() => onCopyCode(currentImpl)}
                    aria-label="Copy code"
                    size="small"
                    sx={{
                      color: '#fff',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.15)' },
                    }}
                  >
                    {codeCopied === currentImpl.library_id ? (
                      <CheckIcon fontSize="small" />
                    ) : (
                      <ContentCopyIcon fontSize="small" />
                    )}
                  </IconButton>
                </Tooltip>
              )}

              <Tooltip title="Download PNG">
                <IconButton
                  onClick={() => onDownload(currentImpl)}
                  aria-label="Download PNG"
                  size="small"
                  sx={{
                    color: '#fff',
                    '&:hover': { bgcolor: 'rgba(255,255,255,0.15)' },
                  }}
                >
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </Tooltip>

              {currentImpl.preview_html && (
                <Tooltip title="Open Interactive">
                  <IconButton
                    component="a"
                    href={`/interactive/${specId}/${currentImpl.library_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() =>
                      onTrackEvent('open_interactive', {
                        spec: specId,
                        library: currentImpl.library_id,
                      })
                    }
                    aria-label="Open interactive"
                    size="small"
                    sx={{
                      color: '#fff',
                      '&:hover': { bgcolor: 'rgba(255,255,255,0.15)' },
                    }}
                  >
                    <OpenInNewIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </Box>
        </Box>
      </Fade>
    </Modal>
  );
}
