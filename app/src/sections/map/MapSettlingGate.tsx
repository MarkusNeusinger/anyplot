import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';

import { colors, fontSize, typography } from 'src/theme';

interface MapSettlingGateProps {
  ready: boolean;
  settled: boolean;
  isDark: boolean;
  tickProgress: number;
}

export function MapSettlingGate({ ready, settled, isDark, tickProgress }: MapSettlingGateProps) {
  if (!ready) return null;

  return (
    <Box
      aria-hidden={settled}
      sx={{
        position: 'absolute',
        inset: 0,
        pointerEvents: settled ? 'none' : 'auto',
        cursor: settled ? 'default' : 'wait',
        zIndex: 1,
        opacity: settled ? 0 : 1,
        transition: 'opacity 250ms ease',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: isDark ? 'rgba(20, 20, 18, 0.55)' : 'rgba(252, 251, 243, 0.55)',
        backdropFilter: 'blur(2px)',
        WebkitBackdropFilter: 'blur(2px)',
      }}
    >
      <Box
        role="status"
        aria-live="polite"
        aria-label="Computing map layout"
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 1.25,
          px: 3,
          py: 2,
          fontFamily: typography.mono,
        }}
      >
        <CircularProgress size={48} thickness={4} />
        <Box sx={{ fontFamily: typography.mono, fontSize: fontSize.sm, color: 'var(--ink)' }}>
          map.simulate()
        </Box>
        <Box
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(tickProgress * 100)}
          aria-label="Layout computation progress"
          sx={{
            width: 160,
            height: 3,
            borderRadius: 2,
            bgcolor: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)',
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              width: `${Math.round(tickProgress * 100)}%`,
              height: '100%',
              bgcolor: colors.primary,
              transition: 'width 140ms linear',
            }}
          />
        </Box>
      </Box>
    </Box>
  );
}
