import Box from '@mui/material/Box';
import { Link } from 'react-router-dom';
import { colors, typography } from '../theme';
import { useAnalytics } from '../hooks';

interface SectionHeaderProps {
  /** Prefix symbol — e.g. `§`, `❯`, `$`. Rendered at the same size as the title. */
  prompt?: string;
  title: React.ReactNode;
  linkText?: string;
  linkTo?: string;
}

const titleFontSize = { xs: '1.5rem', sm: '1.875rem', md: 'clamp(1.875rem, 3.5vw, 2.5rem)' };

export function SectionHeader({ prompt, title, linkText, linkTo }: SectionHeaderProps) {
  const { trackEvent } = useAnalytics();
  return (
    <Box sx={{
      display: 'grid',
      gridTemplateColumns: 'auto 1fr auto',
      alignItems: 'baseline',
      gap: { xs: 1.5, md: 2 },
      mb: 4,
      pt: 2.5,
      pb: 1.5,
      borderBottom: `1px solid var(--rule)`,
    }}>
      {prompt && (
        <Box sx={{
          fontFamily: typography.mono,
          fontSize: { xs: '0.95rem', sm: '1.15rem', md: '1.4rem' },
          fontWeight: 500,
          color: 'var(--ink-muted)',
          whiteSpace: 'nowrap',
        }}>
          {prompt}
        </Box>
      )}
      <Box component="h2" sx={{
        fontFamily: typography.serif,
        fontWeight: 400,
        fontSize: titleFontSize,
        lineHeight: 1.15,
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
          onClick={() => trackEvent('nav_click', { source: 'section_header', target: linkTo })}
          sx={{
            fontFamily: typography.mono,
            fontSize: '12px',
            color: 'var(--ink-soft)',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            transition: 'color 0.2s',
            '&:hover': { color: colors.primary },
          }}
        >
          {linkText}
        </Box>
      )}
    </Box>
  );
}
