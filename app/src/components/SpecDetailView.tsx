/**
 * SpecDetailView component - Single implementation detail view.
 *
 * Shows large image with library carousel and action buttons.
 */

import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Skeleton from '@mui/material/Skeleton';
import DownloadIcon from '@mui/icons-material/Download';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';

import type { Implementation } from '../types';
import { buildSrcSet } from '../utils/responsiveImage';

interface SpecDetailViewProps {
  specId: string;
  specTitle: string;
  selectedLibrary: string;
  currentImpl: Implementation | null;
  implementations: Implementation[];
  imageLoaded: boolean;
  codeCopied: string | null;
  onImageLoad: () => void;
  onImageClick: () => void;
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
  onImageLoad,
  onImageClick,
  onCopyCode,
  onDownload,
  onTrackEvent,
}: SpecDetailViewProps) {
  // Sort implementations alphabetically for the counter
  const sortedImpls = [...implementations].sort((a, b) => a.library_id.localeCompare(b.library_id));
  const currentIndex = sortedImpls.findIndex((impl) => impl.library_id === selectedLibrary);

  return (
    <Box
      sx={{
        maxWidth: { xs: '100%', md: 1200, lg: 1400, xl: 1600 },
        mx: 'auto',
      }}
    >
      <Box
        onClick={onImageClick}
        sx={{
          position: 'relative',
          borderRadius: 2,
          overflow: 'hidden',
          bgcolor: '#fff',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          aspectRatio: '16/9',
          cursor: 'pointer',
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
              width: '100%',
              height: '100%',
              display: imageLoaded ? 'block' : 'none',
            }}
          >
            <source
              type="image/webp"
              srcSet={buildSrcSet(currentImpl.preview_url, 'webp')}
              sizes="(max-width: 600px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
            <source
              type="image/png"
              srcSet={buildSrcSet(currentImpl.preview_url, 'png')}
              sizes="(max-width: 600px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
            <Box
              component="img"
              src={`${currentImpl.preview_url.replace(/\.png$/, '')}_1200.png`}
              alt={`${specTitle} - ${selectedLibrary}`}
              onLoad={onImageLoad}
              width={1200}
              height={750}
              sx={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
              }}
              onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                const target = e.target as HTMLImageElement;
                if (!target.dataset.fallback) {
                  target.dataset.fallback = '1';
                  target.src = currentImpl.preview_url!;
                }
              }}
            />
          </Box>
        )}

        {/* Action Buttons (top-right) - stop propagation */}
        <Box
          onClick={(e) => e.stopPropagation()}
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            display: 'flex',
            gap: 0.5,
          }}
        >
          {currentImpl?.code && (
            <Tooltip title={codeCopied === currentImpl.library_id ? 'Copied!' : 'Copy Code'}>
              <IconButton
                onClick={() => onCopyCode(currentImpl)}
                sx={{
                  bgcolor: 'rgba(255,255,255,0.9)',
                  '&:hover': { bgcolor: '#fff' },
                }}
                size="small"
              >
                {codeCopied === currentImpl.library_id ? (
                  <CheckIcon fontSize="small" color="success" />
                ) : (
                  <ContentCopyIcon fontSize="small" />
                )}
              </IconButton>
            </Tooltip>
          )}
          {currentImpl && (
            <Tooltip title="Download PNG">
              <IconButton
                onClick={() => onDownload(currentImpl)}
                sx={{
                  bgcolor: 'rgba(255,255,255,0.9)',
                  '&:hover': { bgcolor: '#fff' },
                }}
                size="small"
              >
                <DownloadIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          {currentImpl?.preview_html && (
            <Tooltip title="Open Interactive">
              <IconButton
                component={Link}
                to={`/interactive/${specId}/${selectedLibrary}`}
                onClick={(e: React.MouseEvent) => {
                  e.stopPropagation();
                  onTrackEvent('open_interactive', { spec: specId, library: selectedLibrary });
                }}
                sx={{
                  bgcolor: 'rgba(255,255,255,0.9)',
                  '&:hover': { bgcolor: '#fff' },
                }}
                size="small"
              >
                <OpenInNewIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>

        {/* Implementation counter (hover) */}
        {implementations.length > 1 && (
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
              fontFamily: '"MonoLisa", monospace',
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
