import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import Box from '@mui/material/Box';
import InputBase from '@mui/material/InputBase';
import Tooltip from '@mui/material/Tooltip';

import { normalizeQuery, type TrackEvent } from 'src/hooks/useAnalytics';
import { MISS_PAUSE_MS, sendSearchMiss } from 'src/lib/searchMiss';
import { type DropdownItem, FilterMenu } from 'src/sections/plots-gallery/FilterBar/FilterMenu';
import { colors, fontSize, semanticColors, typography } from 'src/theme';
import type { ActiveFilters, FilterCategory, FilterCounts } from 'src/types';
import { FILTER_CATEGORIES, FILTER_LABELS } from 'src/types';
import { getAvailableValues, getSearchResults } from 'src/utils';

export interface FilterSearchProps {
  activeFilters: ActiveFilters;
  filterCounts: FilterCounts | null; // Contextual counts (for AND additions)
  globalCounts: FilterCounts | null; // Unfiltered counts (search hint, search after a clear)
  specTitles: Record<string, string>; // Mapping spec_id -> title for search/tooltips
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
  onAddFilter: (category: FilterCategory, value: string) => void;
  onClearFilters: () => void;
  onTrackEvent: TrackEvent;
}

/**
 * Filter search input: expand/collapse behavior, fuse.js-backed search via
 * getSearchResults, keyboard navigation, and the category dropdown (FilterMenu).
 */
export function FilterSearch({
  activeFilters,
  filterCounts: contextualCounts,
  globalCounts,
  specTitles,
  searchInputRef,
  onAddFilter,
  onClearFilters,
  onTrackEvent,
}: FilterSearchProps) {
  // Without filters the contextual counts equal the global ones once the
  // refetch lands; reading the global ones right away keeps the dropdown
  // filled in between, after `.search_all()` removed the filters.
  const filterCounts =
    activeFilters.length === 0 ? (globalCounts ?? contextualCounts) : contextualCounts;

  // Search/dropdown state
  const [searchQuery, setSearchQuery] = useState('');
  const [dropdownAnchor, setDropdownAnchor] = useState<HTMLElement | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<FilterCategory | null>(null);
  const [isSearchManuallyExpanded, setIsSearchManuallyExpanded] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);
  const localInputRef = useRef<HTMLInputElement>(null);
  const inputRef = searchInputRef || localInputRef;

  // Search is expanded when: no filters OR manually expanded
  const isSearchExpanded = activeFilters.length === 0 || isSearchManuallyExpanded;

  // Dropdown keyboard navigation
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);

  // The finished text of a search that found nothing in the whole catalogue, waiting for the
  // pause after the last keystroke (see the effect below `hiddenMatchCount`). Read and cleared
  // synchronously by every way out of the search, before that way clears the text: the pause,
  // a blur and leaving the page send it (`flushMiss`); the clear cross, Escape and "← back" are
  // how a visitor throws a text away, and drop it (`dropMiss`).
  const pendingMissRef = useRef<string | null>(null);
  const flushMiss = useCallback(() => {
    const query = pendingMissRef.current;
    pendingMissRef.current = null;
    if (query) sendSearchMiss(query);
  }, []);
  const dropMiss = useCallback(() => {
    pendingMissRef.current = null;
  }, []);

  // Expand and open dropdown
  const handleSearchExpand = useCallback(() => {
    setIsSearchManuallyExpanded(true);
    setDropdownAnchor(searchContainerRef.current);
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [inputRef]);

  // Collapse when empty and loses focus (only if there are filters)
  const handleSearchBlur = useCallback(() => {
    // A visitor who leaves the field is done typing: a pending miss goes now.
    flushMiss();
    // Delay to allow click events on dropdown to fire first
    setTimeout(() => {
      if (!searchQuery && !selectedCategory && !dropdownAnchor && activeFilters.length > 0) {
        setIsSearchManuallyExpanded(false);
      }
    }, 200);
  }, [flushMiss, searchQuery, selectedCategory, dropdownAnchor, activeFilters.length]);

  // Close dropdown and collapse if empty. Escape drops a pending miss before it gets here (see
  // `handleKeyDown`); every other way sends it.
  const handleDropdownClose = useCallback(() => {
    flushMiss();
    setDropdownAnchor(null);
    setSelectedCategory(null);
    setSearchQuery('');
    setHighlightedIndex(-1);
    setIsSearchManuallyExpanded(false);
  }, [flushMiss]);

  // The clear cross: drops the pending text with what was typed, and leaves the menu open on
  // the categories.
  const crossRef = useRef<SVGSVGElement>(null);
  const handleClear = useCallback(() => {
    dropMiss();
    setSearchQuery('');
    setSelectedCategory(null);
  }, [dropMiss]);

  // While the menu is open its invisible backdrop covers the page, the field and the cross
  // included, so a press on the cross arrives here as a press on the backdrop. The backdrop
  // keeps the focus on its press (`FilterMenu`), so nothing has been sent yet: a press inside
  // the cross's box is the clear cross, any other press is a loss of focus, which sends a
  // pending miss and leaves the field as before.
  const handleMenuClose = useCallback(
    (event: object, reason: 'backdropClick' | 'escapeKeyDown' | 'tabKeyDown') => {
      const box = crossRef.current?.getBoundingClientRect();
      const press = event as { clientX?: number; clientY?: number };
      const onCross =
        reason === 'backdropClick' &&
        box !== undefined &&
        press.clientX !== undefined &&
        press.clientY !== undefined &&
        press.clientX >= box.left &&
        press.clientX <= box.right &&
        press.clientY >= box.top &&
        press.clientY <= box.bottom;
      if (onCross) {
        handleClear();
        return;
      }
      handleDropdownClose();
      if (reason === 'backdropClick') inputRef.current?.blur();
    },
    [handleClear, handleDropdownClose, inputRef]
  );

  // Select category from dropdown
  const handleCategorySelect = useCallback(
    (category: FilterCategory) => {
      setSelectedCategory(category);
      setSearchQuery('');
      setHighlightedIndex(-1);
      setTimeout(() => inputRef.current?.focus(), 50);
    },
    [inputRef]
  );

  // Select value (add new filter group)
  const handleValueSelect = useCallback(
    (category: FilterCategory, value: string) => {
      onAddFilter(category, value);
      // A pick from a typed search, by its category (filter changes are tracked via pageview).
      // What was typed never goes to the public dashboard.
      if (normalizeQuery(searchQuery)) {
        onTrackEvent('search', { category });
      }
      setSelectedCategory(null);
      setSearchQuery('');
      setHighlightedIndex(-1);
      // Keep expanded and focused for next filter
      setIsSearchManuallyExpanded(true);
      setTimeout(() => {
        setDropdownAnchor(searchContainerRef.current);
        inputRef.current?.focus();
      }, 50);
    },
    [onAddFilter, onTrackEvent, searchQuery, inputRef]
  );

  // Back from a selected category to the category list
  const handleBackToCategories = useCallback(() => {
    dropMiss();
    setSelectedCategory(null);
    setSearchQuery('');
  }, [dropMiss]);

  // Memoize search results to avoid recalculating on every render
  const searchResults = useMemo(
    () => getSearchResults(filterCounts, activeFilters, searchQuery, selectedCategory, specTitles),
    [filterCounts, activeFilters, searchQuery, selectedCategory, specTitles]
  );

  // A search inside the filters only sees the values of the filtered plots.
  // When it finds nothing, count what the same search finds in all plots, so
  // the empty state can say that the filters are the reason.
  const hiddenMatchCount = useMemo(() => {
    if (activeFilters.length === 0 || searchResults.length > 0 || !searchQuery.trim()) return 0;
    return getSearchResults(globalCounts, [], searchQuery, selectedCategory, specTitles).length;
  }, [
    activeFilters.length,
    searchResults.length,
    globalCounts,
    searchQuery,
    selectedCategory,
    specTitles,
  ]);

  // Drop the filters and keep the query, so the dropdown shows the hits in all plots
  const handleSearchAll = useCallback(() => {
    onClearFilters();
    setHighlightedIndex(-1);
    setIsSearchManuallyExpanded(true);
    setTimeout(() => {
      setDropdownAnchor(searchContainerRef.current);
      inputRef.current?.focus();
    }, 50);
  }, [onClearFilters, inputRef]);

  // Whether the text finds nothing anywhere in the catalogue: not in the filtered plots, not in
  // all of them, and in no category, the selected one or another. Only such a text is a miss for
  // the private list. Unknown, and so no miss, until the global counts have loaded.
  const missesCatalogue = useMemo(() => {
    if (searchResults.length > 0 || hiddenMatchCount > 0 || !globalCounts) return false;
    if (!normalizeQuery(searchQuery)) return false;
    return getSearchResults(globalCounts, [], searchQuery, null, specTitles).length === 0;
  }, [searchResults.length, hiddenMatchCount, globalCounts, searchQuery, specTitles]);

  // A miss goes to the private list only as a finished text: once no key was pressed for
  // MISS_PAUSE_MS, or when the field loses focus or the search closes before that (`flushMiss`).
  // A fragment typed on within MISS_PAUSE_MS never goes: the next keystroke replaces it.
  useEffect(() => {
    const query = normalizeQuery(searchQuery);
    if (!missesCatalogue || !query) {
      pendingMissRef.current = null;
      return;
    }
    pendingMissRef.current = query;
    const timer = setTimeout(flushMiss, MISS_PAUSE_MS);
    return () => clearTimeout(timer);
  }, [searchQuery, missesCatalogue, flushMiss]);

  // A miss still pending when the gallery goes away is finished too.
  useEffect(() => flushMiss, [flushMiss]);

  // Count searches with no results inside the active filters (debounced). The event carries no
  // property: what was typed never goes to the public dashboard.
  const lastTrackedQueryRef = useRef<string>('');
  useEffect(() => {
    const query = normalizeQuery(searchQuery);
    // Only track if: query >= 2 chars, no results, not already tracked this query
    if (query.length >= 2 && searchResults.length === 0 && query !== lastTrackedQueryRef.current) {
      const timer = setTimeout(() => {
        onTrackEvent('search_no_results');
        lastTrackedQueryRef.current = query;
      }, 200);
      return () => clearTimeout(timer);
    }
  }, [searchQuery, searchResults.length, onTrackEvent]);

  // Reset tracked query when dropdown closes
  useEffect(() => {
    if (!dropdownAnchor) {
      lastTrackedQueryRef.current = '';
    }
  }, [dropdownAnchor]);

  // Only open if anchor is valid and in document
  const isDropdownOpen = Boolean(dropdownAnchor) && document.body.contains(dropdownAnchor);
  const hasQuery = searchQuery.trim().length > 0;
  const maxFiltersReached = activeFilters.length >= 5;

  // Get dropdown items for keyboard navigation
  const getDropdownItems = useCallback((): DropdownItem[] => {
    if (!selectedCategory && !hasQuery) {
      // Categories list
      return FILTER_CATEGORIES.filter(cat => {
        const available = getAvailableValues(filterCounts, activeFilters, cat);
        return available.length > 0;
      }).map(cat => ({ type: 'category' as const, category: cat }));
    } else if (selectedCategory && !hasQuery) {
      // Category selected but no query - show all available values for this category
      const available = getAvailableValues(filterCounts, activeFilters, selectedCategory);
      return available.map(([value, count]) => ({
        type: 'value' as const,
        category: selectedCategory,
        value,
        count,
        matchType: 'exact' as const,
      }));
    } else if (searchResults.length === 0 && hiddenMatchCount > 0) {
      return [{ type: 'search_all' as const }];
    } else {
      // Search results (with query)
      return searchResults.map(r => ({ type: 'value' as const, ...r }));
    }
  }, [selectedCategory, hasQuery, filterCounts, activeFilters, searchResults, hiddenMatchCount]);

  const dropdownItems = getDropdownItems();

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setHighlightedIndex(prev => Math.min(prev + 1, dropdownItems.length - 1));
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setHighlightedIndex(prev => Math.max(prev - 1, -1));
      } else if (event.key === 'Enter') {
        event.preventDefault();
        const highlighted = dropdownItems[highlightedIndex];
        // A bare Enter takes the first entry, but never `.search_all()`:
        // removing the filters takes an explicit pick.
        const item =
          highlighted ?? (dropdownItems[0]?.type === 'search_all' ? undefined : dropdownItems[0]);
        if (item) {
          if (item.type === 'category') {
            handleCategorySelect(item.category);
            setHighlightedIndex(-1);
          } else if (item.type === 'search_all') {
            handleSearchAll();
          } else {
            handleValueSelect(item.category, item.value);
          }
        }
      } else if (event.key === 'Escape') {
        // Escape throws the text away: dropped before the close and the blur could send it.
        dropMiss();
        handleDropdownClose();
        inputRef.current?.blur();
      }
    },
    [
      dropdownItems,
      highlightedIndex,
      handleCategorySelect,
      handleValueSelect,
      handleSearchAll,
      handleDropdownClose,
      dropMiss,
      inputRef,
    ]
  );

  return (
    <>
      {/* Search input - collapsed icon or expanded input */}
      {!maxFiltersReached && (
        <Box
          ref={searchContainerRef}
          role={isSearchExpanded ? undefined : 'button'}
          tabIndex={isSearchExpanded ? undefined : 0}
          aria-label={isSearchExpanded ? undefined : 'Open filter search'}
          onClick={handleSearchExpand}
          onKeyDown={e => {
            if (!isSearchExpanded && (e.key === 'Enter' || e.key === ' ')) {
              e.preventDefault();
              handleSearchExpand();
            }
          }}
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 0.5,
            px: isSearchExpanded ? 1.5 : 0,
            height: 32,
            width: isSearchExpanded ? { xs: 220, sm: 220, md: 'auto' } : 32,
            minWidth: isSearchExpanded ? { xs: 220, sm: 220, md: 200 } : 32,
            border: isSearchExpanded ? '1px dashed var(--ink-muted)' : 'none',
            borderRadius: '16px',
            bgcolor: isDropdownOpen ? 'var(--bg-elevated)' : 'transparent',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            '&:hover': {
              borderColor: isSearchExpanded ? colors.primary : undefined,
              bgcolor: isSearchExpanded ? 'var(--bg-elevated)' : undefined,
            },
            '&:hover .search-icon': {
              color: colors.primary,
            },
            '&:focus': isSearchExpanded
              ? {}
              : { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
          }}
        >
          <Tooltip title={isSearchExpanded ? '' : '.find()'}>
            <SearchIcon
              className="search-icon"
              sx={{
                color: 'var(--ink-muted)',
                fontSize: isSearchExpanded ? '1rem' : '1.25rem',
                transition: 'all 0.2s ease',
                flexShrink: 0,
              }}
            />
          </Tooltip>
          <label
            htmlFor="filter-search"
            style={{
              position: 'absolute',
              width: 1,
              height: 1,
              overflow: 'hidden',
              clip: 'rect(0,0,0,0)',
            }}
          >
            {selectedCategory ? `Search ${FILTER_LABELS[selectedCategory]}` : 'Search filters'}
          </label>
          <InputBase
            inputRef={inputRef}
            id="filter-search"
            name="filter-search"
            // No fill from the browser or a password manager: what lands here may be sent.
            autoComplete="off"
            inputProps={{
              'aria-label': selectedCategory
                ? `Search ${FILTER_LABELS[selectedCategory]}`
                : 'Search filters',
            }}
            placeholder={selectedCategory ? FILTER_LABELS[selectedCategory] : '.find(_)'}
            value={searchQuery}
            onChange={e => {
              setSearchQuery(e.target.value);
              setHighlightedIndex(-1);
              if (!dropdownAnchor) {
                setDropdownAnchor(searchContainerRef.current);
              }
            }}
            onFocus={() => {
              if (!isSearchManuallyExpanded && activeFilters.length > 0) {
                setIsSearchManuallyExpanded(true);
              }
              setDropdownAnchor(searchContainerRef.current);
              setHighlightedIndex(-1);
            }}
            onBlur={handleSearchBlur}
            onKeyDown={handleKeyDown}
            sx={{
              flex: isSearchExpanded ? 1 : 0,
              width: isSearchExpanded ? 'auto' : 0,
              opacity: isSearchExpanded ? 1 : 0,
              transition: 'all 0.2s ease',
              fontFamily: typography.fontFamily,
              fontSize: fontSize.base,
              color: 'var(--ink)',
              '& input': {
                padding: 0,
                fontFamily: typography.fontFamily,
                fontSize: fontSize.base,
                color: 'var(--ink)',
                '&::placeholder': {
                  color: semanticColors.mutedText,
                  opacity: 1,
                },
              },
            }}
          />
          {isSearchExpanded && (searchQuery || selectedCategory) && (
            <CloseIcon
              ref={crossRef}
              // While the menu is open a press here reaches the menu's backdrop instead
              // (`handleMenuClose`); this covers a press the cross receives itself. Its default
              // is kept from moving the focus: a blur would send the text this press throws away.
              onMouseDown={e => e.preventDefault()}
              onClick={e => {
                e.stopPropagation();
                handleClear();
              }}
              sx={{
                color: 'var(--ink-muted)',
                fontSize: fontSize.lg,
                cursor: 'pointer',
                '&:hover': { color: 'var(--ink-soft)' },
              }}
            />
          )}
        </Box>
      )}

      {/* Dropdown menu */}
      <FilterMenu
        anchorEl={dropdownAnchor}
        open={isDropdownOpen}
        filterCounts={filterCounts}
        activeFilters={activeFilters}
        specTitles={specTitles}
        selectedCategory={selectedCategory}
        hasQuery={hasQuery}
        searchResults={searchResults}
        hiddenMatchCount={hiddenMatchCount}
        dropdownItems={dropdownItems}
        highlightedIndex={highlightedIndex}
        onClose={handleMenuClose}
        onCategorySelect={handleCategorySelect}
        onValueSelect={handleValueSelect}
        onSearchAll={handleSearchAll}
        onBack={handleBackToCategories}
      />
    </>
  );
}
