import { Link } from 'react-router-dom';

import Box from '@mui/material/Box';

import { useAnalytics } from 'src/hooks';
import { colors, typography } from 'src/theme';

interface SectionHeaderBaseProps {
  /** Prefix symbol — e.g. `§`, `❯`, `$`. Rendered at the same size as the title. */
  prompt?: string;
  title: React.ReactNode;
}

/**
 * `linkTo` (internal route) and `linkHref` (external URL) are mutually
 * exclusive. The discriminated union enforces this at the type level so
 * callers can't accidentally pass both.
 */
type SectionHeaderLinkProps =
  | { linkText?: never; linkTo?: never; linkHref?: never }
  | { linkText: string; linkTo: string; linkHref?: never }
  | { linkText: string; linkHref: string; linkTo?: never };

type SectionHeaderProps = SectionHeaderBaseProps & SectionHeaderLinkProps;

const titleFontSize = { xs: '1.5rem', sm: '1.875rem', md: 'clamp(1.875rem, 3.5vw, 2.5rem)' };

/** Derive a low-cardinality identifier (hostname) for analytics dimensions. */
function externalDestination(url: string): string {
  try {
    return new URL(url).hostname;
  } catch {
    return url;
  }
}

export function SectionHeader(props: SectionHeaderProps) {
  const { prompt, title, linkText, linkTo, linkHref } = props;
  const { trackEvent } = useAnalytics();
  const linkSx = {
    fontFamily: typography.mono,
    fontSize: '12px',
    color: 'var(--ink-soft)',
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    transition: 'color 0.2s',
    '&:hover': { color: colors.primary },
  } as const;
  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns: 'auto 1fr auto',
        alignItems: 'baseline',
        gap: { xs: 1.5, md: 2 },
        mb: 4,
        pt: 2.5,
        pb: 1.5,
        borderBottom: `1px solid var(--rule)`,
      }}
    >
      {prompt && (
        <Box
          sx={{
            fontFamily: typography.mono,
            fontSize: { xs: '0.95rem', sm: '1.15rem', md: '1.4rem' },
            fontWeight: 500,
            color: 'var(--ink-muted)',
            whiteSpace: 'nowrap',
          }}
        >
          {prompt}
        </Box>
      )}
      <Box
        component="h2"
        sx={{
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
        }}
      >
        {title}
      </Box>
      {linkText && linkTo && (
        <Box
          component={Link}
          to={linkTo}
          onClick={() => trackEvent('nav_click', { source: 'section_header', target: linkTo })}
          sx={linkSx}
        >
          {linkText}
        </Box>
      )}
      {linkText && linkHref && !linkTo && (
        <Box
          component="a"
          href={linkHref}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() =>
            trackEvent('external_link', {
              source: 'section_header',
              destination: externalDestination(linkHref),
            })
          }
          sx={linkSx}
        >
          {linkText}
        </Box>
      )}
    </Box>
  );
}
