import { memo, useState, useCallback } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Typography from '@mui/material/Typography';
import Tooltip from '@mui/material/Tooltip';
import Link from '@mui/material/Link';
import IconButton from '@mui/material/IconButton';
import CircularProgress from '@mui/material/CircularProgress';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';
import type { PlotImage } from '../types';
import { BATCH_SIZE, type ImageSize } from '../constants';
import { useCodeFetch } from '../hooks';
import { buildSrcSet, getResponsiveSizes, getFallbackSrc } from '../utils/responsiveImage';
import { useThemedPreviewUrl } from '../utils/themedPreview';
import { colors, typography, fontSize, semanticColors } from '../theme';

// Library abbreviations for compact mode
const LIBRARY_ABBR: Record<string, string> = {
  matplotlib: 'mpl',
  seaborn: 'sns',
  plotly: 'ply',
  bokeh: 'bok',
  altair: 'alt',
  plotnine: 'p9',
  pygal: 'pyg',
  highcharts: 'hc',
  letsplot: 'lp',
};

interface ImageCardProps {
  image: PlotImage;
  index: number;
  viewMode: 'spec' | 'library';
  selectedSpec: string;
  libraryDescription?: string;
  libraryDocUrl?: string;
  specDescription?: string;
  openTooltip: string | null;
  imageSize: ImageSize;
  onTooltipToggle: (id: string | null) => void;
  onClick: (image: PlotImage) => void;
  onTrackEvent?: (name: string, props?: Record<string, string | undefined>) => void;
}

export const ImageCard = memo(function ImageCard({
  image,
  index,
  viewMode,
  selectedSpec,
  libraryDescription,
  libraryDocUrl,
  specDescription,
  openTooltip,
  imageSize,
  onTooltipToggle,
  onClick,
  onTrackEvent,
}: ImageCardProps) {
  const theme = useTheme();
  const isXs = useMediaQuery(theme.breakpoints.down('sm')); // < 600px
  const imgUrl = useThemedPreviewUrl(image) ?? image.url;

  const labelFontSize = imageSize === 'compact' ? fontSize.xs : fontSize.md;
  const labelLetterSpacing = isXs ? '-0.03em' : 'normal';
  const { fetchCode } = useCodeFetch();
  const [copyState, setCopyState] = useState<'idle' | 'loading' | 'copied'>('idle');

  // Library display: in compact mode - hidden on xs, abbreviated otherwise
  // In normal mode - always show full name
  const showLibrary = imageSize === 'normal' || !isXs;
  const libraryDisplay = imageSize === 'compact'
    ? (LIBRARY_ABBR[image.library] || image.library)
    : image.library;

  // Stable click handler - calls onClick with image
  const handleClick = useCallback(() => {
    onClick(image);
  }, [onClick, image]);

  const handleCopyCode = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (copyState !== 'idle' || !image.spec_id) return;

    setCopyState('loading');
    try {
      // Use cached code if available, otherwise fetch
      const code = image.code ?? await fetchCode(image.spec_id, image.library);
      if (code) {
        await navigator.clipboard.writeText(code);
        setCopyState('copied');
        onTrackEvent?.('copy_code', { spec: image.spec_id, library: image.library, method: 'card', page: 'home' });
        setTimeout(() => setCopyState('idle'), 2000);
      } else {
        setCopyState('idle');
      }
    } catch {
      setCopyState('idle');
    }
  }, [image.spec_id, image.library, image.code, copyState, fetchCode, onTrackEvent]);

  const cardId = `${image.spec_id}-${image.library}`;
  const specTooltipId = `spec-${cardId}`;
  const libTooltipId = `lib-${cardId}`;
  const isSpecTooltipOpen = openTooltip === specTooltipId;
  const isLibTooltipOpen = openTooltip === libTooltipId;

  // Animate first batch only (initial load), subsequent batches appear instantly
  const isFirstBatch = index < BATCH_SIZE;

  return (
    <Box
      sx={isFirstBatch ? {
        animation: 'fadeIn 0.4s ease-out',
        animationDelay: `${index * 0.03}s`,
        animationFillMode: 'backwards',
        '@keyframes fadeIn': {
          from: { opacity: 0, transform: 'translateY(10px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      } : undefined}
    >
      <Card
        elevation={0}
        onClick={handleClick}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleClick();
          }
        }}
        tabIndex={0}
        role="button"
        aria-label={`View ${viewMode === 'library' ? image.spec_id : image.library} plot in fullscreen`}
        sx={{
          position: 'relative',
          borderRadius: 3,
          overflow: 'hidden',
          border: '1px solid var(--rule)',
          boxShadow: '0 1px 2px rgba(0,0,0,0.02), 0 24px 48px -24px rgba(0,0,0,0.08)',
          transition: 'all 0.3s ease',
          cursor: 'pointer',
          outline: 'none',
          '&:focus-visible': {
            border: `1px solid ${colors.primary}`,
          },
          '&:hover': {
            border: '1px solid rgba(0, 158, 115, 0.2)',
            boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
            transform: 'translateY(-2px)',
          },
        }}
      >
        <Box component="picture" sx={{ display: 'contents' }}>
          <source
            type="image/webp"
            srcSet={buildSrcSet(imgUrl, 'webp')}
            sizes={getResponsiveSizes(imageSize)}
          />
          <source
            type="image/png"
            srcSet={buildSrcSet(imgUrl, 'png')}
            sizes={getResponsiveSizes(imageSize)}
          />
          <Box
            component="img"
            loading={index < BATCH_SIZE ? 'eager' : 'lazy'}
            fetchPriority={index === 0 ? 'high' : undefined}
            src={getFallbackSrc(imgUrl)}
            alt={viewMode === 'library' ? `${image.spec_id} - ${image.library}` : `${selectedSpec} - ${image.library}`}
            sx={{
              display: 'block',
              width: '100%',
              aspectRatio: '16 / 10',
              objectFit: 'contain',
              bgcolor: 'var(--bg-surface)',
            }}
            onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
              const target = e.target as HTMLImageElement;
              // Remove <source> elements and clear srcset so browser falls back to plot.png
              if (!target.dataset.fallback) {
                target.dataset.fallback = '1';
                target.closest('picture')?.querySelectorAll('source').forEach(s => s.remove());
                target.removeAttribute('srcset');
                target.src = imgUrl;
              } else {
                target.style.display = 'none';
              }
            }}
          />
        </Box>
        {/* Copied confirmation */}
        {copyState === 'copied' && (
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
            {'>>> .copied'}
          </Box>
        )}
        {/* Copy button - appears on hover */}
        <IconButton
          onClick={handleCopyCode}
          disabled={copyState === 'loading'}
          aria-label="Copy code"
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            bgcolor: 'rgba(255,255,255,0.9)',
            color: semanticColors.mutedText,
            opacity: 0,
            transition: 'opacity 0.2s, color 0.2s',
            '.MuiCard-root:hover &': { opacity: 1 },
            '&:hover': { bgcolor: 'rgba(255,255,255,1)', color: colors.primary },
          }}
        >
          {copyState === 'loading' ? (
            <CircularProgress size={20} />
          ) : copyState === 'copied' ? (
            <CheckIcon sx={{ fontSize: 20, color: 'success.main' }} />
          ) : (
            <ContentCopyIcon sx={{ fontSize: 20 }} />
          )}
        </IconButton>
      </Card>
      {/* Label below card: clickable spec-id · library */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 1.5, gap: 0.5 }}>
        {/* Clickable Spec ID */}
        <Tooltip
          title={specDescription || 'No description available'}
          arrow
          placement="bottom"
          open={isSpecTooltipOpen}
          disableFocusListener
          disableHoverListener
          disableTouchListener
          slotProps={{
            tooltip: {
              sx: {
                maxWidth: { xs: '80vw', sm: 400 },
                fontFamily: typography.fontFamily,
                fontSize: labelFontSize,
              },
            },
          }}
        >
          <Typography
            data-description-btn
            onClick={(e) => {
              e.stopPropagation();
              onTooltipToggle(isSpecTooltipOpen ? null : specTooltipId);
            }}
            sx={{
              fontSize: labelFontSize,
              letterSpacing: labelLetterSpacing,
              fontWeight: 600,
              fontFamily: typography.fontFamily,
              color: isSpecTooltipOpen ? colors.primary : semanticColors.labelText,
              textTransform: 'lowercase',
              cursor: 'pointer',
              '&:hover': {
                color: colors.primary,
              },
            }}
          >
            {image.spec_id}
          </Typography>
        </Tooltip>

        {showLibrary && (
          <>
            <Typography sx={{ color: 'var(--ink-muted)', fontSize: labelFontSize }}>·</Typography>

            {/* Clickable Library */}
            <Tooltip
              title={
                <Box>
                  <Typography sx={{ fontSize: '0.8rem', mb: 1 }}>
                    {libraryDescription || 'No description available'}
                  </Typography>
                  {libraryDocUrl && (
                    <Link
                      href={libraryDocUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 0.5,
                        fontSize: '0.75rem',
                        color: colors.tooltipLight,
                        textDecoration: 'underline',
                        '&:hover': { color: '#fff' },
                      }}
                    >
                      {libraryDocUrl.replace(/^https?:\/\//, '')} <OpenInNewIcon sx={{ fontSize: 12 }} />
                    </Link>
                  )}
                </Box>
              }
              arrow
              placement="bottom"
              open={isLibTooltipOpen}
              disableFocusListener
              disableHoverListener
              disableTouchListener
              slotProps={{
                tooltip: {
                  sx: {
                    maxWidth: { xs: '80vw', sm: 400 },
                    fontFamily: typography.fontFamily,
                    fontSize: labelFontSize,
                  },
                },
              }}
            >
              <Typography
                data-description-btn
                onClick={(e) => {
                  e.stopPropagation();
                  onTooltipToggle(isLibTooltipOpen ? null : libTooltipId);
                }}
                sx={{
                  fontSize: labelFontSize,
                  letterSpacing: labelLetterSpacing,
                  fontWeight: 600,
                  fontFamily: typography.fontFamily,
                  color: isLibTooltipOpen ? colors.primary : semanticColors.labelText,
                  textTransform: 'lowercase',
                  cursor: 'pointer',
                  '&:hover': {
                    color: colors.primary,
                  },
                }}
              >
                {libraryDisplay}
              </Typography>
            </Tooltip>
          </>
        )}
      </Box>
    </Box>
  );
});
