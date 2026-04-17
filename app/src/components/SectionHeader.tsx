import Box from '@mui/material/Box';
import { Link } from 'react-router-dom';
import { colors, typography } from '../theme';

interface SectionHeaderProps {
  /** Shell-prompt prefix per style-guide §6.3 — e.g. `❯`, `$`, `~/anyplot/`. Preferred. */
  prompt?: string;
  /** Legacy editorial section number — e.g. `§ 01`. Kept for non-landing pages. */
  number?: string;
  title: React.ReactNode;
  linkText?: string;
  linkTo?: string;
}

export function SectionHeader({ prompt, number, title, linkText, linkTo }: SectionHeaderProps) {
  const isPrompt = !!prompt;

  return (
    <Box sx={{
      display: 'grid',
      gridTemplateColumns: 'auto 1fr auto',
      alignItems: 'baseline',
      gap: { xs: 1.5, md: 2 },
      mb: 6,
      pb: 2.5,
      borderBottom: `1px solid var(--rule)`,
    }}>
      <Box sx={isPrompt ? {
        fontFamily: typography.mono,
        fontSize: { xs: '0.95rem', sm: '1.15rem', md: '1.4rem' },
        fontWeight: 500,
        color: 'var(--ink-muted)',
        whiteSpace: 'nowrap',
      } : {
        fontFamily: typography.mono,
        fontSize: '11px',
        color: 'var(--ink-muted)',
        textTransform: 'uppercase',
        letterSpacing: '0.15em',
      }}>
        {isPrompt ? prompt : number}
      </Box>
      <Box component="h2" sx={{
        fontFamily: typography.serif,
        fontWeight: 400,
        fontSize: isPrompt
          ? { xs: '1.5rem', sm: '1.875rem', md: 'clamp(1.875rem, 3.5vw, 2.5rem)' }
          : { xs: '1.75rem', sm: '2.25rem', md: 'clamp(2.25rem, 4.5vw, 3.5rem)' },
        lineHeight: isPrompt ? 1.15 : 1,
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
