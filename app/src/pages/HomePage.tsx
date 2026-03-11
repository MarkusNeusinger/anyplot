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
import { Header, Footer, FilterBar, ImagesGrid } from '../components';
import { useAppData, useHomeState } from '../hooks';

export function HomePage() {
  const navigate = useNavigate();
  const { specsData, librariesData, stats } = useAppData();
  const { homeStateRef, saveScrollPosition } = useHomeState();

  // Disable browser's automatic scroll restoration
  useEffect(() => {
    if ('scrollRestoration' in history) {
      history.scrollRestoration = 'manual';
    }
  }, []);

  // Custom hooks
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

  // Restore scroll position from persistent state (ref for sync access)
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

  // Refs
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Persist imageSize to localStorage
  useEffect(() => {
    localStorage.setItem('imageSize', imageSize);
  }, [imageSize]);

  // Show/hide scroll-to-top button based on scroll position
  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(window.scrollY > 300);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Handle card click - navigate to spec page
  const handleCardClick = useCallback(
    (img: PlotImage) => {
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
      }

      // Save scroll position synchronously to ref before navigation
      saveScrollPosition();

      // Navigate to spec page immediately
      const specId = img.spec_id || '';
      const library = img.library;
      navigate(`/${specId}/${library}`);
    },
    [navigate, saveScrollPosition]
  );

  // Close tooltip when clicking anywhere
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

  // Get selected spec/library for compatibility with existing components
  const specFilter = activeFilters.find((f) => f.category === 'spec');
  const libFilter = activeFilters.find((f) => f.category === 'lib');
  const selectedSpec = specFilter?.values[0] || '';
  const selectedLibrary = libFilter?.values[0] || '';

  return (
    <Box onClick={handleContainerClick}>
      <Helmet>
        <title>pyplots.ai</title>
        <meta name="description" content="library-agnostic, ai-powered python plotting examples. browse, compare, and copy code across 9 libraries." />
        <link rel="canonical" href="https://pyplots.ai/" />
      </Helmet>
      <Header stats={stats} onRandom={handleRandom} />

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
        viewMode={isFiltersEmpty(activeFilters) ? 'library' : 'spec'}
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

      {!loading && allImages.length === 0 && !isFiltersEmpty(activeFilters) && (
        <Alert severity="info" sx={{ maxWidth: 400, mx: 'auto' }}>
          No plots match these filters.
        </Alert>
      )}

      <Footer onTrackEvent={trackEvent} selectedSpec={selectedSpec} selectedLibrary={selectedLibrary} />

      {/* Floating scroll-to-top button */}
      <Fab
        size="small"
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          bgcolor: '#f3f4f6',
          color: '#6b7280',
          opacity: showScrollTop ? 1 : 0,
          visibility: showScrollTop ? 'visible' : 'hidden',
          transition: 'opacity 0.3s, visibility 0.3s',
          '&:hover': { bgcolor: '#e5e7eb', color: '#3776AB' },
        }}
      >
        <KeyboardArrowUpIcon />
      </Fab>
    </Box>
  );
}
