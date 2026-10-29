import Box from '@mui/material/Box';

import { colors, fontSize, typography } from 'src/theme';

export type SortDir = 'asc' | 'desc';

export function SortableHeader({
  label,
  active,
  dir,
  onClick,
  center,
}: {
  label: string;
  active: boolean;
  dir: SortDir;
  onClick: () => void;
  center?: boolean;
}) {
  return (
    <Box
      component="button"
      type="button"
      onClick={onClick}
      sx={{
        background: 'none',
        border: 'none',
        p: 0,
        cursor: 'pointer',
        fontFamily: typography.fontFamily,
        fontSize: fontSize.xs,
        fontWeight: 600,
        color: active ? colors.primary : 'var(--ink-soft)',
        textAlign: center ? 'center' : 'left',
        display: 'flex',
        alignItems: 'center',
        gap: 0.25,
        justifyContent: center ? 'center' : 'flex-start',
        '&:hover': { color: colors.primaryDark },
      }}
    >
      {label}
      {active && (
        <Box component="span" sx={{ fontSize: fontSize.micro }}>
          {dir === 'asc' ? '▲' : '▼'}
        </Box>
      )}
    </Box>
  );
}
