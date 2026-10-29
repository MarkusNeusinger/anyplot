import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';

import { fontSize, typography } from 'src/theme';

export function MapLoadingError({
  specs,
  error,
}: {
  specs: { id: string; title: string }[] | null;
  error: string | null;
}) {
  return (
    <>
      {!specs && !error && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CircularProgress size={28} />
        </Box>
      )}
      {error && (
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--ink-soft)',
            fontFamily: typography.mono,
          }}
        >
          <Typography sx={{ fontFamily: typography.mono, fontSize: fontSize.sm }}>
            Failed to load map: {error}
          </Typography>
        </Box>
      )}
    </>
  );
}
