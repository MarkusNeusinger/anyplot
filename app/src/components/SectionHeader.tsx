import Box from '@mui/material/Box';
import { Link } from 'react-router-dom';
import { colors, typography } from '../theme';

interface SectionHeaderProps {
  number: string;
  title: React.ReactNode;
  linkText?: string;
  linkTo?: string;
}

export function SectionHeader({ number, title, linkText, linkTo }: SectionHeaderProps) {
  return (
    <Box sx={{
      display: 'grid',
      gridTemplateColumns: 'auto 1fr auto',
      alignItems: 'baseline',
      gap: 3,
      mb: 6,
      pb: 2.5,
      borderBottom: `1px solid var(--rule)`,
    }}>
      <Box sx={{
        fontFamily: typography.mono,
        fontSize: '11px',
        color: 'var(--ink-muted)',
        textTransform: 'uppercase',
        letterSpacing: '0.15em',
      }}>
        {number}
      </Box>
      <Box component="h2" sx={{
        fontFamily: typography.serif,
        fontWeight: 400,
        fontSize: { xs: '1.75rem', sm: '2.25rem', md: 'clamp(2.25rem, 4.5vw, 3.5rem)' },
        lineHeight: 1,
        letterSpacing: '-0.02em',
        color: 'var(--ink)',
        m: 0,
        '& em': {
          fontStyle: 'italic',
          color: colors.primary,
          fontWeight: 300,
        },
      }}>
        {title}
      </Box>
      {linkText && linkTo && (
        <Box
          component={Link}
          to={linkTo}
          sx={{
            fontFamily: typography.mono,
            fontSize: '12px',
            color: 'var(--ink-soft)',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 1,
            transition: 'color 0.2s, gap 0.2s',
            '&:hover': { color: colors.primary, gap: 1.5 },
          }}
        >
          {linkText} →
        </Box>
      )}
    </Box>
  );
}
