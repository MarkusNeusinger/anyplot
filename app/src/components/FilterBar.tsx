import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import ListItemText from '@mui/material/ListItemText';
import Typography from '@mui/material/Typography';
import InputBase from '@mui/material/InputBase';
import Divider from '@mui/material/Divider';
import Tooltip from '@mui/material/Tooltip';
import CloseIcon from '@mui/icons-material/Close';
import SearchIcon from '@mui/icons-material/Search';
import AddIcon from '@mui/icons-material/Add';
import useMediaQuery from '@mui/material/useMediaQuery';
import { useTheme } from '@mui/material/styles';

import type { FilterCategory, ActiveFilters, FilterCounts } from '../types';
import { FILTER_LABELS, FILTER_TOOLTIPS, FILTER_CATEGORIES } from '../types';
import type { ImageSize } from '../constants';
import { getAvailableValues, getAvailableValuesForGroup, getSearchResults, type SearchResult } from '../utils';
import { ToolbarActions } from './ToolbarActions';
import { fontSize, semanticColors, colors, typography } from '../theme';

interface FilterBarProps {
  activeFilters: ActiveFilters;
  filterCounts: FilterCounts | null;  // Contextual counts (for AND additions)
  orCounts: Record<string, number>[];  // Per-group counts for OR additions
  specTitles: Record<string, string>;  // Mapping spec_id -> title for search/tooltips
  currentTotal: number;  // Total number of filtered images
  displayedCount: number;  // Currently displayed images
  randomAnimation: { index: number; phase: 'out' | 'in'; oldLabel?: string } | null;
  searchInputRef?: React.RefObject<HTMLInputElement | null>;
  imageSize: ImageSize;
  onImageSizeChange: (size: ImageSize) => void;
  onAddFilter: (category: FilterCategory, value: string) => void;
  onAddValueToGroup: (groupIndex: number, value: string) => void;
  onRemoveFilter: (groupIndex: number, value: string) => void;
  onRemoveGroup: (groupIndex: number) => void;
  onTrackEvent: (event: string, props?: Record<string, string>) => void;
}

export function FilterBar({
  activeFilters,
  filterCounts,
  orCounts,
  specTitles,
  currentTotal,
  displayedCount,
  randomAnimation,
  searchInputRef,
  imageSize,
  onImageSizeChange,
  onAddFilter,
  onAddValueToGroup,
  onRemoveFilter,
  onRemoveGroup,
  onTrackEvent,
}: FilterBarProps) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Scroll percentage and sticky detection
  const [scrollPercent, setScrollPercent] = useState(0);
  const [isSticky, setIsSticky] = useState(false);
  const filterBarRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const calculatePercent = () => {
      const scrollY = window.scrollY;
      const docHeight = document.documentElement.scrollHeight;
      const windowHeight = window.innerHeight;

      // Estimate total height based on ratio of loaded vs total plots
      const loadRatio = displayedCount > 0 && currentTotal > 0
        ? currentTotal / displayedCount
        : 1;
      const estimatedTotalHeight = (docHeight - windowHeight) * loadRatio;

      const percent = Math.round((scrollY / estimatedTotalHeight) * 100);
      setScrollPercent(Math.min(100, Math.max(0, percent || 0)));

      // Detect if bar is in sticky mode (scrolled past threshold).
      // On /plots the masthead+navbar flow with content (~120px), so the FilterBar
      // starts sticking shortly after that. 60px is a conservative trigger.
      setIsSticky(scrollY > 60);
    };
    calculatePercent();
    window.addEventListener('scroll', calculatePercent);
    const resizeObserver = new ResizeObserver(calculatePercent);
    resizeObserver.observe(document.body);
    return () => {
      window.removeEventListener('scroll', calculatePercent);
      resizeObserver.disconnect();
    };
  }, [displayedCount, currentTotal]);

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

  // Chip menu state
  const [chipMenuAnchor, setChipMenuAnchor] = useState<HTMLElement | null>(null);
  const [activeGroupIndex, setActiveGroupIndex] = useState<number | null>(null);

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
  const handleCategorySelect = useCallback((category: FilterCategory) => {
    setSelectedCategory(category);
    setSearchQuery('');
    setHighlightedIndex(-1);
    setTimeout(() => inputRef.current?.focus(), 50);
  }, [inputRef]);

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

  // Chip click - open chip menu
  const handleChipClick = useCallback(
    (event: React.MouseEvent<HTMLElement>, groupIndex: number) => {
      setChipMenuAnchor(event.currentTarget);
      setActiveGroupIndex(groupIndex);
    },
    []
  );

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
  const handleRemoveGroup = useCallback(() => {
    if (activeGroupIndex !== null) {
      onRemoveGroup(activeGroupIndex);
    }
    setChipMenuAnchor(null);
    setActiveGroupIndex(null);
  }, [activeGroupIndex, onRemoveGroup]);

  // Add value to existing group (OR)
  const handleAddValueToExistingGroup = useCallback(
    (value: string) => {
      if (activeGroupIndex !== null) {
        onAddValueToGroup(activeGroupIndex, value);
      }
      setChipMenuAnchor(null);
      setActiveGroupIndex(null);
    },
    [activeGroupIndex, onAddValueToGroup]
  );

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
  const getDropdownItems = useCallback(() => {
    if (!selectedCategory && !hasQuery) {
      // Categories list
      return FILTER_CATEGORIES
        .filter((cat) => {
          const available = getAvailableValues(filterCounts, activeFilters, cat);
          return available.length > 0;
        })
        .map((cat) => ({ type: 'category' as const, category: cat }));
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
      return searchResults.map((r) => ({ type: 'value' as const, ...r }));
    }
  }, [selectedCategory, hasQuery, filterCounts, activeFilters, searchResults]);

  const dropdownItems = getDropdownItems();

  // Handle keyboard navigation
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'ArrowDown') {
        event.preventDefault();
        setHighlightedIndex((prev) => Math.min(prev + 1, dropdownItems.length - 1));
      } else if (event.key === 'ArrowUp') {
        event.preventDefault();
        setHighlightedIndex((prev) => Math.max(prev - 1, -1));
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
    [dropdownItems, highlightedIndex, handleCategorySelect, handleValueSelect, handleDropdownClose, inputRef]
  );

  // Get active group for chip menu
  const activeGroup = activeGroupIndex !== null ? activeFilters[activeGroupIndex] : null;
  const availableValuesForActiveGroup = activeGroupIndex !== null
    ? getAvailableValuesForGroup(activeGroupIndex, activeFilters, orCounts, currentTotal)
    : [];

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
      {/* Filter chips row */}
      <Box
        sx={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 1,
          justifyContent: 'center',
          alignItems: 'center',
          position: { xs: 'static', md: 'relative' },
        }}
      >
        {/* Progress counter - absolute left (desktop only) */}
        {!isMobile && currentTotal > 0 && (
          <Typography
            sx={{
              position: 'absolute',
              left: 0,
              fontFamily: typography.fontFamily,
              fontSize: fontSize.sm,
              color: semanticColors.mutedText,
              whiteSpace: 'nowrap',
            }}
          >
            {scrollPercent}% · {currentTotal}
          </Typography>
        )}
        {/* Toolbar actions - absolute right (desktop only) */}
        {!isMobile && (
          <Box sx={{ position: 'absolute', right: 0 }}>
            <ToolbarActions
              imageSize={imageSize}
              onImageSizeChange={onImageSizeChange}
              onTrackEvent={onTrackEvent}
            />
          </Box>
        )}
        {/* Active filter chips */}
      {activeFilters.map((group, index) => {
        const isAnimating = randomAnimation?.index === index;
        const animationClass = isAnimating ? `chip-blur-${randomAnimation.phase}` : undefined;
        // Show old label during 'out' phase, new label during 'in' phase
        const displayLabel = isAnimating && randomAnimation.phase === 'out' && randomAnimation.oldLabel
          ? randomAnimation.oldLabel
          : `${group.category}:${group.values.join(',')}`;

        return (
          <Chip
            key={`${group.category}-${index}`}
            label={displayLabel}
            onClick={(e) => handleChipClick(e, index)}
            onDelete={() => onRemoveGroup(index)}
            deleteIcon={<CloseIcon sx={{ fontSize: '1rem !important' }} />}
            sx={{
              fontFamily: typography.fontFamily,
              fontSize: fontSize.base,
              height: 32,
              bgcolor: 'var(--bg-surface)',
              border: `1px solid ${colors.primary}`,
              color: 'var(--ink-soft)',
              cursor: 'pointer',
              '&:hover': { bgcolor: 'var(--bg-elevated)' },
              '& .MuiChip-deleteIcon': {
                color: 'var(--ink-muted)',
                '&:hover': { color: colors.primary },
              },
              ...(animationClass === 'chip-blur-out' && {
                animation: 'chip-roll-out 0.5s ease-in forwards',
              }),
              ...(animationClass === 'chip-blur-in' && {
                animation: 'chip-roll-in 0.5s ease-out forwards',
              }),
              '@keyframes chip-roll-out': {
                '0%': { transform: 'perspective(200px) rotateX(0deg)' },
                '100%': { transform: 'perspective(200px) rotateX(180deg)' },
              },
              '@keyframes chip-roll-in': {
                '0%': { transform: 'perspective(200px) rotateX(180deg)' },
                '100%': { transform: 'perspective(200px) rotateX(360deg)' },
              },
            }}
          />
        );
      })}

      {/* Search input - collapsed icon or expanded input */}
      {!maxFiltersReached && (
        <Box
          ref={searchContainerRef}
          role={isSearchExpanded ? undefined : 'button'}
          tabIndex={isSearchExpanded ? undefined : 0}
          aria-label={isSearchExpanded ? undefined : 'Open filter search'}
          onClick={handleSearchExpand}
          onKeyDown={(e) => {
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
            '&:focus': isSearchExpanded ? {} : { outline: `2px solid ${colors.primary}`, outlineOffset: 2 },
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
          <label htmlFor="filter-search" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)' }}>
            {selectedCategory ? `Search ${FILTER_LABELS[selectedCategory]}` : 'Search filters'}
          </label>
          <InputBase
            inputRef={inputRef}
            id="filter-search"
            name="filter-search"
            inputProps={{ 'aria-label': selectedCategory ? `Search ${FILTER_LABELS[selectedCategory]}` : 'Search filters' }}
            placeholder={selectedCategory ? FILTER_LABELS[selectedCategory] : '.find(_)'}
            value={searchQuery}
            onChange={(e) => {
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
              onClick={(e) => {
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
              {scrollPercent}% · {currentTotal}
            </Typography>
          ) : (
            <Box />
          )}
          <ToolbarActions
            imageSize={imageSize}
            onImageSizeChange={onImageSizeChange}
            onTrackEvent={onTrackEvent}
          />
        </Box>
      )}

      {/* Dropdown menu */}
      <Menu
        anchorEl={dropdownAnchor}
        open={isDropdownOpen}
        onClose={handleDropdownClose}
        autoFocus={false}
        disableAutoFocus
        disableRestoreFocus
        disableEnforceFocus
        slotProps={{
          paper: {
            sx: {
              maxHeight: 350,
              minWidth: 240,
              mt: 0.5,
            },
          },
          root: {
            slotProps: {
              backdrop: {
                invisible: true,
              },
            },
          },
        }}
      >
        {!selectedCategory && !hasQuery
          ? // Show categories
            FILTER_CATEGORIES.map((category) => {
              const availableVals = getAvailableValues(filterCounts, activeFilters, category);
              if (availableVals.length === 0) return null;
              // Calculate actual index among visible items
              const visibleIdx = dropdownItems.findIndex((item) => item.type === 'category' && item.category === category);
              return (
                <Tooltip
                  key={category}
                  title={FILTER_TOOLTIPS[category]}
                  placement="right"
                  arrow
                >
                  <MenuItem
                    onClick={() => handleCategorySelect(category)}
                    selected={visibleIdx === highlightedIndex}
                    sx={{ fontFamily: typography.fontFamily }}
                  >
                    <ListItemText
                      primary={FILTER_LABELS[category]}
                      secondary={`${availableVals.length} options`}
                      slotProps={{
                        primary: {
                          sx: {
                            fontFamily: typography.fontFamily,
                            fontSize: fontSize.lg,
                          },
                        },
                        secondary: {
                          sx: {
                            fontFamily: typography.fontFamily,
                            fontSize: fontSize.sm,
                            color: semanticColors.mutedText,
                          },
                        },
                      }}
                    />
                  </MenuItem>
                </Tooltip>
              );
            })
          : // Show search results or category values
            [
              ...(selectedCategory
                ? [
                    <MenuItem
                      key="back"
                      onClick={() => {
                        setSelectedCategory(null);
                        setSearchQuery('');
                      }}
                      sx={{ fontFamily: typography.fontFamily, color: semanticColors.mutedText }}
                    >
                      &larr; {FILTER_LABELS[selectedCategory]}
                    </MenuItem>,
                    <Divider key="divider" />,
                  ]
                : []),
              ...((() => {
                // Use searchResults if query exists, otherwise show all available values for selected category
                const resultsToShow: SearchResult[] = hasQuery
                  ? searchResults
                  : selectedCategory
                    ? getAvailableValues(filterCounts, activeFilters, selectedCategory).map(([value, count]) => ({
                        category: selectedCategory,
                        value,
                        count,
                        matchType: 'exact' as const,
                      }))
                    : [];

                if (resultsToShow.length > 0) {
                  // Split results into exact and fuzzy matches
                  const exactResults = resultsToShow.filter((r) => r.matchType === 'exact');
                  const fuzzyResults = resultsToShow.filter((r) => r.matchType === 'fuzzy');

                  const renderMenuItem = (result: SearchResult, idx: number) => {
                    const { category, value, count } = result;
                    const specTitle = category === 'spec' ? specTitles[value] : undefined;
                    const menuItem = (
                      <MenuItem
                        key={`${category}-${value}`}
                        onClick={() => handleValueSelect(category, value)}
                        selected={idx === highlightedIndex}
                        sx={{ fontFamily: typography.fontFamily }}
                      >
                        <ListItemText
                          primary={value}
                          secondary={!selectedCategory ? FILTER_LABELS[category] : undefined}
                          slotProps={{
                            primary: {
                              sx: {
                                fontFamily: typography.fontFamily,
                                fontSize: fontSize.base,
                              },
                            },
                            secondary: {
                              sx: {
                                fontFamily: typography.fontFamily,
                                fontSize: fontSize.xs,
                                color: semanticColors.mutedText,
                              },
                            },
                          }}
                        />
                        <Typography
                          sx={{
                            fontFamily: typography.fontFamily,
                            fontSize: fontSize.sm,
                            color: semanticColors.mutedText,
                            ml: 2,
                          }}
                        >
                          ({count})
                        </Typography>
                      </MenuItem>
                    );
                    return specTitle ? (
                      <Tooltip key={`${category}-${value}`} title={specTitle} placement="right" arrow>
                        <span>{menuItem}</span>
                      </Tooltip>
                    ) : (
                      menuItem
                    );
                  };

                  const items: React.ReactNode[] = [];
                  // Add exact matches
                  exactResults.forEach((result, i) => {
                    items.push(renderMenuItem(result, i));
                  });
                  // Add fuzzy label/divider if there are fuzzy results
                  if (fuzzyResults.length > 0) {
                    items.push(
                      <Divider key="exact-fuzzy-divider" sx={{ my: 0.5 }}>
                        <Typography
                          sx={{
                            fontSize: fontSize.xs,
                            color: semanticColors.mutedText,
                            fontFamily: typography.fontFamily,
                            px: 1,
                          }}
                        >
                          fuzzy
                        </Typography>
                      </Divider>
                    );
                  }
                  // Add fuzzy matches
                  fuzzyResults.forEach((result, i) => {
                    items.push(renderMenuItem(result, exactResults.length + i));
                  });
                  return items;
                } else {
                  return [
                    <MenuItem key="no-results" disabled>
                      <Typography
                        sx={{
                          fontFamily: typography.fontFamily,
                          fontSize: fontSize.base,
                          color: semanticColors.mutedText,
                        }}
                      >
                        no matches
                      </Typography>
                    </MenuItem>,
                  ];
                }
              })()),
            ]}
      </Menu>

      {/* Chip action menu */}
      <Menu
        anchorEl={chipMenuAnchor}
        open={Boolean(chipMenuAnchor)}
        onClose={() => {
          setChipMenuAnchor(null);
          setActiveGroupIndex(null);
        }}
        slotProps={{
          paper: {
            sx: {
              minWidth: 180,
              maxHeight: 350,
            },
          },
        }}
      >
        {activeGroup && [
          // Add value (OR) - submenu with available values
          ...(availableValuesForActiveGroup.length > 0
            ? [
                <Typography
                  key="add-or-header"
                  sx={{
                    px: 2,
                    py: 0.5,
                    fontSize: fontSize.xs,
                    color: semanticColors.mutedText,
                    fontFamily: typography.fontFamily,
                    textTransform: 'uppercase',
                  }}
                >
                  add (or)
                </Typography>,
                ...availableValuesForActiveGroup.map(([value, count]) => (
                  <MenuItem
                    key={`add-${value}`}
                    onClick={() => handleAddValueToExistingGroup(value)}
                    sx={{ fontFamily: typography.fontFamily, py: 0.5 }}
                  >
                    <AddIcon fontSize="small" sx={{ mr: 1, color: colors.success, fontSize: '1rem' }} />
                    <Typography sx={{ fontSize: fontSize.base, flex: 1 }}>{value}</Typography>
                    <Typography sx={{ fontSize: fontSize.sm, color: semanticColors.mutedText }}>({count})</Typography>
                  </MenuItem>
                )),
                <Divider key="divider-add" />,
              ]
            : []),
          // Remove individual values
          ...activeGroup.values.map((value) => (
            <MenuItem
              key={`remove-${value}`}
              onClick={() => handleRemoveValue(value)}
              sx={{ fontFamily: typography.fontFamily }}
            >
              <CloseIcon fontSize="small" sx={{ mr: 1, color: colors.error }} />
              {value}
            </MenuItem>
          )),
          // Remove all (only if more than 1 value)
          ...(activeGroup.values.length > 1
            ? [
                <Divider key="divider-remove" />,
                <MenuItem
                  key="remove-all"
                  onClick={handleRemoveGroup}
                  sx={{ fontFamily: typography.fontFamily, color: colors.error }}
                >
                  <CloseIcon fontSize="small" sx={{ mr: 1 }} />
                  remove all
                </MenuItem>,
              ]
            : []),
        ]}
      </Menu>
    </Box>
  );
}
