import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import Box from '@mui/material/Box';
import InputBase from '@mui/material/InputBase';
import Tooltip from '@mui/material/Tooltip';

import { type DropdownItem, FilterMenu } from 'src/sections/plots-gallery/FilterBar/FilterMenu';
import { colors, fontSize, semanticColors, typography } from 'src/theme';
import type { ActiveFilters, FilterCategory, FilterCounts } from 'src/types';
import { FILTER_CATEGORIES, FILTER_LABELS } from 'src/types';
import { getAvailableValues, getSearchResults } from 'src/utils';

export interface FilterSearchProps {
  activeFilters: ActiveFilters;
  filterCounts: FilterCounts | null; // Contextual counts (for AND additions)
  specTitles: Record<string, string>; // Mapping spec_id -> title for search/tooltips
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
  onAddFilter: (category: FilterCategory, value: string) => void;
  onTrackEvent: (event: string, props?: Record<string, string>) => void;
}

/**
 * Filter search input: expand/collapse behavior, fuse.js-backed search via
 * getSearchResults, keyboard navigation, and the category dropdown (FilterMenu).
 */
export function FilterSearch({
  activeFilters,
  filterCounts,
  specTitles,
  searchInputRef,
  onAddFilter,
  onTrackEvent,
}: FilterSearchProps) {
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

  // Expand and open dropdown
  const handleSearchExpand = useCallback(() => {
    setIsSearchManuallyExpanded(true);
    setDropdownAnchor(searchContainerRef.current);
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [inputRef]);

  // Collapse when empty and loses focus (only if there are filters)
  const handleSearchBlur = useCallback(() => {
    // Delay to allow click events on dropdown to fire first
    setTimeout(() => {
      if (!searchQuery && !selectedCategory && !dropdownAnchor && activeFilters.length > 0) {
        setIsSearchManuallyExpanded(false);
      }
    }, 200);
  }, [searchQuery, selectedCategory, dropdownAnchor, activeFilters.length]);

  // Close dropdown and collapse if empty
  const handleDropdownClose = useCallback(() => {
    setDropdownAnchor(null);
    setSelectedCategory(null);
    setSearchQuery('');
    setHighlightedIndex(-1);
    setIsSearchManuallyExpanded(false);
  }, []);

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
      // Track search if query was used (filter changes tracked via pageview)
      if (searchQuery.trim()) {
        onTrackEvent('search', { query: searchQuery.trim(), category });
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
    setSelectedCategory(null);
    setSearchQuery('');
  }, []);

  // Memoize search results to avoid recalculating on every render
  const searchResults = useMemo(
    () => getSearchResults(filterCounts, activeFilters, searchQuery, selectedCategory, specTitles),
    [filterCounts, activeFilters, searchQuery, selectedCategory, specTitles]
  );

  // Track searches with no results (debounced, to discover missing specs)
  const lastTrackedQueryRef = useRef<string>('');
  useEffect(() => {
    const query = searchQuery.trim();
    // Only track if: query >= 2 chars, no results, not already tracked this query
    if (query.length >= 2 && searchResults.length === 0 && query !== lastTrackedQueryRef.current) {
      const timer = setTimeout(() => {
        onTrackEvent('search_no_results', { query });
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
    } else {
      // Search results (with query)
      return searchResults.map(r => ({ type: 'value' as const, ...r }));
    }
  }, [selectedCategory, hasQuery, filterCounts, activeFilters, searchResults]);

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
        const item = dropdownItems[highlightedIndex] || dropdownItems[0];
        if (item) {
          if (item.type === 'category') {
            handleCategorySelect(item.category);
            setHighlightedIndex(-1);
          } else {
            handleValueSelect(item.category, item.value);
          }
        }
      } else if (event.key === 'Escape') {
        handleDropdownClose();
        inputRef.current?.blur();
      }
    },
    [
      dropdownItems,
      highlightedIndex,
      handleCategorySelect,
      handleValueSelect,
      handleDropdownClose,
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
              onClick={e => {
                e.stopPropagation();
                setSearchQuery('');
                setSelectedCategory(null);
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
        dropdownItems={dropdownItems}
        highlightedIndex={highlightedIndex}
        onClose={handleDropdownClose}
        onCategorySelect={handleCategorySelect}
        onValueSelect={handleValueSelect}
        onBack={handleBackToCategories}
      />
    </>
  );
}
