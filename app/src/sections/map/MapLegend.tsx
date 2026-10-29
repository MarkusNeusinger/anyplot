import Box from '@mui/material/Box';

import { CLUSTER_COLORS } from 'src/hooks/useForceGraphSimulation';
import { fontSize, typography } from 'src/theme';

interface MapLegendProps {
  graphData: {
    topTypes: string[];
    typeCounts: Map<string, number>;
  };
  legendOpen: boolean;
  setLegendOpen: (open: boolean | ((prev: boolean) => boolean)) => void;
  activeCategory: string;
  hoverType: string | null;
  setHoverType: (type: string | null) => void;
}

export function MapLegend({
  graphData,
  legendOpen,
  setLegendOpen,
  activeCategory,
  hoverType,
  setHoverType,
}: MapLegendProps) {
  if (graphData.topTypes.length === 0) return null;

  return (
    <>
      <Box
        component="button"
        onClick={() => setLegendOpen(o => !o)}
        sx={{
          all: 'unset',
          display: { xs: 'inline-block', sm: 'none' },
          position: 'absolute',
          top: 44,
          right: 10,
          zIndex: 2,
          cursor: 'pointer',
          padding: '6px 6px',
          fontFamily: typography.mono,
          fontSize: fontSize.xs,
          color: legendOpen ? 'var(--ink)' : 'var(--ink-soft)',
          userSelect: 'none',
        }}
      >
        {legendOpen ? 'legend ▾' : 'legend ▸'}
      </Box>
      <Box
        sx={{
          position: 'absolute',
          top: { xs: 76, sm: 16 },
          right: { xs: 16, sm: 32, md: 64, lg: 96 },
          zIndex: 2,
          display: { xs: legendOpen ? 'flex' : 'none', sm: 'flex' },
          flexDirection: 'column',
          gap: 0.5,
          fontFamily: typography.mono,
          fontSize: fontSize.xs,
          color: 'var(--ink-soft)',
          bgcolor: { xs: 'var(--bg-surface)', sm: 'transparent' },
          border: { xs: '1px solid var(--rule)', sm: 'none' },
          borderRadius: { xs: '4px', sm: 0 },
          p: { xs: 1, sm: 0 },
        }}
      >
        <Box sx={{ opacity: 0.6, mb: 0.25 }}>{activeCategory}</Box>
        {graphData.topTypes.map((t, i) => {
          const color = CLUSTER_COLORS[i % CLUSTER_COLORS.length];
          const count = graphData.typeCounts.get(t) ?? 0;
          const dimmed = hoverType != null && hoverType !== t;
          return (
            <Box
              key={t}
              onMouseEnter={() => setHoverType(t)}
              onMouseLeave={() => setHoverType(null)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                cursor: 'pointer',
                opacity: dimmed ? 0.35 : 1,
                transition: 'opacity 0.15s',
                color: hoverType === t ? 'var(--ink)' : 'inherit',
                userSelect: 'none',
              }}
            >
              <Box
                sx={{ width: 10, height: 10, bgcolor: color, borderRadius: '2px', flex: 'none' }}
              />
              <Box component="span" sx={{ minWidth: 60 }}>
                {t}
              </Box>
              <Box component="span" sx={{ opacity: 0.55, fontVariantNumeric: 'tabular-nums' }}>
                {count}
              </Box>
            </Box>
          );
        })}
      </Box>
    </>
  );
}
