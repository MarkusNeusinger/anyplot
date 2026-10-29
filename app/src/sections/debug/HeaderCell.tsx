import Typography from '@mui/material/Typography';

import { fontSize, typography } from 'src/theme';

export function HeaderCell({ children, center }: { children: React.ReactNode; center?: boolean }) {
  return (
    <Typography
      sx={{
        fontFamily: typography.fontFamily,
        fontSize: fontSize.xs,
        fontWeight: 600,
        color: 'var(--ink-soft)',
        textAlign: center ? 'center' : 'left',
      }}
    >
      {children}
    </Typography>
  );
}
