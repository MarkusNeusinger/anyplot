import Box from '@mui/material/Box';

import { fontSize, typography } from 'src/theme';

export function MapHeader({ specsCount, edgesCount }: { specsCount?: number; edgesCount: number }) {
  return (
    <Box
      sx={{
        position: 'absolute',
        top: { xs: 50, sm: 16 },
        left: { xs: 16, sm: 32, md: 64, lg: 96 },
        zIndex: 2,
        fontFamily: typography.mono,
        fontSize: fontSize.xs,
        color: 'var(--ink-soft)',
        pointerEvents: 'none',
      }}
    >
      {specsCount != null ? `${specsCount} specs · ${edgesCount} edges` : ' '}
    </Box>
  );
}
