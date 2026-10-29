import Box from '@mui/material/Box';

import { useTheme } from 'src/hooks/useLayoutContext';
import type { MapPanelData } from 'src/sections/map/useMapSelection';
import { fontSize, typography } from 'src/theme';

interface MapHoverPanelProps {
  hoverId: string | null;
  pinnedId: string | null;
  panelData: MapPanelData | null;
}

export function MapHoverPanel({ hoverId, pinnedId, panelData }: MapHoverPanelProps) {
  const { isDark } = useTheme();

  return (
    <Box
      component="aside"
      aria-hidden={!(hoverId || pinnedId)}
      sx={{
        position: 'absolute',
        bottom: { xs: 8, sm: 16 },
        right: { xs: 16, sm: 32, md: 64, lg: 96 },
        zIndex: 3,
        // Phones + tablets: ~half the width, no tags. Otherwise the
        // panel covers the searched node + its connection lines after
        // fly-to. Desktop only: full 280 px panel with tag chips.
        width: { xs: 160, md: 280 },
        maxWidth: { xs: 'calc(60vw - 32px)', md: 'calc(100vw - 64px)' },
        border: '1px solid var(--rule)',
        borderRadius: '4px',
        bgcolor: 'var(--bg-surface)',
        overflow: 'hidden',
        pointerEvents: 'none',
        opacity: (hoverId || pinnedId) && panelData ? 1 : 0,
        transform: (hoverId || pinnedId) && panelData ? 'translateY(0)' : 'translateY(4px)',
        transition: 'opacity 120ms ease, transform 120ms ease',
        fontFamily: typography.mono,
      }}
    >
      {panelData && (
        <>
          {panelData.previewUrl ? (
            <Box
              component="img"
              src={panelData.previewUrl}
              alt=""
              sx={{
                display: 'block',
                width: '100%',
                height: 'auto',
                maxHeight: { xs: 110, md: 200 },
                objectFit: 'contain',
                bgcolor: isDark ? '#0a0a08' : '#FFFDF6',
              }}
            />
          ) : (
            <Box sx={{ height: { xs: 90, md: 158 }, bgcolor: isDark ? '#0a0a08' : '#FFFDF6' }} />
          )}
          <Box
            sx={{
              p: { xs: 0.75, md: 1.25 },
              display: 'flex',
              flexDirection: 'column',
              gap: 0.5,
            }}
          >
            <Box
              sx={{
                fontSize: fontSize.sm,
                color: 'var(--ink)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {panelData.title}
            </Box>
            {panelData.plotType && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '2px',
                    bgcolor: panelData.chipColor ?? 'var(--ink-soft)',
                    flex: 'none',
                  }}
                />
                <Box sx={{ fontSize: fontSize.xs, color: 'var(--ink-soft)' }}>
                  {panelData.plotType}
                </Box>
              </Box>
            )}
            {panelData.tags.length > 0 && (
              <Box
                sx={{
                  // Phones + tablets: hide tags, the smaller panel
                  // only shows image + title + plot_type chip so it
                  // doesn't cover the focused node and its KNN edges.
                  display: { xs: 'none', md: 'flex' },
                  flexWrap: 'wrap',
                  gap: 0.75,
                  fontSize: fontSize.xs,
                  color: 'var(--ink-soft)',
                  opacity: 0.85,
                }}
              >
                {panelData.tags.map((t: string) => (
                  <Box key={t} component="span">
                    {t}
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </>
      )}
    </Box>
  );
}
