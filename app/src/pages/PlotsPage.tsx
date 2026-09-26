import { useCallback, useEffect, useRef, useState } from 'react';

import { Helmet } from 'react-helmet-async';
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom';

import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';

import { ScrollToTopFab } from 'src/components/ScrollToTopFab';
import type { ImageSize } from 'src/constants';
import { isFiltersEmpty, useAnalytics, useFilterState, useInfiniteScroll } from 'src/hooks';
import { useAppData, useHomeState } from 'src/hooks';
import { specPath } from 'src/routes/paths';
import { FilterBar } from 'src/sections/plots-gallery/FilterBar';
import { ImagesGrid } from 'src/sections/plots-gallery/ImagesGrid';
import { colors, fontSize, typography } from 'src/theme';
import type { PlotImage } from 'src/types';

export function PlotsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { specsData, librariesData, languagesData } = useAppData();
  const { homeStateRef, saveScrollPosition } = useHomeState();

  // Disable browser's automatic scroll restoration so we can restore from
  // our persisted state (homeStateRef.scrollY) instead. Capture the prior
  // mode and restore it on unmount, so we don't clobber any non-default
  // value set elsewhere and other routes get back native behavior.
  useEffect(() => {
    if (!('scrollRestoration' in history)) return;
    const previous = history.scrollRestoration;
    history.scrollRestoration = 'manual';
    return () => {
      history.scrollRestoration = previous;
    };
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

  const searchInputRef = useRef<HTMLInputElement>(null);

  const noFilters = isFiltersEmpty(activeFilters);

  useEffect(() => {
    localStorage.setItem('imageSize', imageSize);
  }, [imageSize]);

  // Focus the FilterBar search input when arriving via NavBar's search pill
  // (?focus=search). The param is consumed (removed) so reload doesn't re-trigger.
  useEffect(() => {
    if (searchParams.get('focus') === 'search' && searchInputRef.current) {
      searchInputRef.current.focus();
      const next = new URLSearchParams(searchParams);
      next.delete('focus');
      setSearchParams(next, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const handleCardClick = useCallback(
    (img: PlotImage) => {
      if (document.activeElement instanceof HTMLElement) {
        document.activeElement.blur();
      }
      saveScrollPosition();
      const specId = img.spec_id || '';
      // If the user is browsing under an active language filter, propagate it
      // as `?language=…` so the destination impl-page carousel stays scoped to
      // that language. Without the filter, the carousel walks all impls.
      const langActive = activeFilters.some(f => f.category === 'lang');
      const qs = langActive && img.language ? `?language=${encodeURIComponent(img.language)}` : '';
      navigate(`${specPath(specId, img.language, img.library)}${qs}`);
    },
    [navigate, saveScrollPosition, activeFilters]
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
      // A focused interactive element owns the keystroke — without this
      // guard, Space/Enter on a focused card, chip, or toggle fires both
      // the element's own handler and these global shortcuts.
      if (
        e.target instanceof Element &&
        e.target.closest('input, textarea, select, button, a, [role="button"], [tabindex]')
      )
        return;

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

  const specFilter = activeFilters.find(f => f.category === 'spec');
  const selectedSpec = specFilter?.values[0] || '';
  // The gallery filtered to one spec shows the same implementations as that
  // spec's own page, but never linked to it: the page was reachable only via
  // an implementation's `.compare()`. Offered only for exactly one known spec —
  // `selectedSpec` takes the first value even when several are OR-combined.
  const singleSpec =
    activeFilters.filter(f => f.category === 'spec').length === 1 &&
    specFilter?.values.length === 1 &&
    specsData.some(s => s.id === selectedSpec)
      ? selectedSpec
      : '';

  return (
    <Box onClick={handleContainerClick}>
      <Helmet>
        <title>plots | anyplot.ai</title>
        <meta
          name="description"
          content="Browse and filter 2,600+ visualization examples across 15 libraries in Python, R, Julia, and JavaScript. Search by plot type, domain, features, and more."
        />
        <link rel="canonical" href="https://anyplot.ai/plots" />
      </Helmet>

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

      {singleSpec && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <Box
            component={RouterLink}
            to={specPath(singleSpec)}
            onClick={() =>
              trackEvent('nav_click', {
                source: 'gallery_spec_hub',
                target: specPath(singleSpec),
                spec: singleSpec,
              })
            }
            aria-label={`Compare all implementations of ${specTitles[singleSpec] || singleSpec}`}
            sx={{
              display: 'inline-flex',
              alignItems: 'baseline',
              gap: 0.75,
              fontFamily: typography.mono,
              fontSize: fontSize.sm,
              color: 'var(--ink-soft)',
              textDecoration: 'none',
              transition: 'color 0.2s',
              '& .hub-arrow': { transition: 'transform 0.2s' },
              '&:hover': { color: colors.primary },
              '&:hover .hub-arrow': { transform: 'translateX(3px)' },
              '&:focus-visible': {
                outline: `2px solid ${colors.primary}`,
                outlineOffset: 2,
                borderRadius: '2px',
              },
            }}
          >
            {/* One tone on purpose: the house two-tone subject (opacity 0.7)
                drops to ~3.7:1 on the light background, below WCAG AA. */}
            <Box component="span">{`${singleSpec}.compare()`}</Box>
            <Box component="span" className="hub-arrow">
              →
            </Box>
          </Box>
        </Box>
      )}

      <ImagesGrid
        images={displayedImages}
        viewMode={noFilters ? 'library' : 'spec'}
        selectedSpec={selectedSpec}
        loading={loading}
        hasMore={hasMore}
        isLoadingMore={false}
        isTransitioning={false}
        librariesData={librariesData}
        languagesData={languagesData}
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
          no plots match these filters.
        </Alert>
      )}

      <ScrollToTopFab />
    </Box>
  );
}
