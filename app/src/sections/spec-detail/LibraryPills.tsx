import { memo, useMemo } from 'react';

import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';

import { colors, fontSize, semanticColors, typography } from 'src/theme';

// Library abbreviations (same as filter display)
const LIBRARY_ABBREV: Record<string, string> = {
  matplotlib: 'mpl',
  seaborn: 'sns',
  plotly: 'ply',
  bokeh: 'bok',
  altair: 'alt',
  plotnine: 'p9',
  pygal: 'pyg',
  highcharts: 'hc',
  letsplot: 'lp',
};

interface Implementation {
  library_id: string;
  library_name: string;
  language: string;
  quality_score: number | null;
}

interface LibraryPillsProps {
  implementations: Implementation[];
  selectedLibrary: string;
  onSelect: (libraryId: string) => void;
  onAll?: () => void;
  /**
   * "Use with my data": present only when SpecPage's `useAgentEligibility` names a lane
   * for this pair. Renders `.use_my_data() →` to the right of the carousel, the mirror of
   * `← .compare()` on its left.
   */
  onUseWithMyData?: () => void;
}

/**
 * Accessible name of the agent chat entry; the visible label is `.use_my_data() →`. It
 * says nothing the label does not: "experimental" is the chat's notice to make, once open.
 */
export const USE_MY_DATA_LABEL = 'Use with my data';

/**
 * One of the two text actions that flank the carousel: mono, `--ink-soft`, green on
 * hover, the arrow nudging outwards. `arrow` says on which side the arrow sits.
 */
function TextAction({
  arrow,
  ariaLabel,
  onActivate,
  children,
}: {
  arrow: 'left' | 'right';
  ariaLabel: string;
  onActivate: () => void;
  children: React.ReactNode;
}) {
  const arrowGlyph = (
    <Box component="span" className="action-arrow">
      {arrow === 'left' ? '←' : '→'}
    </Box>
  );
  return (
    <Box
      onClick={onActivate}
      role="button"
      tabIndex={0}
      onKeyDown={(e: React.KeyboardEvent) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onActivate();
        }
      }}
      aria-label={ariaLabel}
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 0.75,
        fontFamily: typography.mono,
        fontSize: fontSize.sm,
        color: 'var(--ink-soft)',
        cursor: 'pointer',
        whiteSpace: 'nowrap',
        transition: 'color 0.2s',
        '& .action-arrow': { transition: 'transform 0.2s' },
        '&:hover': { color: colors.primary },
        '&:hover .action-arrow': { transform: `translateX(${arrow === 'left' ? -3 : 3}px)` },
        '&:focus-visible': {
          outline: `2px solid ${colors.primary}`,
          outlineOffset: 2,
          borderRadius: '2px',
        },
      }}
    >
      {arrow === 'left' && arrowGlyph}
      {children}
      {arrow === 'right' && arrowGlyph}
    </Box>
  );
}

/**
 * Vertical rule between a text action and the carousel, desktop only. The margin next to
 * the carousel is the smaller one: it compensates for the arrow IconButton's ~5 px internal
 * padding so the visible whitespace on either side of the rule is equal.
 */
function ActionRule({ side }: { side: 'left' | 'right' }) {
  return (
    <Box
      sx={{
        height: 20,
        width: '1px',
        bgcolor: 'var(--rule)',
        ...(side === 'left' ? { ml: 1.5, mr: '7px' } : { ml: '7px', mr: 1.5 }),
        display: { xs: 'none', md: 'block' },
      }}
    />
  );
}

export const LibraryPills = memo(function LibraryPills({
  implementations,
  selectedLibrary,
  onSelect,
  onAll,
  onUseWithMyData,
}: LibraryPillsProps) {
  // Sort implementations alphabetically
  const sortedImpls = useMemo(() => {
    return [...implementations].sort((a, b) => a.library_id.localeCompare(b.library_id));
  }, [implementations]);

  // Get current index
  const currentIndex = useMemo(() => {
    const idx = sortedImpls.findIndex(impl => impl.library_id === selectedLibrary);
    return idx >= 0 ? idx : 0;
  }, [sortedImpls, selectedLibrary]);

  // Get visible items (prev, current, next) with wrap-around
  const visibleItems = useMemo(() => {
    const len = sortedImpls.length;
    if (len === 0) return [];
    if (len === 1) return [{ impl: sortedImpls[0], position: 'center' as const }];
    if (len === 2) {
      return [
        { impl: sortedImpls[(currentIndex - 1 + len) % len], position: 'left' as const },
        { impl: sortedImpls[currentIndex], position: 'center' as const },
      ];
    }

    const prevIdx = (currentIndex - 1 + len) % len;
    const nextIdx = (currentIndex + 1) % len;

    return [
      { impl: sortedImpls[prevIdx], position: 'left' as const },
      { impl: sortedImpls[currentIndex], position: 'center' as const },
      { impl: sortedImpls[nextIdx], position: 'right' as const },
    ];
  }, [sortedImpls, currentIndex]);

  const handlePrev = () => {
    const len = sortedImpls.length;
    const newIndex = (currentIndex - 1 + len) % len;
    onSelect(sortedImpls[newIndex].library_id);
  };

  const handleNext = () => {
    const len = sortedImpls.length;
    const newIndex = (currentIndex + 1) % len;
    onSelect(sortedImpls[newIndex].library_id);
  };

  if (sortedImpls.length === 0) return null;

  // Layout. From md up, one row on a three-column grid whose side columns are equal
  // (`minmax(0, 1fr)`): the carousel is the centre column, so it stays centred over the
  // image whether or not the right-hand action is there, and the action can fade in after
  // the eligibility probe without moving anything. Below md the carousel's own width
  // leaves no room beside it, so the two text actions share a line above it, `.compare()`
  // at the left edge and `.use_my_data()` at the right, and the carousel takes the line
  // below. That first line is there for `.compare()` anyway, so the late action does not
  // move the page either.
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: {
          xs: 'minmax(0, 1fr) minmax(0, 1fr)',
          md: 'minmax(0, 1fr) auto minmax(0, 1fr)',
        },
        gridTemplateAreas: {
          xs: '"compare action" "carousel carousel"',
          md: '"compare carousel action"',
        },
        alignItems: 'center',
        // From md up the rules' own margins space the row, so the grid adds none.
        columnGap: { xs: 1, md: 0 },
        rowGap: onAll || onUseWithMyData ? 1 : 0,
        py: 2,
      }}
    >
      <Box
        sx={{
          gridArea: 'compare',
          justifySelf: { xs: 'start', md: 'end' },
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {onAll && (
          <>
            <TextAction arrow="left" ariaLabel="Back to library comparison" onActivate={onAll}>
              <Box component="span">.compare()</Box>
            </TextAction>
            <ActionRule side="left" />
          </>
        )}
      </Box>

      {/* Carousel row; in the DOM between the two actions, so the tab order follows the
          desktop row from left to right */}
      <Box
        sx={{
          gridArea: 'carousel',
          justifySelf: 'center',
          display: 'flex',
          alignItems: 'center',
          gap: 0.5,
        }}
      >
        {/* Left Arrow */}
        <IconButton
          onClick={handlePrev}
          aria-label="Previous library"
          size="small"
          sx={{
            color: semanticColors.mutedText,
            '&:hover': { color: colors.primary, bgcolor: 'var(--bg-surface)' },
          }}
        >
          <ChevronLeftIcon />
        </IconButton>

        {/* Pills Container */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 0.75,
            justifyContent: 'center',
          }}
        >
          {visibleItems.map(({ impl, position }) => {
            const isCenter = position === 'center';

            return (
              <Box
                key={impl.library_id}
                onClick={() => onSelect(impl.library_id)}
                title={!isCenter ? impl.library_id : undefined}
                sx={{
                  px: 1.5,
                  py: 0.5,
                  borderRadius: 2,
                  fontFamily: typography.fontFamily,
                  fontSize: fontSize.base,
                  fontWeight: isCenter ? 600 : 400,
                  bgcolor: 'var(--bg-surface)',
                  border: isCenter ? `1px solid ${colors.primary}` : '1px solid transparent',
                  color: isCenter ? 'var(--ink-soft)' : semanticColors.mutedText,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  whiteSpace: 'nowrap',
                  '&:hover': {
                    bgcolor: 'var(--bg-elevated)',
                    borderColor: colors.primary,
                    color: 'var(--ink-soft)',
                  },
                }}
              >
                {/* Full name on desktop, abbreviated on mobile */}
                <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
                  {impl.library_id}
                </Box>
                <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>
                  {isCenter ? impl.library_id : LIBRARY_ABBREV[impl.library_id] || impl.library_id}
                </Box>
              </Box>
            );
          })}
        </Box>

        {/* Right Arrow */}
        <IconButton
          onClick={handleNext}
          aria-label="Next library"
          size="small"
          sx={{
            color: semanticColors.mutedText,
            '&:hover': { color: colors.primary, bgcolor: 'var(--bg-surface)' },
          }}
        >
          <ChevronRightIcon />
        </IconButton>
      </Box>

      <Box
        sx={{
          gridArea: 'action',
          justifySelf: { xs: 'end', md: 'start' },
          display: 'flex',
          alignItems: 'center',
        }}
      >
        {onUseWithMyData && (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              animation: 'useMyDataFadeIn 0.3s ease-out',
              '@keyframes useMyDataFadeIn': { from: { opacity: 0 }, to: { opacity: 1 } },
              '@media (prefers-reduced-motion: reduce)': { animation: 'none' },
            }}
          >
            <ActionRule side="right" />
            <TextAction arrow="right" ariaLabel={USE_MY_DATA_LABEL} onActivate={onUseWithMyData}>
              <Box component="span">.use_my_data()</Box>
            </TextAction>
          </Box>
        )}
      </Box>
    </Box>
  );
});
