import AddIcon from '@mui/icons-material/Add';
import CloseIcon from '@mui/icons-material/Close';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Typography from '@mui/material/Typography';

import { colors, fontSize, semanticColors, typography } from 'src/theme';
import type { ActiveFilters } from 'src/types';
import { getAvailableValuesForGroup } from 'src/utils';

/** Random-button chip animation state (owned by PlotsPage). */
export interface RandomAnimation {
  index: number;
  phase: 'out' | 'in';
  oldLabel?: string;
}

export interface FilterChipsProps {
  activeFilters: ActiveFilters;
  randomAnimation: RandomAnimation | null;
  orCounts: Record<string, number>[]; // Per-group counts for OR additions
  currentTotal: number; // Total number of filtered images
  chipMenuAnchor: HTMLElement | null;
  activeGroupIndex: number | null;
  onChipClick: (event: React.MouseEvent<HTMLElement>, groupIndex: number) => void;
  onChipMenuClose: () => void;
  onRemoveValue: (value: string) => void; // Remove one value from the active group
  onRemoveActiveGroup: () => void; // Remove the entire active group (via chip menu)
  onAddValueToActiveGroup: (value: string) => void; // Add value to active group (OR)
  onRemoveGroup: (groupIndex: number) => void; // Remove a group directly (chip delete icon)
}

/**
 * Active-filter chips with roll animation plus the per-chip action menu
 * (add OR value, remove single value, remove all).
 */
export function FilterChips({
  activeFilters,
  randomAnimation,
  orCounts,
  currentTotal,
  chipMenuAnchor,
  activeGroupIndex,
  onChipClick,
  onChipMenuClose,
  onRemoveValue,
  onRemoveActiveGroup,
  onAddValueToActiveGroup,
  onRemoveGroup,
}: FilterChipsProps) {
  // Get active group for chip menu
  const activeGroup = activeGroupIndex !== null ? activeFilters[activeGroupIndex] : null;
  const availableValuesForActiveGroup =
    activeGroupIndex !== null
      ? getAvailableValuesForGroup(activeGroupIndex, activeFilters, orCounts, currentTotal)
      : [];

  return (
    <>
      {/* Active filter chips */}
      {activeFilters.map((group, index) => {
        const isAnimating = randomAnimation?.index === index;
        const animationClass = isAnimating ? `chip-blur-${randomAnimation.phase}` : undefined;
        // Show old label during 'out' phase, new label during 'in' phase
        const displayLabel =
          isAnimating && randomAnimation.phase === 'out' && randomAnimation.oldLabel
            ? randomAnimation.oldLabel
            : `${group.category}:${group.values.join(',')}`;

        return (
          <Chip
            key={`${group.category}-${index}`}
            label={displayLabel}
            onClick={e => onChipClick(e, index)}
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

      {/* Chip action menu */}
      <Menu
        anchorEl={chipMenuAnchor}
        open={Boolean(chipMenuAnchor)}
        onClose={onChipMenuClose}
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
                    onClick={() => onAddValueToActiveGroup(value)}
                    sx={{ fontFamily: typography.fontFamily, py: 0.5 }}
                  >
                    <AddIcon
                      fontSize="small"
                      sx={{ mr: 1, color: colors.success, fontSize: '1rem' }}
                    />
                    <Typography sx={{ fontSize: fontSize.base, flex: 1 }}>{value}</Typography>
                    <Typography sx={{ fontSize: fontSize.sm, color: semanticColors.mutedText }}>
                      ({count})
                    </Typography>
                  </MenuItem>
                )),
                <Divider key="divider-add" />,
              ]
            : []),
          // Remove individual values
          ...activeGroup.values.map(value => (
            <MenuItem
              key={`remove-${value}`}
              onClick={() => onRemoveValue(value)}
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
                  onClick={onRemoveActiveGroup}
                  sx={{ fontFamily: typography.fontFamily, color: colors.error }}
                >
                  <CloseIcon fontSize="small" sx={{ mr: 1 }} />
                  remove all
                </MenuItem>,
              ]
            : []),
        ]}
      </Menu>
    </>
  );
}
