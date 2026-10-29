import Box from '@mui/material/Box';

import { typography } from 'src/theme';

export function MapHoverPanel({
  hoverId,
  pinnedId,
  panelData,
  isDark,
}: {
  hoverId: string | null;
  pinnedId: string | null;
  panelData: {
    title: string;
    plotType: string | null;
    chipColor: string | null;
    tags: string[];
    previewUrl: string | null;
  } | null;
  isDark: boolean;
}) {
  return (
    <Box
      component="aside"
      aria-hidden={!(hoverId || pinnedId)}
      sx={{
        position: 'absolute',
        bottom: { xs: 8, sm: 16 },
        right: { xs: 16, sm: 32, md: 64, lg: 96 },
        zIndex: 3,
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
              gap: { xs: 0.5, md: 1 },
              borderTop: '1px solid var(--rule)',
            }}
          >
            <Box
              sx={{
                fontSize: { xs: '0.6rem', md: '0.75rem' },
                lineHeight: 1.3,
                color: 'var(--ink)',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {panelData.title}
            </Box>
            <Box
              sx={{
                display: { xs: 'none', md: 'flex' },
                flexWrap: 'wrap',
                gap: 0.5,
              }}
            >
              {panelData.plotType && (
                <Box
                  sx={{
                    px: 0.5,
                    py: 0.25,
                    fontSize: '0.65rem',
                    color: panelData.chipColor ? 'var(--bg-page)' : isDark ? '#FFFDF6' : '#242420',
                    bgcolor:
                      panelData.chipColor ??
                      (isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)'),
                    borderRadius: '2px',
                  }}
                >
                  {panelData.plotType}
                </Box>
              )}
              {panelData.tags.map(t => (
                <Box
                  key={t}
                  sx={{
                    px: 0.5,
                    py: 0.25,
                    fontSize: '0.65rem',
                    color: 'var(--ink-soft)',
                    border: '1px solid var(--rule)',
                    borderRadius: '2px',
                  }}
                >
                  {t}
                </Box>
              ))}
            </Box>
          </Box>
        </>
      )}
    </Box>
  );
}
