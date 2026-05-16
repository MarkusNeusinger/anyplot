import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import { Link as RouterLink } from 'react-router-dom';
import { GITHUB_URL } from '../constants';
import { colors, fontSize, semanticColors, typography } from '../theme';

interface FooterProps {
  onTrackEvent?: (name: string, props?: Record<string, string | undefined>) => void;
  selectedSpec?: string;
  selectedLibrary?: string;
}

const linkSx = {
  color: semanticColors.mutedText,
  textDecoration: 'none',
  position: 'relative' as const,
  '&::after': {
    content: '""',
    position: 'absolute' as const,
    bottom: -1,
    left: 0,
    right: 0,
    height: '1px',
    background: colors.primary,
    transform: 'scaleX(0)',
    transformOrigin: 'left',
    transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  },
  '&:hover': {
    color: 'var(--ink)',
    '&::after': { transform: 'scaleX(1)' },
  },
} as const;

const ISSUE_CHOOSER_URL = `${GITHUB_URL}/issues/new/choose`;

export function Footer({ onTrackEvent, selectedSpec, selectedLibrary }: FooterProps) {
  const track = (destination: string) => () =>
    onTrackEvent?.('external_link', { destination, spec: selectedSpec, library: selectedLibrary });
  const trackInternal = (destination: string) => () =>
    onTrackEvent?.('internal_link', { destination, spec: selectedSpec, library: selectedLibrary });

  return (
    <Box component="footer" sx={{
      mt: 4,
      pt: 4,
      borderTop: '1px solid var(--rule)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: 1,
      fontSize: fontSize.md,
      fontFamily: typography.mono,
      color: semanticColors.mutedText,
      letterSpacing: '0.08em',
    }}>
      <Link
        href={GITHUB_URL}
        target="_blank"
        rel="noopener noreferrer"
        onClick={track('github')}
        sx={linkSx}
      >
        github
      </Link>
      <span>·</span>
      <Link
        href={ISSUE_CHOOSER_URL}
        target="_blank"
        rel="noopener noreferrer"
        onClick={track('github_issue_chooser')}
        sx={linkSx}
      >
        report
      </Link>
      <Box component="span" sx={{ display: { xs: 'none', md: 'contents' } }}>
        <span>·</span>
        <Link
          href="https://www.linkedin.com/in/markus-neusinger/"
          target="_blank"
          rel="noopener noreferrer"
          onClick={track('linkedin')}
          sx={linkSx}
        >
          markus neusinger
        </Link>
      </Box>
      <span>·</span>
      <Link
        component={RouterLink}
        to="/about"
        onClick={trackInternal('about')}
        sx={linkSx}
      >
        about
      </Link>
      <span>·</span>
      <Link
        component={RouterLink}
        to="/legal"
        onClick={trackInternal('legal')}
        sx={linkSx}
      >
        legal
      </Link>
    </Box>
  );
}
