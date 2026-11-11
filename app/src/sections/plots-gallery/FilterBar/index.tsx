import { useCallback, useEffect, useRef, useState } from 'react';

import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import Typography from '@mui/material/Typography';
import useMediaQuery from '@mui/material/useMediaQuery';

import type { ImageSize } from 'src/constants';
import {
  FilterChips,
  type RandomAnimation,
} from 'src/sections/plots-gallery/FilterBar/FilterChips';
import { FilterSearch } from 'src/sections/plots-gallery/FilterBar/FilterSearch';
import { FilterSizeToggle } from 'src/sections/plots-gallery/FilterBar/FilterSizeToggle';
import { fontSize, semanticColors, typography } from 'src/theme';
import type { ActiveFilters, FilterCategory, FilterCounts } from 'src/types';
import { formatGalleryTotals, galleryScrollPercent } from 'src/utils';

export interface FilterBarProps {
  activeFilters: ActiveFilters;
  filterCounts: FilterCounts | null; // Contextual counts (for AND additions)
  globalCounts: FilterCounts | null; // Unfiltered counts (search hint, search after a clear)
  orCounts: Record<string, number>[]; // Per-group counts for OR additions
  specTitles: Record<string, string>; // Mapping spec_id -> title for search/tooltips
  currentTotal: number; // Total number of filtered images
  currentSpecTotal: number; // Distinct specs among the filtered images
  displayedCount: number; // Currently displayed images
  randomAnimation: RandomAnimation | null;
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
  imageSize: ImageSize;
  onImageSizeChange: (size: ImageSize) => void;
  onAddFilter: (category: FilterCategory, value: string) => void;
  onAddValueToGroup: (groupIndex: number, value: string) => void;
  onRemoveFilter: (groupIndex: number, value: string) => void;
  onRemoveGroup: (groupIndex: number) => void;
  onClearFilters: () => void;
  onTrackEvent: (event: string, props?: Record<string, string>) => void;
}

/**
 * Sticky filter toolbar of the plots gallery: scroll-progress counter,
 * active-filter chips, filter search with category dropdown, and grid-size toggle.
 */
export function FilterBar({
  activeFilters,
  filterCounts,
  globalCounts,
  orCounts,
  specTitles,
  currentTotal,
  currentSpecTotal,
  displayedCount,
  randomAnimation,
  searchInputRef,
  imageSize,
  onImageSizeChange,
  onAddFilter,
  onAddValueToGroup,
  onRemoveFilter,
  onRemoveGroup,
  onClearFilters,
  onTrackEvent,
}: FilterBarProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const totals = formatGalleryTotals(currentSpecTotal, currentTotal);

  // Scroll percentage and sticky detection
  const [scrollPercent, setScrollPercent] = useState(0);
  const [isSticky, setIsSticky] = useState(false);
  const filterBarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const calculatePercent = () => {
      const scrollY = window.scrollY;
      setScrollPercent(
        galleryScrollPercent({
          scrollY,
          docHeight: document.documentElement.scrollHeight,
          viewportHeight: window.innerHeight,
          displayedCount,
          total: currentTotal,
        })
      );

      // Detect if bar is in sticky mode (scrolled past threshold).
      // On /plots the masthead+navbar flow with content (~120px), so the FilterBar
      // starts sticking shortly after that. 60px is a conservative trigger.
      setIsSticky(scrollY > 60);
    };
    calculatePercent();
    // passive: true — scroll handler doesn't preventDefault, so let the
    // browser scroll without waiting for our handler to ack. Matters on
    // /plots, the busiest scroll path in the app.
    window.addEventListener('scroll', calculatePercent, { passive: true });
    const resizeObserver = new ResizeObserver(calculatePercent);
    resizeObserver.observe(document.body);
    return () => {
      window.removeEventListener('scroll', calculatePercent);
      resizeObserver.disconnect();
    };
  }, [displayedCount, currentTotal]);

  // Chip menu state
  const [chipMenuAnchor, setChipMenuAnchor] = useState<HTMLElement | null>(null);
  const [activeGroupIndex, setActiveGroupIndex] = useState<number | null>(null);

  // Chip click - open chip menu
  const handleChipClick = useCallback(
    (event: React.MouseEvent<HTMLElement>, groupIndex: number) => {
      setChipMenuAnchor(event.currentTarget);
      setActiveGroupIndex(groupIndex);
    },
    []
  );

  // Close chip menu
  const handleChipMenuClose = useCallback(() => {
    setChipMenuAnchor(null);
    setActiveGroupIndex(null);
  }, []);

  // Remove single value from group
  const handleRemoveValue = useCallback(
    (value: string) => {
      if (activeGroupIndex !== null) {
        onRemoveFilter(activeGroupIndex, value);
      }
      setChipMenuAnchor(null);
      setActiveGroupIndex(null);
    },
    [activeGroupIndex, onRemoveFilter]
  );

  // Remove entire group
  const handleRemoveActiveGroup = useCallback(() => {
    if (activeGroupIndex !== null) {
      onRemoveGroup(activeGroupIndex);
    }
    setChipMenuAnchor(null);
    setActiveGroupIndex(null);
  }, [activeGroupIndex, onRemoveGroup]);

  // Add value to existing group (OR)
  const handleAddValueToActiveGroup = useCallback(
    (value: string) => {
      if (activeGroupIndex !== null) {
        onAddValueToGroup(activeGroupIndex, value);
      }
      setChipMenuAnchor(null);
      setActiveGroupIndex(null);
    },
    [activeGroupIndex, onAddValueToGroup]
  );

  return (
    <Box
      ref={filterBarRef}
      sx={{
        mb: 4,
        position: 'sticky',
        top: 0,
        zIndex: 100,
        py: 1,
        transition: 'background-color 0.2s, border-color 0.2s, margin 0.2s, padding 0.2s',
        // Only apply full-width styling when sticky
        ...(isSticky
          ? {
              mx: { xs: -2, sm: -4, md: -8, lg: -12 },
              px: { xs: 2, sm: 4, md: 8, lg: 12 },
              bgcolor: 'var(--bg-surface)',
              borderBottom: '1px solid var(--rule)',
            }
          : {
              px: 2,
              bgcolor: 'transparent',
              borderBottom: '1px solid transparent',
            }),
      }}
    >
      {/* Filter chips row. On desktop a grid of counter | chips | toggle: the
          side columns are equal while there is room, so the chips stay centered,
          and never narrower than their content, so the counter cannot run
          under a chip when the chips need the space. */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: 'minmax(0, 1fr)', md: '1fr auto 1fr' },
          columnGap: 2,
          alignItems: 'center',
        }}
      >
        {/* Progress counter (desktop only) */}
        {!isMobile && (
          <Typography
            sx={{
              justifySelf: 'start',
              fontFamily: typography.fontFamily,
              fontSize: fontSize.sm,
              color: semanticColors.mutedText,
              whiteSpace: 'nowrap',
            }}
          >
            {currentTotal > 0 && `${scrollPercent}% · ${totals}`}
          </Typography>
        )}
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 1,
            justifyContent: 'center',
            alignItems: 'center',
          }}
        >
          {/* Active filter chips + chip action menu */}
          <FilterChips
            activeFilters={activeFilters}
            randomAnimation={randomAnimation}
            orCounts={orCounts}
            currentTotal={currentTotal}
            chipMenuAnchor={chipMenuAnchor}
            activeGroupIndex={activeGroupIndex}
            onChipClick={handleChipClick}
            onChipMenuClose={handleChipMenuClose}
            onRemoveValue={handleRemoveValue}
            onRemoveActiveGroup={handleRemoveActiveGroup}
            onAddValueToActiveGroup={handleAddValueToActiveGroup}
            onRemoveGroup={onRemoveGroup}
          />
          {/* Search input + category dropdown */}
          <FilterSearch
            activeFilters={activeFilters}
            filterCounts={filterCounts}
            globalCounts={globalCounts}
            specTitles={specTitles}
            searchInputRef={searchInputRef}
            onAddFilter={onAddFilter}
            onClearFilters={onClearFilters}
            onTrackEvent={onTrackEvent}
          />
        </Box>
        {/* Toolbar actions (desktop only) */}
        {!isMobile && (
          <Box sx={{ justifySelf: 'end' }}>
            <FilterSizeToggle
              imageSize={imageSize}
              onImageSizeChange={onImageSizeChange}
              onTrackEvent={onTrackEvent}
            />
          </Box>
        )}
      </Box>

      {/* Counter and toggle row (mobile only) */}
      {isMobile && (
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            mt: 1,
          }}
        >
          {currentTotal > 0 ? (
            <Typography
              sx={{
                fontFamily: typography.fontFamily,
                fontSize: fontSize.sm,
                color: semanticColors.mutedText,
                whiteSpace: 'nowrap',
              }}
            >
              {scrollPercent}% · {totals}
            </Typography>
          ) : (
            <Box />
          )}
          <FilterSizeToggle
            imageSize={imageSize}
            onImageSizeChange={onImageSizeChange}
            onTrackEvent={onTrackEvent}
          />
        </Box>
      )}
    </Box>
  );
}
