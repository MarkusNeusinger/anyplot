import { memo, useMemo } from 'react';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import { fontSize, semanticColors } from '../theme';

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
  quality_score: number | null;
}

interface LibraryPillsProps {
  implementations: Implementation[];
  selectedLibrary: string;
  onSelect: (libraryId: string) => void;
}

export const LibraryPills = memo(function LibraryPills({
  implementations,
  selectedLibrary,
  onSelect,
}: LibraryPillsProps) {
  // Sort implementations alphabetically
  const sortedImpls = useMemo(() => {
    return [...implementations].sort((a, b) => a.library_id.localeCompare(b.library_id));
  }, [implementations]);

  // Get current index
  const currentIndex = useMemo(() => {
    const idx = sortedImpls.findIndex((impl) => impl.library_id === selectedLibrary);
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

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 0.5,
        py: 2,
      }}
    >
      {/* Left Arrow */}
      <IconButton
        onClick={handlePrev}
        aria-label="Previous library"
        size="small"
        sx={{
          color: semanticColors.mutedText,
          '&:hover': { color: '#3776AB', bgcolor: '#f3f4f6' },
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
          const score = impl.quality_score;

          return (
            <Box
              key={impl.library_id}
              onClick={() => onSelect(impl.library_id)}
              title={!isCenter ? impl.library_id : undefined}
              sx={{
                px: 1.5,
                py: 0.5,
                borderRadius: 2,
                fontFamily: '"MonoLisa", monospace',
                fontSize: fontSize.base,
                fontWeight: isCenter ? 600 : 400,
                bgcolor: '#f3f4f6',
                border: isCenter ? '1px solid #3776AB' : '1px solid transparent',
                color: isCenter ? '#374151' : semanticColors.mutedText,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                '&:hover': {
                  bgcolor: '#e5e7eb',
                  borderColor: '#3776AB',
                  color: '#374151',
                },
              }}
            >
              {/* Full name on desktop, abbreviated on mobile */}
              <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>
                {impl.library_id}
              </Box>
              <Box component="span" sx={{ display: { xs: 'inline', sm: 'none' } }}>
                {isCenter ? impl.library_id : (LIBRARY_ABBREV[impl.library_id] || impl.library_id)}
              </Box>
              {score && isCenter && (
                <Box
                  component="span"
                  sx={{
                    ml: 0.5,
                    fontSize: fontSize.xs,
                    color: '#6b7280',
                  }}
                >
                  {Math.round(score)}
                </Box>
              )}
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
          '&:hover': { color: '#3776AB', bgcolor: '#f3f4f6' },
        }}
      >
        <ChevronRightIcon />
      </IconButton>
    </Box>
  );
});
