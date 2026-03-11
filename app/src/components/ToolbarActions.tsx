/**
 * Toolbar action buttons: catalog link and grid size toggle.
 * Extracted from FilterBar to eliminate code duplication between desktop and mobile views.
 */

import { Link } from 'react-router-dom';
import Box from '@mui/material/Box';
import Tooltip from '@mui/material/Tooltip';
import ViewAgendaIcon from '@mui/icons-material/ViewAgenda';
import ViewModuleIcon from '@mui/icons-material/ViewModule';
import ListIcon from '@mui/icons-material/List';

import type { ImageSize } from '../constants';

interface ToolbarActionsProps {
  imageSize: ImageSize;
  onImageSizeChange: (size: ImageSize) => void;
  onTrackEvent: (event: string, props?: Record<string, string>) => void;
}

/**
 * Catalog link component - navigates to /catalog page.
 */
export function CatalogLink() {
  return (
    <Tooltip title="catalog">
      <Box
        component={Link}
        to="/catalog"
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 32,
          height: 32,
          color: '#9ca3af',
          '&:hover': { color: '#3776AB' },
        }}
      >
        <ListIcon sx={{ fontSize: '1.25rem' }} />
      </Box>
    </Tooltip>
  );
}

/**
 * Grid size toggle button - switches between normal and compact view.
 */
export function GridSizeToggle({ imageSize, onImageSizeChange, onTrackEvent }: ToolbarActionsProps) {
  const handleToggle = () => {
    const newSize = imageSize === 'normal' ? 'compact' : 'normal';
    onImageSizeChange(newSize);
    onTrackEvent('grid_resize', { size: newSize });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleToggle();
    }
  };

  return (
    <Tooltip title={imageSize === 'normal' ? 'compact view' : 'normal view'}>
      <Box
        role="button"
        tabIndex={0}
        aria-label={imageSize === 'normal' ? 'Switch to compact view' : 'Switch to normal view'}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 32,
          height: 32,
          cursor: 'pointer',
          color: '#9ca3af',
          '&:hover': { color: '#3776AB' },
          '&:focus': { outline: '2px solid #3776AB', outlineOffset: 2 },
        }}
      >
        {imageSize === 'normal' ? (
          <ViewAgendaIcon sx={{ fontSize: '1.25rem' }} />
        ) : (
          <ViewModuleIcon sx={{ fontSize: '1.25rem' }} />
        )}
      </Box>
    </Tooltip>
  );
}

/**
 * Combined toolbar actions component with catalog link and grid toggle.
 */
export function ToolbarActions({ imageSize, onImageSizeChange, onTrackEvent }: ToolbarActionsProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      <CatalogLink />
      <GridSizeToggle
        imageSize={imageSize}
        onImageSizeChange={onImageSizeChange}
        onTrackEvent={onTrackEvent}
      />
    </Box>
  );
}
