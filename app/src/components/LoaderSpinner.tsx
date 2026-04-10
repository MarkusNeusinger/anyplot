import Box from '@mui/material/Box';
import { colors } from '../theme';

interface LoaderSpinnerProps {
  size?: 'large' | 'small';
}

export function LoaderSpinner({ size = 'large' }: LoaderSpinnerProps) {
  const isLarge = size === 'large';
  const width = isLarge ? 100 : 75;
  const dotSize = isLarge ? 16 : 12;
  const offset = isLarge ? 32 : 24;
  const doubleOffset = isLarge ? 64 : 48;

  return (
    <Box
      sx={{
        position: 'relative',
        width,
        height: dotSize,
        '&::before': {
          content: '""',
          position: 'absolute',
          width: dotSize,
          height: dotSize,
          borderRadius: '50%',
          background: colors.primary,
          boxShadow: `${offset}px 0 ${colors.primary}`,
          left: 0,
          top: 0,
          animation: 'ballMoveX 2s linear infinite',
        },
        '&::after': {
          content: '""',
          position: 'absolute',
          width: dotSize,
          height: dotSize,
          borderRadius: '50%',
          background: colors.primary,
          left: 0,
          top: 0,
          transform: `translateX(${doubleOffset}px) scale(1)`,
          zIndex: 2,
          animation: 'trfLoader 2s linear infinite',
        },
        '@keyframes trfLoader': {
          '0%, 5%': {
            transform: `translateX(${doubleOffset}px) scale(1)`,
            background: colors.primary,
          },
          '10%': {
            transform: `translateX(${doubleOffset}px) scale(1)`,
            background: colors.accent,
          },
          '40%': {
            transform: `translateX(${offset}px) scale(1.5)`,
            background: colors.accent,
          },
          '90%, 95%': {
            transform: 'translateX(0px) scale(1)',
            background: colors.accent,
          },
          '100%': {
            transform: 'translateX(0px) scale(1)',
            background: colors.primary,
          },
        },
        '@keyframes ballMoveX': {
          '0%, 10%': { transform: 'translateX(0)' },
          '90%, 100%': { transform: `translateX(${offset}px)` },
        },
      }}
    />
  );
}
