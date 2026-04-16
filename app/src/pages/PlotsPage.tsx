import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import Box from '@mui/material/Box';
import Alert from '@mui/material/Alert';
import Fab from '@mui/material/Fab';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

import type { PlotImage } from '../types';
import type { ImageSize } from '../constants';
import { useInfiniteScroll, useAnalytics, useFilterState, isFiltersEmpty } from '../hooks';
import { NavBar } from '../components/NavBar';
import { Footer } from '../components/Footer';
import { FilterBar } from '../components/FilterBar';
import { ImagesGrid } from '../components/ImagesGrid';
import { useAppData, useHomeState } from '../hooks';
import { specPath } from '../utils/paths';
import { colors } from '../theme';
import Container from '@mui/material/Container';

export function PlotsPage() {
  const navigate = useNavigate();
  const { specsData, librariesData } = useAppData();
  const { homeStateRef, saveScrollPosition } = useHomeState();

  // Disable browser's automatic scroll restoration
  useEffect(() => {
    if ('scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }
  }, []);

  const { trackPageview, trackEvent } = useAnalytics();

  const {
    activeFilters,
    filterCounts,
    orCounts,
    specTitles,
    allImages,
    displayedImages,
    hasMore,
    loading,
    error,
    setDisplayedImages,
    setHasMore,
    handleAddFilter,
    handleAddValueToGroup,
    handleRemoveFilter,
    handleRemoveGroup,
    handleRandom,
    randomAnimation,
  } = useFilterState({
    onTrackPageview: trackPageview,
    onTrackEvent: trackEvent,
  });

  const { loadMoreRef } = useInfiniteScroll({
    allImages,
    displayedImages,
    hasMore,
    setDisplayedImages,
    setHasMore,
  });

  // Restore scroll position from persistent state
  const scrollRestoredRef = useRef(false);
  useEffect(() => {
    if (scrollRestoredRef.current) return;
    const savedScrollY = homeStateRef.current.scrollY;
    if (savedScrollY > 0 && displayedImages.length > 0) {
      requestAnimationFrame(() => {
        window.scrollTo(0, savedScrollY);
        scrollRestoredRef.current = true;
      });
    } else if (displayedImages.length > 0) {
      scrollRestoredRef.current = true;
    }
  }, [homeStateRef, displayedImages.length]);

  // UI state
  const [openImageTooltip, setOpenImageTooltip] = useState<string | null>(null);
  const [imageSize, setImageSize] = useState<ImageSize>(() => {
    const stored = localStorage.getItem('imageSize');
    return stored === 'normal' || stored === 'compact' ? stored : 'normal';
  });
  const [showScrollTop, setShowScrollTop] = useState(false);

  const searchInputRef = useRef<HTMLInputElement>(null);

  const noFilters = isFiltersEmpty(activeFilters);

  useEffect(() => {
    localStorage.setItem('imageSize', imageSize);
  }, [imageSize]);

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 300);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handleCardClick = useCallback(
    (img: PlotImage) => {
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
      }
      saveScrollPosition();
      const specId = img.spec_id || '';
      const library = img.library;
      navigate(specPath(specId, library));
    },
    [navigate, saveScrollPosition]
  );

  const handleContainerClick = useCallback(
    (e: React.MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.closest('[data-description-btn]')) return;
      if (openImageTooltip) setOpenImageTooltip(null);
    },
    [openImageTooltip]
  );

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;

      if (e.key === ' ') {
        e.preventDefault();
        handleRandom('space');
      } else if (e.key === 'Enter' && searchInputRef.current) {
        e.preventDefault();
        searchInputRef.current.focus();
      } else if (e.key === 'Backspace' && activeFilters.length > 0) {
        e.preventDefault();
        handleRemoveGroup(activeFilters.length - 1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleRandom, handleRemoveGroup, activeFilters.length]);

  const specFilter = activeFilters.find((f) => f.category === 'spec');
  const libFilter = activeFilters.find((f) => f.category === 'lib');
  const selectedSpec = specFilter?.values[0] || '';
  const selectedLibrary = libFilter?.values[0] || '';

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'var(--bg-page)' }} onClick={handleContainerClick}>
      <Helmet>
        <title>plots | anyplot.ai</title>
        <meta name="description" content="Browse and filter 2,600+ Python visualization examples across 9 libraries. Search by plot type, domain, features, and more." />
        <link rel="canonical" href="https://anyplot.ai/plots" />
      </Helmet>
      <Container maxWidth={false} sx={{ px: { xs: 2, sm: 4, md: 8, lg: 12, xl: 16 }, maxWidth: 1600, mx: 'auto' }}>
      <NavBar searchInputRef={searchInputRef} />

      {error && (
        <Alert severity="error" sx={{ mb: 4, maxWidth: 500, mx: 'auto' }}>
          {error}
        </Alert>
      )}

      <FilterBar
        activeFilters={activeFilters}
        filterCounts={filterCounts}
        orCounts={orCounts}
        specTitles={specTitles}
        currentTotal={allImages.length}
        displayedCount={displayedImages.length}
        randomAnimation={randomAnimation}
        searchInputRef={searchInputRef}
        imageSize={imageSize}
        onImageSizeChange={setImageSize}
        onAddFilter={handleAddFilter}
        onAddValueToGroup={handleAddValueToGroup}
        onRemoveFilter={handleRemoveFilter}
        onRemoveGroup={handleRemoveGroup}
        onTrackEvent={trackEvent}
      />

      <ImagesGrid
        images={displayedImages}
        viewMode={noFilters ? 'library' : 'spec'}
        selectedSpec={selectedSpec}
        selectedLibrary={selectedLibrary}
        loading={loading}
        hasMore={hasMore}
        isLoadingMore={false}
        isTransitioning={false}
        librariesData={librariesData}
        specsData={specsData}
        openTooltip={openImageTooltip}
        loadMoreRef={loadMoreRef}
        imageSize={imageSize}
        onTooltipToggle={setOpenImageTooltip}
        onCardClick={handleCardClick}
        onTrackEvent={trackEvent}
      />

      {!loading && allImages.length === 0 && !noFilters && (
        <Alert severity="info" sx={{ maxWidth: 400, mx: 'auto' }}>
          No plots match these filters.
        </Alert>
      )}

      <Footer onTrackEvent={trackEvent} selectedSpec={selectedSpec} selectedLibrary={selectedLibrary} />
      </Container>

      <Fab
        size="small"
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          bgcolor: colors.gray[100],
          color: colors.gray[500],
          opacity: showScrollTop ? 1 : 0,
          visibility: showScrollTop ? 'visible' : 'hidden',
          transition: 'opacity 0.3s, visibility 0.3s',
          '&:hover': { bgcolor: colors.gray[200], color: colors.primary },
        }}
      >
        <KeyboardArrowUpIcon />
      </Fab>
    </Box>
  );
}
