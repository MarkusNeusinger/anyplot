import { useCallback, useEffect, useRef } from 'react';

import { BATCH_SIZE } from 'src/constants';
import type { PlotImage } from 'src/types';

interface UseInfiniteScrollProps {
  allImages: PlotImage[];
  displayedImages: PlotImage[];
  hasMore: boolean;
  setDisplayedImages: React.Dispatch<React.SetStateAction<PlotImage[]>>;
  setHasMore: React.Dispatch<React.SetStateAction<boolean>>;
}

export function useInfiniteScroll({
  allImages,
  displayedImages,
  hasMore,
  setDisplayedImages,
  setHasMore,
}: UseInfiniteScrollProps) {
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Use refs to avoid stale closures in scroll handler
  const stateRef = useRef({ allImages, displayedImages, hasMore });
  stateRef.current = { allImages, displayedImages, hasMore };

  // Track document height to detect layout transitions
  const lastDocHeightRef = useRef(0);
  const layoutTransitionRef = useRef(false);
  const loadBlockedRef = useRef(false);

  // Block loading and reset tracking when data changes (new filter results)
  useEffect(() => {
    // Block loading to prevent race conditions during filter change
    loadBlockedRef.current = true;
    lastDocHeightRef.current = 0;
    layoutTransitionRef.current = false;

    // Unblock after state has settled
    const timer = setTimeout(() => {
      loadBlockedRef.current = false;
    }, 150);

    return () => clearTimeout(timer);
  }, [allImages]);

  // Load more images
  const loadMore = useCallback(() => {
    // Skip if loading is blocked (filter change in progress)
    if (loadBlockedRef.current) return;

    const { allImages: all, displayedImages: displayed, hasMore: more } = stateRef.current;
    if (!more) return;

    const currentLength = displayed.length;
    const remaining = all.length - currentLength;
    if (remaining <= 0) return;

    const itemsToLoad = Math.min(BATCH_SIZE, remaining);
    const nextBatch = all.slice(currentLength, currentLength + itemsToLoad);

    setDisplayedImages(prev => [...prev, ...nextBatch]);
    setHasMore(currentLength + itemsToLoad < all.length);
  }, [setDisplayedImages, setHasMore]);

  // Check if we need to load more based on scroll position
  const checkAndLoad = useCallback(() => {
    // Skip if loading is blocked (filter change in progress)
    if (loadBlockedRef.current) return;

    const { hasMore: more } = stateRef.current;
    if (!more) return;

    const scrollBottom = window.scrollY + window.innerHeight;
    const docHeight = document.documentElement.scrollHeight;

    // Detect layout transitions (significant height changes)
    const heightDiff = Math.abs(docHeight - lastDocHeightRef.current);
    if (heightDiff > 500 && lastDocHeightRef.current > 0) {
      // Layout is transitioning (e.g., compact/normal switch), pause loading
      layoutTransitionRef.current = true;
      setTimeout(() => {
        layoutTransitionRef.current = false;
      }, 300);
    }
    lastDocHeightRef.current = docHeight;

    // Skip loading during layout transitions
    if (layoutTransitionRef.current) return;

    // If within 2500px of bottom, load more
    if (scrollBottom + 2500 > docHeight) {
      loadMore();
    }
  }, [loadMore]);

  // Intersection Observer for normal scrolling
  useEffect(() => {
    if (!hasMore) return;

    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '2400px 0px',
      }
    );

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => observer.disconnect();
  }, [hasMore, loadMore]);

  // Scroll event for fast scrolling - uses ref to always have fresh state
  useEffect(() => {
    let ticking = false;

    const handleScroll = () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          checkAndLoad();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    // Also check on resize and initial mount
    checkAndLoad();

    return () => window.removeEventListener('scroll', handleScroll);
  }, [checkAndLoad]);

  // Re-check after images are added (in case we need more)
  // Use longer delay to reduce state churn during rapid scrolling
  useEffect(() => {
    const timer = setTimeout(checkAndLoad, 200);
    return () => clearTimeout(timer);
  }, [displayedImages.length, checkAndLoad]);

  return {
    loadMoreRef,
    loadMore,
  };
}
