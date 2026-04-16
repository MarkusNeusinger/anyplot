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
    color: colors.gray[800],
    '&::after': { transform: 'scaleX(1)' },
  },
} as const;

export function Footer({ onTrackEvent, selectedSpec, selectedLibrary }: FooterProps) {
  return (
    <Box component="footer" sx={{
      mt: 4,
      pt: 4,
      borderTop: `1px solid ${colors.gray[200]}`,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
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
        onClick={() => onTrackEvent?.('external_link', { destination: 'github', spec: selectedSpec, library: selectedLibrary })}
        sx={linkSx}
      >
        github
      </Link>
      <span>·</span>
      <Link
        component={RouterLink}
        to="/plots"
        onClick={() => onTrackEvent?.('internal_link', { destination: 'plots', spec: selectedSpec, library: selectedLibrary })}
        sx={linkSx}
      >
        plots
      </Link>
      <span>·</span>
      <Link
        component={RouterLink}
        to="/stats"
        onClick={() => onTrackEvent?.('internal_link', { destination: 'stats', spec: selectedSpec, library: selectedLibrary })}
        sx={linkSx}
      >
        stats
      </Link>
      <Box component="span" sx={{ display: { xs: 'none', md: 'contents' } }}>
        <span>·</span>
        <Link
          href="https://www.linkedin.com/in/markus-neusinger/"
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => onTrackEvent?.('external_link', { destination: 'linkedin', spec: selectedSpec, library: selectedLibrary })}
          sx={linkSx}
        >
          markus neusinger
        </Link>
      </Box>
      <span>·</span>
      <Link
        component={RouterLink}
        to="/mcp"
        onClick={() => onTrackEvent?.('internal_link', { destination: 'mcp', spec: selectedSpec, library: selectedLibrary })}
        sx={linkSx}
      >
        mcp
      </Link>
      <span>·</span>
      <Link
        component={RouterLink}
        to="/legal"
        onClick={() => onTrackEvent?.('internal_link', { destination: 'legal', spec: selectedSpec, library: selectedLibrary })}
        sx={linkSx}
      >
        legal
      </Link>
    </Box>
  );
}
