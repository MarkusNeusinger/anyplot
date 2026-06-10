import Divider from '@mui/material/Divider';
import ListItemText from '@mui/material/ListItemText';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { fontSize, semanticColors, typography } from 'src/theme';
import type { ActiveFilters, FilterCategory, FilterCounts } from 'src/types';
import { FILTER_CATEGORIES, FILTER_LABELS, FILTER_TOOLTIPS } from 'src/types';
import { getAvailableValues, type SearchResult } from 'src/utils';

/** A keyboard-navigable entry of the dropdown: a category or a concrete value. */
export type DropdownItem =
  | { type: 'category'; category: FilterCategory }
  | ({ type: 'value' } & SearchResult);

export interface FilterMenuProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  filterCounts: FilterCounts | null;
  activeFilters: ActiveFilters;
  specTitles: Record<string, string>; // Mapping spec_id -> title for tooltips
  selectedCategory: FilterCategory | null;
  hasQuery: boolean;
  searchResults: SearchResult[];
  dropdownItems: DropdownItem[]; // Visible items, for keyboard-highlight mapping
  highlightedIndex: number;
  onClose: () => void;
  onCategorySelect: (category: FilterCategory) => void;
  onValueSelect: (category: FilterCategory, value: string) => void;
  onBack: () => void; // Back from a selected category to the category list
}

/**
 * Category dropdown of the filter search: lists categories, drills into a
 * category's values, and shows exact/fuzzy search results.
 */
export function FilterMenu({
  anchorEl,
  open,
  filterCounts,
  activeFilters,
  specTitles,
  selectedCategory,
  hasQuery,
  searchResults,
  dropdownItems,
  highlightedIndex,
  onClose,
  onCategorySelect,
  onValueSelect,
  onBack,
}: FilterMenuProps) {
  return (
    <Menu
      anchorEl={anchorEl}
      open={open}
      onClose={onClose}
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
          FILTER_CATEGORIES.map(category => {
            const availableVals = getAvailableValues(filterCounts, activeFilters, category);
            if (availableVals.length === 0) return null;
            // Calculate actual index among visible items
            const visibleIdx = dropdownItems.findIndex(
              item => item.type === 'category' && item.category === category
            );
            return (
              <Tooltip key={category} title={FILTER_TOOLTIPS[category]} placement="right" arrow>
                <MenuItem
                  onClick={() => onCategorySelect(category)}
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
                    onClick={onBack}
                    sx={{ fontFamily: typography.fontFamily, color: semanticColors.mutedText }}
                  >
                    &larr; {FILTER_LABELS[selectedCategory]}
                  </MenuItem>,
                  <Divider key="divider" />,
                ]
              : []),
            ...(() => {
              // Use searchResults if query exists, otherwise show all available values for selected category
              const resultsToShow: SearchResult[] = hasQuery
                ? searchResults
                : selectedCategory
                  ? getAvailableValues(filterCounts, activeFilters, selectedCategory).map(
                      ([value, count]) => ({
                        category: selectedCategory,
                        value,
                        count,
                        matchType: 'exact' as const,
                      })
                    )
                  : [];

              if (resultsToShow.length > 0) {
                // Split results into exact and fuzzy matches
                const exactResults = resultsToShow.filter(r => r.matchType === 'exact');
                const fuzzyResults = resultsToShow.filter(r => r.matchType === 'fuzzy');

                const renderMenuItem = (result: SearchResult, idx: number) => {
                  const { category, value, count } = result;
                  const specTitle = category === 'spec' ? specTitles[value] : undefined;
                  const menuItem = (
                    <MenuItem
                      key={`${category}-${value}`}
                      onClick={() => onValueSelect(category, value)}
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
                      aria-label="No matches"
                      sx={{
                        fontFamily: typography.mono,
                        fontSize: fontSize.base,
                        color: semanticColors.mutedText,
                        '& .subj': { opacity: 0.7 },
                      }}
                    >
                      <span className="subj">results</span>.empty()
                    </Typography>
                  </MenuItem>,
                ];
              }
            })(),
          ]}
    </Menu>
  );
}
