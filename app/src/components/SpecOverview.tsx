/**
 * SpecOverview component - Grid of implementations for a specification.
 *
 * Displays all implementations in a 3-column grid with hover actions.
 */

import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Skeleton from '@mui/material/Skeleton';
import MuiLink from '@mui/material/Link';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import DownloadIcon from '@mui/icons-material/Download';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';

import type { Implementation } from '../types';
import { buildSrcSet, OVERVIEW_SIZES } from '../utils/responsiveImage';
import { fontSize, semanticColors } from '../theme';

interface LibraryMeta {
  id: string;
  name: string;
  description?: string;
  documentation_url?: string;
}

interface SpecOverviewProps {
  specId: string;
  specTitle: string;
  implementations: Implementation[];
  codeCopied: string | null;
  openTooltip: string | null;
  onImplClick: (libraryId: string) => void;
  onCopyCode: (impl: Implementation) => void;
  onDownload: (impl: Implementation) => void;
  onTooltipToggle: (tooltipId: string | null) => void;
  getLibraryMeta: (libraryId: string) => LibraryMeta | undefined;
  onTrackEvent: (event: string, props?: Record<string, string | undefined>) => void;
}

export function SpecOverview({
  specId,
  specTitle,
  implementations,
  codeCopied,
  openTooltip,
  onImplClick,
  onCopyCode,
  onDownload,
  onTooltipToggle,
  getLibraryMeta,
  onTrackEvent,
}: SpecOverviewProps) {
  // Sort implementations alphabetically
  const sortedImpls = [...implementations].sort((a, b) => a.library_id.localeCompare(b.library_id));

  return (
    <Box
      sx={{
        maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1800 },
        mx: 'auto',
        mt: 4,
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
        gap: 3,
      }}
    >
      {sortedImpls.map((impl) => (
        <ImplementationCard
          key={impl.library_id}
          impl={impl}
          specId={specId}
          specTitle={specTitle}
          codeCopied={codeCopied}
          openTooltip={openTooltip}
          onImplClick={onImplClick}
          onCopyCode={onCopyCode}
          onDownload={onDownload}
          onTooltipToggle={onTooltipToggle}
          getLibraryMeta={getLibraryMeta}
          onTrackEvent={onTrackEvent}
        />
      ))}
    </Box>
  );
}

interface ImplementationCardProps {
  impl: Implementation;
  specId: string;
  specTitle: string;
  codeCopied: string | null;
  openTooltip: string | null;
  onImplClick: (libraryId: string) => void;
  onCopyCode: (impl: Implementation) => void;
  onDownload: (impl: Implementation) => void;
  onTooltipToggle: (tooltipId: string | null) => void;
  getLibraryMeta: (libraryId: string) => LibraryMeta | undefined;
  onTrackEvent: (event: string, props?: Record<string, string | undefined>) => void;
}

function ImplementationCard({
  impl,
  specId,
  specTitle,
  codeCopied,
  openTooltip,
  onImplClick,
  onCopyCode,
  onDownload,
  onTooltipToggle,
  getLibraryMeta,
  onTrackEvent,
}: ImplementationCardProps) {
  const libMeta = getLibraryMeta(impl.library_id);
  const tooltipId = `lib-${impl.library_id}`;
  const isTooltipOpen = openTooltip === tooltipId;

  return (
    <Box>
      {/* Card */}
      <Box
        onClick={() => onImplClick(impl.library_id)}
        sx={{
          position: 'relative',
          borderRadius: 3,
          overflow: 'hidden',
          border: '2px solid rgba(55, 118, 171, 0.2)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          '&:hover': {
            border: '2px solid rgba(55, 118, 171, 0.4)',
            boxShadow: '0 8px 30px rgba(0,0,0,0.15)',
            transform: 'scale(1.03)',
          },
          '&:hover .action-buttons': {
            opacity: 1,
          },
        }}
      >
        {impl.preview_url ? (
          <Box component="picture" sx={{ display: 'contents' }}>
            <source
              type="image/webp"
              srcSet={buildSrcSet(impl.preview_url, 'webp')}
              sizes={OVERVIEW_SIZES}
            />
            <source
              type="image/png"
              srcSet={buildSrcSet(impl.preview_url, 'png')}
              sizes={OVERVIEW_SIZES}
            />
            <Box
              component="img"
              src={`${impl.preview_url.replace(/\.png$/, '')}_800.png`}
              alt={`${specTitle} - ${impl.library_id}`}
              sx={{
                display: 'block',
                width: '100%',
                aspectRatio: '16/10',
                objectFit: 'contain',
                bgcolor: '#fff',
              }}
              onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                const target = e.target as HTMLImageElement;
                if (!target.dataset.fallback) {
                  target.dataset.fallback = '1';
                  target.closest('picture')?.querySelectorAll('source').forEach(s => s.remove());
                  target.removeAttribute('srcset');
                  target.src = impl.preview_url!;
                }
              }}
            />
          </Box>
        ) : (
          <Skeleton variant="rectangular" sx={{ width: '100%', aspectRatio: '16/10' }} />
        )}

        {/* Action Buttons (top-right) */}
        <Box
          className="action-buttons"
          onClick={(e) => e.stopPropagation()}
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            display: 'flex',
            gap: 0.5,
            opacity: 0,
            transition: 'opacity 0.2s',
          }}
        >
          {impl.code && (
            <Tooltip title={codeCopied === impl.library_id ? 'Copied!' : 'Copy Code'}>
              <IconButton
                onClick={() => onCopyCode(impl)}
                aria-label="Copy code"
                sx={{
                  bgcolor: 'rgba(255,255,255,0.9)',
                  '&:hover': { bgcolor: '#fff', color: '#3776AB' },
                }}
                size="small"
              >
                {codeCopied === impl.library_id ? (
                  <CheckIcon fontSize="small" color="success" />
                ) : (
                  <ContentCopyIcon fontSize="small" />
                )}
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="Download PNG">
            <IconButton
              onClick={() => onDownload(impl)}
              aria-label="Download PNG"
              sx={{
                bgcolor: 'rgba(255,255,255,0.9)',
                '&:hover': { bgcolor: '#fff' },
              }}
              size="small"
            >
              <DownloadIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          {impl.preview_html && (
            <Tooltip title="Open Interactive">
              <IconButton
                component={Link}
                to={`/interactive/${specId}/${impl.library_id}`}
                aria-label="Open interactive"
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onTrackEvent('open_interactive', { spec: specId, library: impl.library_id });
                }}
                sx={{
                  bgcolor: 'rgba(255,255,255,0.9)',
                  '&:hover': { bgcolor: '#fff', color: '#3776AB' },
                }}
                size="small"
              >
                <OpenInNewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Label below card with library tooltip */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mt: 1.5,
          gap: 0.5,
        }}
      >
        <ClickAwayListener onClickAway={() => isTooltipOpen && onTooltipToggle(null)}>
          <Box component="span">
            <Tooltip
              title={
                <Box>
                  <Typography sx={{ fontSize: fontSize.md, mb: libMeta?.documentation_url ? 1 : 0 }}>
                    {libMeta?.description || 'No description available'}
                  </Typography>
                  {libMeta?.documentation_url && (
                    <MuiLink
                      href={libMeta.documentation_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      sx={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 0.5,
                        fontSize: fontSize.xs,
                        color: '#90caf9',
                        textDecoration: 'underline',
                        '&:hover': { color: '#fff' },
                      }}
                    >
                      {libMeta.documentation_url.replace(/^https?:\/\//, '')}
                      <OpenInNewIcon sx={{ fontSize: 12 }} />
                    </MuiLink>
                  )}
                </Box>
              }
              arrow
              placement="bottom"
              open={isTooltipOpen}
              disableFocusListener
              disableHoverListener
              disableTouchListener
              slotProps={{
                tooltip: {
                  sx: {
                    maxWidth: { xs: '80vw', sm: 400 },
                    fontFamily: '"MonoLisa", monospace',
                    fontSize: fontSize.md,
                  },
                },
              }}
            >
              <Typography
                onClick={(e) => {
                  e.stopPropagation();
                  onTooltipToggle(isTooltipOpen ? null : tooltipId);
                }}
                sx={{
                  fontSize: fontSize.md,
                  fontWeight: 600,
                  fontFamily: '"MonoLisa", monospace',
                  color: isTooltipOpen ? '#3776AB' : semanticColors.labelText,
                  textTransform: 'lowercase',
                  cursor: 'pointer',
                  '&:hover': { color: '#3776AB' },
                }}
              >
                {impl.library_id}
              </Typography>
            </Tooltip>
          </Box>
        </ClickAwayListener>
        {impl.quality_score && (
          <>
            <Typography sx={{ color: semanticColors.mutedText, fontSize: fontSize.md }}>·</Typography>
            <Typography
              sx={{
                fontSize: fontSize.md,
                fontWeight: 600,
                fontFamily: '"MonoLisa", monospace',
                color: semanticColors.labelText,
              }}
            >
              {Math.round(impl.quality_score)}
            </Typography>
          </>
        )}
      </Box>
    </Box>
  );
}
