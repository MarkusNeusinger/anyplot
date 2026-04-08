import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import { Link as RouterLink } from 'react-router-dom';
import { GITHUB_URL } from '../constants';
import { fontSize, semanticColors } from '../theme';

interface FooterProps {
  onTrackEvent?: (name: string, props?: Record<string, string | undefined>) => void;
  selectedSpec?: string;
  selectedLibrary?: string;
}

export function Footer({ onTrackEvent, selectedSpec, selectedLibrary }: FooterProps) {
  return (
    <Box component="footer" sx={{ textAlign: 'center', mt: 4, pt: 4, borderTop: '1px solid #f3f4f6' }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 1,
          fontSize: fontSize.md,
          fontFamily: '"MonoLisa", "MonoLisa Fallback", monospace',
          color: semanticColors.mutedText,
        }}
      >
        <Link
          href={GITHUB_URL}
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => onTrackEvent?.('external_link', { destination: 'github', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: semanticColors.mutedText,
            textDecoration: 'none',
            '&:hover': { color: '#374151' },
          }}
        >
          github
        </Link>
        <span>·</span>
        <Link
          component={RouterLink}
          to="/catalog"
          onClick={() => onTrackEvent?.('internal_link', { destination: 'catalog', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: semanticColors.mutedText,
            textDecoration: 'none',
            '&:hover': { color: '#374151' },
          }}
        >
          catalog
        </Link>
        <span>·</span>
        <Link
          component={RouterLink}
          to="/stats"
          onClick={() => onTrackEvent?.('internal_link', { destination: 'stats', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: semanticColors.mutedText,
            textDecoration: 'none',
            '&:hover': { color: '#374151' },
          }}
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
            sx={{
              color: semanticColors.mutedText,
              textDecoration: 'none',
              '&:hover': { color: '#374151' },
            }}
          >
            markus neusinger
          </Link>
        </Box>
        <span>·</span>
        <Link
          component={RouterLink}
          to="/mcp"
          onClick={() => onTrackEvent?.('internal_link', { destination: 'mcp', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: semanticColors.mutedText,
            textDecoration: 'none',
            '&:hover': { color: '#374151' },
          }}
        >
          mcp
        </Link>
        <span>·</span>
        <Link
          component={RouterLink}
          to="/legal"
          onClick={() => onTrackEvent?.('internal_link', { destination: 'legal', spec: selectedSpec, library: selectedLibrary })}
          sx={{
            color: semanticColors.mutedText,
            textDecoration: 'none',
            '&:hover': { color: '#374151' },
          }}
        >
          legal
        </Link>
      </Box>
    </Box>
  );
}
